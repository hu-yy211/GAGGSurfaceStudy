#ifndef GAGG_PHOTON_TRACK_INFORMATION_HH
#define GAGG_PHOTON_TRACK_INFORMATION_HH

#include "G4VUserTrackInformation.hh"
#include "globals.hh"

namespace gagg {

class PhotonTrackInformation final : public G4VUserTrackInformation {
 public:
  void AddTopInteraction() { ++fTopInteractions; }
  void AddBottomInteraction() { ++fBottomInteractions; }
  void AddSideInteraction() { ++fSideInteractions; }

  G4int GetTopInteractions() const { return fTopInteractions; }
  G4int GetBottomInteractions() const { return fBottomInteractions; }
  G4int GetSideInteractions() const { return fSideInteractions; }
  G4int GetFaceInteractions() const {
    return fTopInteractions + fBottomInteractions + fSideInteractions;
  }

 private:
  G4int fTopInteractions = 0;
  G4int fBottomInteractions = 0;
  G4int fSideInteractions = 0;
};

}  // namespace gagg

#endif
