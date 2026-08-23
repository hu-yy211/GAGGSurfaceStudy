#ifndef GAGG_STEPPING_ACTION_HH
#define GAGG_STEPPING_ACTION_HH

#include "G4UserSteppingAction.hh"

class G4OpBoundaryProcess;

namespace gagg {

class EventAction;

class SteppingAction final : public G4UserSteppingAction {
 public:
  explicit SteppingAction(EventAction* eventAction);
  void UserSteppingAction(const G4Step*) override;

 private:
  G4OpBoundaryProcess* FindBoundaryProcess();

  EventAction* fEventAction = nullptr;
  G4OpBoundaryProcess* fBoundaryProcess = nullptr;
};

}  // namespace gagg

#endif
