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
class DetectorConstruction;
struct EventRecord;

class RunAction final : public G4UserRunAction {
 public:
  RunAction(PrimaryGeneratorAction* primaryGenerator,
            const DetectorConstruction* detector);
  ~RunAction() override;

  void BeginOfRunAction(const G4Run*) override;
  void EndOfRunAction(const G4Run*) override;

  void WriteEvent(const EventRecord& record);
  G4bool ShouldPrintEvent(G4int eventId) const;

 private:
  std::unique_ptr<G4GenericMessenger> fMessenger;
  PrimaryGeneratorAction* fPrimaryGenerator = nullptr;
  const DetectorConstruction* fDetector = nullptr;
  G4String fCsvPath;
  G4int fEventPrintModulo = 1;
  std::ofstream fCsv;
  G4int fRowsWritten = 0;
  G4double fEnergyDeposit = 0.0;
  std::int64_t fScintillation = 0;
  std::int64_t fGenerated = 0;
  std::int64_t fOutput = 0;
  std::int64_t fCrystalAbsorption = 0;
  std::int64_t fReflectorAbsorption = 0;
  std::int64_t fSurfaceAbsorption = 0;
  std::int64_t fTopSurfaceAbsorption = 0;
  std::int64_t fBottomSurfaceAbsorption = 0;
  std::int64_t fSideSurfaceAbsorption = 0;
  std::int64_t fBlackSurfaceAbsorption = 0;
  std::int64_t fOtherSurfaceAbsorption = 0;
  std::int64_t fOtherAbsorption = 0;
  std::int64_t fOtherWorldExit = 0;
  std::int64_t fLutInteractions = 0;
  std::int64_t fTopSurfaceInteractions = 0;
  std::int64_t fBottomSurfaceInteractions = 0;
  std::int64_t fSideSurfaceInteractions = 0;
  std::int64_t fUnclassified = 0;
};

}  // namespace gagg

#endif
