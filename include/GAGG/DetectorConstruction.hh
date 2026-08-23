#ifndef GAGG_DETECTOR_CONSTRUCTION_HH
#define GAGG_DETECTOR_CONSTRUCTION_HH

#include "G4VUserDetectorConstruction.hh"

namespace gagg {

class DetectorConstruction final : public G4VUserDetectorConstruction {
 public:
  G4VPhysicalVolume* Construct() override;
};

}  // namespace gagg

#endif

