#ifndef GAGG_SIMULATION_CONFIG_HH
#define GAGG_SIMULATION_CONFIG_HH

#include "G4PhysicalConstants.hh"
#include "G4SystemOfUnits.hh"
#include "globals.hh"

namespace gagg::config {

inline constexpr G4double kWorldHalfLength = 10.0 * cm;
inline constexpr G4double kCrystalRadius = 12.7 * mm;
inline constexpr G4double kCrystalLength = 25.4 * mm;
inline constexpr G4double kCrystalDensity = 6.63 * g / cm3;
inline constexpr G4double kEmissionWavelength = 550.0 * nm;
inline constexpr G4double kScintillationWavelengthMin = 545.0 * nm;
inline constexpr G4double kScintillationWavelengthMax = 555.0 * nm;
inline constexpr G4double kGaggRefractiveIndex = 1.91;
inline constexpr G4double kWorldRefractiveIndex = 1.0;
inline constexpr G4double kSelfAbsorptionCoefficient = 0.0155 / cm;
inline constexpr G4double kAbsorptionLength =
    1.0 / kSelfAbsorptionCoefficient;
inline constexpr G4double kReflectorThickness = 1.0 * mm;
inline constexpr G4double kReflectorDensity = 2.2 * g / cm3;
inline constexpr G4double kReflectorRefractiveIndex = 1.35;
inline constexpr G4double kReflectorAbsorptionCoefficient = 100.0 / cm;
inline constexpr G4double kReflectorAbsorptionLength =
    1.0 / kReflectorAbsorptionCoefficient;
inline constexpr G4double kReflectorOuterRadius =
    kCrystalRadius + kReflectorThickness;
inline constexpr G4double kTopReflectorCenterZ =
    0.5 * (kCrystalLength + kReflectorThickness);
inline constexpr G4double kOpticalEnergyMin = 2.0 * eV;
inline constexpr G4double kOpticalEnergyMax = 3.0 * eV;
inline constexpr G4double kScintillationYield = 54000.0 / MeV;
inline constexpr G4double kScintillationResolutionScale = 0.0;
inline constexpr G4double kFastScintillationTimeConstant = 62.53 * ns;
inline constexpr G4double kSlowScintillationTimeConstant = 190.89 * ns;
inline constexpr G4double kStageAGammaEnergy = 662.0 * keV;
inline constexpr G4double kStageAGammaSourceClearance = 1.0 * mm;
inline constexpr G4double kStageAGammaSourceZ =
    0.5 * kCrystalLength + kReflectorThickness +
    kStageAGammaSourceClearance;

inline G4double EmissionPhotonEnergy() {
  return h_Planck * c_light / kEmissionWavelength;
}

inline G4double PhotonEnergy(G4double wavelength) {
  return h_Planck * c_light / wavelength;
}

}  // namespace gagg::config

#endif
