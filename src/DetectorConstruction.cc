#include "GAGG/DetectorConstruction.hh"

#include "GAGG/SimulationConfig.hh"

#include "G4Box.hh"
#include "G4Colour.hh"
#include "G4GenericMessenger.hh"
#include "G4LogicalVolume.hh"
#include "G4Material.hh"
#include "G4MaterialPropertiesTable.hh"
#include "G4Navigator.hh"
#include "G4NistManager.hh"
#include "G4PVPlacement.hh"
#include "G4StateManager.hh"
#include "G4TransportationManager.hh"
#include "G4Tubs.hh"
#include "G4VisAttributes.hh"
#include "G4ios.hh"

#include <algorithm>
#include <cmath>
#include <vector>

namespace {

bool RelativeClose(G4double actual, G4double expected,
                   G4double relativeTolerance = 1.0e-12) {
  return std::abs(actual - expected) <=
         relativeTolerance * std::max(std::abs(expected), 1.0);
}

}  // namespace

namespace gagg {

DetectorConstruction::DetectorConstruction()
    : fMessenger(std::make_unique<G4GenericMessenger>(
          this, "/gagg/geometry/", "GAGG geometry controls")),
      fOpticsMessenger(std::make_unique<G4GenericMessenger>(
          this, "/gagg/optics/", "GAGG optical-material controls")) {
  auto& modeCommand = fMessenger->DeclareMethod(
      "mode", &DetectorConstruction::SetGeometryMode,
      "Select bare A0 geometry or paper A2 reflector geometry.");
  modeCommand.SetParameterName("mode", false);
  modeCommand.SetCandidates("bare paper");
  modeCommand.SetDefaultValue("bare");
  modeCommand.SetStates(G4State_PreInit);

  auto& validateCommand = fMessenger->DeclareMethod(
      "validate", &DetectorConstruction::ValidateGeometry,
      "Validate the initialized paper geometry.");
  validateCommand.SetStates(G4State_Idle);

  auto& absorptionCommand = fOpticsMessenger->DeclareProperty(
      "gaggBulkAbsorption", fGaggBulkAbsorption,
      "Enable the literature GAGG bulk self-absorption length.");
  absorptionCommand.SetStates(G4State_PreInit);
}

DetectorConstruction::~DetectorConstruction() = default;

void DetectorConstruction::SetGeometryMode(const G4String& mode) {
  fGeometryMode = mode;
}

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
  if (fGaggBulkAbsorption) {
    gaggMpt->AddProperty("ABSLENGTH", energies, absorption);
  }
  gagg->SetMaterialPropertiesTable(gaggMpt);

  auto* reflector = nist->FindOrBuildMaterial("G4_TEFLON");
  const std::vector<G4double> reflectorIndex = {
      config::kReflectorRefractiveIndex,
      config::kReflectorRefractiveIndex};
  const std::vector<G4double> reflectorAbsorption = {
      config::kReflectorAbsorptionLength,
      config::kReflectorAbsorptionLength};
  auto* reflectorMpt = new G4MaterialPropertiesTable();
  reflectorMpt->AddProperty("RINDEX", energies, reflectorIndex);
  reflectorMpt->AddProperty("ABSLENGTH", energies, reflectorAbsorption);
  reflector->SetMaterialPropertiesTable(reflectorMpt);

  auto* worldSolid =
      new G4Box("World", config::kWorldHalfLength, config::kWorldHalfLength,
                config::kWorldHalfLength);
  auto* worldLogical = new G4LogicalVolume(worldSolid, vacuum, "World");
  worldLogical->SetVisAttributes(G4VisAttributes::GetInvisible());
  fWorldPhysical =
      new G4PVPlacement(nullptr, {}, worldLogical, "World", nullptr, false, 0,
                        true);

  auto* crystalSolid =
      new G4Tubs("GAGG", 0.0, config::kCrystalRadius,
                 0.5 * config::kCrystalLength, 0.0, twopi);
  auto* crystalLogical = new G4LogicalVolume(crystalSolid, gagg, "GAGG");
  auto* crystalVis = new G4VisAttributes(G4Colour(0.95, 0.72, 0.08, 0.45));
  crystalVis->SetForceSolid(true);
  crystalLogical->SetVisAttributes(crystalVis);
  fCrystalPhysical =
      new G4PVPlacement(nullptr, {}, crystalLogical, "GAGG", worldLogical,
                        false, 0, true);

  fSideReflectorPhysical = nullptr;
  fTopReflectorPhysical = nullptr;
  if (fGeometryMode == "paper") {
    auto* sideSolid =
        new G4Tubs("SideReflectorSolid", config::kCrystalRadius,
                   config::kReflectorOuterRadius,
                   0.5 * config::kCrystalLength, 0.0, twopi);
    auto* sideLogical =
        new G4LogicalVolume(sideSolid, reflector, "SideReflectorLogical");
    auto* sideVis =
        new G4VisAttributes(G4Colour(0.20, 0.55, 0.95, 0.38));
    sideVis->SetForceSolid(true);
    sideLogical->SetVisAttributes(sideVis);
    fSideReflectorPhysical = new G4PVPlacement(
        nullptr, {}, sideLogical, "SideReflector", worldLogical, false, 0,
        true);

    auto* topSolid =
        new G4Tubs("TopReflectorSolid", 0.0,
                   config::kReflectorOuterRadius,
                   0.5 * config::kReflectorThickness, 0.0, twopi);
    auto* topLogical =
        new G4LogicalVolume(topSolid, reflector, "TopReflectorLogical");
    auto* topVis =
        new G4VisAttributes(G4Colour(0.55, 0.80, 1.00, 0.45));
    topVis->SetForceSolid(true);
    topLogical->SetVisAttributes(topVis);
    fTopReflectorPhysical = new G4PVPlacement(
        nullptr, {0.0, 0.0, config::kTopReflectorCenterZ}, topLogical,
        "TopReflector", worldLogical, false, 0, true);
  }

  G4cout << "[geometry] mode=" << fGeometryMode
         << " reflector_density=" << reflector->GetDensity() / (g / cm3)
         << " g/cm3 gagg_bulk_absorption="
         << (fGaggBulkAbsorption ? "on" : "off") << G4endl;
  return fWorldPhysical;
}

void DetectorConstruction::ValidateGeometry() {
  if (fGeometryMode != "paper" || fWorldPhysical == nullptr ||
      fCrystalPhysical == nullptr || fSideReflectorPhysical == nullptr ||
      fTopReflectorPhysical == nullptr) {
    G4cout << "[a2] geometry status=FAIL reason=paper_geometry_not_built"
           << G4endl;
    return;
  }

  const auto crystalExpected =
      pi * config::kCrystalRadius * config::kCrystalRadius *
      config::kCrystalLength;
  const auto sideExpected =
      pi * (config::kReflectorOuterRadius *
                config::kReflectorOuterRadius -
            config::kCrystalRadius * config::kCrystalRadius) *
      config::kCrystalLength;
  const auto topExpected =
      pi * config::kReflectorOuterRadius *
      config::kReflectorOuterRadius * config::kReflectorThickness;

  const auto crystalActual =
      fCrystalPhysical->GetLogicalVolume()->GetSolid()->GetCubicVolume();
  const auto sideActual = fSideReflectorPhysical->GetLogicalVolume()
                              ->GetSolid()
                              ->GetCubicVolume();
  const auto topActual = fTopReflectorPhysical->GetLogicalVolume()
                             ->GetSolid()
                             ->GetCubicVolume();
  const auto volumesPass = RelativeClose(crystalActual, crystalExpected) &&
                           RelativeClose(sideActual, sideExpected) &&
                           RelativeClose(topActual, topExpected);

  const auto overlaps = fCrystalPhysical->CheckOverlaps(10000, 0.0, false) ||
                        fSideReflectorPhysical->CheckOverlaps(10000, 0.0,
                                                              false) ||
                        fTopReflectorPhysical->CheckOverlaps(10000, 0.0,
                                                             false);

  auto* navigator = G4TransportationManager::GetTransportationManager()
                        ->GetNavigatorForTracking();
  const auto locateName = [navigator](const G4ThreeVector& point) {
    const auto* volume =
        navigator->LocateGlobalPointAndSetup(point, nullptr, false);
    return volume == nullptr ? G4String("none") : volume->GetName();
  };

  const auto centerName = locateName({0.0, 0.0, 0.0});
  const auto sideName = locateName(
      {config::kCrystalRadius + 0.5 * config::kReflectorThickness, 0.0, 0.0});
  const auto topName =
      locateName({0.0, 0.0, config::kTopReflectorCenterZ});
  const auto outputName = locateName(
      {0.0, 0.0,
       -0.5 * config::kCrystalLength - 0.25 * config::kReflectorThickness});
  const auto probesPass = centerName == "GAGG" &&
                          sideName == "SideReflector" &&
                          topName == "TopReflector" && outputName == "World";
  const auto* reflectorMaterial =
      fSideReflectorPhysical->GetLogicalVolume()->GetMaterial();
  const auto* reflectorProperties =
      reflectorMaterial->GetMaterialPropertiesTable();
  const auto* reflectorIndex = reflectorProperties == nullptr
                                   ? nullptr
                                   : reflectorProperties->GetProperty("RINDEX");
  const auto* reflectorAbsorption =
      reflectorProperties == nullptr
          ? nullptr
          : reflectorProperties->GetProperty("ABSLENGTH");
  const auto densityPass = RelativeClose(reflectorMaterial->GetDensity(),
                                         config::kReflectorDensity);
  const auto opticalPropertiesPass =
      reflectorIndex != nullptr && reflectorAbsorption != nullptr &&
      RelativeClose(reflectorIndex->Value(config::EmissionPhotonEnergy()),
                    config::kReflectorRefractiveIndex) &&
      RelativeClose(
          reflectorAbsorption->Value(config::EmissionPhotonEnergy()),
          config::kReflectorAbsorptionLength);
  const auto allPass = volumesPass && !overlaps && probesPass && densityPass &&
                       opticalPropertiesPass;

  G4cout << "[a2] crystal_volume_mm3=" << crystalActual / mm3
         << " side_volume_mm3=" << sideActual / mm3
         << " top_volume_mm3=" << topActual / mm3
         << " analytic_volumes=" << (volumesPass ? "PASS" : "FAIL")
         << G4endl;
  G4cout << "[a2] overlaps=" << (overlaps ? 1 : 0) << G4endl;
  G4cout << "[a2] center_probe=" << centerName
         << " side_probe=" << sideName << " top_probe=" << topName
         << " output_probe=" << outputName << G4endl;
  G4cout << "[a2] reflector_density_g_cm-3="
         << reflectorMaterial->GetDensity() / (g / cm3)
         << " check=" << (densityPass ? "PASS" : "FAIL") << G4endl;
  G4cout << "[a2] reflector_rindex="
         << (reflectorIndex == nullptr
                 ? -1.0
                 : reflectorIndex->Value(config::EmissionPhotonEnergy()))
         << " absorption_length_mm="
         << (reflectorAbsorption == nullptr
                 ? -1.0
                 : reflectorAbsorption->Value(
                       config::EmissionPhotonEnergy()) /
                       mm)
         << " bulk_properties="
         << (opticalPropertiesPass ? "PASS" : "FAIL") << G4endl;
  G4cout << "[a2] geometry status=" << (allPass ? "PASS" : "FAIL")
         << G4endl;
}

}  // namespace gagg
