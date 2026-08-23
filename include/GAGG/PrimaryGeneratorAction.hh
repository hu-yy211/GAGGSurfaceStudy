#ifndef GAGG_PRIMARY_GENERATOR_ACTION_HH
#define GAGG_PRIMARY_GENERATOR_ACTION_HH

#include "G4VUserPrimaryGeneratorAction.hh"

#include <memory>

class G4ParticleGun;

namespace gagg {

class PrimaryGeneratorAction final : public G4VUserPrimaryGeneratorAction {
 public:
  PrimaryGeneratorAction();
  ~PrimaryGeneratorAction() override;
  void GeneratePrimaries(G4Event*) override;

 private:
  std::unique_ptr<G4ParticleGun> fParticleGun;
};

}  // namespace gagg

#endif

