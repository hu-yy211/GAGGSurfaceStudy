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
  G4bool IsPhotonAuditEnabled() const;

  void RecordOutput() { ++fOutput; }
  void RecordCrystalAbsorption() { ++fCrystalAbsorption; }
  void RecordReflectorAbsorption() { ++fReflectorAbsorption; }
  void RecordTopSurfaceAbsorption() {
    ++fSurfaceAbsorption;
    ++fTopSurfaceAbsorption;
  }
  void RecordBottomSurfaceAbsorption() {
    ++fSurfaceAbsorption;
    ++fBottomSurfaceAbsorption;
  }
  void RecordSideSurfaceAbsorption() {
    ++fSurfaceAbsorption;
    ++fSideSurfaceAbsorption;
  }
  void RecordBlackSurfaceAbsorption() {
    ++fSurfaceAbsorption;
    ++fBlackSurfaceAbsorption;
  }
  void RecordOtherSurfaceAbsorption() {
    ++fSurfaceAbsorption;
    ++fOtherSurfaceAbsorption;
  }
  void RecordOtherAbsorption() { ++fOtherAbsorption; }
  void RecordOtherWorldExit() { ++fOtherWorldExit; }
  void RecordLutInteraction() { ++fLutInteractions; }
  void RecordTopSurfaceInteraction() { ++fTopSurfaceInteractions; }
  void RecordBottomSurfaceInteraction() { ++fBottomSurfaceInteractions; }
  void RecordSideSurfaceInteraction() { ++fSideSurfaceInteractions; }
  void RecordEnergyDeposit(G4double energy) { fEnergyDeposit += energy; }
  void RecordOpticalStepLength(G4double length) {
    fTotalOpticalPath += length;
  }
  void RecordOutputPhotonDiagnostics(G4double pathLength,
                                     G4int topInteractions,
                                     G4int bottomInteractions,
                                     G4int sideInteractions,
                                     G4double incidenceAngle) {
    ++fOutputDiagnosticPhotons;
    fOutputOpticalPath += pathLength;
    fOutputTopInteractions += topInteractions;
    fOutputBottomInteractions += bottomInteractions;
    fOutputSideInteractions += sideInteractions;
    fOutputIncidenceAngle += incidenceAngle;
  }
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
  G4int fTopSurfaceAbsorption = 0;
  G4int fBottomSurfaceAbsorption = 0;
  G4int fSideSurfaceAbsorption = 0;
  G4int fBlackSurfaceAbsorption = 0;
  G4int fOtherSurfaceAbsorption = 0;
  G4int fOtherAbsorption = 0;
  G4int fOtherWorldExit = 0;
  G4int fLutInteractions = 0;
  G4int fTopSurfaceInteractions = 0;
  G4int fBottomSurfaceInteractions = 0;
  G4int fSideSurfaceInteractions = 0;
  G4double fTotalOpticalPath = 0.0;
  G4double fOutputOpticalPath = 0.0;
  G4int fOutputDiagnosticPhotons = 0;
  G4int fOutputTopInteractions = 0;
  G4int fOutputBottomInteractions = 0;
  G4int fOutputSideInteractions = 0;
  G4double fOutputIncidenceAngle = 0.0;
};

}  // namespace gagg

#endif
