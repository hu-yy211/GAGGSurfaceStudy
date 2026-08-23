#ifndef GAGG_STACKING_ACTION_HH
#define GAGG_STACKING_ACTION_HH

#include "G4UserStackingAction.hh"
#include "globals.hh"

#include <memory>

class G4GenericMessenger;

namespace gagg {

class EventAction;

class StackingAction final : public G4UserStackingAction {
 public:
  explicit StackingAction(EventAction* eventAction);
  G4ClassificationOfNewTrack ClassifyNewTrack(const G4Track*) override;

 private:
  std::unique_ptr<G4GenericMessenger> fMessenger;
  EventAction* fEventAction = nullptr;
  G4bool fDeferScintillationPhotons = false;
};

}  // namespace gagg

#endif
