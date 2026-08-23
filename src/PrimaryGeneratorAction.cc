#include "GAGG/PrimaryGeneratorAction.hh"

#include "GAGG/SimulationConfig.hh"

#include "G4OpticalPhoton.hh"
#include "G4ParticleGun.hh"

namespace gagg {

PrimaryGeneratorAction::PrimaryGeneratorAction()
    : fParticleGun(std::make_unique<G4ParticleGun>(1)) {
  fParticleGun->SetParticleDefinition(G4OpticalPhoton::Definition());
  fParticleGun->SetParticleEnergy(config::EmissionPhotonEnergy());
  fParticleGun->SetParticlePosition({0.0, 0.0, 0.0});
  fParticleGun->SetParticleMomentumDirection({0.0, 0.0, 1.0});
  fParticleGun->SetParticlePolarization({1.0, 0.0, 0.0});
}

PrimaryGeneratorAction::~PrimaryGeneratorAction() = default;

void PrimaryGeneratorAction::GeneratePrimaries(G4Event* event) {
  fParticleGun->GeneratePrimaryVertex(event);
}

}  // namespace gagg

