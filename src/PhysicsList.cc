#include "GAGG/PhysicsList.hh"

#include "G4EmStandardPhysics.hh"
#include "G4OpticalParameters.hh"
#include "G4OpticalPhysics.hh"
#include "G4ios.hh"

namespace gagg {

PhysicsList::PhysicsList() {
  SetVerboseLevel(0);
  auto* opticalParameters = G4OpticalParameters::Instance();
  opticalParameters->SetProcessActivation("Cerenkov", false);
  opticalParameters->SetProcessActivation("Scintillation", true);
  opticalParameters->SetScintTrackSecondariesFirst(true);
  opticalParameters->SetScintFiniteRiseTime(false);
  RegisterPhysics(new G4EmStandardPhysics(0));
  RegisterPhysics(new G4OpticalPhysics(0));
  G4cout << "[physics] cerenkov=off scintillation=on" << G4endl;
}

void PhysicsList::SetCuts() {
  SetCutsWithDefault();
}

}  // namespace gagg
