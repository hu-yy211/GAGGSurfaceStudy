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

#include <memory>

namespace {

void PrintUsage(const char* executable) {
  G4cerr << "Usage:\n"
         << "  " << executable << " <macro-file>\n"
         << "  " << executable << " --interactive <visualization-macro>\n"
         << "  " << executable << " --validate-materials" << G4endl;
}

}  // namespace

int main(int argc, char** argv) {
  if (argc == 2 && G4String(argv[1]) == "--validate-materials") {
    return gagg::RunMaterialValidation();
  }

  const auto interactive =
      argc == 3 && G4String(argv[1]) == "--interactive";
  if ((!interactive && argc != 2) || (interactive && argc != 3)) {
    PrintUsage(argv[0]);
    return 2;
  }
  const G4String macro = interactive ? argv[2] : argv[1];

  std::unique_ptr<G4UIExecutive> ui;
  if (interactive) {
    ui = std::make_unique<G4UIExecutive>(1, argv);
  }

  auto runManager =
      std::unique_ptr<G4RunManager>(G4RunManagerFactory::CreateRunManager(
          G4RunManagerType::SerialOnly));
  auto* detector = new gagg::DetectorConstruction();
  runManager->SetUserInitialization(detector);
  runManager->SetUserInitialization(new gagg::PhysicsList());
  auto* primaryGenerator = new gagg::PrimaryGeneratorAction();
  runManager->SetUserAction(primaryGenerator);
  auto* runAction = new gagg::RunAction(primaryGenerator, detector);
  runManager->SetUserAction(runAction);
  auto* eventAction = new gagg::EventAction(runAction, primaryGenerator);
  runManager->SetUserAction(eventAction);
  runManager->SetUserAction(new gagg::StackingAction(eventAction));
  runManager->SetUserAction(new gagg::SteppingAction(eventAction));

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
