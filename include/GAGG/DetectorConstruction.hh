#ifndef GAGG_DETECTOR_CONSTRUCTION_HH
#define GAGG_DETECTOR_CONSTRUCTION_HH

#include "G4VUserDetectorConstruction.hh"
#include "globals.hh"

#include <memory>

class G4GenericMessenger;
class G4VPhysicalVolume;

namespace gagg {

class DetectorConstruction final : public G4VUserDetectorConstruction {
 public:
  DetectorConstruction();
  ~DetectorConstruction() override;

  G4VPhysicalVolume* Construct() override;

  void SetGeometryMode(const G4String& mode);
  void ValidateGeometry();

 private:
  std::unique_ptr<G4GenericMessenger> fMessenger;
  G4String fGeometryMode = "bare";
  G4VPhysicalVolume* fWorldPhysical = nullptr;
  G4VPhysicalVolume* fCrystalPhysical = nullptr;
  G4VPhysicalVolume* fSideReflectorPhysical = nullptr;
  G4VPhysicalVolume* fTopReflectorPhysical = nullptr;
};

}  // namespace gagg

#endif
