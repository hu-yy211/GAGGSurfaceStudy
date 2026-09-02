#include "GAGG/PhysicsList.hh"

#include "G4DecayPhysics.hh"
#include "G4EmStandardPhysics.hh"
#include "G4OpticalParameters.hh"
#include "G4OpticalPhysics.hh"
#include "G4RadioactiveDecayPhysics.hh"
#include "G4ios.hh"

namespace gagg {

PhysicsList::PhysicsList(G4bool enableOptical)
    : fEnableOptical(enableOptical) {
  SetVerboseLevel(0);
  RegisterPhysics(new G4DecayPhysics(0));
  RegisterPhysics(new G4EmStandardPhysics(0));
  RegisterPhysics(new G4RadioactiveDecayPhysics(0));
  if (fEnableOptical) {
    auto* opticalParameters = G4OpticalParameters::Instance();
    opticalParameters->SetProcessActivation("Cerenkov", false);
    opticalParameters->SetProcessActivation("Scintillation", true);
    opticalParameters->SetScintTrackSecondariesFirst(true);
    opticalParameters->SetScintFiniteRiseTime(false);
    RegisterPhysics(new G4OpticalPhysics(0));
  }
  G4cout << "[physics] em=G4EmStandardPhysics decay=on"
         << " radioactive_decay=on optical="
         << (fEnableOptical ? "on" : "off")
         << " scintillation=" << (fEnableOptical ? "on" : "off")
         << " cerenkov=off" << G4endl;
}

void PhysicsList::SetCuts() {
  SetCutsWithDefault();
}

}  // namespace gagg
