B0 is the validated experimental-geometry and optical-transport baseline.

The measured crystal is 5.75 mm x 5.75 mm x 20 mm. The model convention is
top ESR at +z and PMT window at -z, with an explicit side air volume and an
ideal black surrounding structure.

Run:

  ../validation/b0_geometry.mac
  ../validation/b0_transport.mac
  ../validation/b0_vis.mac

B0 uses transmitted photons entering PMTWindow as N_PMT. Its gap, housing,
ESR and window dimensions are explicit runtime-selectable placeholders, not
fits. The GAGG faces are all polished in B0. Six surface states and the shared
UNIFIED sigma_alpha belong to B1 and later.
