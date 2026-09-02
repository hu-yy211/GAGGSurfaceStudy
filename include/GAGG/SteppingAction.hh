#ifndef GAGG_STEPPING_ACTION_HH
#define GAGG_STEPPING_ACTION_HH

#include "G4UserSteppingAction.hh"
#include "globals.hh"

#include <memory>

class G4GenericMessenger;
class G4OpBoundaryProcess;

namespace gagg {

class EventAction;
class DetectorConstruction;
class RunAction;

class SteppingAction final : public G4UserSteppingAction {
 public:
  SteppingAction(EventAction* eventAction,
                 const DetectorConstruction* detector,
                 RunAction* runAction);
  void UserSteppingAction(const G4Step*) override;

 private:
  G4OpBoundaryProcess* FindBoundaryProcess();

  std::unique_ptr<G4GenericMessenger> fDebugMessenger;
  EventAction* fEventAction = nullptr;
  const DetectorConstruction* fDetector = nullptr;
  RunAction* fRunAction = nullptr;
  G4OpBoundaryProcess* fBoundaryProcess = nullptr;
  G4bool fDecayDebugEnabled = false;
  G4int fDecayDebugEvents = 3;
};

}  // namespace gagg

#endif
