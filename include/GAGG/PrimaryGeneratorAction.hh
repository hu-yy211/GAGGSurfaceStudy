#ifndef GAGG_PRIMARY_GENERATOR_ACTION_HH
#define GAGG_PRIMARY_GENERATOR_ACTION_HH

#include "G4ThreeVector.hh"
#include "G4UImessenger.hh"
#include "G4VUserPrimaryGeneratorAction.hh"
#include "globals.hh"

#include <cstdint>
#include <memory>

class G4GenericMessenger;
class G4ParticleGun;
class G4UIcmdWith3VectorAndUnit;

namespace gagg {

class PrimaryGeneratorAction final : public G4VUserPrimaryGeneratorAction,
                                     public G4UImessenger {
 public:
  PrimaryGeneratorAction();
  ~PrimaryGeneratorAction() override;
  void GeneratePrimaries(G4Event*) override;
  void SetNewValue(G4UIcommand*, G4String) override;

  void SetDirectionMode(const G4String& mode);
  void SetPhotonsPerEvent(G4int count);
  void SetPosition(const G4ThreeVector& position);

  const G4String& GetDirectionMode() const { return fDirectionMode; }
  G4int GetPhotonsPerEvent() const { return fPhotonsPerEvent; }
  const G4ThreeVector& GetPosition() const { return fPosition; }
  void ResetDirectionDiagnostics();
  void ReportDirectionDiagnostics() const;

 private:
  void ValidateConfiguration() const;
  void ConfigureIsotropicPhoton();

  std::unique_ptr<G4GenericMessenger> fMessenger;
  std::unique_ptr<G4UIcmdWith3VectorAndUnit> fPositionCommand;
  std::unique_ptr<G4ParticleGun> fParticleGun;
  G4String fDirectionMode = "fixed";
  G4int fPhotonsPerEvent = 1;
  G4ThreeVector fPosition;
  std::int64_t fDirectionSamples = 0;
  G4ThreeVector fDirectionSum;
  G4ThreeVector fDirectionSquareSum;
};

}  // namespace gagg

#endif
