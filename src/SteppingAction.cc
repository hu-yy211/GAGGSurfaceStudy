#include "GAGG/SteppingAction.hh"

#include "GAGG/EventAction.hh"
#include "GAGG/SimulationConfig.hh"

#include "G4GeometryTolerance.hh"
#include "G4OpticalPhoton.hh"
#include "G4Step.hh"
#include "G4Track.hh"
#include "G4VProcess.hh"

#include <cmath>

namespace gagg {

SteppingAction::SteppingAction(EventAction* eventAction)
    : fEventAction(eventAction) {}

void SteppingAction::UserSteppingAction(const G4Step* step) {
  if (step->GetTrack()->GetDefinition() != G4OpticalPhoton::Definition()) {
    return;
  }

  const auto* post = step->GetPostStepPoint();
  const auto* pre = step->GetPreStepPoint();
  const auto* preVolume = pre->GetPhysicalVolume();
  const auto* postVolume = post->GetPhysicalVolume();
  const auto surfaceTolerance =
      G4GeometryTolerance::GetInstance()->GetSurfaceTolerance();

  const auto outputFaceCrossing =
      post->GetStepStatus() == fGeomBoundary && preVolume != nullptr &&
      postVolume != nullptr && preVolume->GetName() == "GAGG" &&
      postVolume->GetName() == "World" &&
      std::abs(post->GetPosition().z() + 0.5 * config::kCrystalLength) <
          surfaceTolerance &&
      post->GetPosition().perp() <
          config::kCrystalRadius - surfaceTolerance;
  if (outputFaceCrossing) {
    fEventAction->RecordOutput();
    step->GetTrack()->SetTrackStatus(fStopAndKill);
    return;
  }

  if (post->GetStepStatus() == fWorldBoundary) {
    fEventAction->RecordOtherWorldExit();
    return;
  }

  const auto* process = post->GetProcessDefinedStep();
  if (process != nullptr && process->GetProcessName() == "OpAbsorption") {
    const auto volumeName =
        preVolume == nullptr ? G4String("none") : preVolume->GetName();
    if (volumeName == "GAGG") {
      fEventAction->RecordCrystalAbsorption();
    } else if (volumeName == "SideReflector" ||
               volumeName == "TopReflector") {
      fEventAction->RecordReflectorAbsorption();
    } else {
      fEventAction->RecordOtherAbsorption();
    }
  }
}

}  // namespace gagg
