#include "GAGG/SteppingAction.hh"

#include "GAGG/DetectorConstruction.hh"
#include "GAGG/EventAction.hh"

#include "G4GeometryTolerance.hh"
#include "G4LogicalBorderSurface.hh"
#include "G4OpBoundaryProcess.hh"
#include "G4OpticalPhoton.hh"
#include "G4ProcessManager.hh"
#include "G4ProcessVector.hh"
#include "G4Step.hh"
#include "G4Track.hh"
#include "G4VProcess.hh"

#include <cmath>

namespace gagg {

SteppingAction::SteppingAction(EventAction* eventAction,
                               const DetectorConstruction* detector)
    : fEventAction(eventAction), fDetector(detector) {}

G4OpBoundaryProcess* SteppingAction::FindBoundaryProcess() {
  if (fBoundaryProcess != nullptr) {
    return fBoundaryProcess;
  }
  auto* manager = G4OpticalPhoton::Definition()->GetProcessManager();
  if (manager == nullptr) {
    return nullptr;
  }
  auto* processes = manager->GetProcessList();
  for (G4int index = 0; index < manager->GetProcessListLength(); ++index) {
    if ((*processes)[index] != nullptr &&
        (*processes)[index]->GetProcessName() == "OpBoundary") {
      fBoundaryProcess =
          dynamic_cast<G4OpBoundaryProcess*>((*processes)[index]);
      break;
    }
  }
  return fBoundaryProcess;
}

void SteppingAction::UserSteppingAction(const G4Step* step) {
  const auto* pre = step->GetPreStepPoint();
  const auto* preVolume = pre->GetPhysicalVolume();
  const auto isOpticalPhoton =
      step->GetTrack()->GetDefinition() == G4OpticalPhoton::Definition();
  if (!isOpticalPhoton && preVolume != nullptr &&
      preVolume->GetName() == "GAGG" &&
      step->GetTotalEnergyDeposit() > 0.0) {
    fEventAction->RecordEnergyDeposit(step->GetTotalEnergyDeposit());
  }

  if (!isOpticalPhoton) {
    return;
  }

  const auto* post = step->GetPostStepPoint();
  const auto* postVolume = post->GetPhysicalVolume();
  const auto surfaceTolerance =
      G4GeometryTolerance::GetInstance()->GetSurfaceTolerance();

  const auto outputFaceArrival =
      post->GetStepStatus() == fGeomBoundary && preVolume != nullptr &&
      preVolume->GetName() == "GAGG" &&
      fDetector->IsOnOutputFace(post->GetPosition(), surfaceTolerance);
  auto* outputBoundary =
      outputFaceArrival ? FindBoundaryProcess() : nullptr;
  const auto outputBoundaryStatus =
      outputBoundary == nullptr ? Undefined : outputBoundary->GetStatus();
  const auto outputFaceCrossing =
      outputFaceArrival && postVolume != nullptr &&
      postVolume->GetName() == fDetector->GetOutputReceiverVolumeName() &&
      (outputBoundaryStatus == FresnelRefraction ||
       outputBoundaryStatus == Transmission ||
       outputBoundaryStatus == SameMaterial);
  if (outputFaceArrival &&
      fDetector->GetOutputScoringMode() == "firstArrival") {
    fEventAction->RecordOutput();
    step->GetTrack()->SetTrackStatus(fStopAndKill);
    return;
  }
  if (outputFaceCrossing) {
    fEventAction->RecordOutput();
    step->GetTrack()->SetTrackStatus(fStopAndKill);
    return;
  }

  if (post->GetStepStatus() == fGeomBoundary && preVolume != nullptr &&
      postVolume != nullptr &&
      G4LogicalBorderSurface::GetSurface(preVolume, postVolume) != nullptr) {
    auto* boundary = FindBoundaryProcess();
    const auto status =
        boundary == nullptr ? Undefined : boundary->GetStatus();
    if (status != Undefined && status != NotAtBoundary &&
        status != StepTooSmall) {
      fEventAction->RecordLutInteraction();
    }
    if (status == Absorption || status == Detection) {
      fEventAction->RecordSurfaceAbsorption();
      return;
    }
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
