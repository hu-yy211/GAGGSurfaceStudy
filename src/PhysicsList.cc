#include "GAGG/PhysicsList.hh"

#include "G4EmStandardPhysics.hh"
#include "G4OpticalPhysics.hh"

namespace gagg {

PhysicsList::PhysicsList() {
  SetVerboseLevel(0);
  RegisterPhysics(new G4EmStandardPhysics(0));
  RegisterPhysics(new G4OpticalPhysics(0));
}

void PhysicsList::SetCuts() {
  SetCutsWithDefault();
}

}  // namespace gagg
