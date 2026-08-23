#include "GAGG/SteppingAction.hh"

#include "GAGG/EventAction.hh"

#include "G4OpticalPhoton.hh"
#include "G4Step.hh"
#include "G4Track.hh"
#include "G4VProcess.hh"

namespace gagg {

SteppingAction::SteppingAction(EventAction* eventAction)
    : fEventAction(eventAction) {}

void SteppingAction::UserSteppingAction(const G4Step* step) {
  if (step->GetTrack()->GetDefinition() != G4OpticalPhoton::Definition()) {
    return;
  }

  const auto* post = step->GetPostStepPoint();
  if (post->GetStepStatus() == fWorldBoundary) {
    fEventAction->RecordWorldExit();
    return;
  }

  const auto* process = post->GetProcessDefinedStep();
  if (process != nullptr && process->GetProcessName() == "OpAbsorption") {
    fEventAction->RecordBulkAbsorption();
  }
}

}  // namespace gagg
