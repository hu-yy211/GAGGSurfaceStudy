#include "GAGG/PrimaryGeneratorAction.hh"

#include "GAGG/SimulationConfig.hh"

#include "G4Exception.hh"
#include "G4Electron.hh"
#include "G4GenericMessenger.hh"
#include "G4OpticalPhoton.hh"
#include "G4ParticleGun.hh"
#include "G4PhysicalConstants.hh"
#include "G4StateManager.hh"
#include "G4UIcmdWith3VectorAndUnit.hh"
#include "G4ios.hh"
#include "Randomize.hh"

#include <cmath>

namespace gagg {

PrimaryGeneratorAction::PrimaryGeneratorAction()
    : fMessenger(std::make_unique<G4GenericMessenger>(
          this, "/gagg/source/", "Primary source controls")),
      fParticleGun(std::make_unique<G4ParticleGun>(1)) {
  auto& particleCommand = fMessenger->DeclareMethod(
      "particle", &PrimaryGeneratorAction::SetParticleMode,
      "Select optical primaries or one controlled electron per event.");
  particleCommand.SetParameterName("particle", false);
  particleCommand.SetCandidates("optical electron");
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
      "Set the kinetic energy of the controlled electron source.");
  energyCommand.SetParameterName("energy", false);
  energyCommand.SetRange("energy>0.");
  energyCommand.SetDefaultValue("20.");
  energyCommand.SetStates(G4State_PreInit, G4State_Idle);

  fPositionCommand = std::make_unique<G4UIcmdWith3VectorAndUnit>(
      "/gagg/source/position", this);
  fPositionCommand->SetGuidance(
      "Set the common optical-photon source position.");
  fPositionCommand->SetParameterName("x", "y", "z", false, false);
  fPositionCommand->SetDefaultUnit("mm");
  fPositionCommand->SetUnitCandidates("nm um mm cm m");
  fPositionCommand->AvailableForStates(G4State_PreInit, G4State_Idle);

  fParticleGun->SetParticleDefinition(G4OpticalPhoton::Definition());
  fParticleGun->SetParticleEnergy(config::EmissionPhotonEnergy());
  fParticleGun->SetParticleMomentumDirection({0.0, 0.0, 1.0});
  fParticleGun->SetParticlePolarization({1.0, 0.0, 0.0});
}

PrimaryGeneratorAction::~PrimaryGeneratorAction() = default;

void PrimaryGeneratorAction::GeneratePrimaries(G4Event* event) {
  ValidateConfiguration();
  fParticleGun->SetParticlePosition(fPosition);
  if (fParticleMode == "electron") {
    fParticleGun->SetParticleDefinition(G4Electron::Definition());
    fParticleGun->SetParticleEnergy(fKineticEnergy);
    fParticleGun->SetParticleMomentumDirection({0.0, 0.0, 1.0});
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

G4double PrimaryGeneratorAction::GetSourceEnergy() const {
  return fParticleMode == "optical" ? config::EmissionPhotonEnergy()
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
}

void PrimaryGeneratorAction::ReportDirectionDiagnostics() const {
  if (fParticleMode != "optical" || fDirectionMode != "isotropic" ||
      fDirectionSamples == 0) {
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
  G4cout << "[source] isotropy samples=" << fDirectionSamples
         << " mean=" << mean << " second_moment=" << secondMoment
         << " status="
         << (fDirectionSamples < 1000 ? "SKIP" : (pass ? "PASS" : "FAIL"))
         << G4endl;
}

void PrimaryGeneratorAction::ValidateConfiguration() const {
  const auto radialSquared = fPosition.x() * fPosition.x() +
                             fPosition.y() * fPosition.y();
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

void PrimaryGeneratorAction::ConfigureIsotropicPhoton() {
  const auto cosineTheta = 2.0 * G4UniformRand() - 1.0;
  const auto sineTheta = std::sqrt(1.0 - cosineTheta * cosineTheta);
  const auto phi = twopi * G4UniformRand();
  const G4ThreeVector direction(sineTheta * std::cos(phi),
                                sineTheta * std::sin(phi), cosineTheta);
  ++fDirectionSamples;
  fDirectionSum += direction;
  fDirectionSquareSum +=
      {direction.x() * direction.x(), direction.y() * direction.y(),
       direction.z() * direction.z()};

  const auto firstTransverse = direction.orthogonal().unit();
  const auto secondTransverse = direction.cross(firstTransverse).unit();
  const auto polarizationAngle = twopi * G4UniformRand();
  const auto polarization = std::cos(polarizationAngle) * firstTransverse +
                            std::sin(polarizationAngle) * secondTransverse;
  fParticleGun->SetParticleMomentumDirection(direction);
  fParticleGun->SetParticlePolarization(polarization);
}

}  // namespace gagg
