#include "GAGG/RunAction.hh"

#include "GAGG/DetectorConstruction.hh"
#include "GAGG/EventRecord.hh"
#include "GAGG/PrimaryGeneratorAction.hh"
#include "GAGG/SimulationConfig.hh"

#include "G4GenericMessenger.hh"
#include "G4Run.hh"
#include "G4StateManager.hh"
#include "G4UnitsTable.hh"
#include "G4ios.hh"

#include <filesystem>
#include <iomanip>

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
  G4cout << "[config] geometry_mode=" << fDetector->GetGeometryMode()
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

  if (fCsvPath.empty()) {
    return;
  }

  const std::filesystem::path outputPath(fCsvPath.c_str());
  if (outputPath.has_parent_path()) {
    std::filesystem::create_directories(outputPath.parent_path());
  }
  fCsv.open(outputPath, std::ios::out | std::ios::trunc);
  if (!fCsv) {
    G4cerr << "[output] failed_to_open=" << fCsvPath << G4endl;
    return;
  }
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

void RunAction::EndOfRunAction(const G4Run* run) {
  if (fCsv.is_open()) {
    fCsv.close();
    G4cout << "[output] csv=" << fCsvPath << " rows=" << fRowsWritten
           << G4endl;
  }
  const auto efficiency =
      fGenerated == 0 ? 0.0 : static_cast<G4double>(fOutput) / fGenerated;
  const auto measuredYield =
      fEnergyDeposit == 0.0
          ? 0.0
          : static_cast<G4double>(fScintillation) /
                (fEnergyDeposit / MeV);
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
