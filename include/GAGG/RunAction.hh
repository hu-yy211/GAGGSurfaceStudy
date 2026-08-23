#ifndef GAGG_RUN_ACTION_HH
#define GAGG_RUN_ACTION_HH

#include "G4UserRunAction.hh"
#include "globals.hh"

#include <fstream>
#include <cstdint>
#include <memory>

class G4GenericMessenger;

namespace gagg {

class PrimaryGeneratorAction;
struct EventRecord;

class RunAction final : public G4UserRunAction {
 public:
  explicit RunAction(PrimaryGeneratorAction* primaryGenerator);
  ~RunAction() override;

  void BeginOfRunAction(const G4Run*) override;
  void EndOfRunAction(const G4Run*) override;

  void WriteEvent(const EventRecord& record);
  G4bool ShouldPrintEvent(G4int eventId) const;

 private:
  std::unique_ptr<G4GenericMessenger> fMessenger;
  PrimaryGeneratorAction* fPrimaryGenerator = nullptr;
  G4String fCsvPath;
  G4int fEventPrintModulo = 1;
  std::ofstream fCsv;
  G4int fRowsWritten = 0;
  std::int64_t fGenerated = 0;
  std::int64_t fOutput = 0;
  std::int64_t fCrystalAbsorption = 0;
  std::int64_t fReflectorAbsorption = 0;
  std::int64_t fOtherAbsorption = 0;
  std::int64_t fOtherWorldExit = 0;
  std::int64_t fUnclassified = 0;
};

}  // namespace gagg

#endif
