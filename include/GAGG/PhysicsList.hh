#ifndef GAGG_PHYSICS_LIST_HH
#define GAGG_PHYSICS_LIST_HH

#include "G4VModularPhysicsList.hh"

namespace gagg {

class PhysicsList final : public G4VModularPhysicsList {
 public:
  PhysicsList();
  void SetCuts() override;
};

}  // namespace gagg

#endif

