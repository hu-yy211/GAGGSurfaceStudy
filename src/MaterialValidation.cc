#include "GAGG/MaterialValidation.hh"

#include "GAGG/SimulationConfig.hh"

#include "G4SystemOfUnits.hh"
#include "G4ios.hh"

#include <cmath>

namespace {

bool CloseTo(G4double actual, G4double expected, G4double tolerance) {
  return std::abs(actual - expected) <= tolerance;
}

}  // namespace

namespace gagg {

int RunMaterialValidation() {
  const auto densityGPerCm3 = config::kCrystalDensity / (g / cm3);
  const auto photonEnergyEv = config::EmissionPhotonEnergy() / eV;
  const auto absorptionLengthCm = config::kAbsorptionLength / cm;
  const auto reflectorThicknessMm = config::kReflectorThickness / mm;
  const auto reflectorLengthMm = config::kReflectorAbsorptionLength / mm;
  const auto gridIncreasing =
      config::kOpticalEnergyMin < config::kOpticalEnergyMax;
  const auto gridCoversEmission =
      config::kOpticalEnergyMin < config::EmissionPhotonEnergy() &&
      config::EmissionPhotonEnergy() < config::kOpticalEnergyMax;

  const auto densityPass = CloseTo(densityGPerCm3, 6.63, 1.0e-12);
  const auto refractiveIndexPass =
      CloseTo(config::kGaggRefractiveIndex, 1.91, 1.0e-12);
  const auto energyPass = CloseTo(photonEnergyEv, 2.25426, 1.0e-5);
  const auto gaggLengthPass =
      CloseTo(absorptionLengthCm, 64.516129, 1.0e-5);
  const auto reflectorLengthPass =
      CloseTo(reflectorLengthMm, 0.1, 1.0e-12);
  const auto reflectorPropertiesPass =
      CloseTo(reflectorThicknessMm, 1.0, 1.0e-12) &&
      CloseTo(config::kReflectorRefractiveIndex, 1.35, 1.0e-12);
  const auto allPass = densityPass && refractiveIndexPass && energyPass &&
                       gaggLengthPass && reflectorLengthPass &&
                       reflectorPropertiesPass && gridIncreasing &&
                       gridCoversEmission;

  G4cout << "[a1] density_g_cm-3=" << densityGPerCm3
         << " refractive_index=" << config::kGaggRefractiveIndex
         << " check="
         << (densityPass && refractiveIndexPass ? "PASS" : "FAIL")
         << G4endl;
  G4cout << "[a1] wavelength_nm=" << config::kEmissionWavelength / nm
         << " photon_energy_eV=" << photonEnergyEv
         << " check=" << (energyPass ? "PASS" : "FAIL") << G4endl;
  G4cout << "[a1] gagg_absorption_coefficient_cm-1="
         << config::kSelfAbsorptionCoefficient * cm
         << " absorption_length_cm=" << absorptionLengthCm
         << " check=" << (gaggLengthPass ? "PASS" : "FAIL") << G4endl;
  G4cout << "[a1] reflector_absorption_coefficient_cm-1="
         << config::kReflectorAbsorptionCoefficient * cm
         << " absorption_length_mm=" << reflectorLengthMm
         << " check=" << (reflectorLengthPass ? "PASS" : "FAIL") << G4endl;
  G4cout << "[a1] reflector_thickness_mm=" << reflectorThicknessMm
         << " refractive_index=" << config::kReflectorRefractiveIndex
         << " check=" << (reflectorPropertiesPass ? "PASS" : "FAIL")
         << G4endl;
  G4cout << "[a1] optical_grid_increasing="
         << (gridIncreasing ? "true" : "false")
         << " covers_emission=" << (gridCoversEmission ? "true" : "false")
         << G4endl;
  G4cout << "[a1] material_units status=" << (allPass ? "PASS" : "FAIL")
         << G4endl;
  return allPass ? 0 : 4;
}

}  // namespace gagg
