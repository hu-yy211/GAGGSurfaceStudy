#ifndef GAGG_STACKING_ACTION_HH
#define GAGG_STACKING_ACTION_HH

#include "G4UserStackingAction.hh"

namespace gagg {

class EventAction;

class StackingAction final : public G4UserStackingAction {
 public:
  explicit StackingAction(EventAction* eventAction);
  G4ClassificationOfNewTrack ClassifyNewTrack(const G4Track*) override;

 private:
  EventAction* fEventAction = nullptr;
};

}  // namespace gagg

#endif
