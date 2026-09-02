#include "GAGG/EventAction.hh"

#include "GAGG/EventRecord.hh"
#include "GAGG/PhotonAuditRecord.hh"
#include "GAGG/PrimaryGeneratorAction.hh"
#include "GAGG/RunAction.hh"

#include "G4Event.hh"
#include "G4ios.hh"

namespace gagg {

EventAction::EventAction(RunAction* runAction,
                         const PrimaryGeneratorAction* primaryGenerator)
    : fRunAction(runAction), fPrimaryGenerator(primaryGenerator) {}

G4bool EventAction::IsPhotonAuditEnabled() const {
  return fRunAction->IsPhotonAuditEnabled();
}

void EventAction::BeginOfEventAction(const G4Event*) {
  fEnergyDeposit = 0.0;
  fScintillation = 0;
  fGenerated = fPrimaryGenerator->GetPrimaryOpticalPhotonsPerEvent();
  fOutput = 0;
  fCrystalAbsorption = 0;
  fReflectorAbsorption = 0;
  fSurfaceAbsorption = 0;
  fTopSurfaceAbsorption = 0;
  fBottomSurfaceAbsorption = 0;
  fSideSurfaceAbsorption = 0;
  fBlackSurfaceAbsorption = 0;
  fOtherSurfaceAbsorption = 0;
  fOtherAbsorption = 0;
  fOtherWorldExit = 0;
  fLutInteractions = 0;
  fTopSurfaceInteractions = 0;
  fBottomSurfaceInteractions = 0;
  fSideSurfaceInteractions = 0;
  fTotalOpticalPath = 0.0;
  fOutputOpticalPath = 0.0;
  fOutputDiagnosticPhotons = 0;
  fOutputTopInteractions = 0;
  fOutputBottomInteractions = 0;
  fOutputSideInteractions = 0;
  fOutputIncidenceAngle = 0.0;
}

void EventAction::EndOfEventAction(const G4Event* event) {
  const auto classified = fOutput + fCrystalAbsorption +
                          fReflectorAbsorption + fSurfaceAbsorption +
                          fOtherAbsorption + fOtherWorldExit;
  const auto unclassified = fGenerated - classified;

  const EventRecord record{event->GetEventID(),
                           fPrimaryGenerator->GetEventPosition(),
                           fEnergyDeposit,
                           fScintillation,
                           fGenerated,
                           fOutput,
                           fCrystalAbsorption,
                           fReflectorAbsorption,
                           fSurfaceAbsorption,
                           fTopSurfaceAbsorption,
                           fBottomSurfaceAbsorption,
                           fSideSurfaceAbsorption,
                           fBlackSurfaceAbsorption,
                           fOtherSurfaceAbsorption,
                           fOtherAbsorption,
                           fOtherWorldExit,
                           fLutInteractions,
                           fTopSurfaceInteractions,
                           fBottomSurfaceInteractions,
                           fSideSurfaceInteractions,
                           unclassified};
  const PhotonAuditRecord audit{
      event->GetEventID(),
      fGenerated,
      fOutputDiagnosticPhotons,
      fTotalOpticalPath,
      fOutputOpticalPath,
      fOutputTopInteractions + fOutputBottomInteractions +
          fOutputSideInteractions,
      fOutputTopInteractions,
      fOutputBottomInteractions,
      fOutputSideInteractions,
      fOutputIncidenceAngle};

  if (fRunAction->ShouldPrintEvent(event->GetEventID()) || unclassified != 0) {
    G4cout << "[event] id=" << event->GetEventID()
           << " edep_keV=" << fEnergyDeposit / keV
           << " scintillation=" << fScintillation
           << " generated=" << fGenerated << " output=" << fOutput
           << " crystal_absorption=" << fCrystalAbsorption
           << " reflector_absorption=" << fReflectorAbsorption
           << " surface_absorption=" << fSurfaceAbsorption
           << " top_surface_absorption=" << fTopSurfaceAbsorption
           << " bottom_surface_absorption=" << fBottomSurfaceAbsorption
           << " side_surface_absorption=" << fSideSurfaceAbsorption
           << " black_surface_absorption=" << fBlackSurfaceAbsorption
           << " other_surface_absorption=" << fOtherSurfaceAbsorption
           << " other_absorption=" << fOtherAbsorption
           << " other_world_exit=" << fOtherWorldExit
           << " lut_interactions=" << fLutInteractions
           << " top_surface_interactions=" << fTopSurfaceInteractions
           << " bottom_surface_interactions=" << fBottomSurfaceInteractions
           << " side_surface_interactions=" << fSideSurfaceInteractions
           << " unclassified=" << unclassified << G4endl;
  }
  fRunAction->WriteEvent(record);
  fRunAction->WritePhotonAudit(audit);
}

}  // namespace gagg
