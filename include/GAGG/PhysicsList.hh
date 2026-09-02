#ifndef GAGG_PHYSICS_LIST_HH
#define GAGG_PHYSICS_LIST_HH

#include "G4VModularPhysicsList.hh"

namespace gagg {

class PhysicsList final : public G4VModularPhysicsList {
 public:
  explicit PhysicsList(G4bool enableOptical = true);
  void SetCuts() override;

  G4bool IsOpticalEnabled() const { return fEnableOptical; }

 private:
  G4bool fEnableOptical = true;
};

}  // namespace gagg

#endif
