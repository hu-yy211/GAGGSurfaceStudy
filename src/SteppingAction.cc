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
  const auto atGeometryBoundary = post->GetStepStatus() == fGeomBoundary;
  const auto* borderSurface =
      atGeometryBoundary && preVolume != nullptr && postVolume != nullptr
          ? G4LogicalBorderSurface::GetSurface(preVolume, postVolume)
          : nullptr;
  auto* boundary = atGeometryBoundary ? FindBoundaryProcess() : nullptr;
  const auto boundaryStatus =
      boundary == nullptr ? Undefined : boundary->GetStatus();
  const auto validBoundaryInteraction =
      borderSurface != nullptr && boundaryStatus != Undefined &&
      boundaryStatus != NotAtBoundary && boundaryStatus != StepTooSmall;
  if (validBoundaryInteraction) {
    fEventAction->RecordLutInteraction();
    if (preVolume->GetName() == "GAGG") {
      if (postVolume->GetName() == "ExperimentESR") {
        fEventAction->RecordTopSurfaceInteraction();
      } else if (postVolume->GetName() == "PMTWindow") {
        fEventAction->RecordBottomSurfaceInteraction();
      } else if (postVolume->GetName() == "ExperimentSideAirGap") {
        fEventAction->RecordSideSurfaceInteraction();
      }
    }
  }

  const auto outputFaceArrival =
      atGeometryBoundary && preVolume != nullptr &&
      preVolume->GetName() == "GAGG" &&
      fDetector->IsOnOutputFace(post->GetPosition(), surfaceTolerance);
  const auto outputFaceCrossing =
      outputFaceArrival && postVolume != nullptr &&
      postVolume->GetName() == fDetector->GetOutputReceiverVolumeName() &&
      (boundaryStatus == FresnelRefraction ||
       boundaryStatus == Transmission ||
       boundaryStatus == SameMaterial);
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

  if (borderSurface != nullptr) {
    if (boundaryStatus == Absorption || boundaryStatus == Detection) {
      const auto preName =
          preVolume == nullptr ? G4String("none") : preVolume->GetName();
      const auto postName =
          postVolume == nullptr ? G4String("none") : postVolume->GetName();
      if (preName == "GAGG" && postName == "ExperimentESR") {
        fEventAction->RecordTopSurfaceAbsorption();
      } else if (preName == "GAGG" && postName == "PMTWindow") {
        fEventAction->RecordBottomSurfaceAbsorption();
      } else if (preName == "GAGG" &&
                 postName == "ExperimentSideAirGap") {
        fEventAction->RecordSideSurfaceAbsorption();
      } else if (preName == "ExperimentSideAirGap" &&
                 postName == "ExperimentBlackHousing") {
        fEventAction->RecordBlackSurfaceAbsorption();
      } else {
        fEventAction->RecordOtherSurfaceAbsorption();
      }
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
