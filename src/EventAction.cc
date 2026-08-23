#include "GAGG/EventAction.hh"

#include "GAGG/EventRecord.hh"
#include "GAGG/PrimaryGeneratorAction.hh"
#include "GAGG/RunAction.hh"

#include "G4Event.hh"
#include "G4ios.hh"

namespace gagg {

EventAction::EventAction(RunAction* runAction,
                         const PrimaryGeneratorAction* primaryGenerator)
    : fRunAction(runAction), fPrimaryGenerator(primaryGenerator) {}

void EventAction::BeginOfEventAction(const G4Event*) {
  fEnergyDeposit = 0.0;
  fScintillation = 0;
  fGenerated = fPrimaryGenerator->GetPrimaryOpticalPhotonsPerEvent();
  fOutput = 0;
  fCrystalAbsorption = 0;
  fReflectorAbsorption = 0;
  fSurfaceAbsorption = 0;
  fOtherAbsorption = 0;
  fOtherWorldExit = 0;
  fLutInteractions = 0;
}

void EventAction::EndOfEventAction(const G4Event* event) {
  const auto classified = fOutput + fCrystalAbsorption +
                          fReflectorAbsorption + fSurfaceAbsorption +
                          fOtherAbsorption + fOtherWorldExit;
  const auto unclassified = fGenerated - classified;

  const EventRecord record{event->GetEventID(),
                           fPrimaryGenerator->GetPosition(),
                           fEnergyDeposit,
                           fScintillation,
                           fGenerated,
                           fOutput,
                           fCrystalAbsorption,
                           fReflectorAbsorption,
                           fSurfaceAbsorption,
                           fOtherAbsorption,
                           fOtherWorldExit,
                           fLutInteractions,
                           unclassified};

  if (fRunAction->ShouldPrintEvent(event->GetEventID()) || unclassified != 0) {
    G4cout << "[event] id=" << event->GetEventID()
           << " edep_keV=" << fEnergyDeposit / keV
           << " scintillation=" << fScintillation
           << " generated=" << fGenerated << " output=" << fOutput
           << " crystal_absorption=" << fCrystalAbsorption
           << " reflector_absorption=" << fReflectorAbsorption
           << " surface_absorption=" << fSurfaceAbsorption
           << " other_absorption=" << fOtherAbsorption
           << " other_world_exit=" << fOtherWorldExit
           << " lut_interactions=" << fLutInteractions
           << " unclassified=" << unclassified << G4endl;
  }
  fRunAction->WriteEvent(record);
}

}  // namespace gagg
