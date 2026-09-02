#ifndef GAGG_RUN_ACTION_HH
#define GAGG_RUN_ACTION_HH

#include "G4UserRunAction.hh"
#include "G4ThreeVector.hh"
#include "globals.hh"

#include <fstream>
#include <cstdint>
#include <map>
#include <memory>
#include <set>

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
  void RecordPositronCreated(G4int eventId, G4int trackId,
                             const G4String& creatorProcess,
                             const G4ThreeVector& vertexPosition);
  void RecordPositronAnnihilation(G4int eventId, G4int trackId,
                                  const G4ThreeVector& position,
                                  G4double kineticEnergyBefore,
                                  const G4String& volumeName,
                                  G4int annihilationGammaCount);
  void RecordPositronWorldExit(G4int eventId, G4int trackId,
                               const G4ThreeVector& position,
                               G4double kineticEnergy,
                               const G4String& volumeName);
  void RecordPositronOtherTermination(G4int eventId, G4int trackId,
                                      const G4ThreeVector& position,
                                      G4double kineticEnergy,
                                      const G4String& volumeName);

 private:
  struct PositronFate {
    G4int eventId = -1;
    G4int trackId = -1;
    G4String creatorProcess;
    G4ThreeVector vertexPosition;
    G4ThreeVector sourcePosition;
    G4String fate = "unresolved";
    G4ThreeVector terminalPosition;
    G4double terminalKineticEnergy = 0.0;
    G4String terminalVolume = "none";
  };

  static std::uint64_t PositronKey(G4int eventId, G4int trackId);
  void SetPositronFate(G4int eventId, G4int trackId,
                       const G4String& fate,
                       const G4ThreeVector& position,
                       G4double kineticEnergy,
                       const G4String& volumeName);

  std::unique_ptr<G4GenericMessenger> fMessenger;
  PrimaryGeneratorAction* fPrimaryGenerator = nullptr;
  const DetectorConstruction* fDetector = nullptr;
  G4String fCsvPath;
  G4String fAnnihilationCsvPath;
  G4String fPositronFateCsvPath;
  G4int fEventPrintModulo = 1;
  std::ofstream fCsv;
  std::ofstream fAnnihilationCsv;
  std::map<std::uint64_t, PositronFate> fPositronFates;
  std::set<std::uint64_t> fRecordedAnnihilations;
  std::int64_t fAnnihilationVertices = 0;
  std::int64_t fAnnihilationGammas = 0;
  std::int64_t fDuplicateAnnihilationRecords = 0;
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
