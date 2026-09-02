#include "GAGG/DetectorConstruction.hh"
#include "GAGG/EventAction.hh"
#include "GAGG/MaterialValidation.hh"
#include "GAGG/PhysicsList.hh"
#include "GAGG/PrimaryGeneratorAction.hh"
#include "GAGG/RunAction.hh"
#include "GAGG/StackingAction.hh"
#include "GAGG/SteppingAction.hh"

#include "G4RunManager.hh"
#include "G4RunManagerFactory.hh"
#include "G4UIExecutive.hh"
#include "G4UImanager.hh"
#include "G4VisExecutive.hh"
#include "G4ios.hh"
#include "Randomize.hh"

#include <memory>

namespace {

void PrintUsage(const char* executable) {
  G4cerr << "Usage:\n"
         << "  " << executable << " <macro-file>\n"
         << "  " << executable << " --interactive <visualization-macro>\n"
         << "  " << executable << " --decay-only <macro-file>\n"
         << "  " << executable
         << " --decay-only-interactive <visualization-macro>\n"
         << "  " << executable << " --validate-materials" << G4endl;
}

}  // namespace

int main(int argc, char** argv) {
  if (argc == 2 && G4String(argv[1]) == "--validate-materials") {
    return gagg::RunMaterialValidation();
  }

  const auto option = argc >= 2 ? G4String(argv[1]) : G4String();
  const auto interactive =
      argc == 3 &&
      (option == "--interactive" || option == "--decay-only-interactive");
  const auto decayOnly =
      argc == 3 &&
      (option == "--decay-only" || option == "--decay-only-interactive");
  const auto standardBatch = argc == 2;
  if (!standardBatch && !interactive && !decayOnly) {
    PrintUsage(argv[0]);
    return 2;
  }
  const G4String macro = (interactive || decayOnly) ? argv[2] : argv[1];

  std::unique_ptr<G4UIExecutive> ui;
  if (interactive) {
    ui = std::make_unique<G4UIExecutive>(1, argv);
  }

  auto runManager =
      std::unique_ptr<G4RunManager>(G4RunManagerFactory::CreateRunManager(
          G4RunManagerType::SerialOnly));
  G4cout << "[random] engine=" << G4Random::getTheEngine()->name()
         << G4endl;
  const auto enableOptical = !decayOnly;
  auto* detector = new gagg::DetectorConstruction(enableOptical);
  runManager->SetUserInitialization(detector);
  runManager->SetUserInitialization(new gagg::PhysicsList(enableOptical));
  auto* primaryGenerator = new gagg::PrimaryGeneratorAction();
  runManager->SetUserAction(primaryGenerator);
  auto* runAction = new gagg::RunAction(primaryGenerator, detector);
  runManager->SetUserAction(runAction);
  auto* eventAction = new gagg::EventAction(runAction, primaryGenerator);
  runManager->SetUserAction(eventAction);
  if (enableOptical) {
    runManager->SetUserAction(new gagg::StackingAction(eventAction));
  }
  runManager->SetUserAction(
      new gagg::SteppingAction(eventAction, detector, runAction));

  std::unique_ptr<G4VisManager> visManager;
  if (interactive) {
    visManager = std::make_unique<G4VisExecutive>("warnings");
    visManager->Initialize();
  }

  const auto status = G4UImanager::GetUIpointer()->ApplyCommand(
      G4String("/control/execute ") + macro);
  if (status != 0) {
    G4cerr << "[run] macro_failed status=" << status << " macro=" << macro
           << G4endl;
    return 3;
  }

  if (interactive) {
    ui->SessionStart();
    G4cout << "[interactive] session completed" << G4endl;
    return 0;
  }

  G4cout << "[smoke] run completed" << G4endl;
  return 0;
}
