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
  fOutput = 0;
  fCrystalAbsorption = 0;
  fReflectorAbsorption = 0;
  fSurfaceAbsorption = 0;
  fOtherAbsorption = 0;
  fOtherWorldExit = 0;
  fLutInteractions = 0;
}

void EventAction::EndOfEventAction(const G4Event* event) {
  const auto generated = fPrimaryGenerator->GetPhotonsPerEvent();
  const auto classified = fOutput + fCrystalAbsorption +
                          fReflectorAbsorption + fSurfaceAbsorption +
                          fOtherAbsorption + fOtherWorldExit;
  const auto unclassified = generated - classified;

  const EventRecord record{event->GetEventID(),
                           fPrimaryGenerator->GetPosition(),
                           generated,
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
           << " generated=" << generated << " output=" << fOutput
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
