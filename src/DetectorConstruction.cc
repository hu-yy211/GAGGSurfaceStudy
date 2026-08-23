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
#include "G4SubtractionSolid.hh"
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

G4double StageASurfaceReflectivity(const G4String& name) {
  if (name == "polishedvm2000air" || name == "groundvm2000air") {
    return gagg::config::kVm2000Reflectivity;
  }
  if (name == "polishedtioair" || name == "groundtioair") {
    return gagg::config::kTiOReflectivity;
  }
  return 0.0;
}

struct StageBFaceTreatment {
  G4bool topRough = false;
  G4bool bottomRough = false;
  G4bool sideRough = false;
};

StageBFaceTreatment StageBFaceTreatmentFor(const G4String& state) {
  if (state == "all_polished") {
    return {};
  }
  if (state == "bottom_rough") {
    return {false, true, false};
  }
  if (state == "top_rough") {
    return {true, false, false};
  }
  if (state == "side_rough") {
    return {false, false, true};
  }
  if (state == "bottom_polished_others_rough") {
    return {true, false, true};
  }
  if (state == "top_polished_others_rough") {
    return {false, true, true};
  }
  G4ExceptionDescription description;
  description << "Unsupported Stage B surface state: " << state;
  G4Exception("StageBFaceTreatmentFor", "GAGG-B1-001", FatalException,
              description);
  return {};
}

const char* FaceFinishLabel(G4bool rough) {
  return rough ? "rough" : "polished";
}

}  // namespace

namespace gagg {

DetectorConstruction::DetectorConstruction()
    : fMessenger(std::make_unique<G4GenericMessenger>(
          this, "/gagg/geometry/", "GAGG geometry controls")),
      fOpticsMessenger(std::make_unique<G4GenericMessenger>(
          this, "/gagg/optics/", "GAGG optical-material controls")),
      fStageAMessenger(std::make_unique<G4GenericMessenger>(
          this, "/gagg/stageA/", "Stage A LUT surface controls")),
      fStageBMessenger(std::make_unique<G4GenericMessenger>(
          this, "/gagg/stageB/", "Stage B experiment geometry controls")),
      fScoringMessenger(std::make_unique<G4GenericMessenger>(
          this, "/gagg/scoring/", "Optical output scoring controls")) {
  auto& modeCommand = fMessenger->DeclareMethod(
      "mode", &DetectorConstruction::SetGeometryMode,
      "Select bare A0, paper Stage A, or experimental Stage B geometry.");
  modeCommand.SetParameterName("mode", false);
  modeCommand.SetCandidates("bare paper experiment");
  modeCommand.SetDefaultValue("bare");
  modeCommand.SetStates(G4State_PreInit);

  auto& validateCommand = fMessenger->DeclareMethod(
      "validate", &DetectorConstruction::ValidateGeometry,
      "Validate the initialized paper or experiment geometry.");
  validateCommand.SetStates(G4State_Idle);

  auto& absorptionCommand = fOpticsMessenger->DeclareProperty(
      "gaggBulkAbsorption", fGaggBulkAbsorption,
      "Enable the literature GAGG bulk self-absorption length.");
  absorptionCommand.SetStates(G4State_PreInit);

  auto& absorptionScaleCommand = fOpticsMessenger->DeclareProperty(
      "gaggAbsorptionLengthScale", fGaggAbsorptionLengthScale,
      "Scale the validated GAGG absorption length for explicitly labeled "
      "diagnostic runs; the physical default is 1.");
  absorptionScaleCommand.SetParameterName("scale", false);
  absorptionScaleCommand.SetRange("scale>0.");
  absorptionScaleCommand.SetDefaultValue("1.");
  absorptionScaleCommand.SetStates(G4State_PreInit);

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

  auto& reflectivityCommand = fStageAMessenger->DeclareProperty(
      "usePaperReflectivity", fStageAUsePaperReflectivity,
      "Use the paper's 0.98 VM2000 and 0.95 TiO reflectivity lower bounds; "
      "false is reserved for LUT-default diagnostics.");
  reflectivityCommand.SetStates(G4State_PreInit);

  auto& interfaceCommand = fStageAMessenger->DeclareProperty(
      "interfaceMode", fStageAInterfaceMode,
      "Connect the LUT directly to the reflector or through an explicit air "
      "volume for a labeled A7 diagnostic.");
  interfaceCommand.SetCandidates("direct airgap");
  interfaceCommand.SetDefaultValue("direct");
  interfaceCommand.SetStates(G4State_PreInit);

  auto& airGapCommand = fStageAMessenger->DeclarePropertyWithUnit(
      "airGap", "mm", fStageAAirGap,
      "Diagnostic explicit Stage A air-gap thickness; not a paper fit "
      "parameter.");
  airGapCommand.SetParameterName("gap", false);
  airGapCommand.SetRange("gap>0.");
  airGapCommand.SetDefaultValue("0.1");
  airGapCommand.SetStates(G4State_PreInit);

  auto& validateSurfaceCommand = fStageAMessenger->DeclareMethod(
      "validate", &DetectorConstruction::ValidateStageASurface,
      "Validate the active Stage A LUT surface and border assignments.");
  validateSurfaceCommand.SetStates(G4State_Idle);

  auto& outputModeCommand = fScoringMessenger->DeclareProperty(
      "outputMode", fOutputScoringMode,
      "Count transmitted photons or terminate/count each photon at its first "
      "geometrical arrival at the crystal output face.");
  outputModeCommand.SetCandidates("transmitted firstArrival");
  outputModeCommand.SetDefaultValue("firstArrival");
  outputModeCommand.SetStates(G4State_PreInit);

  auto& experimentAirGapCommand =
      fStageBMessenger->DeclarePropertyWithUnit(
          "sideAirGap", "mm", fExperimentSideAirGap,
          "Stage B side air gap. The B0 default is an explicit unmeasured "
          "placeholder.");
  experimentAirGapCommand.SetParameterName("gap", false);
  experimentAirGapCommand.SetRange("gap>0.");
  experimentAirGapCommand.SetDefaultValue("0.1");
  experimentAirGapCommand.SetStates(G4State_PreInit);

  auto& experimentBlackCommand =
      fStageBMessenger->DeclarePropertyWithUnit(
          "blackHousingThickness", "mm",
          fExperimentBlackHousingThickness,
          "Stage B black absorbing side-housing thickness.");
  experimentBlackCommand.SetParameterName("thickness", false);
  experimentBlackCommand.SetRange("thickness>0.");
  experimentBlackCommand.SetDefaultValue("1.0");
  experimentBlackCommand.SetStates(G4State_PreInit);

  auto& experimentEsrCommand =
      fStageBMessenger->DeclarePropertyWithUnit(
          "esrThickness", "mm", fExperimentEsrThickness,
          "Stage B top ESR thickness; B0 uses a documented placeholder.");
  experimentEsrCommand.SetParameterName("thickness", false);
  experimentEsrCommand.SetRange("thickness>0.");
  experimentEsrCommand.SetDefaultValue("0.1");
  experimentEsrCommand.SetStates(G4State_PreInit);

  auto& experimentPmtCommand =
      fStageBMessenger->DeclarePropertyWithUnit(
          "pmtWindowThickness", "mm", fExperimentPmtWindowThickness,
          "Stage B PMT receiver-window thickness; B0 uses direct crystal "
          "contact.");
  experimentPmtCommand.SetParameterName("thickness", false);
  experimentPmtCommand.SetRange("thickness>0.");
  experimentPmtCommand.SetDefaultValue("0.5");
  experimentPmtCommand.SetStates(G4State_PreInit);

  auto& experimentSurfaceStateCommand = fStageBMessenger->DeclareMethod(
      "surfaceState", &DetectorConstruction::SetStageBSurfaceState,
      "Select one of the six experimental GAGG face-treatment states.");
  experimentSurfaceStateCommand.SetParameterName("state", false);
  experimentSurfaceStateCommand.SetCandidates(
      "all_polished bottom_rough top_rough side_rough "
      "bottom_polished_others_rough top_polished_others_rough");
  experimentSurfaceStateCommand.SetDefaultValue("all_polished");
  experimentSurfaceStateCommand.SetStates(G4State_PreInit, G4State_Idle);

  auto& experimentSigmaCommand =
      fStageBMessenger->DeclareMethodWithUnit(
          "sigmaAlpha", "rad", &DetectorConstruction::SetStageBSigmaAlpha,
          "Set the one shared UNIFIED micro-facet sigma_alpha for every "
          "rough GAGG face.");
  experimentSigmaCommand.SetParameterName("sigma_alpha", false);
  experimentSigmaCommand.SetRange("sigma_alpha>=0. && sigma_alpha<1.5708");
  experimentSigmaCommand.SetDefaultValue("0.20");
  experimentSigmaCommand.SetStates(G4State_PreInit, G4State_Idle);

  auto& experimentSurfaceValidateCommand =
      fStageBMessenger->DeclareMethod(
          "validate", &DetectorConstruction::ValidateStageBSurfaces,
          "Validate Stage B top, bottom and side UNIFIED face assignments.");
  experimentSurfaceValidateCommand.SetStates(G4State_Idle);
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
    ResetPhysicalVolumePointers();
    G4RunManager::GetRunManager()->ReinitializeGeometry(true);
    G4cout << "[a4] surface_change old=" << oldSurface
           << " new=" << fStageASurface
           << " geometry_reinitialization_requested=true" << G4endl;
  }
}

void DetectorConstruction::SetStageBSurfaceState(const G4String& state) {
  StageBFaceTreatmentFor(state);
  if (state == fStageBSurfaceState) {
    G4cout << "[b1] surface_state_change old=" << fStageBSurfaceState
           << " new=" << state << " geometry_reinitialized=false"
           << " reason=unchanged" << G4endl;
    return;
  }
  const auto oldState = fStageBSurfaceState;
  fStageBSurfaceState = state;
  if (G4StateManager::GetStateManager()->GetCurrentState() == G4State_Idle) {
    G4LogicalBorderSurface::CleanSurfaceTable();
    ResetPhysicalVolumePointers();
    G4RunManager::GetRunManager()->ReinitializeGeometry(true);
    G4cout << "[b1] surface_state_change old=" << oldState
           << " new=" << fStageBSurfaceState
           << " geometry_reinitialization_requested=true" << G4endl;
  }
}

void DetectorConstruction::SetStageBSigmaAlpha(G4double sigmaAlpha) {
  if (sigmaAlpha < 0.0 || sigmaAlpha >= halfpi) {
    G4Exception("DetectorConstruction::SetStageBSigmaAlpha", "GAGG-B1-002",
                FatalException,
                "Stage B sigma_alpha must satisfy 0 <= value < pi/2");
  }
  if (RelativeClose(sigmaAlpha, fStageBSigmaAlpha)) {
    G4cout << "[b1] sigma_alpha_change old_rad=" << fStageBSigmaAlpha / rad
           << " new_rad=" << sigmaAlpha / rad
           << " geometry_reinitialized=false reason=unchanged" << G4endl;
    return;
  }
  const auto oldSigma = fStageBSigmaAlpha;
  fStageBSigmaAlpha = sigmaAlpha;
  if (G4StateManager::GetStateManager()->GetCurrentState() == G4State_Idle) {
    G4LogicalBorderSurface::CleanSurfaceTable();
    ResetPhysicalVolumePointers();
    G4RunManager::GetRunManager()->ReinitializeGeometry(true);
    G4cout << "[b1] sigma_alpha_change old_rad=" << oldSigma / rad
           << " new_rad=" << fStageBSigmaAlpha / rad
           << " geometry_reinitialization_requested=true" << G4endl;
  }
}

void DetectorConstruction::ResetPhysicalVolumePointers() {
  fWorldPhysical = nullptr;
  fCrystalPhysical = nullptr;
  fSideReflectorPhysical = nullptr;
  fTopReflectorPhysical = nullptr;
  fSideAirGapPhysical = nullptr;
  fTopAirGapPhysical = nullptr;
  fExperimentSideAirGapPhysical = nullptr;
  fExperimentBlackHousingPhysical = nullptr;
  fExperimentEsrPhysical = nullptr;
  fExperimentPmtWindowPhysical = nullptr;
}

G4String DetectorConstruction::GetRealSurfaceDataPath() const {
  const auto* path = std::getenv("G4REALSURFACEDATA");
  return path == nullptr ? G4String() : G4String(path);
}

G4double DetectorConstruction::GetStageAReflectivity() const {
  return fStageAUsePaperReflectivity
             ? StageASurfaceReflectivity(fStageASurface)
             : 1.0;
}

G4double DetectorConstruction::GetCrystalSizeX() const {
  return fGeometryMode == "experiment"
             ? config::kExperimentCrystalWidth
             : 2.0 * config::kCrystalRadius;
}

G4double DetectorConstruction::GetCrystalSizeY() const {
  return fGeometryMode == "experiment"
             ? config::kExperimentCrystalDepth
             : 2.0 * config::kCrystalRadius;
}

G4double DetectorConstruction::GetCrystalSizeZ() const {
  return fGeometryMode == "experiment"
             ? config::kExperimentCrystalLength
             : config::kCrystalLength;
}

G4bool DetectorConstruction::IsOnOutputFace(
    const G4ThreeVector& position, G4double tolerance) const {
  if (fGeometryMode == "experiment") {
    return std::abs(position.z() +
                    0.5 * config::kExperimentCrystalLength) < tolerance &&
           std::abs(position.x()) <
               0.5 * config::kExperimentCrystalWidth - tolerance &&
           std::abs(position.y()) <
               0.5 * config::kExperimentCrystalDepth - tolerance;
  }
  return std::abs(position.z() + 0.5 * config::kCrystalLength) < tolerance &&
         position.perp() < config::kCrystalRadius - tolerance;
}

G4String DetectorConstruction::GetOutputReceiverVolumeName() const {
  return fGeometryMode == "experiment" ? "PMTWindow" : "World";
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
        config::kAbsorptionLength * fGaggAbsorptionLengthScale,
        config::kAbsorptionLength * fGaggAbsorptionLengthScale};
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

  auto* air = nist->FindOrBuildMaterial("G4_AIR");
  if (air->GetMaterialPropertiesTable() == nullptr) {
    const std::vector<G4double> airIndex = {config::kWorldRefractiveIndex,
                                             config::kWorldRefractiveIndex};
    auto* airMpt = new G4MaterialPropertiesTable();
    airMpt->AddProperty("RINDEX", energies, airIndex);
    air->SetMaterialPropertiesTable(airMpt);
  }

  auto* experimentBlack = nist->FindOrBuildMaterial("G4_GRAPHITE");
  if (experimentBlack->GetMaterialPropertiesTable() == nullptr) {
    const std::vector<G4double> blackIndex = {
        config::kExperimentBlackRefractiveIndex,
        config::kExperimentBlackRefractiveIndex};
    const std::vector<G4double> blackAbsorption = {
        config::kExperimentBlackAbsorptionLength,
        config::kExperimentBlackAbsorptionLength};
    auto* blackMpt = new G4MaterialPropertiesTable();
    blackMpt->AddProperty("RINDEX", energies, blackIndex);
    blackMpt->AddProperty("ABSLENGTH", energies, blackAbsorption);
    experimentBlack->SetMaterialPropertiesTable(blackMpt);
  }

  auto* experimentEsr = nist->FindOrBuildMaterial("G4_MYLAR");
  auto* experimentPmtWindow =
      nist->FindOrBuildMaterial("G4_Pyrex_Glass");
  if (experimentPmtWindow->GetMaterialPropertiesTable() == nullptr) {
    const std::vector<G4double> windowIndex = {
        config::kExperimentPmtWindowRefractiveIndex,
        config::kExperimentPmtWindowRefractiveIndex};
    auto* windowMpt = new G4MaterialPropertiesTable();
    windowMpt->AddProperty("RINDEX", energies, windowIndex);
    experimentPmtWindow->SetMaterialPropertiesTable(windowMpt);
  }

  auto* worldSolid =
      new G4Box("World", config::kWorldHalfLength, config::kWorldHalfLength,
                config::kWorldHalfLength);
  auto* worldLogical = new G4LogicalVolume(worldSolid, vacuum, "World");
  worldLogical->SetVisAttributes(G4VisAttributes::GetInvisible());
  fWorldPhysical =
      new G4PVPlacement(nullptr, {}, worldLogical, "World", nullptr, false, 0,
                        true);

  G4VSolid* crystalSolid = nullptr;
  if (fGeometryMode == "experiment") {
    crystalSolid = new G4Box(
        "GAGG", 0.5 * config::kExperimentCrystalWidth,
        0.5 * config::kExperimentCrystalDepth,
        0.5 * config::kExperimentCrystalLength);
  } else {
    crystalSolid =
        new G4Tubs("GAGG", 0.0, config::kCrystalRadius,
                   0.5 * config::kCrystalLength, 0.0, twopi);
  }
  auto* crystalLogical = new G4LogicalVolume(crystalSolid, gagg, "GAGG");
  auto* crystalVis = new G4VisAttributes(G4Colour(0.95, 0.72, 0.08, 0.45));
  crystalVis->SetForceSolid(true);
  crystalLogical->SetVisAttributes(crystalVis);
  fCrystalPhysical =
      new G4PVPlacement(nullptr, {}, crystalLogical, "GAGG", worldLogical,
                        false, 0, true);

  fSideReflectorPhysical = nullptr;
  fTopReflectorPhysical = nullptr;
  fSideAirGapPhysical = nullptr;
  fTopAirGapPhysical = nullptr;
  fExperimentSideAirGapPhysical = nullptr;
  fExperimentBlackHousingPhysical = nullptr;
  fExperimentEsrPhysical = nullptr;
  fExperimentPmtWindowPhysical = nullptr;
  if (fGeometryMode == "paper") {
    const auto explicitAirGap = fStageAInterfaceMode == "airgap";
    const auto gap = explicitAirGap ? fStageAAirGap : 0.0;
    const auto reflectorInnerRadius = config::kCrystalRadius + gap;
    const auto reflectorOuterRadius =
        reflectorInnerRadius + config::kReflectorThickness;

    if (explicitAirGap) {
      auto* sideAirSolid = new G4Tubs(
          "SideAirGapSolid", config::kCrystalRadius, reflectorInnerRadius,
          0.5 * config::kCrystalLength, 0.0, twopi);
      auto* sideAirLogical =
          new G4LogicalVolume(sideAirSolid, air, "SideAirGapLogical");
      auto* airVis =
          new G4VisAttributes(G4Colour(0.70, 0.90, 1.00, 0.18));
      airVis->SetForceSolid(true);
      sideAirLogical->SetVisAttributes(airVis);
      fSideAirGapPhysical = new G4PVPlacement(
          nullptr, {}, sideAirLogical, "SideAirGap", worldLogical, false, 0,
          true);

      auto* topAirSolid =
          new G4Tubs("TopAirGapSolid", 0.0, reflectorOuterRadius,
                     0.5 * gap, 0.0, twopi);
      auto* topAirLogical =
          new G4LogicalVolume(topAirSolid, air, "TopAirGapLogical");
      topAirLogical->SetVisAttributes(airVis);
      fTopAirGapPhysical = new G4PVPlacement(
          nullptr, {0.0, 0.0, 0.5 * config::kCrystalLength + 0.5 * gap},
          topAirLogical, "TopAirGap", worldLogical, false, 0, true);
    }

    auto* sideSolid =
        new G4Tubs("SideReflectorSolid", reflectorInnerRadius,
                   reflectorOuterRadius,
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
                   reflectorOuterRadius,
                   0.5 * config::kReflectorThickness, 0.0, twopi);
    auto* topLogical =
        new G4LogicalVolume(topSolid, reflector, "TopReflectorLogical");
    auto* topVis =
        new G4VisAttributes(G4Colour(0.55, 0.80, 1.00, 0.45));
    topVis->SetForceSolid(true);
    topLogical->SetVisAttributes(topVis);
    fTopReflectorPhysical = new G4PVPlacement(
        nullptr,
        {0.0, 0.0,
         0.5 * config::kCrystalLength + gap +
             0.5 * config::kReflectorThickness},
        topLogical,
        "TopReflector", worldLogical, false, 0, true);

    ConfigureStageASurface();
  } else if (fGeometryMode == "experiment") {
    const auto crystalHalfX = 0.5 * config::kExperimentCrystalWidth;
    const auto crystalHalfY = 0.5 * config::kExperimentCrystalDepth;
    const auto crystalHalfZ = 0.5 * config::kExperimentCrystalLength;
    const auto gapOuterHalfX = crystalHalfX + fExperimentSideAirGap;
    const auto gapOuterHalfY = crystalHalfY + fExperimentSideAirGap;
    const auto housingOuterHalfX =
        gapOuterHalfX + fExperimentBlackHousingThickness;
    const auto housingOuterHalfY =
        gapOuterHalfY + fExperimentBlackHousingThickness;

    auto* gapOuter =
        new G4Box("ExperimentSideAirGapOuter", gapOuterHalfX,
                  gapOuterHalfY, crystalHalfZ);
    auto* gapInner =
        new G4Box("ExperimentSideAirGapInner", crystalHalfX,
                  crystalHalfY, crystalHalfZ);
    auto* gapSolid = new G4SubtractionSolid(
        "ExperimentSideAirGapSolid", gapOuter, gapInner);
    auto* gapLogical = new G4LogicalVolume(
        gapSolid, air, "ExperimentSideAirGapLogical");
    auto* gapVis =
        new G4VisAttributes(G4Colour(0.65, 0.90, 1.00, 0.18));
    gapVis->SetForceSolid(true);
    gapLogical->SetVisAttributes(gapVis);
    fExperimentSideAirGapPhysical = new G4PVPlacement(
        nullptr, {}, gapLogical, "ExperimentSideAirGap", worldLogical,
        false, 0, true);

    auto* housingOuter =
        new G4Box("ExperimentBlackHousingOuter", housingOuterHalfX,
                  housingOuterHalfY, crystalHalfZ);
    auto* housingInner =
        new G4Box("ExperimentBlackHousingInner", gapOuterHalfX,
                  gapOuterHalfY, crystalHalfZ);
    auto* housingSolid = new G4SubtractionSolid(
        "ExperimentBlackHousingSolid", housingOuter, housingInner);
    auto* housingLogical = new G4LogicalVolume(
        housingSolid, experimentBlack, "ExperimentBlackHousingLogical");
    auto* housingVis =
        new G4VisAttributes(G4Colour(0.05, 0.05, 0.05, 0.75));
    housingVis->SetForceSolid(true);
    housingLogical->SetVisAttributes(housingVis);
    fExperimentBlackHousingPhysical = new G4PVPlacement(
        nullptr, {}, housingLogical, "ExperimentBlackHousing", worldLogical,
        false, 0, true);

    auto* esrSolid =
        new G4Box("ExperimentESRSolid", crystalHalfX, crystalHalfY,
                  0.5 * fExperimentEsrThickness);
    auto* esrLogical = new G4LogicalVolume(
        esrSolid, experimentEsr, "ExperimentESRLogical");
    auto* esrVis =
        new G4VisAttributes(G4Colour(0.85, 0.90, 1.00, 0.70));
    esrVis->SetForceSolid(true);
    esrLogical->SetVisAttributes(esrVis);
    fExperimentEsrPhysical = new G4PVPlacement(
        nullptr,
        {0.0, 0.0, crystalHalfZ + 0.5 * fExperimentEsrThickness},
        esrLogical, "ExperimentESR", worldLogical, false, 0, true);

    auto* pmtSolid =
        new G4Box("ExperimentPMTWindowSolid", crystalHalfX, crystalHalfY,
                  0.5 * fExperimentPmtWindowThickness);
    auto* pmtLogical = new G4LogicalVolume(
        pmtSolid, experimentPmtWindow, "ExperimentPMTWindowLogical");
    auto* pmtVis =
        new G4VisAttributes(G4Colour(0.25, 0.75, 0.85, 0.55));
    pmtVis->SetForceSolid(true);
    pmtLogical->SetVisAttributes(pmtVis);
    fExperimentPmtWindowPhysical = new G4PVPlacement(
        nullptr,
        {0.0, 0.0,
         -crystalHalfZ - 0.5 * fExperimentPmtWindowThickness},
        pmtLogical, "PMTWindow", worldLogical, false, 0, true);

    ConfigureExperimentSurfaces();
  } else if (HasStageALutSurface()) {
    G4Exception("DetectorConstruction::Construct", "GAGG-A4-002",
                FatalException,
                "A Stage A LUT surface requires /gagg/geometry/mode paper");
  }

  G4cout << "[geometry] mode=" << fGeometryMode
         << " reflector_density=" << reflector->GetDensity() / (g / cm3)
         << " g/cm3 gagg_bulk_absorption="
         << (fGaggBulkAbsorption ? "on" : "off")
         << " gagg_absorption_length_scale=" << fGaggAbsorptionLengthScale
         << " stage_a_interface=" << fStageAInterfaceMode
         << " stage_a_air_gap_mm=" << fStageAAirGap / mm
         << " stage_b_side_air_gap_mm=" << fExperimentSideAirGap / mm
         << " output_scoring=" << fOutputScoringMode
         << G4endl;
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
  const auto reflectivity = GetStageAReflectivity();
  const std::vector<G4double> surfaceReflectivity = {
      reflectivity, reflectivity};
  const std::vector<G4double> surfaceTransmittance = {
      1.0 - reflectivity, 1.0 - reflectivity};
  const std::vector<G4double> energies = {
      config::kOpticalEnergyMin, config::kOpticalEnergyMax};
  fStageASurfaceProperties =
      std::make_unique<G4MaterialPropertiesTable>();
  fStageASurfaceProperties->AddProperty("REFLECTIVITY", energies,
                                        surfaceReflectivity);
  fStageASurfaceProperties->AddProperty("TRANSMITTANCE", energies,
                                         surfaceTransmittance);
  fStageAOpticalSurface->SetMaterialPropertiesTable(
      fStageASurfaceProperties.get());

  auto* sideTarget = fStageAInterfaceMode == "airgap"
                         ? fSideAirGapPhysical
                         : fSideReflectorPhysical;
  auto* topTarget = fStageAInterfaceMode == "airgap"
                        ? fTopAirGapPhysical
                        : fTopReflectorPhysical;
  new G4LogicalBorderSurface("GAGGToSideStageALUT", fCrystalPhysical,
                             sideTarget,
                             fStageAOpticalSurface.get());
  new G4LogicalBorderSurface("GAGGToTopStageALUT", fCrystalPhysical,
                             topTarget,
                             fStageAOpticalSurface.get());

  G4cout << "[a4] surface=" << fStageASurface
         << " model=LUT type=dielectric_LUT borders=2 data_path=" << dataPath
         << " data_file=" << dataFile
         << " reflectivity=" << reflectivity
         << " transmittance=" << 1.0 - reflectivity
         << " interface=" << fStageAInterfaceMode
         << " air_gap_mm=" << fStageAAirGap / mm
         << " data_status=PASS" << G4endl;
}

void DetectorConstruction::ConfigureExperimentSurfaces() {
  const std::vector<G4double> energies = {
      config::kOpticalEnergyMin, config::kOpticalEnergyMax};
  const std::vector<G4double> zeroEfficiency = {0.0, 0.0};
  const auto treatment = StageBFaceTreatmentFor(fStageBSurfaceState);
  const auto finishFor = [](G4bool rough) {
    return rough ? ground : polished;
  };

  if (fExperimentTopSurface == nullptr) {
    fExperimentTopSurface = std::make_unique<G4OpticalSurface>(
        "ExperimentTopSurface", unified, finishFor(treatment.topRough),
        dielectric_metal);
  }
  fExperimentTopSurface->SetModel(unified);
  fExperimentTopSurface->SetType(dielectric_metal);
  fExperimentTopSurface->SetFinish(finishFor(treatment.topRough));
  fExperimentTopSurface->SetSigmaAlpha(fStageBSigmaAlpha);
  const std::vector<G4double> esrReflectivity = {
      config::kExperimentEsrReflectivity,
      config::kExperimentEsrReflectivity};
  const std::vector<G4double> esrSpecularLobe = {
      config::kExperimentEsrSpecularLobe,
      config::kExperimentEsrSpecularLobe};
  const std::vector<G4double> esrSpecularSpike = {
      config::kExperimentEsrSpecularSpike,
      config::kExperimentEsrSpecularSpike};
  const std::vector<G4double> esrBackscatter = {
      config::kExperimentEsrBackscatter,
      config::kExperimentEsrBackscatter};
  fExperimentEsrProperties =
      std::make_unique<G4MaterialPropertiesTable>();
  fExperimentEsrProperties->AddProperty(
      "REFLECTIVITY", energies, esrReflectivity);
  fExperimentEsrProperties->AddProperty(
      "EFFICIENCY", energies, zeroEfficiency);
  fExperimentEsrProperties->AddProperty(
      "SPECULARLOBECONSTANT", energies, esrSpecularLobe);
  fExperimentEsrProperties->AddProperty(
      "SPECULARSPIKECONSTANT", energies, esrSpecularSpike);
  fExperimentEsrProperties->AddProperty(
      "BACKSCATTERCONSTANT", energies, esrBackscatter);
  fExperimentTopSurface->SetMaterialPropertiesTable(
      fExperimentEsrProperties.get());

  if (fExperimentBottomSurface == nullptr) {
    fExperimentBottomSurface = std::make_unique<G4OpticalSurface>(
        "ExperimentBottomSurface", unified,
        finishFor(treatment.bottomRough), dielectric_dielectric);
  }
  fExperimentBottomSurface->SetModel(unified);
  fExperimentBottomSurface->SetType(dielectric_dielectric);
  fExperimentBottomSurface->SetFinish(finishFor(treatment.bottomRough));
  fExperimentBottomSurface->SetSigmaAlpha(fStageBSigmaAlpha);

  if (fExperimentSideSurface == nullptr) {
    fExperimentSideSurface = std::make_unique<G4OpticalSurface>(
        "ExperimentSideSurface", unified, finishFor(treatment.sideRough),
        dielectric_dielectric);
  }
  fExperimentSideSurface->SetModel(unified);
  fExperimentSideSurface->SetType(dielectric_dielectric);
  fExperimentSideSurface->SetFinish(finishFor(treatment.sideRough));
  fExperimentSideSurface->SetSigmaAlpha(fStageBSigmaAlpha);

  if (fExperimentBlackSurface == nullptr) {
    fExperimentBlackSurface = std::make_unique<G4OpticalSurface>(
        "ExperimentBlackSurface", unified, polished, dielectric_metal);
  }
  const std::vector<G4double> blackReflectivity = {
      config::kExperimentBlackReflectivity,
      config::kExperimentBlackReflectivity};
  fExperimentBlackProperties =
      std::make_unique<G4MaterialPropertiesTable>();
  fExperimentBlackProperties->AddProperty(
      "REFLECTIVITY", energies, blackReflectivity);
  fExperimentBlackProperties->AddProperty(
      "EFFICIENCY", energies, zeroEfficiency);
  fExperimentBlackSurface->SetMaterialPropertiesTable(
      fExperimentBlackProperties.get());

  new G4LogicalBorderSurface(
      "GAGGToExperimentTop", fCrystalPhysical, fExperimentEsrPhysical,
      fExperimentTopSurface.get());
  new G4LogicalBorderSurface(
      "GAGGToExperimentBottom", fCrystalPhysical,
      fExperimentPmtWindowPhysical, fExperimentBottomSurface.get());
  new G4LogicalBorderSurface(
      "GAGGToExperimentSide", fCrystalPhysical,
      fExperimentSideAirGapPhysical, fExperimentSideSurface.get());
  new G4LogicalBorderSurface(
      "AirGapToExperimentBlack", fExperimentSideAirGapPhysical,
      fExperimentBlackHousingPhysical, fExperimentBlackSurface.get());

  G4cout << "[b1] surfaces state=" << fStageBSurfaceState
         << " model=UNIFIED top=" << FaceFinishLabel(treatment.topRough)
         << " bottom=" << FaceFinishLabel(treatment.bottomRough)
         << " side=" << FaceFinishLabel(treatment.sideRough)
         << " sigma_alpha_rad=" << fStageBSigmaAlpha / rad
         << " esr_reflectivity="
         << config::kExperimentEsrReflectivity
         << " black_reflectivity=" << config::kExperimentBlackReflectivity
         << " borders=4 status=PASS" << G4endl;
}

void DetectorConstruction::ValidateStageBSurfaces() {
  if (fGeometryMode != "experiment" || fCrystalPhysical == nullptr ||
      fExperimentSideAirGapPhysical == nullptr ||
      fExperimentBlackHousingPhysical == nullptr ||
      fExperimentEsrPhysical == nullptr ||
      fExperimentPmtWindowPhysical == nullptr) {
    G4cout << "[b1] surface_validation status=FAIL"
           << " reason=experiment_geometry_not_built" << G4endl;
    return;
  }

  const auto opticalSurface =
      [](const G4VPhysicalVolume* from, const G4VPhysicalVolume* to) {
        const auto* border = G4LogicalBorderSurface::GetSurface(from, to);
        return border == nullptr
                   ? static_cast<const G4OpticalSurface*>(nullptr)
                   : dynamic_cast<const G4OpticalSurface*>(
                         border->GetSurfaceProperty());
      };
  const auto* top =
      opticalSurface(fCrystalPhysical, fExperimentEsrPhysical);
  const auto* bottom =
      opticalSurface(fCrystalPhysical, fExperimentPmtWindowPhysical);
  const auto* side =
      opticalSurface(fCrystalPhysical, fExperimentSideAirGapPhysical);
  const auto* black =
      opticalSurface(fExperimentSideAirGapPhysical,
                     fExperimentBlackHousingPhysical);
  const auto treatment = StageBFaceTreatmentFor(fStageBSurfaceState);
  const auto expectedFinish = [](G4bool rough) {
    return rough ? ground : polished;
  };
  const auto topPass =
      top != nullptr && top->GetModel() == unified &&
      top->GetType() == dielectric_metal &&
      top->GetFinish() == expectedFinish(treatment.topRough);
  const auto bottomPass =
      bottom != nullptr && bottom->GetModel() == unified &&
      bottom->GetType() == dielectric_dielectric &&
      bottom->GetFinish() == expectedFinish(treatment.bottomRough);
  const auto sidePass =
      side != nullptr && side->GetModel() == unified &&
      side->GetType() == dielectric_dielectric &&
      side->GetFinish() == expectedFinish(treatment.sideRough);
  const auto blackPass =
      black != nullptr && black->GetModel() == unified &&
      black->GetType() == dielectric_metal &&
      black->GetFinish() == polished;
  const auto sigmaPass =
      top != nullptr && bottom != nullptr && side != nullptr &&
      RelativeClose(top->GetSigmaAlpha(), fStageBSigmaAlpha) &&
      RelativeClose(bottom->GetSigmaAlpha(), fStageBSigmaAlpha) &&
      RelativeClose(side->GetSigmaAlpha(), fStageBSigmaAlpha);
  const auto* topProperties =
      top == nullptr ? nullptr : top->GetMaterialPropertiesTable();
  const auto* topReflectivity =
      topProperties == nullptr
          ? nullptr
          : topProperties->GetProperty("REFLECTIVITY");
  const auto* topSpecularLobe =
      topProperties == nullptr
          ? nullptr
          : topProperties->GetProperty("SPECULARLOBECONSTANT");
  const auto* topSpecularSpike =
      topProperties == nullptr
          ? nullptr
          : topProperties->GetProperty("SPECULARSPIKECONSTANT");
  const auto* topBackscatter =
      topProperties == nullptr
          ? nullptr
          : topProperties->GetProperty("BACKSCATTERCONSTANT");
  const auto reflectivityPass =
      topReflectivity != nullptr &&
      RelativeClose(
          topReflectivity->Value(config::EmissionPhotonEnergy()),
          config::kExperimentEsrReflectivity);
  const auto reflectionComponentsPass =
      topSpecularLobe != nullptr && topSpecularSpike != nullptr &&
      topBackscatter != nullptr &&
      RelativeClose(
          topSpecularLobe->Value(config::EmissionPhotonEnergy()),
          config::kExperimentEsrSpecularLobe) &&
      RelativeClose(
          topSpecularSpike->Value(config::EmissionPhotonEnergy()),
          config::kExperimentEsrSpecularSpike) &&
      RelativeClose(
          topBackscatter->Value(config::EmissionPhotonEnergy()),
          config::kExperimentEsrBackscatter) &&
      RelativeClose(config::kExperimentEsrSpecularLobe +
                        config::kExperimentEsrSpecularSpike +
                        config::kExperimentEsrBackscatter,
                    1.0);
  const auto borderPass =
      G4LogicalBorderSurface::GetNumberOfBorderSurfaces() == 4;
  const auto allPass = topPass && bottomPass && sidePass && blackPass &&
                       sigmaPass && reflectivityPass &&
                       reflectionComponentsPass && borderPass;

  G4cout << "[b1] surface_validation state=" << fStageBSurfaceState
         << " top=" << FaceFinishLabel(treatment.topRough)
         << " bottom=" << FaceFinishLabel(treatment.bottomRough)
         << " side=" << FaceFinishLabel(treatment.sideRough)
         << " sigma_alpha_rad=" << fStageBSigmaAlpha / rad
         << " rough_shared=" << (sigmaPass ? "PASS" : "FAIL")
         << " esr_reflectivity="
         << (topReflectivity == nullptr
                 ? -1.0
                 : topReflectivity->Value(config::EmissionPhotonEnergy()))
         << " esr_specular_lobe="
         << (topSpecularLobe == nullptr
                 ? -1.0
                 : topSpecularLobe->Value(config::EmissionPhotonEnergy()))
         << " esr_specular_spike="
         << (topSpecularSpike == nullptr
                 ? -1.0
                 : topSpecularSpike->Value(config::EmissionPhotonEnergy()))
         << " esr_backscatter="
         << (topBackscatter == nullptr
                 ? -1.0
                 : topBackscatter->Value(config::EmissionPhotonEnergy()))
         << " borders=" << G4LogicalBorderSurface::GetNumberOfBorderSurfaces()
         << " status=" << (allPass ? "PASS" : "FAIL") << G4endl;
}

void DetectorConstruction::ValidateStageASurface() {
  const auto dataPath = GetRealSurfaceDataPath();
  const auto dataFile = StageASurfaceDataFile(fStageASurface);
  const auto dataPass = HasStageALutSurface() && !dataPath.empty() &&
                        std::filesystem::is_regular_file(
                            std::filesystem::path(dataPath.c_str()) /
                            dataFile.c_str());
  auto* sideTarget = fStageAInterfaceMode == "airgap"
                         ? fSideAirGapPhysical
                         : fSideReflectorPhysical;
  auto* topTarget = fStageAInterfaceMode == "airgap"
                        ? fTopAirGapPhysical
                        : fTopReflectorPhysical;
  const auto* sideBorder =
      G4LogicalBorderSurface::GetSurface(fCrystalPhysical, sideTarget);
  const auto* topBorder =
      G4LogicalBorderSurface::GetSurface(fCrystalPhysical, topTarget);
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
  const auto* surfaceProperties =
      sideSurface == nullptr ? nullptr
                             : sideSurface->GetMaterialPropertiesTable();
  const auto* reflectivityProperty =
      surfaceProperties == nullptr
          ? nullptr
          : surfaceProperties->GetProperty("REFLECTIVITY");
  const auto* transmittanceProperty =
      surfaceProperties == nullptr
          ? nullptr
          : surfaceProperties->GetProperty("TRANSMITTANCE");
  const auto expectedReflectivity = GetStageAReflectivity();
  const auto opticalValuesPass =
      reflectivityProperty != nullptr && transmittanceProperty != nullptr &&
      RelativeClose(reflectivityProperty->Value(
                        config::EmissionPhotonEnergy()),
                    expectedReflectivity) &&
      RelativeClose(transmittanceProperty->Value(
                        config::EmissionPhotonEnergy()),
                    1.0 - expectedReflectivity);
  const auto borderPass =
      G4LogicalBorderSurface::GetNumberOfBorderSurfaces() == 2;
  const auto interfacePass =
      (fStageAInterfaceMode == "direct" &&
       fSideAirGapPhysical == nullptr && fTopAirGapPhysical == nullptr) ||
      (fStageAInterfaceMode == "airgap" &&
       fSideAirGapPhysical != nullptr && fTopAirGapPhysical != nullptr);
  const auto allPass = fGeometryMode == "paper" && dataPass && surfacePass &&
                       opticalValuesPass && borderPass && interfacePass;

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
         << " reflectivity=" << expectedReflectivity
         << " transmittance=" << 1.0 - expectedReflectivity
         << " interface=" << fStageAInterfaceMode
         << " air_gap_mm=" << fStageAAirGap / mm
         << " interface_status=" << (interfacePass ? "PASS" : "FAIL")
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
  if (fGeometryMode == "experiment") {
    ValidateExperimentGeometry();
    return;
  }
  if (fGeometryMode != "paper" || fWorldPhysical == nullptr ||
      fCrystalPhysical == nullptr || fSideReflectorPhysical == nullptr ||
      fTopReflectorPhysical == nullptr) {
    G4cout << "[a2] geometry status=FAIL reason=paper_geometry_not_built"
           << G4endl;
    return;
  }

  const auto explicitAirGap = fStageAInterfaceMode == "airgap";
  const auto gap = explicitAirGap ? fStageAAirGap : 0.0;
  const auto reflectorInnerRadius = config::kCrystalRadius + gap;
  const auto reflectorOuterRadius =
      reflectorInnerRadius + config::kReflectorThickness;
  const auto crystalExpected =
      pi * config::kCrystalRadius * config::kCrystalRadius *
      config::kCrystalLength;
  const auto sideExpected =
      pi * (reflectorOuterRadius * reflectorOuterRadius -
            reflectorInnerRadius * reflectorInnerRadius) *
      config::kCrystalLength;
  const auto topExpected =
      pi * reflectorOuterRadius * reflectorOuterRadius *
      config::kReflectorThickness;
  const auto sideAirExpected =
      pi * (reflectorInnerRadius * reflectorInnerRadius -
            config::kCrystalRadius * config::kCrystalRadius) *
      config::kCrystalLength;
  const auto topAirExpected =
      pi * reflectorOuterRadius * reflectorOuterRadius * gap;

  const auto crystalActual =
      fCrystalPhysical->GetLogicalVolume()->GetSolid()->GetCubicVolume();
  const auto sideActual = fSideReflectorPhysical->GetLogicalVolume()
                              ->GetSolid()
                              ->GetCubicVolume();
  const auto topActual = fTopReflectorPhysical->GetLogicalVolume()
                             ->GetSolid()
                             ->GetCubicVolume();
  const auto sideAirActual =
      fSideAirGapPhysical == nullptr
          ? 0.0
          : fSideAirGapPhysical->GetLogicalVolume()
                ->GetSolid()
                ->GetCubicVolume();
  const auto topAirActual =
      fTopAirGapPhysical == nullptr
          ? 0.0
          : fTopAirGapPhysical->GetLogicalVolume()
                ->GetSolid()
                ->GetCubicVolume();
  const auto volumesPass = RelativeClose(crystalActual, crystalExpected) &&
                           RelativeClose(sideActual, sideExpected) &&
                           RelativeClose(topActual, topExpected) &&
                           RelativeClose(sideAirActual, sideAirExpected) &&
                           RelativeClose(topAirActual, topAirExpected);

  auto overlaps = fCrystalPhysical->CheckOverlaps(10000, 0.0, false) ||
                  fSideReflectorPhysical->CheckOverlaps(10000, 0.0, false) ||
                  fTopReflectorPhysical->CheckOverlaps(10000, 0.0, false);
  if (fSideAirGapPhysical != nullptr) {
    overlaps = overlaps ||
               fSideAirGapPhysical->CheckOverlaps(10000, 0.0, false);
  }
  if (fTopAirGapPhysical != nullptr) {
    overlaps =
        overlaps || fTopAirGapPhysical->CheckOverlaps(10000, 0.0, false);
  }

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
  const auto sideAirName = locateName(
      {config::kCrystalRadius + 0.5 * gap, 0.0, 0.0});
  const auto topAirName = locateName(
      {0.0, 0.0, 0.5 * config::kCrystalLength + 0.5 * gap});
  const auto outputName = locateName(
      {0.0, 0.0,
       -0.5 * config::kCrystalLength - 0.25 * config::kReflectorThickness});
  const auto probesPass = centerName == "GAGG" &&
                          sideName == "SideReflector" &&
                          topName == "TopReflector" && outputName == "World";
  const auto airProbesPass =
      !explicitAirGap ||
      (sideAirName == "SideAirGap" && topAirName == "TopAirGap");
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
  const auto allPass = volumesPass && !overlaps && probesPass &&
                       airProbesPass && densityPass && opticalPropertiesPass;

  G4cout << "[a2] crystal_volume_mm3=" << crystalActual / mm3
         << " side_volume_mm3=" << sideActual / mm3
         << " top_volume_mm3=" << topActual / mm3
         << " side_air_volume_mm3=" << sideAirActual / mm3
         << " top_air_volume_mm3=" << topAirActual / mm3
         << " analytic_volumes=" << (volumesPass ? "PASS" : "FAIL")
         << G4endl;
  G4cout << "[a2] overlaps=" << (overlaps ? 1 : 0) << G4endl;
  G4cout << "[a2] center_probe=" << centerName
         << " side_probe=" << sideName << " top_probe=" << topName
         << " side_air_probe=" << sideAirName
         << " top_air_probe=" << topAirName
         << " output_probe=" << outputName
         << " interface=" << fStageAInterfaceMode
         << " probe_status=" << (airProbesPass ? "PASS" : "FAIL")
         << G4endl;
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

void DetectorConstruction::ValidateExperimentGeometry() {
  if (fWorldPhysical == nullptr || fCrystalPhysical == nullptr ||
      fExperimentSideAirGapPhysical == nullptr ||
      fExperimentBlackHousingPhysical == nullptr ||
      fExperimentEsrPhysical == nullptr ||
      fExperimentPmtWindowPhysical == nullptr) {
    G4cout << "[b0] geometry status=FAIL reason=experiment_geometry_not_built"
           << G4endl;
    return;
  }

  const auto width = config::kExperimentCrystalWidth;
  const auto depth = config::kExperimentCrystalDepth;
  const auto length = config::kExperimentCrystalLength;
  const auto gap = fExperimentSideAirGap;
  const auto black = fExperimentBlackHousingThickness;
  const auto gapOuterWidth = width + 2.0 * gap;
  const auto gapOuterDepth = depth + 2.0 * gap;
  const auto housingOuterWidth = gapOuterWidth + 2.0 * black;
  const auto housingOuterDepth = gapOuterDepth + 2.0 * black;

  const auto crystalExpected = width * depth * length;
  const auto gapExpected =
      (gapOuterWidth * gapOuterDepth - width * depth) * length;
  const auto housingExpected =
      (housingOuterWidth * housingOuterDepth -
       gapOuterWidth * gapOuterDepth) *
      length;
  const auto esrExpected =
      width * depth * fExperimentEsrThickness;
  const auto pmtExpected =
      width * depth * fExperimentPmtWindowThickness;

  const auto volume = [](const G4VPhysicalVolume* physical) {
    return physical->GetLogicalVolume()->GetSolid()->GetCubicVolume();
  };
  const auto crystalActual = volume(fCrystalPhysical);
  const auto gapActual = volume(fExperimentSideAirGapPhysical);
  const auto housingActual = volume(fExperimentBlackHousingPhysical);
  const auto esrActual = volume(fExperimentEsrPhysical);
  const auto pmtActual = volume(fExperimentPmtWindowPhysical);
  const auto volumesPass =
      RelativeClose(crystalActual, crystalExpected) &&
      RelativeClose(gapActual, gapExpected, 2.0e-3) &&
      RelativeClose(housingActual, housingExpected, 2.0e-3) &&
      RelativeClose(esrActual, esrExpected) &&
      RelativeClose(pmtActual, pmtExpected);

  const auto overlaps =
      fCrystalPhysical->CheckOverlaps(10000, 0.0, false) ||
      fExperimentSideAirGapPhysical->CheckOverlaps(10000, 0.0, false) ||
      fExperimentBlackHousingPhysical->CheckOverlaps(10000, 0.0, false) ||
      fExperimentEsrPhysical->CheckOverlaps(10000, 0.0, false) ||
      fExperimentPmtWindowPhysical->CheckOverlaps(10000, 0.0, false);

  auto* navigator = G4TransportationManager::GetTransportationManager()
                        ->GetNavigatorForTracking();
  const auto locateName = [navigator](const G4ThreeVector& point) {
    const auto* physical =
        navigator->LocateGlobalPointAndSetup(point, nullptr, false);
    return physical == nullptr ? G4String("none") : physical->GetName();
  };
  const auto crystalHalfX = 0.5 * width;
  const auto crystalHalfZ = 0.5 * length;
  const auto centerName = locateName({0.0, 0.0, 0.0});
  const auto gapName =
      locateName({crystalHalfX + 0.5 * gap, 0.0, 0.0});
  const auto blackName = locateName(
      {crystalHalfX + gap + 0.5 * black, 0.0, 0.0});
  const auto esrName = locateName(
      {0.0, 0.0, crystalHalfZ + 0.5 * fExperimentEsrThickness});
  const auto pmtName = locateName(
      {0.0, 0.0,
       -crystalHalfZ - 0.5 * fExperimentPmtWindowThickness});
  const auto probesPass =
      centerName == "GAGG" && gapName == "ExperimentSideAirGap" &&
      blackName == "ExperimentBlackHousing" &&
      esrName == "ExperimentESR" && pmtName == "PMTWindow";

  const auto* esrBorder = G4LogicalBorderSurface::GetSurface(
      fCrystalPhysical, fExperimentEsrPhysical);
  const auto* bottomBorder = G4LogicalBorderSurface::GetSurface(
      fCrystalPhysical, fExperimentPmtWindowPhysical);
  const auto* sideBorder = G4LogicalBorderSurface::GetSurface(
      fCrystalPhysical, fExperimentSideAirGapPhysical);
  const auto* blackBorder = G4LogicalBorderSurface::GetSurface(
      fExperimentSideAirGapPhysical,
      fExperimentBlackHousingPhysical);
  const auto* esrSurface =
      esrBorder == nullptr
          ? nullptr
          : dynamic_cast<const G4OpticalSurface*>(
                esrBorder->GetSurfaceProperty());
  const auto* blackSurface =
      blackBorder == nullptr
          ? nullptr
          : dynamic_cast<const G4OpticalSurface*>(
                blackBorder->GetSurfaceProperty());
  const auto* bottomSurface =
      bottomBorder == nullptr
          ? nullptr
          : dynamic_cast<const G4OpticalSurface*>(
                bottomBorder->GetSurfaceProperty());
  const auto* sideSurface =
      sideBorder == nullptr
          ? nullptr
          : dynamic_cast<const G4OpticalSurface*>(
                sideBorder->GetSurfaceProperty());
  const auto surfacePass =
      esrSurface != nullptr && bottomSurface != nullptr &&
      sideSurface != nullptr && blackSurface != nullptr &&
      esrSurface->GetModel() == unified &&
      bottomSurface->GetModel() == unified &&
      sideSurface->GetModel() == unified &&
      blackSurface->GetModel() == unified &&
      esrSurface->GetType() == dielectric_metal &&
      bottomSurface->GetType() == dielectric_dielectric &&
      sideSurface->GetType() == dielectric_dielectric &&
      blackSurface->GetType() == dielectric_metal &&
      G4LogicalBorderSurface::GetNumberOfBorderSurfaces() == 4;

  const auto* pmtProperties =
      fExperimentPmtWindowPhysical->GetLogicalVolume()
          ->GetMaterial()
          ->GetMaterialPropertiesTable();
  const auto* pmtIndex =
      pmtProperties == nullptr
          ? nullptr
          : pmtProperties->GetProperty("RINDEX");
  const auto pmtPass =
      pmtIndex != nullptr &&
      RelativeClose(
          pmtIndex->Value(config::EmissionPhotonEnergy()),
          config::kExperimentPmtWindowRefractiveIndex);
  const auto allPass = volumesPass && !overlaps && probesPass &&
                       surfacePass && pmtPass;

  G4cout << "[b0] crystal_size_mm=" << width / mm << "x"
         << depth / mm << "x" << length / mm
         << " crystal_volume_mm3=" << crystalActual / mm3
         << " side_air_volume_mm3=" << gapActual / mm3
         << " black_volume_mm3=" << housingActual / mm3
         << " esr_volume_mm3=" << esrActual / mm3
         << " pmt_window_volume_mm3=" << pmtActual / mm3
         << " analytic_volumes=" << (volumesPass ? "PASS" : "FAIL")
         << G4endl;
  G4cout << "[b0] side_air_gap_mm=" << gap / mm
         << " black_thickness_mm=" << black / mm
         << " esr_thickness_mm=" << fExperimentEsrThickness / mm
         << " pmt_window_thickness_mm="
         << fExperimentPmtWindowThickness / mm
         << " provenance=unmeasured_B0_placeholders" << G4endl;
  G4cout << "[b0] center_probe=" << centerName
         << " side_air_probe=" << gapName
         << " black_probe=" << blackName
         << " top_esr_probe=" << esrName
         << " bottom_pmt_probe=" << pmtName
         << " probes=" << (probesPass ? "PASS" : "FAIL") << G4endl;
  G4cout << "[b0] overlaps=" << (overlaps ? 1 : 0)
         << " unified_surfaces=" << (surfacePass ? "PASS" : "FAIL")
         << " pmt_rindex=" << (pmtIndex == nullptr
                                   ? -1.0
                                   : pmtIndex->Value(
                                         config::EmissionPhotonEnergy()))
         << G4endl;
  G4cout << "[b0] geometry status=" << (allPass ? "PASS" : "FAIL")
         << G4endl;
}

}  // namespace gagg
