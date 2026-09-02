#include "GAGG/SteppingAction.hh"

#include "GAGG/DetectorConstruction.hh"
#include "GAGG/EventAction.hh"
#include "GAGG/RunAction.hh"

#include "G4GeometryTolerance.hh"
#include "G4Event.hh"
#include "G4EventManager.hh"
#include "G4GenericMessenger.hh"
#include "G4LogicalBorderSurface.hh"
#include "G4LogicalSkinSurface.hh"
#include "G4OpBoundaryProcess.hh"
#include "G4OpticalPhoton.hh"
#include "G4Gamma.hh"
#include "G4Positron.hh"
#include "G4ProcessManager.hh"
#include "G4ProcessVector.hh"
#include "G4Step.hh"
#include "G4Track.hh"
#include "G4VProcess.hh"
#include "G4ios.hh"

#include <cmath>

namespace gagg {

SteppingAction::SteppingAction(EventAction* eventAction,
                               const DetectorConstruction* detector,
                               RunAction* runAction)
    : fDebugMessenger(std::make_unique<G4GenericMessenger>(
          this, "/gagg/decayDebug/", "Radioactive-decay track diagnostics")),
      fEventAction(eventAction),
      fDetector(detector),
      fRunAction(runAction) {
  auto& enabledCommand = fDebugMessenger->DeclareProperty(
      "enabled", fDecayDebugEnabled,
      "Print the first step of secondary tracks for the first few events.");
  enabledCommand.SetStates(G4State_PreInit, G4State_Idle);
  auto& eventsCommand = fDebugMessenger->DeclareProperty(
      "events", fDecayDebugEvents,
      "Number of initial events included in radioactive-decay debug output.");
  eventsCommand.SetParameterName("count", false);
  eventsCommand.SetRange("count>=0");
  eventsCommand.SetStates(G4State_PreInit, G4State_Idle);
}

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
  const auto* track = step->GetTrack();
  const auto* currentEvent =
      G4EventManager::GetEventManager()->GetConstCurrentEvent();
  if (fDecayDebugEnabled && currentEvent != nullptr &&
      currentEvent->GetEventID() < fDecayDebugEvents &&
      track->GetParentID() > 0 && track->GetCurrentStepNumber() == 1) {
    const auto* definition = track->GetDefinition();
    const auto* creator = track->GetCreatorProcess();
    G4cout << "[decay-debug] event=" << currentEvent->GetEventID()
           << " particle=" << definition->GetParticleName()
           << " pdg=" << definition->GetPDGEncoding()
           << " type=" << definition->GetParticleType()
           << " vertex_kinetic_keV="
           << track->GetVertexKineticEnergy() / keV
           << " first_step_post_keV=" << track->GetKineticEnergy() / keV
           << " creator="
           << (creator == nullptr ? G4String("primary")
                                  : creator->GetProcessName())
           << " parent_id=" << track->GetParentID()
           << " track_id=" << track->GetTrackID()
           << " vertex_position_mm=" << track->GetVertexPosition() / mm
           << " first_step_post_position_mm="
           << track->GetPosition() / mm << G4endl;
  }

  const auto* pre = step->GetPreStepPoint();
  const auto* preVolume = pre->GetPhysicalVolume();
  const auto* post = step->GetPostStepPoint();

  if (track->GetDefinition() == G4Positron::Definition() &&
      currentEvent != nullptr) {
    const auto eventId = currentEvent->GetEventID();
    const auto trackId = track->GetTrackID();
    const auto volumeName =
        preVolume == nullptr ? G4String("none") : preVolume->GetName();
    if (track->GetCurrentStepNumber() == 1) {
      const auto* creator = track->GetCreatorProcess();
      fRunAction->RecordPositronCreated(
          eventId, trackId,
          creator == nullptr ? G4String("primary")
                             : creator->GetProcessName(),
          track->GetVertexPosition());
    }

    const auto* process = post->GetProcessDefinedStep();
    const auto annihilationStep =
        process != nullptr && process->GetProcessName() == "annihil";
    const auto worldExit = post->GetStepStatus() == fWorldBoundary ||
                           post->GetPhysicalVolume() == nullptr;
    if (annihilationStep) {
      G4int annihilationGammaCount = 0;
      // The parent post-step point is the creation point used by the
      // annihilation process. A just-created secondary has not yet begun
      // tracking, so its G4Track vertex field is not reliable here.
      G4ThreeVector annihilationVertex = post->GetPosition();
      const auto* secondaries = step->GetSecondaryInCurrentStep();
      if (secondaries != nullptr) {
        for (const auto* secondary : *secondaries) {
          const auto* creator = secondary->GetCreatorProcess();
          if (secondary->GetDefinition() == G4Gamma::Definition() &&
              creator != nullptr && creator->GetProcessName() == "annihil") {
            ++annihilationGammaCount;
          }
        }
      }
      if (annihilationGammaCount > 0) {
        fRunAction->RecordPositronAnnihilation(
            eventId, trackId, annihilationVertex, pre->GetKineticEnergy(),
            volumeName, annihilationGammaCount);
      } else {
        if (worldExit) {
          fRunAction->RecordPositronWorldExit(
              eventId, trackId, post->GetPosition(),
              post->GetKineticEnergy(), volumeName);
        } else if (track->GetTrackStatus() == fStopAndKill ||
                   track->GetTrackStatus() == fKillTrackAndSecondaries) {
          if (volumeName == "World") {
            fRunAction->RecordPositronWorldExit(
                eventId, trackId, post->GetPosition(),
                post->GetKineticEnergy(), volumeName);
          } else {
            fRunAction->RecordPositronOtherTermination(
                eventId, trackId, post->GetPosition(),
                post->GetKineticEnergy(), volumeName);
          }
        }
      }
    } else if (worldExit) {
      fRunAction->RecordPositronWorldExit(
          eventId, trackId, post->GetPosition(), post->GetKineticEnergy(),
          volumeName);
    } else if (track->GetTrackStatus() == fStopAndKill ||
               track->GetTrackStatus() == fKillTrackAndSecondaries) {
      if (volumeName == "World") {
        fRunAction->RecordPositronWorldExit(
            eventId, trackId, post->GetPosition(),
            post->GetKineticEnergy(), volumeName);
      } else {
        fRunAction->RecordPositronOtherTermination(
            eventId, trackId, post->GetPosition(), post->GetKineticEnergy(),
            volumeName);
      }
    }
  }

  const auto isOpticalPhoton =
      track->GetDefinition() == G4OpticalPhoton::Definition();
  if (!isOpticalPhoton && preVolume != nullptr &&
      preVolume->GetName() == "GAGG" &&
      step->GetTotalEnergyDeposit() > 0.0) {
    fEventAction->RecordEnergyDeposit(step->GetTotalEnergyDeposit());
  }

  if (!isOpticalPhoton) {
    return;
  }

  const auto* postVolume = post->GetPhysicalVolume();
  const auto surfaceTolerance =
      G4GeometryTolerance::GetInstance()->GetSurfaceTolerance();
  const auto atGeometryBoundary = post->GetStepStatus() == fGeomBoundary;
  const auto* borderSurface =
      atGeometryBoundary && preVolume != nullptr && postVolume != nullptr
          ? G4LogicalBorderSurface::GetSurface(preVolume, postVolume)
          : nullptr;
  const auto* skinSurface =
      atGeometryBoundary && borderSurface == nullptr &&
              postVolume != nullptr
          ? G4LogicalSkinSurface::GetSurface(
                postVolume->GetLogicalVolume())
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
      if (postVolume->GetName() == "ExperimentTopAirGap") {
        fEventAction->RecordTopSurfaceInteraction();
      } else if (postVolume->GetName() == "ExperimentBottomAirGap") {
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
  const auto receiverCrossing =
      atGeometryBoundary && preVolume != nullptr && postVolume != nullptr &&
      postVolume->GetName() == fDetector->GetOutputReceiverVolumeName() &&
      ((fDetector->GetGeometryMode() == "experiment" &&
        preVolume->GetName() == "ExperimentBottomAirGap") ||
       (fDetector->GetGeometryMode() != "experiment" &&
        outputFaceArrival)) &&
      (boundaryStatus == FresnelRefraction ||
       boundaryStatus == Transmission ||
       boundaryStatus == SameMaterial);
  if (outputFaceArrival &&
      fDetector->GetOutputScoringMode() == "firstArrival") {
    fEventAction->RecordOutput();
    step->GetTrack()->SetTrackStatus(fStopAndKill);
    return;
  }
  if (receiverCrossing) {
    fEventAction->RecordOutput();
    step->GetTrack()->SetTrackStatus(fStopAndKill);
    return;
  }

  if (borderSurface != nullptr || skinSurface != nullptr) {
    if (boundaryStatus == Absorption || boundaryStatus == Detection) {
      const auto preName =
          preVolume == nullptr ? G4String("none") : preVolume->GetName();
      const auto postName =
          postVolume == nullptr ? G4String("none") : postVolume->GetName();
      if ((preName == "GAGG" &&
           postName == "ExperimentTopAirGap") ||
          (preName == "ExperimentTopAirGap" &&
           postName == "ExperimentESR")) {
        fEventAction->RecordTopSurfaceAbsorption();
      } else if ((preName == "GAGG" &&
                  postName == "ExperimentBottomAirGap") ||
                 (preName == "ExperimentBottomAirGap" &&
                  postName == "PMTWindow")) {
        fEventAction->RecordBottomSurfaceAbsorption();
      } else if (preName == "GAGG" &&
                 postName == "ExperimentSideAirGap") {
        fEventAction->RecordSideSurfaceAbsorption();
      } else if (preName == "ExperimentSideAirGap" &&
                 postName == "ExperimentBlackHousing") {
        fEventAction->RecordBlackSurfaceAbsorption();
      } else if (postName == "ExperimentTopStructure" ||
                 preName == "ExperimentTopStructure") {
        fEventAction->RecordOtherSurfaceAbsorption();
      } else {
        fEventAction->RecordOtherSurfaceAbsorption();
      }
      return;
    }
  }

  // Geant4 can terminate an optical photon at an implicit material boundary
  // (for example NoRINDEX) without a user border or skin surface. Preserve
  // complete event accounting by assigning those rare terminal boundary
  // losses to the existing catch-all surface category.
  if (atGeometryBoundary &&
      (boundaryStatus == Absorption || boundaryStatus == Detection ||
       boundaryStatus == NoRINDEX)) {
    fEventAction->RecordOtherSurfaceAbsorption();
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
    return;
  }

  // Last-resort classification for an optical track stopped by a process not
  // represented above. This should remain extremely rare, but no generated
  // scintillation photon may silently disappear from the event balance.
  if (step->GetTrack()->GetTrackStatus() == fStopAndKill) {
    fEventAction->RecordOtherAbsorption();
  }
}

}  // namespace gagg
