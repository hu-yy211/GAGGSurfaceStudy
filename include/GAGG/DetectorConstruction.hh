#ifndef GAGG_DETECTOR_CONSTRUCTION_HH
#define GAGG_DETECTOR_CONSTRUCTION_HH

#include "GAGG/SimulationConfig.hh"

#include "G4ThreeVector.hh"
#include "G4VUserDetectorConstruction.hh"
#include "globals.hh"

#include <memory>

class G4GenericMessenger;
class G4MaterialPropertiesTable;
class G4OpticalSurface;
class G4VPhysicalVolume;

namespace gagg {

class DetectorConstruction final : public G4VUserDetectorConstruction {
 public:
  DetectorConstruction();
  ~DetectorConstruction() override;

  G4VPhysicalVolume* Construct() override;

  void SetGeometryMode(const G4String& mode);
  void SetStageASurface(const G4String& surface);
  void SetStageBSurfaceState(const G4String& state);
  void SetStageBSigmaAlpha(G4double sigmaAlpha);
  void ValidateGeometry();
  void ValidateStageASurface();
  void ValidateStageBSurfaces();
  void ValidateScintillation();

  const G4String& GetStageASurfaceName() const { return fStageASurface; }
  G4bool HasStageALutSurface() const { return fStageASurface != "none"; }
  G4String GetRealSurfaceDataPath() const;
  G4double GetScintillationTimeConstant() const {
    return fScintillationTimeConstant;
  }
  G4double GetStageAReflectivity() const;
  const G4String& GetGeometryMode() const { return fGeometryMode; }
  G4double GetCrystalSizeX() const;
  G4double GetCrystalSizeY() const;
  G4double GetCrystalSizeZ() const;
  const G4String& GetStageBSurfaceState() const {
    return fStageBSurfaceState;
  }
  G4double GetStageBSigmaAlpha() const { return fStageBSigmaAlpha; }
  const G4String& GetStageAInterfaceMode() const {
    return fStageAInterfaceMode;
  }
  G4double GetStageAAirGap() const { return fStageAAirGap; }
  const G4String& GetOutputScoringMode() const { return fOutputScoringMode; }
  G4bool IsOnOutputFace(const G4ThreeVector& position,
                        G4double tolerance) const;
  G4String GetOutputReceiverVolumeName() const;

 private:
  void ConfigureStageASurface();
  void ConfigureExperimentSurfaces();
  void ValidateExperimentGeometry();
  void ResetPhysicalVolumePointers();

  std::unique_ptr<G4GenericMessenger> fMessenger;
  std::unique_ptr<G4GenericMessenger> fOpticsMessenger;
  std::unique_ptr<G4GenericMessenger> fStageAMessenger;
  std::unique_ptr<G4GenericMessenger> fStageBMessenger;
  std::unique_ptr<G4GenericMessenger> fScoringMessenger;
  std::unique_ptr<G4OpticalSurface> fStageAOpticalSurface;
  std::unique_ptr<G4MaterialPropertiesTable> fStageASurfaceProperties;
  std::unique_ptr<G4OpticalSurface> fExperimentTopSurface;
  std::unique_ptr<G4OpticalSurface> fExperimentEsrSurface;
  std::unique_ptr<G4OpticalSurface> fExperimentBottomSurface;
  std::unique_ptr<G4OpticalSurface> fExperimentPmtSurface;
  std::unique_ptr<G4OpticalSurface> fExperimentSideSurface;
  std::unique_ptr<G4OpticalSurface> fExperimentBlackSurface;
  std::unique_ptr<G4MaterialPropertiesTable> fExperimentEsrProperties;
  std::unique_ptr<G4MaterialPropertiesTable> fExperimentBlackProperties;
  G4String fGeometryMode = "bare";
  G4String fStageASurface = "none";
  G4String fStageAInterfaceMode = "direct";
  G4double fStageAAirGap = config::kStageAAirGapDiagnostic;
  G4String fOutputScoringMode = "firstArrival";
  G4String fStageBSurfaceState = "all_polished";
  G4double fStageBSigmaAlpha = config::kStageBSigmaAlphaValidation;
  G4double fExperimentSideAirGap =
      config::kExperimentSideAirGapDefault;
  G4double fExperimentTopAirGap =
      config::kExperimentTopAirGapDefault;
  G4double fExperimentBottomAirGap =
      config::kExperimentBottomAirGapDefault;
  G4double fExperimentBlackHousingThickness =
      config::kExperimentBlackHousingThicknessDefault;
  G4double fExperimentEsrThickness =
      config::kExperimentEsrThicknessDefault;
  G4double fExperimentPmtWindowThickness =
      config::kExperimentPmtWindowThicknessDefault;
  G4bool fGaggBulkAbsorption = true;
  G4double fGaggAbsorptionLengthScale = 1.0;
  G4double fScintillationTimeConstant =
      config::kFastScintillationTimeConstant;
  G4bool fStageAUsePaperReflectivity = true;
  G4VPhysicalVolume* fWorldPhysical = nullptr;
  G4VPhysicalVolume* fCrystalPhysical = nullptr;
  G4VPhysicalVolume* fSideReflectorPhysical = nullptr;
  G4VPhysicalVolume* fTopReflectorPhysical = nullptr;
  G4VPhysicalVolume* fSideAirGapPhysical = nullptr;
  G4VPhysicalVolume* fTopAirGapPhysical = nullptr;
  G4VPhysicalVolume* fExperimentSideAirGapPhysical = nullptr;
  G4VPhysicalVolume* fExperimentTopAirGapPhysical = nullptr;
  G4VPhysicalVolume* fExperimentBottomAirGapPhysical = nullptr;
  G4VPhysicalVolume* fExperimentBlackHousingPhysical = nullptr;
  G4VPhysicalVolume* fExperimentTopStructurePhysical = nullptr;
  G4VPhysicalVolume* fExperimentEsrPhysical = nullptr;
  G4VPhysicalVolume* fExperimentPmtWindowPhysical = nullptr;
};

}  // namespace gagg

#endif
