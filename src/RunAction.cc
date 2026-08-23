#include "GAGG/RunAction.hh"

#include "GAGG/SimulationConfig.hh"

#include "G4GenericMessenger.hh"
#include "G4Run.hh"
#include "G4StateManager.hh"
#include "G4UnitsTable.hh"
#include "G4ios.hh"

#include <filesystem>

namespace gagg {

RunAction::RunAction()
    : fMessenger(std::make_unique<G4GenericMessenger>(
          this, "/gagg/output/", "GAGG output controls")) {
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
  fRowsWritten = 0;
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
  fCsv << "event_id,generated,world_exit,bulk_absorption,unclassified\n";
  G4cout << "[output] csv_open=" << fCsvPath << G4endl;
}

void RunAction::EndOfRunAction(const G4Run* run) {
  if (fCsv.is_open()) {
    fCsv.close();
    G4cout << "[output] csv=" << fCsvPath << " rows=" << fRowsWritten
           << G4endl;
  }
  G4cout << "[run] events=" << run->GetNumberOfEvent() << G4endl;
}

void RunAction::WriteEvent(G4int eventId, G4int generated, G4int worldExit,
                           G4int bulkAbsorption, G4int unclassified) {
  if (!fCsv.is_open()) {
    return;
  }
  fCsv << eventId << ',' << generated << ',' << worldExit << ','
       << bulkAbsorption << ',' << unclassified << '\n';
  ++fRowsWritten;
}

G4bool RunAction::ShouldPrintEvent(G4int eventId) const {
  return fEventPrintModulo > 0 && eventId % fEventPrintModulo == 0;
}

}  // namespace gagg
