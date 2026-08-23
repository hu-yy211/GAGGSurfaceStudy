#include "GAGG/EventAction.hh"

#include "GAGG/RunAction.hh"

#include "G4Event.hh"
#include "G4ios.hh"

namespace gagg {

EventAction::EventAction(RunAction* runAction) : fRunAction(runAction) {}

void EventAction::BeginOfEventAction(const G4Event*) {
  fWorldExit = 0;
  fBulkAbsorption = 0;
}

void EventAction::EndOfEventAction(const G4Event* event) {
  constexpr G4int generated = 1;
  const auto classified = fWorldExit + fBulkAbsorption;
  const auto unclassified = generated - classified;

  if (fRunAction->ShouldPrintEvent(event->GetEventID()) || unclassified != 0) {
    G4cout << "[event] id=" << event->GetEventID()
           << " generated=" << generated << " world_exit=" << fWorldExit
           << " bulk_absorption=" << fBulkAbsorption
           << " unclassified=" << unclassified << G4endl;
  }
  fRunAction->WriteEvent(event->GetEventID(), generated, fWorldExit,
                         fBulkAbsorption, unclassified);
}

}  // namespace gagg
