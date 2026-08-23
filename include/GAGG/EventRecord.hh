#ifndef GAGG_EVENT_RECORD_HH
#define GAGG_EVENT_RECORD_HH

#include "G4ThreeVector.hh"
#include "globals.hh"

namespace gagg {

struct EventRecord {
  G4int eventId = 0;
  G4ThreeVector sourcePosition;
  G4int generated = 0;
  G4int output = 0;
  G4int crystalAbsorption = 0;
  G4int reflectorAbsorption = 0;
  G4int surfaceAbsorption = 0;
  G4int otherAbsorption = 0;
  G4int otherWorldExit = 0;
  G4int lutInteractions = 0;
  G4int unclassified = 0;

  G4int WorldExit() const { return output + otherWorldExit; }
  G4int BulkAbsorption() const {
    return crystalAbsorption + reflectorAbsorption + otherAbsorption;
  }
};

}  // namespace gagg

#endif
