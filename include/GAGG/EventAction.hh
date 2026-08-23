#ifndef GAGG_EVENT_ACTION_HH
#define GAGG_EVENT_ACTION_HH

#include "G4UserEventAction.hh"
#include "globals.hh"

namespace gagg {

class PrimaryGeneratorAction;
class RunAction;

class EventAction final : public G4UserEventAction {
 public:
  EventAction(RunAction* runAction,
              const PrimaryGeneratorAction* primaryGenerator);
  void BeginOfEventAction(const G4Event*) override;
  void EndOfEventAction(const G4Event*) override;

  void RecordOutput() { ++fOutput; }
  void RecordCrystalAbsorption() { ++fCrystalAbsorption; }
  void RecordReflectorAbsorption() { ++fReflectorAbsorption; }
  void RecordSurfaceAbsorption() { ++fSurfaceAbsorption; }
  void RecordOtherAbsorption() { ++fOtherAbsorption; }
  void RecordOtherWorldExit() { ++fOtherWorldExit; }
  void RecordLutInteraction() { ++fLutInteractions; }
  void RecordTopSurfaceInteraction() { ++fTopSurfaceInteractions; }
  void RecordBottomSurfaceInteraction() { ++fBottomSurfaceInteractions; }
  void RecordSideSurfaceInteraction() { ++fSideSurfaceInteractions; }
  void RecordEnergyDeposit(G4double energy) { fEnergyDeposit += energy; }
  void RecordScintillationPhoton() {
    ++fScintillation;
    ++fGenerated;
  }

 private:
  RunAction* fRunAction = nullptr;
  const PrimaryGeneratorAction* fPrimaryGenerator = nullptr;
  G4double fEnergyDeposit = 0.0;
  G4int fScintillation = 0;
  G4int fGenerated = 0;
  G4int fOutput = 0;
  G4int fCrystalAbsorption = 0;
  G4int fReflectorAbsorption = 0;
  G4int fSurfaceAbsorption = 0;
  G4int fOtherAbsorption = 0;
  G4int fOtherWorldExit = 0;
  G4int fLutInteractions = 0;
  G4int fTopSurfaceInteractions = 0;
  G4int fBottomSurfaceInteractions = 0;
  G4int fSideSurfaceInteractions = 0;
};

}  // namespace gagg

#endif
