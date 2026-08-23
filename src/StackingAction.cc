#include "GAGG/StackingAction.hh"

#include "GAGG/EventAction.hh"

#include "G4OpticalPhoton.hh"
#include "G4GenericMessenger.hh"
#include "G4StateManager.hh"
#include "G4Track.hh"
#include "G4VProcess.hh"

namespace gagg {

StackingAction::StackingAction(EventAction* eventAction)
    : fMessenger(std::make_unique<G4GenericMessenger>(
          this, "/gagg/optics/", "GAGG optical-transport controls")),
      fEventAction(eventAction) {
  auto& deferCommand = fMessenger->DeclareProperty(
      "deferScintillationPhotons", fDeferScintillationPhotons,
      "Defer scintillation tracks until non-optical event transport is "
      "complete, isolating A7 random streams.");
  deferCommand.SetStates(G4State_PreInit, G4State_Idle);
}

G4ClassificationOfNewTrack StackingAction::ClassifyNewTrack(
    const G4Track* track) {
  const auto* creator = track->GetCreatorProcess();
  if (track->GetDefinition() == G4OpticalPhoton::Definition() &&
      creator != nullptr && creator->GetProcessName() == "Scintillation") {
    fEventAction->RecordScintillationPhoton();
    if (fDeferScintillationPhotons) {
      return fWaiting;
    }
  }
  return fUrgent;
}

}  // namespace gagg
