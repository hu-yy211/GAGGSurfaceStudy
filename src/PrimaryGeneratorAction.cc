#include "GAGG/PrimaryGeneratorAction.hh"

#include "GAGG/SimulationConfig.hh"

#include "G4Exception.hh"
#include "G4Electron.hh"
#include "G4Event.hh"
#include "G4Gamma.hh"
#include "G4GenericMessenger.hh"
#include "G4OpticalPhoton.hh"
#include "G4ParticleGun.hh"
#include "G4PhysicalConstants.hh"
#include "G4PrimaryParticle.hh"
#include "G4PrimaryVertex.hh"
#include "G4StateManager.hh"
#include "G4UIcmdWith3VectorAndUnit.hh"
#include "G4ios.hh"
#include "Randomize.hh"

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <iomanip>

namespace gagg {

PrimaryGeneratorAction::PrimaryGeneratorAction()
    : fMessenger(std::make_unique<G4GenericMessenger>(
          this, "/gagg/source/", "Primary source controls")),
      fParticleGun(std::make_unique<G4ParticleGun>(1)) {
  auto& particleCommand = fMessenger->DeclareMethod(
      "particle", &PrimaryGeneratorAction::SetParticleMode,
      "Select optical primaries, one electron, one gamma, or an effective "
      "two-gamma annihilation pair per event.");
  particleCommand.SetParameterName("particle", false);
  particleCommand.SetCandidates("optical electron gamma annihilationPair");
  particleCommand.SetDefaultValue("optical");
  particleCommand.SetStates(G4State_PreInit, G4State_Idle);

  auto& modeCommand = fMessenger->DeclareMethod(
      "mode", &PrimaryGeneratorAction::SetDirectionMode,
      "Select fixed +z or isotropic photon directions.");
  modeCommand.SetParameterName("mode", false);
  modeCommand.SetCandidates("fixed isotropic");
  modeCommand.SetDefaultValue("fixed");
  modeCommand.SetStates(G4State_PreInit, G4State_Idle);

  auto& countCommand = fMessenger->DeclareMethod(
      "photonsPerEvent", &PrimaryGeneratorAction::SetPhotonsPerEvent,
      "Set the fixed number of optical photons generated per event.");
  countCommand.SetParameterName("count", false);
  countCommand.SetStates(G4State_PreInit, G4State_Idle);

  auto& energyCommand = fMessenger->DeclareMethodWithUnit(
      "kineticEnergy", "keV", &PrimaryGeneratorAction::SetKineticEnergy,
      "Set the kinetic energy of the controlled electron or gamma source.");
  energyCommand.SetParameterName("energy", false);
  energyCommand.SetRange("energy>0.");
  energyCommand.SetDefaultValue("20.");
  energyCommand.SetStates(G4State_PreInit, G4State_Idle);

  auto& beamRadiusCommand = fMessenger->DeclareMethodWithUnit(
      "beamRadius", "mm", &PrimaryGeneratorAction::SetBeamRadius,
      "Set the radius of a uniform circular parallel gamma beam; zero "
      "selects a pencil beam.");
  beamRadiusCommand.SetParameterName("radius", false);
  beamRadiusCommand.SetRange("radius>=0.");
  beamRadiusCommand.SetDefaultValue("0.");
  beamRadiusCommand.SetStates(G4State_PreInit, G4State_Idle);

  auto& faceSizeCommand = fMessenger->DeclareMethodWithUnit(
      "faceSize", "mm", &PrimaryGeneratorAction::SetFaceSize,
      "Set the side length of a uniform square gamma-source face; zero "
      "keeps the existing point/circular-beam source.");
  faceSizeCommand.SetParameterName("size", false);
  faceSizeCommand.SetRange("size>=0.");
  faceSizeCommand.SetDefaultValue("0.");
  faceSizeCommand.SetStates(G4State_PreInit, G4State_Idle);

  auto& eventSeedCommand = fMessenger->DeclareMethod(
      "eventSeedBase", &PrimaryGeneratorAction::SetEventSeedBase,
      "Set a positive deterministic per-event seed base; zero keeps the "
      "run-level random stream.");
  eventSeedCommand.SetParameterName("seed", false);
  eventSeedCommand.SetRange("seed>=0");
  eventSeedCommand.SetDefaultValue("0");
  eventSeedCommand.SetStates(G4State_PreInit, G4State_Idle);

  auto& sourceAuditCommand = fMessenger->DeclareProperty(
      "auditCsv", fSourceAuditCsvPath,
      "Optional B7 source-only CSV containing generated positions, "
      "energies, and directions.");
  sourceAuditCommand.SetStates(G4State_PreInit, G4State_Idle);

  fPositionCommand = std::make_unique<G4UIcmdWith3VectorAndUnit>(
      "/gagg/source/position", this);
  fPositionCommand->SetGuidance(
      "Set the source centre; face sampling, when enabled, is relative to it.");
  fPositionCommand->SetParameterName("x", "y", "z", false, false);
  fPositionCommand->SetDefaultUnit("mm");
  fPositionCommand->SetUnitCandidates("nm um mm cm m");
  fPositionCommand->AvailableForStates(G4State_PreInit, G4State_Idle);

  fParticleGun->SetParticleDefinition(G4OpticalPhoton::Definition());
  fParticleGun->SetParticleEnergy(config::EmissionPhotonEnergy());
  fParticleGun->SetParticleMomentumDirection({0.0, 0.0, 1.0});
  fParticleGun->SetParticlePolarization({1.0, 0.0, 0.0});
}

PrimaryGeneratorAction::~PrimaryGeneratorAction() {
  if (fSourceAuditCsv.is_open()) {
    fSourceAuditCsv.close();
    G4cout << "[b7.2-source] audit_csv=" << fSourceAuditCsvPath
           << " rows=" << fSourceAuditRows << G4endl;
  }
}

void PrimaryGeneratorAction::GeneratePrimaries(G4Event* event) {
  if (fEventSeedBase > 0) {
    const auto eventId = static_cast<G4long>(event->GetEventID());
    // CLHEP::HepRandom documents a zero-terminated seed list, while the active
    // MixMaxRng also accepts an explicit number of supplied seeds. Satisfy both
    // contracts so deterministic event seeding is engine-explicit.
    G4long seeds[3] = {fEventSeedBase + 104729 * eventId,
                       fEventSeedBase + 130363 * eventId + 1, 0};
    // This hardens the seed interface; B2 process isolation separately handles
    // the observed same-process rough-surface run-history effect.
    G4Random::setTheSeeds(seeds, 2);
  }
  ValidateConfiguration();
  fEventPosition = fPosition;
  const auto gammaLike =
      fParticleMode == "gamma" || fParticleMode == "annihilationPair";
  if (gammaLike && fFaceSize > 0.0) {
    fEventPosition +=
        G4ThreeVector(fFaceSize * (G4UniformRand() - 0.5),
                      fFaceSize * (G4UniformRand() - 0.5), 0.0);
  } else if (gammaLike && fBeamRadius > 0.0) {
    const auto radius = fBeamRadius * std::sqrt(G4UniformRand());
    const auto phi = twopi * G4UniformRand();
    fEventPosition +=
        G4ThreeVector(radius * std::cos(phi), radius * std::sin(phi), 0.0);
  }
  fParticleGun->SetParticlePosition(fEventPosition);
  if (fParticleMode == "annihilationPair") {
    GenerateAnnihilationPair(event);
    return;
  }
  if (fParticleMode == "electron") {
    fParticleGun->SetParticleDefinition(G4Electron::Definition());
    fParticleGun->SetParticleEnergy(fKineticEnergy);
    fParticleGun->SetParticleMomentumDirection({0.0, 0.0, 1.0});
    fParticleGun->GeneratePrimaryVertex(event);
    return;
  }

  if (fParticleMode == "gamma") {
    fParticleGun->SetParticleDefinition(G4Gamma::Definition());
    fParticleGun->SetParticleEnergy(fKineticEnergy);
    fParticleGun->SetParticleMomentumDirection({0.0, 0.0, -1.0});
    fParticleGun->GeneratePrimaryVertex(event);
    return;
  }

  fParticleGun->SetParticleDefinition(G4OpticalPhoton::Definition());
  fParticleGun->SetParticleEnergy(config::EmissionPhotonEnergy());
  for (G4int photon = 0; photon < fPhotonsPerEvent; ++photon) {
    if (fDirectionMode == "isotropic") {
      ConfigureIsotropicPhoton();
    } else {
      fParticleGun->SetParticleMomentumDirection({0.0, 0.0, 1.0});
      fParticleGun->SetParticlePolarization({1.0, 0.0, 0.0});
    }
    fParticleGun->GeneratePrimaryVertex(event);
  }
}

void PrimaryGeneratorAction::SetNewValue(G4UIcommand* command,
                                         G4String value) {
  if (command == fPositionCommand.get()) {
    SetPosition(fPositionCommand->GetNew3VectorValue(value));
  }
}

void PrimaryGeneratorAction::SetDirectionMode(const G4String& mode) {
  fDirectionMode = mode;
}

void PrimaryGeneratorAction::SetParticleMode(const G4String& particle) {
  fParticleMode = particle;
}

void PrimaryGeneratorAction::SetKineticEnergy(G4double energy) {
  if (energy <= 0.0) {
    G4Exception("PrimaryGeneratorAction::SetKineticEnergy", "GAGG-A5-001",
                FatalException, "kineticEnergy must be positive");
  }
  fKineticEnergy = energy;
}

void PrimaryGeneratorAction::SetBeamRadius(G4double radius) {
  if (radius < 0.0) {
    G4Exception("PrimaryGeneratorAction::SetBeamRadius", "GAGG-A7-001",
                FatalException, "beamRadius must be non-negative");
  }
  fBeamRadius = radius;
}

void PrimaryGeneratorAction::SetFaceSize(G4double size) {
  if (size < 0.0) {
    G4Exception("PrimaryGeneratorAction::SetFaceSize", "GAGG-B7-001",
                FatalException, "faceSize must be non-negative");
  }
  fFaceSize = size;
}

void PrimaryGeneratorAction::SetEventSeedBase(G4long seed) {
  if (seed < 0) {
    G4Exception("PrimaryGeneratorAction::SetEventSeedBase", "GAGG-A7-002",
                FatalException, "eventSeedBase must be non-negative");
  }
  fEventSeedBase = seed;
}

G4double PrimaryGeneratorAction::GetSourceEnergy() const {
  if (fParticleMode == "optical") {
    return config::EmissionPhotonEnergy();
  }
  return fParticleMode == "annihilationPair"
             ? config::kB7AnnihilationGammaEnergy
             : fKineticEnergy;
}

void PrimaryGeneratorAction::SetPhotonsPerEvent(G4int count) {
  if (count <= 0) {
    G4Exception("PrimaryGeneratorAction::SetPhotonsPerEvent", "GAGG-A3-001",
                FatalException, "photonsPerEvent must be positive");
  }
  fPhotonsPerEvent = count;
}

void PrimaryGeneratorAction::SetPosition(const G4ThreeVector& position) {
  fPosition = position;
}

void PrimaryGeneratorAction::ResetDirectionDiagnostics() {
  fDirectionSamples = 0;
  fDirectionSum = {};
  fDirectionSquareSum = {};
  fAnnihilationPairEvents = 0;
  fPairDirectionDotSum = 0.0;
  fPairDirectionMaxDeviation = 0.0;
}

void PrimaryGeneratorAction::ReportDirectionDiagnostics() const {
  const auto expectsIsotropy =
      (fParticleMode == "optical" && fDirectionMode == "isotropic") ||
      fParticleMode == "annihilationPair";
  if (!expectsIsotropy || fDirectionSamples == 0) {
    G4cout << "[source] isotropy status=SKIP particle=" << fParticleMode
           << " mode=" << fDirectionMode
           << G4endl;
    return;
  }

  const auto mean = fDirectionSum / fDirectionSamples;
  const auto secondMoment = fDirectionSquareSum / fDirectionSamples;
  constexpr G4double tolerance = 0.02;
  const auto pass =
      fDirectionSamples < 1000 ||
      (std::abs(mean.x()) < tolerance &&
       std::abs(mean.y()) < tolerance &&
       std::abs(mean.z()) < tolerance &&
       std::abs(secondMoment.x() - 1.0 / 3.0) < tolerance &&
       std::abs(secondMoment.y() - 1.0 / 3.0) < tolerance &&
       std::abs(secondMoment.z() - 1.0 / 3.0) < tolerance);
  const auto pairPass =
      fParticleMode != "annihilationPair" ||
      (fAnnihilationPairEvents == fDirectionSamples &&
       std::abs(fPairDirectionDotSum / fAnnihilationPairEvents + 1.0) <
           1.0e-12 &&
       fPairDirectionMaxDeviation < 1.0e-12);
  G4cout << "[source] isotropy samples=" << fDirectionSamples
         << " mean=" << mean << " second_moment=" << secondMoment
         << " pair_events=" << fAnnihilationPairEvents
         << " pair_dot_mean="
         << (fAnnihilationPairEvents == 0
                 ? 0.0
                 : fPairDirectionDotSum / fAnnihilationPairEvents)
         << " pair_dot_max_deviation=" << fPairDirectionMaxDeviation
         << " status="
         << (fDirectionSamples < 1000
                 ? "SKIP"
                 : (pass && pairPass ? "PASS" : "FAIL"))
         << G4endl;
}

void PrimaryGeneratorAction::ValidateConfiguration() const {
  const auto radialSquared = fPosition.x() * fPosition.x() +
                             fPosition.y() * fPosition.y();
  if (fParticleMode == "gamma" || fParticleMode == "annihilationPair") {
    if (fFaceSize > 0.0 && fBeamRadius > 0.0) {
      G4Exception("PrimaryGeneratorAction::ValidateConfiguration",
                  "GAGG-B7-002", FatalException,
                  "faceSize and beamRadius cannot both be non-zero");
    }
    const auto sourceHalfExtent = 0.5 * fFaceSize;
    const auto insideWorld =
        std::abs(fPosition.x()) + sourceHalfExtent <
            config::kWorldHalfLength &&
        std::abs(fPosition.y()) + sourceHalfExtent <
            config::kWorldHalfLength &&
        std::abs(fPosition.z()) < config::kWorldHalfLength;
    const auto beamCenterRadius = std::sqrt(radialSquared);
    const auto squareCornerRadius = std::sqrt(2.0) * sourceHalfExtent;
    const auto transverseExtent =
        fFaceSize > 0.0 ? squareCornerRadius : fBeamRadius;
    const auto aimedAtCrystal =
        beamCenterRadius + transverseExtent <= config::kCrystalRadius;
    const auto abovePaperGeometry =
        fPosition.z() >= config::kStageAGammaSourceZ;
    const auto pairConfigurationPass =
        fParticleMode != "annihilationPair" ||
        (fDirectionMode == "isotropic" && fFaceSize > 0.0 &&
         fBeamRadius == 0.0);
    const auto gammaConfigurationPass =
        fParticleMode != "gamma" || fDirectionMode == "fixed";
    if (!pairConfigurationPass || !gammaConfigurationPass || !insideWorld ||
        !aimedAtCrystal || !abovePaperGeometry) {
      G4Exception("PrimaryGeneratorAction::ValidateConfiguration",
                  "GAGG-B7-003", FatalException,
                  "A gamma source must start inside the world above the "
                  "geometry and fit within the crystal projection; the B7 "
                  "annihilationPair additionally requires isotropic mode, "
                  "non-zero faceSize, and zero beamRadius");
    }
    return;
  }

  const auto insideRadius =
      radialSquared < config::kCrystalRadius * config::kCrystalRadius;
  const auto insideLength =
      std::abs(fPosition.z()) < 0.5 * config::kCrystalLength;
  if (!insideRadius || !insideLength) {
    G4Exception("PrimaryGeneratorAction::ValidateConfiguration",
                "GAGG-A3-002", FatalException,
                "The optical-photon source position must be inside GAGG");
  }
}

void PrimaryGeneratorAction::GenerateAnnihilationPair(G4Event* event) {
  const auto firstDirection = SampleIsotropicDirection();
  const auto secondDirection = -firstDirection;
  RecordDirectionSample(firstDirection);
  ++fAnnihilationPairEvents;
  const auto directionDot = firstDirection.dot(secondDirection);
  fPairDirectionDotSum += directionDot;
  fPairDirectionMaxDeviation =
      std::max(fPairDirectionMaxDeviation, std::abs(directionDot + 1.0));

  auto* vertex = new G4PrimaryVertex(fEventPosition, 0.0);
  auto* firstGamma = new G4PrimaryParticle(G4Gamma::Definition());
  firstGamma->SetKineticEnergy(config::kB7AnnihilationGammaEnergy);
  firstGamma->SetMomentumDirection(firstDirection);
  vertex->SetPrimary(firstGamma);
  auto* secondGamma = new G4PrimaryParticle(G4Gamma::Definition());
  secondGamma->SetKineticEnergy(config::kB7AnnihilationGammaEnergy);
  secondGamma->SetMomentumDirection(secondDirection);
  vertex->SetPrimary(secondGamma);
  event->AddPrimaryVertex(vertex);

  if (event->GetNumberOfPrimaryVertex() != 1 ||
      vertex->GetNumberOfParticle() != 2) {
    G4Exception("PrimaryGeneratorAction::GenerateAnnihilationPair",
                "GAGG-B7-004", FatalException,
                "B7 annihilationPair must create two gammas at one vertex");
  }
  WriteSourceAudit(event->GetEventID(), firstDirection, secondDirection);
  if (event->GetEventID() == 0) {
    G4cout << "[b7.2-source] particle=annihilationPair"
           << " primary_vertices=" << event->GetNumberOfPrimaryVertex()
           << " primaries=" << vertex->GetNumberOfParticle()
           << " gamma_energy_keV="
           << config::kB7AnnihilationGammaEnergy / keV
           << " position_mm=" << fEventPosition / mm
           << " direction_dot=" << directionDot << G4endl;
  }
}

G4ThreeVector PrimaryGeneratorAction::SampleIsotropicDirection() const {
  const auto cosineTheta = 2.0 * G4UniformRand() - 1.0;
  const auto sineTheta = std::sqrt(1.0 - cosineTheta * cosineTheta);
  const auto phi = twopi * G4UniformRand();
  return {sineTheta * std::cos(phi), sineTheta * std::sin(phi), cosineTheta};
}

void PrimaryGeneratorAction::RecordDirectionSample(
    const G4ThreeVector& direction) {
  ++fDirectionSamples;
  fDirectionSum += direction;
  fDirectionSquareSum +=
      {direction.x() * direction.x(), direction.y() * direction.y(),
       direction.z() * direction.z()};
}

void PrimaryGeneratorAction::WriteSourceAudit(
    G4int eventId, const G4ThreeVector& firstDirection,
    const G4ThreeVector& secondDirection) {
  if (fSourceAuditCsvPath.empty()) {
    return;
  }
  if (!fSourceAuditCsv.is_open()) {
    const std::filesystem::path outputPath(fSourceAuditCsvPath.c_str());
    if (outputPath.has_parent_path()) {
      std::filesystem::create_directories(outputPath.parent_path());
    }
    fSourceAuditCsv.open(outputPath, std::ios::out | std::ios::trunc);
    if (!fSourceAuditCsv) {
      G4Exception("PrimaryGeneratorAction::WriteSourceAudit",
                  "GAGG-B7-005", FatalException,
                  "Failed to open the B7 source audit CSV");
    }
    fSourceAuditCsv
        << "event_id,source_x_mm,source_y_mm,source_z_mm,"
           "primary_vertex_count,primary_count,gamma1_energy_keV,"
           "gamma1_dx,gamma1_dy,gamma1_dz,gamma2_energy_keV,"
           "gamma2_dx,gamma2_dy,gamma2_dz,direction_dot\n";
  }
  fSourceAuditCsv << std::setprecision(12)
                  << eventId << ',' << fEventPosition.x() / mm << ','
                  << fEventPosition.y() / mm << ','
                  << fEventPosition.z() / mm << ",1,2,"
                  << config::kB7AnnihilationGammaEnergy / keV << ','
                  << firstDirection.x() << ',' << firstDirection.y() << ','
                  << firstDirection.z() << ','
                  << config::kB7AnnihilationGammaEnergy / keV << ','
                  << secondDirection.x() << ',' << secondDirection.y() << ','
                  << secondDirection.z() << ','
                  << firstDirection.dot(secondDirection) << '\n';
  ++fSourceAuditRows;
}

void PrimaryGeneratorAction::ConfigureIsotropicPhoton() {
  const auto direction = SampleIsotropicDirection();
  RecordDirectionSample(direction);

  const auto firstTransverse = direction.orthogonal().unit();
  const auto secondTransverse = direction.cross(firstTransverse).unit();
  const auto polarizationAngle = twopi * G4UniformRand();
  const auto polarization = std::cos(polarizationAngle) * firstTransverse +
                            std::sin(polarizationAngle) * secondTransverse;
  fParticleGun->SetParticleMomentumDirection(direction);
  fParticleGun->SetParticlePolarization(polarization);
}

}  // namespace gagg
