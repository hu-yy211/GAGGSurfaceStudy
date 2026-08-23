#ifndef GAGG_DETECTOR_CONSTRUCTION_HH
#define GAGG_DETECTOR_CONSTRUCTION_HH

#include "GAGG/SimulationConfig.hh"

#include "G4VUserDetectorConstruction.hh"
#include "globals.hh"

#include <memory>

class G4GenericMessenger;
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
  void ValidateGeometry();
  void ValidateStageASurface();
  void ValidateScintillation();

  const G4String& GetStageASurfaceName() const { return fStageASurface; }
  G4bool HasStageALutSurface() const { return fStageASurface != "none"; }
  G4String GetRealSurfaceDataPath() const;
  G4double GetScintillationTimeConstant() const {
    return fScintillationTimeConstant;
  }

 private:
  void ConfigureStageASurface();

  std::unique_ptr<G4GenericMessenger> fMessenger;
  std::unique_ptr<G4GenericMessenger> fOpticsMessenger;
  std::unique_ptr<G4GenericMessenger> fStageAMessenger;
  std::unique_ptr<G4OpticalSurface> fStageAOpticalSurface;
  G4String fGeometryMode = "bare";
  G4String fStageASurface = "none";
  G4bool fGaggBulkAbsorption = true;
  G4double fScintillationTimeConstant =
      config::kFastScintillationTimeConstant;
  G4VPhysicalVolume* fWorldPhysical = nullptr;
  G4VPhysicalVolume* fCrystalPhysical = nullptr;
  G4VPhysicalVolume* fSideReflectorPhysical = nullptr;
  G4VPhysicalVolume* fTopReflectorPhysical = nullptr;
};

}  // namespace gagg

#endif
