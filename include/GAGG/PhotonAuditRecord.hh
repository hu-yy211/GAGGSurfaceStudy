#ifndef GAGG_PHOTON_AUDIT_RECORD_HH
#define GAGG_PHOTON_AUDIT_RECORD_HH

#include "globals.hh"

namespace gagg {

struct PhotonAuditRecord {
  G4int eventId = 0;
  G4int generated = 0;
  G4int output = 0;
  G4double totalOpticalPath = 0.0;
  G4double outputOpticalPath = 0.0;
  G4int outputFaceInteractions = 0;
  G4int outputTopInteractions = 0;
  G4int outputBottomInteractions = 0;
  G4int outputSideInteractions = 0;
  G4double outputIncidenceAngle = 0.0;
};

}  // namespace gagg

#endif
