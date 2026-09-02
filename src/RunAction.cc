#include "GAGG/RunAction.hh"

#include "GAGG/DetectorConstruction.hh"
#include "GAGG/EventRecord.hh"
#include "GAGG/PrimaryGeneratorAction.hh"
#include "GAGG/SimulationConfig.hh"

#include "G4GenericMessenger.hh"
#include "G4LogicalBorderSurface.hh"
#include "G4LogicalSkinSurface.hh"
#include "G4Material.hh"
#include "G4ProcessTable.hh"
#include "G4Run.hh"
#include "G4StateManager.hh"
#include "G4UnitsTable.hh"
#include "G4ios.hh"

#include <filesystem>
#include <iomanip>
#include <algorithm>
#include <cmath>

namespace gagg {

RunAction::RunAction(PrimaryGeneratorAction* primaryGenerator,
                     const DetectorConstruction* detector)
    : fMessenger(std::make_unique<G4GenericMessenger>(
          this, "/gagg/output/", "GAGG output controls")),
      fPrimaryGenerator(primaryGenerator),
      fDetector(detector) {
  auto& csvCommand = fMessenger->DeclareProperty(
      "csv", fCsvPath, "Event-level CSV file; empty disables CSV output.");
  csvCommand.SetStates(G4State_PreInit, G4State_Idle);

  auto& annihilationCsvCommand = fMessenger->DeclareProperty(
      "annihilationCsv", fAnnihilationCsvPath,
      "One-row-per-positron-annihilation vertex CSV; empty disables it.");
  annihilationCsvCommand.SetStates(G4State_PreInit, G4State_Idle);

  auto& fateCsvCommand = fMessenger->DeclareProperty(
      "positronFateCsv", fPositronFateCsvPath,
      "One-row-per-created-positron final-fate CSV; empty disables it.");
  fateCsvCommand.SetStates(G4State_PreInit, G4State_Idle);

  auto& printCommand = fMessenger->DeclareProperty(
      "eventPrintModulo", fEventPrintModulo,
      "Print every Nth event; zero disables normal per-event printing.");
  printCommand.SetStates(G4State_PreInit, G4State_Idle);
}

RunAction::~RunAction() = default;

void RunAction::BeginOfRunAction(const G4Run*) {
  fPrimaryGenerator->ResetDirectionDiagnostics();
  fRowsWritten = 0;
  fEnergyDeposit = 0.0;
  fScintillation = 0;
  fGenerated = 0;
  fOutput = 0;
  fCrystalAbsorption = 0;
  fReflectorAbsorption = 0;
  fSurfaceAbsorption = 0;
  fTopSurfaceAbsorption = 0;
  fBottomSurfaceAbsorption = 0;
  fSideSurfaceAbsorption = 0;
  fBlackSurfaceAbsorption = 0;
  fOtherSurfaceAbsorption = 0;
  fOtherAbsorption = 0;
  fOtherWorldExit = 0;
  fLutInteractions = 0;
  fTopSurfaceInteractions = 0;
  fBottomSurfaceInteractions = 0;
  fSideSurfaceInteractions = 0;
  fUnclassified = 0;
  fPositronFates.clear();
  fRecordedAnnihilations.clear();
  fAnnihilationVertices = 0;
  fAnnihilationGammas = 0;
  fDuplicateAnnihilationRecords = 0;
  G4cout << "[config] geometry_mode=" << fDetector->GetGeometryMode()
         << " optical_model="
         << (fDetector->IsOpticalModelEnabled() ? "on" : "off")
         << " crystal_size_x="
         << G4BestUnit(fDetector->GetCrystalSizeX(), "Length")
         << " crystal_size_y="
         << G4BestUnit(fDetector->GetCrystalSizeY(), "Length")
         << " crystal_size_z="
         << G4BestUnit(fDetector->GetCrystalSizeZ(), "Length")
         << " density=" << config::kCrystalDensity / (g / cm3) << " g/cm3"
         << G4endl;
  G4cout << "[config] wavelength=" << config::kEmissionWavelength / nm
         << " nm photon_energy=" << config::EmissionPhotonEnergy() / eV
         << " eV rindex=" << config::kGaggRefractiveIndex
         << " absorption_length=" << config::kAbsorptionLength / cm << " cm"
         << G4endl;
  G4cout << "[source] particle=" << fPrimaryGenerator->GetParticleMode()
         << " energy_keV=" << fPrimaryGenerator->GetSourceEnergy() / keV
         << " mode=" << fPrimaryGenerator->GetDirectionMode()
         << " configured_optical_photons_per_event="
         << fPrimaryGenerator->GetPhotonsPerEvent()
         << " beam_radius_mm=" << fPrimaryGenerator->GetBeamRadius() / mm
         << " event_seed_base=" << fPrimaryGenerator->GetEventSeedBase()
         << " position_mm=" << fPrimaryGenerator->GetPosition() / mm
         << " source_distance_from_incident_face_mm="
         << fPrimaryGenerator->GetSourceDistance() / mm
         << G4endl;
  G4cout << "[a4-run] surface=" << fDetector->GetStageASurfaceName()
         << " model="
         << (fDetector->HasStageALutSurface() ? "LUT" : "none")
         << " real_surface_data="
         << (fDetector->GetRealSurfaceDataPath().empty()
                 ? G4String("unset")
                 : fDetector->GetRealSurfaceDataPath())
         << " data_status="
         << (fDetector->HasStageALutSurface() ? "PASS" : "SKIP")
         << " reflectivity=" << fDetector->GetStageAReflectivity()
         << " interface=" << fDetector->GetStageAInterfaceMode()
         << " air_gap_mm=" << fDetector->GetStageAAirGap() / mm
         << " output_scoring=" << fDetector->GetOutputScoringMode()
         << G4endl;
  G4cout << "[a5-run] scintillation_yield_photons_per_MeV="
         << config::kScintillationYield * MeV
         << " time_constant_ns="
         << fDetector->GetScintillationTimeConstant() / ns
         << " cerenkov=off" << G4endl;
  G4cout << "[a6-run] em_physics=G4EmStandardPhysics"
         << " gamma_energy_keV=" << config::kStageAGammaEnergy / keV
         << " gamma_source_z_mm=" << config::kStageAGammaSourceZ / mm
         << " direction=minus_z" << G4endl;
  G4cout << "[b1-run] surface_state="
         << fDetector->GetStageBSurfaceState()
         << " sigma_alpha_rad=" << fDetector->GetStageBSigmaAlpha() / rad
         << G4endl;

  if (!fDetector->IsOpticalModelEnabled()) {
    const auto* processNames =
        G4ProcessTable::GetProcessTable()->GetNameList();
    const auto hasProcess = [processNames](const G4String& name) {
      return processNames != nullptr &&
             std::find(processNames->begin(), processNames->end(), name) !=
                 processNames->end();
    };
    const auto opticalProcessPresent =
        hasProcess("Scintillation") || hasProcess("Cerenkov") ||
        hasProcess("OpAbsorption") || hasProcess("OpBoundary") ||
        hasProcess("OpRayleigh") || hasProcess("OpWLS") ||
        hasProcess("OpWLS2");
    const auto* gagg = G4Material::GetMaterial("GAGG_Ce", false);
    const auto gaggMptAbsent =
        gagg != nullptr && gagg->GetMaterialPropertiesTable() == nullptr;
    const auto borderCount = G4LogicalBorderSurface::GetNumberOfBorderSurfaces();
    const auto skinCount = G4LogicalSkinSurface::GetNumberOfSkinSurfaces();
    const auto pass = !opticalProcessPresent && gaggMptAbsent &&
                      borderCount == 0 && skinCount == 0;
    G4cout << "[na22-optical-audit] optical_processes="
           << (opticalProcessPresent ? "present" : "absent")
           << " gagg_material_properties="
           << (gaggMptAbsent ? "none" : "present")
           << " border_surfaces=" << borderCount
           << " skin_surfaces=" << skinCount
           << " status=" << (pass ? "PASS" : "FAIL") << G4endl;
  }

  if (fCsvPath.empty()) {
    // The annihilation audit has independent output controls.
  } else {
    const std::filesystem::path outputPath(fCsvPath.c_str());
    if (outputPath.has_parent_path()) {
      std::filesystem::create_directories(outputPath.parent_path());
    }
    fCsv.open(outputPath, std::ios::out | std::ios::trunc);
    if (!fCsv) {
      G4cerr << "[output] failed_to_open=" << fCsvPath << G4endl;
    } else {
      fCsv << "event_id,source_x_mm,source_y_mm,source_z_mm,source_particle,"
              "source_energy_keV,stage_a_surface,stage_b_surface_state,"
              "stage_b_sigma_alpha_rad,edep_keV,scintillation,"
              "generated,output,"
              "crystal_absorption,reflector_absorption,other_absorption,"
              "surface_absorption,top_surface_absorption,"
              "bottom_surface_absorption,side_surface_absorption,"
              "black_surface_absorption,other_surface_absorption,"
              "other_world_exit,world_exit,bulk_absorption,"
              "lut_interactions,top_surface_interactions,"
              "bottom_surface_interactions,side_surface_interactions,"
              "unclassified\n";
      G4cout << "[output] csv_open=" << fCsvPath << G4endl;
    }
  }

  if (!fAnnihilationCsvPath.empty()) {
    const std::filesystem::path outputPath(fAnnihilationCsvPath.c_str());
    if (outputPath.has_parent_path()) {
      std::filesystem::create_directories(outputPath.parent_path());
    }
    fAnnihilationCsv.open(outputPath, std::ios::out | std::ios::trunc);
    if (!fAnnihilationCsv) {
      G4cerr << "[annihilation-audit] failed_to_open="
             << fAnnihilationCsvPath << G4endl;
    } else {
      fAnnihilationCsv
          << "event_id,parent_positron_track_id,annihilation_x_mm,"
             "annihilation_y_mm,annihilation_z_mm,"
             "distance_from_Na22_source_mm,"
             "positron_energy_before_annihilation_keV,"
             "annihilation_volume,annihilation_gamma_count,"
             "source_x_mm,source_y_mm,source_z_mm,"
             "gagg_z_min_mm,gagg_z_max_mm\n";
      G4cout << "[annihilation-audit] csv_open="
             << fAnnihilationCsvPath << G4endl;
    }
  }
}

void RunAction::EndOfRunAction(const G4Run* run) {
  if (fCsv.is_open()) {
    fCsv.close();
    G4cout << "[output] csv=" << fCsvPath << " rows=" << fRowsWritten
           << G4endl;
  }
  if (fAnnihilationCsv.is_open()) {
    fAnnihilationCsv.close();
    G4cout << "[annihilation-audit] csv=" << fAnnihilationCsvPath
           << " rows=" << fAnnihilationVertices << G4endl;
  }

  std::int64_t annihilated = 0;
  std::int64_t worldExits = 0;
  std::int64_t otherTerminated = 0;
  std::int64_t unresolved = 0;
  for (const auto& entry : fPositronFates) {
    const auto& fate = entry.second.fate;
    annihilated += fate == "annihilated";
    worldExits += fate == "world_exit";
    otherTerminated += fate == "other_terminated";
    unresolved += fate == "unresolved";
  }

  if (!fPositronFateCsvPath.empty()) {
    const std::filesystem::path outputPath(fPositronFateCsvPath.c_str());
    if (outputPath.has_parent_path()) {
      std::filesystem::create_directories(outputPath.parent_path());
    }
    std::ofstream fateCsv(outputPath, std::ios::out | std::ios::trunc);
    if (!fateCsv) {
      G4cerr << "[annihilation-audit] failed_to_open="
             << fPositronFateCsvPath << G4endl;
    } else {
      fateCsv
          << "event_id,positron_track_id,creator_process,vertex_x_mm,"
             "vertex_y_mm,vertex_z_mm,fate,terminal_x_mm,terminal_y_mm,"
             "terminal_z_mm,terminal_kinetic_energy_keV,terminal_volume,"
             "source_x_mm,source_y_mm,source_z_mm\n";
      fateCsv << std::setprecision(12);
      for (const auto& entry : fPositronFates) {
        const auto& fate = entry.second;
        fateCsv << fate.eventId << ',' << fate.trackId << ','
                << fate.creatorProcess << ','
                << fate.vertexPosition.x() / mm << ','
                << fate.vertexPosition.y() / mm << ','
                << fate.vertexPosition.z() / mm << ',' << fate.fate << ','
                << fate.terminalPosition.x() / mm << ','
                << fate.terminalPosition.y() / mm << ','
                << fate.terminalPosition.z() / mm << ','
                << fate.terminalKineticEnergy / keV << ','
                << fate.terminalVolume << ','
                << fate.sourcePosition.x() / mm << ','
                << fate.sourcePosition.y() / mm << ','
                << fate.sourcePosition.z() / mm << '\n';
      }
      G4cout << "[annihilation-audit] fate_csv=" << fPositronFateCsvPath
             << " rows=" << fPositronFates.size() << G4endl;
    }
  }

  if (!fAnnihilationCsvPath.empty() || !fPositronFateCsvPath.empty()) {
    G4cout << "[annihilation-audit] positrons_created="
           << fPositronFates.size()
           << " annihilation_vertices=" << fAnnihilationVertices
           << " annihilation_gammas=" << fAnnihilationGammas
           << " duplicate_records=" << fDuplicateAnnihilationRecords
           << " world_exits=" << worldExits
           << " other_terminated=" << otherTerminated
           << " unresolved=" << unresolved
           << " fate_annihilated=" << annihilated
           << " status="
           << (unresolved == 0 &&
                       annihilated == fAnnihilationVertices &&
                       fDuplicateAnnihilationRecords == 0
                   ? "PASS"
                   : "FAIL")
           << G4endl;
  }
  const auto efficiency =
      fGenerated == 0 ? 0.0 : static_cast<G4double>(fOutput) / fGenerated;
  const auto measuredYield =
      fEnergyDeposit == 0.0
          ? 0.0
          : static_cast<G4double>(fScintillation) /
                (fEnergyDeposit / MeV);
  if (!fDetector->IsOpticalModelEnabled()) {
    G4cout << "[na22-run] edep_gagg_total_keV="
           << fEnergyDeposit / keV
           << " optical_model=off generated_optical_photons="
           << fGenerated
           << " event_level_edep=true status="
           << (fGenerated == 0 ? "PASS" : "FAIL") << G4endl;
  }
  G4cout << "[a3] generated=" << fGenerated << " output=" << fOutput
         << " efficiency=" << efficiency
         << " crystal_absorption=" << fCrystalAbsorption
         << " reflector_absorption=" << fReflectorAbsorption
         << " surface_absorption=" << fSurfaceAbsorption
         << " top_surface_absorption=" << fTopSurfaceAbsorption
         << " bottom_surface_absorption=" << fBottomSurfaceAbsorption
         << " side_surface_absorption=" << fSideSurfaceAbsorption
         << " black_surface_absorption=" << fBlackSurfaceAbsorption
         << " other_surface_absorption=" << fOtherSurfaceAbsorption
         << " other_absorption=" << fOtherAbsorption
         << " other_world_exit=" << fOtherWorldExit
         << " lut_interactions=" << fLutInteractions
         << " top_surface_interactions=" << fTopSurfaceInteractions
         << " bottom_surface_interactions=" << fBottomSurfaceInteractions
         << " side_surface_interactions=" << fSideSurfaceInteractions
         << " unclassified=" << fUnclassified << G4endl;
  G4cout << "[a5] edep_keV=" << fEnergyDeposit / keV
         << " scintillation=" << fScintillation
         << " generated=" << fGenerated
         << " measured_yield_photons_per_MeV=" << measuredYield
         << " expected_yield_photons_per_MeV="
         << config::kScintillationYield * MeV
         << " unclassified=" << fUnclassified << G4endl;
  G4cout << "[a4] surface=" << fDetector->GetStageASurfaceName()
         << " generated=" << fGenerated << " output=" << fOutput
         << " efficiency=" << efficiency
         << " surface_absorption=" << fSurfaceAbsorption
         << " lut_interactions=" << fLutInteractions
         << " unclassified=" << fUnclassified << G4endl;
  fPrimaryGenerator->ReportDirectionDiagnostics();
  G4cout << "[run] events=" << run->GetNumberOfEvent() << G4endl;
}

std::uint64_t RunAction::PositronKey(G4int eventId, G4int trackId) {
  return (static_cast<std::uint64_t>(static_cast<std::uint32_t>(eventId))
          << 32U) |
         static_cast<std::uint32_t>(trackId);
}

void RunAction::RecordPositronCreated(
    G4int eventId, G4int trackId, const G4String& creatorProcess,
    const G4ThreeVector& vertexPosition) {
  const auto key = PositronKey(eventId, trackId);
  auto& fate = fPositronFates[key];
  fate.eventId = eventId;
  fate.trackId = trackId;
  fate.creatorProcess = creatorProcess;
  fate.vertexPosition = vertexPosition;
  fate.sourcePosition = fPrimaryGenerator->GetEventPosition();
}

void RunAction::SetPositronFate(
    G4int eventId, G4int trackId, const G4String& fateName,
    const G4ThreeVector& position, G4double kineticEnergy,
    const G4String& volumeName) {
  const auto key = PositronKey(eventId, trackId);
  auto found = fPositronFates.find(key);
  if (found == fPositronFates.end()) {
    RecordPositronCreated(eventId, trackId, "unknown", position);
    found = fPositronFates.find(key);
  }
  auto& fate = found->second;
  fate.fate = fateName;
  fate.terminalPosition = position;
  fate.terminalKineticEnergy = kineticEnergy;
  fate.terminalVolume = volumeName;
}

void RunAction::RecordPositronAnnihilation(
    G4int eventId, G4int trackId, const G4ThreeVector& position,
    G4double kineticEnergyBefore, const G4String& volumeName,
    G4int annihilationGammaCount) {
  const auto key = PositronKey(eventId, trackId);
  if (!fRecordedAnnihilations.insert(key).second) {
    ++fDuplicateAnnihilationRecords;
    return;
  }
  SetPositronFate(eventId, trackId, "annihilated", position,
                  kineticEnergyBefore, volumeName);
  ++fAnnihilationVertices;
  fAnnihilationGammas += annihilationGammaCount;
  if (!fAnnihilationCsv.is_open()) {
    return;
  }
  const auto source = fPrimaryGenerator->GetEventPosition();
  const auto distance = (position - source).mag();
  const auto crystalCentreZ = fDetector->GetCrystalCenterZ();
  const auto crystalHalfZ = 0.5 * fDetector->GetCrystalSizeZ();
  fAnnihilationCsv << std::setprecision(12)
                   << eventId << ',' << trackId << ','
                   << position.x() / mm << ',' << position.y() / mm << ','
                   << position.z() / mm << ',' << distance / mm << ','
                   << kineticEnergyBefore / keV << ',' << volumeName << ','
                   << annihilationGammaCount << ',' << source.x() / mm << ','
                   << source.y() / mm << ',' << source.z() / mm << ','
                   << (crystalCentreZ - crystalHalfZ) / mm << ','
                   << (crystalCentreZ + crystalHalfZ) / mm << '\n';
}

void RunAction::RecordPositronWorldExit(
    G4int eventId, G4int trackId, const G4ThreeVector& position,
    G4double kineticEnergy, const G4String& volumeName) {
  SetPositronFate(eventId, trackId, "world_exit", position, kineticEnergy,
                  volumeName);
}

void RunAction::RecordPositronOtherTermination(
    G4int eventId, G4int trackId, const G4ThreeVector& position,
    G4double kineticEnergy, const G4String& volumeName) {
  SetPositronFate(eventId, trackId, "other_terminated", position,
                  kineticEnergy, volumeName);
}

void RunAction::WriteEvent(const EventRecord& record) {
  fEnergyDeposit += record.energyDeposit;
  fScintillation += record.scintillation;
  fGenerated += record.generated;
  fOutput += record.output;
  fCrystalAbsorption += record.crystalAbsorption;
  fReflectorAbsorption += record.reflectorAbsorption;
  fSurfaceAbsorption += record.surfaceAbsorption;
  fTopSurfaceAbsorption += record.topSurfaceAbsorption;
  fBottomSurfaceAbsorption += record.bottomSurfaceAbsorption;
  fSideSurfaceAbsorption += record.sideSurfaceAbsorption;
  fBlackSurfaceAbsorption += record.blackSurfaceAbsorption;
  fOtherSurfaceAbsorption += record.otherSurfaceAbsorption;
  fOtherAbsorption += record.otherAbsorption;
  fOtherWorldExit += record.otherWorldExit;
  fLutInteractions += record.lutInteractions;
  fTopSurfaceInteractions += record.topSurfaceInteractions;
  fBottomSurfaceInteractions += record.bottomSurfaceInteractions;
  fSideSurfaceInteractions += record.sideSurfaceInteractions;
  fUnclassified += record.unclassified;

  if (fCsv.is_open()) {
    fCsv << record.eventId << ',' << std::setprecision(10)
         << record.sourcePosition.x() / mm << ','
         << record.sourcePosition.y() / mm << ','
         << record.sourcePosition.z() / mm << ','
         << fPrimaryGenerator->GetParticleMode() << ','
         << fPrimaryGenerator->GetSourceEnergy() / keV << ','
         << fDetector->GetStageASurfaceName() << ','
         << fDetector->GetStageBSurfaceState() << ','
         << fDetector->GetStageBSigmaAlpha() / rad << ','
         << record.energyDeposit / keV << ',' << record.scintillation << ','
         << record.generated << ',' << record.output << ','
         << record.crystalAbsorption << ','
         << record.reflectorAbsorption << ',' << record.otherAbsorption << ','
         << record.surfaceAbsorption << ','
         << record.topSurfaceAbsorption << ','
         << record.bottomSurfaceAbsorption << ','
         << record.sideSurfaceAbsorption << ','
         << record.blackSurfaceAbsorption << ','
         << record.otherSurfaceAbsorption << ','
         << record.otherWorldExit << ','
         << record.WorldExit() << ',' << record.BulkAbsorption() << ','
         << record.lutInteractions << ','
         << record.topSurfaceInteractions << ','
         << record.bottomSurfaceInteractions << ','
         << record.sideSurfaceInteractions << ','
         << record.unclassified << '\n';
    ++fRowsWritten;
  }
}

G4bool RunAction::ShouldPrintEvent(G4int eventId) const {
  return fEventPrintModulo > 0 && eventId % fEventPrintModulo == 0;
}

}  // namespace gagg
