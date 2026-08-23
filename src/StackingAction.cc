#include "GAGG/StackingAction.hh"

#include "GAGG/EventAction.hh"

#include "G4OpticalPhoton.hh"
#include "G4Track.hh"
#include "G4VProcess.hh"

namespace gagg {

StackingAction::StackingAction(EventAction* eventAction)
    : fEventAction(eventAction) {}

G4ClassificationOfNewTrack StackingAction::ClassifyNewTrack(
    const G4Track* track) {
  const auto* creator = track->GetCreatorProcess();
  if (track->GetDefinition() == G4OpticalPhoton::Definition() &&
      creator != nullptr && creator->GetProcessName() == "Scintillation") {
    fEventAction->RecordScintillationPhoton();
  }
  return fUrgent;
}

}  // namespace gagg
