#include "GAGG/DetectorConstruction.hh"

#include "GAGG/SimulationConfig.hh"

#include "G4Box.hh"
#include "G4Colour.hh"
#include "G4Exception.hh"
#include "G4GenericMessenger.hh"
#include "G4LogicalBorderSurface.hh"
#include "G4LogicalVolume.hh"
#include "G4Material.hh"
#include "G4MaterialPropertyVector.hh"
#include "G4MaterialPropertiesTable.hh"
#include "G4Navigator.hh"
#include "G4NistManager.hh"
#include "G4OpticalSurface.hh"
#include "G4PVPlacement.hh"
#include "G4RunManager.hh"
#include "G4StateManager.hh"
#include "G4TransportationManager.hh"
#include "G4Tubs.hh"
#include "G4VisAttributes.hh"
#include "G4ios.hh"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <filesystem>
#include <vector>

namespace {

bool RelativeClose(G4double actual, G4double expected,
                   G4double relativeTolerance = 1.0e-12) {
  return std::abs(actual - expected) <=
         relativeTolerance * std::max(std::abs(expected), 1.0);
}

G4OpticalSurfaceFinish StageASurfaceFinish(const G4String& name) {
  if (name == "polishedvm2000air") {
    return polishedvm2000air;
  }
  if (name == "polishedtioair") {
    return polishedtioair;
  }
  if (name == "groundvm2000air") {
    return groundvm2000air;
  }
  if (name == "groundtioair") {
    return groundtioair;
  }
  G4ExceptionDescription description;
  description << "Unsupported Stage A LUT surface: " << name;
  G4Exception("StageASurfaceFinish", "GAGG-A4-001", FatalException,
              description);
  return polishedvm2000air;
}

G4String StageASurfaceDataFile(const G4String& name) {
  if (name == "polishedvm2000air") {
    return "PolishedVM2000.z";
  }
  if (name == "polishedtioair") {
    return "PolishedTiO.z";
  }
  if (name == "groundvm2000air") {
    return "GroundVM2000.z";
  }
  if (name == "groundtioair") {
    return "GroundTiO.z";
  }
  return "none";
}

}  // namespace

namespace gagg {

DetectorConstruction::DetectorConstruction()
    : fMessenger(std::make_unique<G4GenericMessenger>(
          this, "/gagg/geometry/", "GAGG geometry controls")),
      fOpticsMessenger(std::make_unique<G4GenericMessenger>(
          this, "/gagg/optics/", "GAGG optical-material controls")),
      fStageAMessenger(std::make_unique<G4GenericMessenger>(
          this, "/gagg/stageA/", "Stage A LUT surface controls")) {
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

  auto& scintillationTimeCommand = fOpticsMessenger->DeclarePropertyWithUnit(
      "scintillationTimeConstant", "ns", fScintillationTimeConstant,
      "Set the single-component GAGG scintillation decay time.");
  scintillationTimeCommand.SetParameterName("tau", false);
  scintillationTimeCommand.SetRange("tau>0.");
  scintillationTimeCommand.SetDefaultValue("62.53");
  scintillationTimeCommand.SetStates(G4State_PreInit);

  auto& validateScintillationCommand = fOpticsMessenger->DeclareMethod(
      "validateScintillation", &DetectorConstruction::ValidateScintillation,
      "Validate the initialized GAGG scintillation properties.");
  validateScintillationCommand.SetStates(G4State_Idle);

  auto& surfaceCommand = fStageAMessenger->DeclareMethod(
      "surface", &DetectorConstruction::SetStageASurface,
      "Select the Stage A LBNL LUT finish; none disables the LUT boundary.");
  surfaceCommand.SetParameterName("finish", false);
  surfaceCommand.SetCandidates(
      "none polishedvm2000air polishedtioair groundvm2000air groundtioair");
  surfaceCommand.SetDefaultValue("none");
  surfaceCommand.SetStates(G4State_PreInit, G4State_Idle);

  auto& validateSurfaceCommand = fStageAMessenger->DeclareMethod(
      "validate", &DetectorConstruction::ValidateStageASurface,
      "Validate the active Stage A LUT surface and border assignments.");
  validateSurfaceCommand.SetStates(G4State_Idle);
}

DetectorConstruction::~DetectorConstruction() = default;

void DetectorConstruction::SetGeometryMode(const G4String& mode) {
  fGeometryMode = mode;
}

void DetectorConstruction::SetStageASurface(const G4String& surface) {
  if (surface == fStageASurface) {
    G4cout << "[a4] surface_change old=" << fStageASurface
           << " new=" << surface << " geometry_reinitialized=false"
           << " reason=unchanged" << G4endl;
    return;
  }

  const auto oldSurface = fStageASurface;
  fStageASurface = surface;
  if (G4StateManager::GetStateManager()->GetCurrentState() == G4State_Idle) {
    G4LogicalBorderSurface::CleanSurfaceTable();
    fWorldPhysical = nullptr;
    fCrystalPhysical = nullptr;
    fSideReflectorPhysical = nullptr;
    fTopReflectorPhysical = nullptr;
    G4RunManager::GetRunManager()->ReinitializeGeometry(true);
    G4cout << "[a4] surface_change old=" << oldSurface
           << " new=" << fStageASurface
           << " geometry_reinitialization_requested=true" << G4endl;
  }
}

G4String DetectorConstruction::GetRealSurfaceDataPath() const {
  const auto* path = std::getenv("G4REALSURFACEDATA");
  return path == nullptr ? G4String() : G4String(path);
}

G4VPhysicalVolume* DetectorConstruction::Construct() {
  auto* nist = G4NistManager::Instance();
  const std::vector<G4double> energies = {
      config::kOpticalEnergyMin, config::kOpticalEnergyMax};

  auto* vacuum = nist->FindOrBuildMaterial("G4_Galactic");
  if (vacuum->GetMaterialPropertiesTable() == nullptr) {
    const std::vector<G4double> vacuumIndex = {1.0, 1.0};
    auto* vacuumMpt = new G4MaterialPropertiesTable();
    vacuumMpt->AddProperty("RINDEX", energies, vacuumIndex);
    vacuum->SetMaterialPropertiesTable(vacuumMpt);
  }

  auto* gagg = G4Material::GetMaterial("GAGG_Ce", false);
  if (gagg == nullptr) {
    gagg = new G4Material("GAGG_Ce", config::kCrystalDensity, 4);
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
    const std::vector<G4double> scintillationEnergies = {
        config::PhotonEnergy(config::kScintillationWavelengthMax),
        config::EmissionPhotonEnergy(),
        config::PhotonEnergy(config::kScintillationWavelengthMin)};
    const std::vector<G4double> scintillationIntensity = {0.0, 1.0, 0.0};
    gaggMpt->AddProperty("SCINTILLATIONCOMPONENT1", scintillationEnergies,
                         scintillationIntensity);
    gaggMpt->AddConstProperty("SCINTILLATIONYIELD",
                              config::kScintillationYield);
    gaggMpt->AddConstProperty("RESOLUTIONSCALE",
                              config::kScintillationResolutionScale);
    gaggMpt->AddConstProperty("SCINTILLATIONTIMECONSTANT1",
                              fScintillationTimeConstant);
    gaggMpt->AddConstProperty("SCINTILLATIONYIELD1", 1.0);
    gagg->SetMaterialPropertiesTable(gaggMpt);
  }

  auto* reflector = nist->FindOrBuildMaterial("G4_TEFLON");
  if (reflector->GetMaterialPropertiesTable() == nullptr) {
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
  }

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

    ConfigureStageASurface();
  } else if (HasStageALutSurface()) {
    G4Exception("DetectorConstruction::Construct", "GAGG-A4-002",
                FatalException,
                "A Stage A LUT surface requires /gagg/geometry/mode paper");
  }

  G4cout << "[geometry] mode=" << fGeometryMode
         << " reflector_density=" << reflector->GetDensity() / (g / cm3)
         << " g/cm3 gagg_bulk_absorption="
         << (fGaggBulkAbsorption ? "on" : "off") << G4endl;
  return fWorldPhysical;
}

void DetectorConstruction::ConfigureStageASurface() {
  if (!HasStageALutSurface()) {
    G4cout << "[a4] surface=none model=none borders=0 data_status=SKIP"
           << G4endl;
    return;
  }

  const auto dataPath = GetRealSurfaceDataPath();
  const auto dataFile = StageASurfaceDataFile(fStageASurface);
  const auto fullPath =
      std::filesystem::path(dataPath.c_str()) / dataFile.c_str();
  if (dataPath.empty() || !std::filesystem::is_regular_file(fullPath)) {
    G4ExceptionDescription description;
    description << "G4REALSURFACEDATA does not provide " << dataFile
                << "; resolved path=" << fullPath.string();
    G4Exception("DetectorConstruction::ConfigureStageASurface",
                "GAGG-A4-003", FatalException, description);
  }

  const auto finish = StageASurfaceFinish(fStageASurface);
  if (fStageAOpticalSurface == nullptr) {
    fStageAOpticalSurface = std::make_unique<G4OpticalSurface>(
        "StageALUTOpticalSurface", LUT, finish, dielectric_LUT);
  } else {
    fStageAOpticalSurface->SetFinish(finish);
  }

  new G4LogicalBorderSurface("GAGGToSideStageALUT", fCrystalPhysical,
                             fSideReflectorPhysical,
                             fStageAOpticalSurface.get());
  new G4LogicalBorderSurface("GAGGToTopStageALUT", fCrystalPhysical,
                             fTopReflectorPhysical,
                             fStageAOpticalSurface.get());

  G4cout << "[a4] surface=" << fStageASurface
         << " model=LUT type=dielectric_LUT borders=2 data_path=" << dataPath
         << " data_file=" << dataFile << " data_status=PASS" << G4endl;
}

void DetectorConstruction::ValidateStageASurface() {
  const auto dataPath = GetRealSurfaceDataPath();
  const auto dataFile = StageASurfaceDataFile(fStageASurface);
  const auto dataPass = HasStageALutSurface() && !dataPath.empty() &&
                        std::filesystem::is_regular_file(
                            std::filesystem::path(dataPath.c_str()) /
                            dataFile.c_str());
  const auto* sideBorder =
      G4LogicalBorderSurface::GetSurface(fCrystalPhysical,
                                         fSideReflectorPhysical);
  const auto* topBorder =
      G4LogicalBorderSurface::GetSurface(fCrystalPhysical,
                                         fTopReflectorPhysical);
  const auto* sideSurface =
      sideBorder == nullptr
          ? nullptr
          : dynamic_cast<const G4OpticalSurface*>(
                sideBorder->GetSurfaceProperty());
  const auto* topSurface =
      topBorder == nullptr
          ? nullptr
          : dynamic_cast<const G4OpticalSurface*>(
                topBorder->GetSurfaceProperty());
  const auto expectedFinish = HasStageALutSurface()
                                  ? StageASurfaceFinish(fStageASurface)
                                  : polished;
  const auto surfacePass = sideSurface != nullptr && topSurface != nullptr &&
                           sideSurface == topSurface &&
                           sideSurface->GetModel() == LUT &&
                           sideSurface->GetType() == dielectric_LUT &&
                           sideSurface->GetFinish() == expectedFinish;
  const auto borderPass =
      G4LogicalBorderSurface::GetNumberOfBorderSurfaces() == 2;
  const auto allPass = fGeometryMode == "paper" && dataPass && surfacePass &&
                       borderPass;

  G4cout << "[a4] surface_validation finish=" << fStageASurface
         << " model="
         << (sideSurface == nullptr || sideSurface->GetModel() != LUT
                 ? "invalid"
                 : "LUT")
         << " type="
         << (sideSurface == nullptr ||
                     sideSurface->GetType() != dielectric_LUT
                 ? "invalid"
                 : "dielectric_LUT")
         << " borders="
         << G4LogicalBorderSurface::GetNumberOfBorderSurfaces()
         << " data_file=" << dataFile
         << " data_status=" << (dataPass ? "PASS" : "FAIL")
         << " status=" << (allPass ? "PASS" : "FAIL") << G4endl;
}

void DetectorConstruction::ValidateScintillation() {
  const auto* gagg = G4Material::GetMaterial("GAGG_Ce", false);
  const auto* properties =
      gagg == nullptr ? nullptr : gagg->GetMaterialPropertiesTable();
  const auto* spectrum =
      properties == nullptr
          ? nullptr
          : properties->GetProperty("SCINTILLATIONCOMPONENT1");
  const auto constantsPass =
      properties != nullptr &&
      properties->ConstPropertyExists("SCINTILLATIONYIELD") &&
      properties->ConstPropertyExists("RESOLUTIONSCALE") &&
      properties->ConstPropertyExists("SCINTILLATIONTIMECONSTANT1") &&
      properties->ConstPropertyExists("SCINTILLATIONYIELD1");
  const auto yield = constantsPass
                         ? properties->GetConstProperty("SCINTILLATIONYIELD")
                         : -1.0;
  const auto resolutionScale =
      constantsPass ? properties->GetConstProperty("RESOLUTIONSCALE") : -1.0;
  const auto timeConstant =
      constantsPass
          ? properties->GetConstProperty("SCINTILLATIONTIMECONSTANT1")
          : -1.0;
  const auto componentFraction =
      constantsPass ? properties->GetConstProperty("SCINTILLATIONYIELD1")
                    : -1.0;
  const auto constantsValuesPass =
      constantsPass && RelativeClose(yield, config::kScintillationYield) &&
      RelativeClose(resolutionScale,
                    config::kScintillationResolutionScale) &&
      RelativeClose(timeConstant, fScintillationTimeConstant) &&
      RelativeClose(componentFraction, 1.0);

  const auto spectrumPass =
      spectrum != nullptr && spectrum->GetVectorLength() == 3 &&
      RelativeClose(
          spectrum->Energy(0),
          config::PhotonEnergy(config::kScintillationWavelengthMax)) &&
      RelativeClose(spectrum->Energy(1), config::EmissionPhotonEnergy()) &&
      RelativeClose(
          spectrum->Energy(2),
          config::PhotonEnergy(config::kScintillationWavelengthMin)) &&
      RelativeClose((*spectrum)[0], 0.0) &&
      RelativeClose((*spectrum)[1], 1.0) &&
      RelativeClose((*spectrum)[2], 0.0);
  const auto allPass = constantsValuesPass && spectrumPass;

  G4cout << "[a5] scintillation_yield_photons_per_MeV=" << yield * MeV
         << " resolution_scale=" << resolutionScale
         << " time_constant_ns=" << timeConstant / ns
         << " component_fraction=" << componentFraction << G4endl;
  G4cout << "[a5] emission_min_nm="
         << config::kScintillationWavelengthMin / nm
         << " emission_peak_nm=" << config::kEmissionWavelength / nm
         << " emission_max_nm="
         << config::kScintillationWavelengthMax / nm
         << " spectrum_points="
         << (spectrum == nullptr ? 0 : spectrum->GetVectorLength())
         << " spectrum_status=" << (spectrumPass ? "PASS" : "FAIL")
         << G4endl;
  G4cout << "[a5] scintillation_material status="
         << (allPass ? "PASS" : "FAIL") << G4endl;
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
