#include "GAGG/RunAction.hh"

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

RunAction::RunAction(PrimaryGeneratorAction* primaryGenerator)
    : fMessenger(std::make_unique<G4GenericMessenger>(
          this, "/gagg/output/", "GAGG output controls")),
      fPrimaryGenerator(primaryGenerator) {
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
  fGenerated = 0;
  fOutput = 0;
  fCrystalAbsorption = 0;
  fReflectorAbsorption = 0;
  fOtherAbsorption = 0;
  fOtherWorldExit = 0;
  fUnclassified = 0;
  G4cout << "[config] crystal_diameter="
         << G4BestUnit(2.0 * config::kCrystalRadius, "Length")
         << " crystal_length=" << G4BestUnit(config::kCrystalLength, "Length")
         << " density=" << config::kCrystalDensity / (g / cm3) << " g/cm3"
         << G4endl;
  G4cout << "[config] wavelength=" << config::kEmissionWavelength / nm
         << " nm photon_energy=" << config::EmissionPhotonEnergy() / eV
         << " eV rindex=" << config::kGaggRefractiveIndex
         << " absorption_length=" << config::kAbsorptionLength / cm << " cm"
         << G4endl;
  G4cout << "[source] mode=" << fPrimaryGenerator->GetDirectionMode()
         << " photons_per_event="
         << fPrimaryGenerator->GetPhotonsPerEvent()
         << " position_mm=" << fPrimaryGenerator->GetPosition() / mm
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
  fCsv << "event_id,source_x_mm,source_y_mm,source_z_mm,generated,output,"
          "crystal_absorption,reflector_absorption,other_absorption,"
          "other_world_exit,world_exit,bulk_absorption,unclassified\n";
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
  G4cout << "[a3] generated=" << fGenerated << " output=" << fOutput
         << " efficiency=" << efficiency
         << " crystal_absorption=" << fCrystalAbsorption
         << " reflector_absorption=" << fReflectorAbsorption
         << " other_absorption=" << fOtherAbsorption
         << " other_world_exit=" << fOtherWorldExit
         << " unclassified=" << fUnclassified << G4endl;
  fPrimaryGenerator->ReportDirectionDiagnostics();
  G4cout << "[run] events=" << run->GetNumberOfEvent() << G4endl;
}

void RunAction::WriteEvent(const EventRecord& record) {
  fGenerated += record.generated;
  fOutput += record.output;
  fCrystalAbsorption += record.crystalAbsorption;
  fReflectorAbsorption += record.reflectorAbsorption;
  fOtherAbsorption += record.otherAbsorption;
  fOtherWorldExit += record.otherWorldExit;
  fUnclassified += record.unclassified;

  if (fCsv.is_open()) {
    fCsv << record.eventId << ',' << std::setprecision(10)
         << record.sourcePosition.x() / mm << ','
         << record.sourcePosition.y() / mm << ','
         << record.sourcePosition.z() / mm << ',' << record.generated << ','
         << record.output << ',' << record.crystalAbsorption << ','
         << record.reflectorAbsorption << ',' << record.otherAbsorption << ','
         << record.otherWorldExit << ',' << record.WorldExit() << ','
         << record.BulkAbsorption() << ',' << record.unclassified << '\n';
    ++fRowsWritten;
  }
}

G4bool RunAction::ShouldPrintEvent(G4int eventId) const {
  return fEventPrintModulo > 0 && eventId % fEventPrintModulo == 0;
}

}  // namespace gagg
