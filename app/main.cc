#include "GAGG/DetectorConstruction.hh"
#include "GAGG/PhysicsList.hh"
#include "GAGG/PrimaryGeneratorAction.hh"
#include "GAGG/SimulationConfig.hh"

#include "G4Event.hh"
#include "G4OpticalPhoton.hh"
#include "G4Run.hh"
#include "G4RunManager.hh"
#include "G4RunManagerFactory.hh"
#include "G4Step.hh"
#include "G4SystemOfUnits.hh"
#include "G4UImanager.hh"
#include "G4UnitsTable.hh"
#include "G4UserEventAction.hh"
#include "G4UserRunAction.hh"
#include "G4UserSteppingAction.hh"
#include "G4VProcess.hh"
#include "G4ios.hh"

#include <memory>

namespace {

class EventAction final : public G4UserEventAction {
 public:
  void BeginOfEventAction(const G4Event*) override {
    fWorldExit = 0;
    fBulkAbsorption = 0;
  }

  void EndOfEventAction(const G4Event* event) override {
    const auto classified = fWorldExit + fBulkAbsorption;
    G4cout << "[event] id=" << event->GetEventID()
           << " generated=1"
           << " world_exit=" << fWorldExit
           << " bulk_absorption=" << fBulkAbsorption
           << " unclassified=" << (1 - classified) << G4endl;
  }

  void RecordWorldExit() { ++fWorldExit; }
  void RecordBulkAbsorption() { ++fBulkAbsorption; }

 private:
  G4int fWorldExit = 0;
  G4int fBulkAbsorption = 0;
};

class SteppingAction final : public G4UserSteppingAction {
 public:
  explicit SteppingAction(EventAction* eventAction)
      : fEventAction(eventAction) {}

  void UserSteppingAction(const G4Step* step) override {
    if (step->GetTrack()->GetDefinition() != G4OpticalPhoton::Definition()) {
      return;
    }
    const auto* post = step->GetPostStepPoint();
    if (post->GetStepStatus() == fWorldBoundary) {
      fEventAction->RecordWorldExit();
      return;
    }
    const auto* process = post->GetProcessDefinedStep();
    if (process != nullptr && process->GetProcessName() == "OpAbsorption") {
      fEventAction->RecordBulkAbsorption();
    }
  }

 private:
  EventAction* fEventAction;
};

class RunAction final : public G4UserRunAction {
 public:
  void BeginOfRunAction(const G4Run*) override {
    G4cout << "[config] crystal_diameter="
           << G4BestUnit(2.0 * gagg::config::kCrystalRadius, "Length")
           << " crystal_length="
           << G4BestUnit(gagg::config::kCrystalLength, "Length")
           << " density=" << gagg::config::kCrystalDensity / (g / cm3)
           << " g/cm3" << G4endl;
    G4cout << "[config] wavelength="
           << gagg::config::kEmissionWavelength / nm << " nm"
           << " photon_energy="
           << gagg::config::EmissionPhotonEnergy() / eV << " eV"
           << " rindex=" << gagg::config::kGaggRefractiveIndex
           << " absorption_length="
           << gagg::config::kAbsorptionLength / cm << " cm" << G4endl;
  }

  void EndOfRunAction(const G4Run* run) override {
    G4cout << "[run] events=" << run->GetNumberOfEvent() << G4endl;
  }
};

}  // namespace

int main(int argc, char** argv) {
  if (argc != 2) {
    G4cerr << "Usage: " << argv[0] << " <macro-file>" << G4endl;
    return 2;
  }

  auto runManager =
      std::unique_ptr<G4RunManager>(G4RunManagerFactory::CreateRunManager(
          G4RunManagerType::SerialOnly));
  runManager->SetUserInitialization(new gagg::DetectorConstruction());
  runManager->SetUserInitialization(new gagg::PhysicsList());
  runManager->SetUserAction(new gagg::PrimaryGeneratorAction());
  runManager->SetUserAction(new RunAction());
  auto* eventAction = new EventAction();
  runManager->SetUserAction(eventAction);
  runManager->SetUserAction(new SteppingAction(eventAction));

  const auto status = G4UImanager::GetUIpointer()->ApplyCommand(
      G4String("/control/execute ") + G4String(argv[1]));
  if (status != 0) {
    G4cerr << "[smoke] macro failed with status " << status << G4endl;
    return 3;
  }
  G4cout << "[smoke] run completed" << G4endl;
  return 0;
}

