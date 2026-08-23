#include "GAGG/DetectorConstruction.hh"

#include "GAGG/SimulationConfig.hh"

#include "G4Box.hh"
#include "G4LogicalVolume.hh"
#include "G4Material.hh"
#include "G4MaterialPropertiesTable.hh"
#include "G4NistManager.hh"
#include "G4PVPlacement.hh"
#include "G4Tubs.hh"

#include <vector>

namespace gagg {

G4VPhysicalVolume* DetectorConstruction::Construct() {
  auto* nist = G4NistManager::Instance();
  const std::vector<G4double> energies = {
      config::kOpticalEnergyMin, config::kOpticalEnergyMax};

  auto* vacuum = nist->FindOrBuildMaterial("G4_Galactic");
  const std::vector<G4double> vacuumIndex = {1.0, 1.0};
  auto* vacuumMpt = new G4MaterialPropertiesTable();
  vacuumMpt->AddProperty("RINDEX", energies, vacuumIndex);
  vacuum->SetMaterialPropertiesTable(vacuumMpt);

  auto* gagg = new G4Material("GAGG_Ce", config::kCrystalDensity, 4);
  gagg->AddElement(nist->FindOrBuildElement("Gd"), 3);
  gagg->AddElement(nist->FindOrBuildElement("Al"), 2);
  gagg->AddElement(nist->FindOrBuildElement("Ga"), 3);
  gagg->AddElement(nist->FindOrBuildElement("O"), 12);

  const std::vector<G4double> gaggIndex = {
      config::kGaggRefractiveIndex, config::kGaggRefractiveIndex};
  const std::vector<G4double> absorption = {
      config::kAbsorptionLength, config::kAbsorptionLength};
  auto* gaggMpt = new G4MaterialPropertiesTable();
  gaggMpt->AddProperty("RINDEX", energies, gaggIndex);
  gaggMpt->AddProperty("ABSLENGTH", energies, absorption);
  gagg->SetMaterialPropertiesTable(gaggMpt);

  auto* worldSolid =
      new G4Box("World", config::kWorldHalfLength, config::kWorldHalfLength,
                config::kWorldHalfLength);
  auto* worldLogical = new G4LogicalVolume(worldSolid, vacuum, "World");
  auto* worldPhysical =
      new G4PVPlacement(nullptr, {}, worldLogical, "World", nullptr, false, 0,
                        true);

  auto* crystalSolid =
      new G4Tubs("GAGG", 0.0, config::kCrystalRadius,
                 0.5 * config::kCrystalLength, 0.0, twopi);
  auto* crystalLogical = new G4LogicalVolume(crystalSolid, gagg, "GAGG");
  new G4PVPlacement(nullptr, {}, crystalLogical, "GAGG", worldLogical, false,
                    0, true);
  return worldPhysical;
}

}  // namespace gagg
