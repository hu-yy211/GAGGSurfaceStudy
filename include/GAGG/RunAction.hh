#ifndef GAGG_RUN_ACTION_HH
#define GAGG_RUN_ACTION_HH

#include "G4UserRunAction.hh"
#include "globals.hh"

#include <fstream>
#include <memory>

class G4GenericMessenger;

namespace gagg {

class RunAction final : public G4UserRunAction {
 public:
  RunAction();
  ~RunAction() override;

  void BeginOfRunAction(const G4Run*) override;
  void EndOfRunAction(const G4Run*) override;

  void WriteEvent(G4int eventId, G4int generated, G4int worldExit,
                  G4int bulkAbsorption, G4int unclassified);
  G4bool ShouldPrintEvent(G4int eventId) const;

 private:
  std::unique_ptr<G4GenericMessenger> fMessenger;
  G4String fCsvPath;
  G4int fEventPrintModulo = 1;
  std::ofstream fCsv;
  G4int fRowsWritten = 0;
};

}  // namespace gagg

#endif
