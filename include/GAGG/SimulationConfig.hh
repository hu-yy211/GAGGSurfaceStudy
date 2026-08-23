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
// Diagnostic-only explicit air separation used to test the meaning of the
// legacy LUT finishes ending in "air". This is not a measured paper value.
inline constexpr G4double kStageAAirGapDiagnostic = 0.1 * mm;
inline constexpr G4double kReflectorDensity = 2.2 * g / cm3;
inline constexpr G4double kReflectorRefractiveIndex = 1.35;
inline constexpr G4double kReflectorAbsorptionCoefficient = 100.0 / cm;
inline constexpr G4double kReflectorAbsorptionLength =
    1.0 / kReflectorAbsorptionCoefficient;
inline constexpr G4double kVm2000Reflectivity = 0.98;
inline constexpr G4double kTiOReflectivity = 0.95;
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

// Stage B measured crystal dimensions.
inline constexpr G4double kExperimentCrystalWidth = 5.75 * mm;
inline constexpr G4double kExperimentCrystalDepth = 5.75 * mm;
inline constexpr G4double kExperimentCrystalLength = 20.0 * mm;

// B0 geometry placeholders. These remain runtime-selectable and must be
// replaced by measurements before quantitative Stage B comparison.
inline constexpr G4double kExperimentSideAirGapDefault = 0.1 * mm;
inline constexpr G4double kExperimentBlackHousingThicknessDefault = 1.0 * mm;
inline constexpr G4double kExperimentEsrThicknessDefault = 0.1 * mm;
inline constexpr G4double kExperimentPmtWindowThicknessDefault = 0.5 * mm;
inline constexpr G4double kExperimentPmtWindowRefractiveIndex = 1.52;
inline constexpr G4double kExperimentBlackRefractiveIndex = 1.50;
inline constexpr G4double kExperimentBlackAbsorptionLength = 1.0 * um;
inline constexpr G4double kExperimentEsrReflectivity = 0.98;
inline constexpr G4double kExperimentBlackReflectivity = 0.0;
// B1 validation-only free parameter. It is shared by every rough GAGG face
// and is not fitted to the six experimental light-output values.
inline constexpr G4double kStageBSigmaAlphaValidation = 0.20 * rad;

inline G4double EmissionPhotonEnergy() {
  return h_Planck * c_light / kEmissionWavelength;
}

inline G4double PhotonEnergy(G4double wavelength) {
  return h_Planck * c_light / wavelength;
}

}  // namespace gagg::config

#endif
