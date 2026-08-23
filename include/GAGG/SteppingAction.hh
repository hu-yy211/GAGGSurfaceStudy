#ifndef GAGG_STEPPING_ACTION_HH
#define GAGG_STEPPING_ACTION_HH

#include "G4UserSteppingAction.hh"

namespace gagg {

class EventAction;

class SteppingAction final : public G4UserSteppingAction {
 public:
  explicit SteppingAction(EventAction* eventAction);
  void UserSteppingAction(const G4Step*) override;

 private:
  EventAction* fEventAction = nullptr;
};

}  // namespace gagg

#endif
