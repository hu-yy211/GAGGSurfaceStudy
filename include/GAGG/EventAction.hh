#ifndef GAGG_EVENT_ACTION_HH
#define GAGG_EVENT_ACTION_HH

#include "G4UserEventAction.hh"
#include "globals.hh"

namespace gagg {

class RunAction;

class EventAction final : public G4UserEventAction {
 public:
  explicit EventAction(RunAction* runAction);
  void BeginOfEventAction(const G4Event*) override;
  void EndOfEventAction(const G4Event*) override;

  void RecordWorldExit() { ++fWorldExit; }
  void RecordBulkAbsorption() { ++fBulkAbsorption; }

 private:
  RunAction* fRunAction = nullptr;
  G4int fWorldExit = 0;
  G4int fBulkAbsorption = 0;
};

}  // namespace gagg

#endif
