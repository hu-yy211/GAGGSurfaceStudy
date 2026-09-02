B0 is the validated experimental-geometry and optical-transport baseline.

The measured crystal is 5.75 mm x 5.75 mm x 20 mm. The model convention is
top ESR at +z and PMT window at -z, with explicit side, top and bottom air
volumes and an ideal black surrounding structure.

Run:

  ../validation/b0_geometry.mac
  ../validation/b0_transport.mac
  ../validation/b0_vis.mac

B0 uses photons transmitted from ExperimentBottomAirGap into PMTWindow as
N_PMT. Its three gaps, housing, ESR and window dimensions are explicit
runtime-selectable placeholders, not fits. The GAGG faces are all polished in
B0.

B1 is the validated six-state UNIFIED switching and face-counter diagnostic.
Run:

  b1_compare.mac
  ../validation/b1_vis.mac

Select states with /gagg/stageB/surfaceState and set the single shared rough
value with /gagg/stageB/sigmaAlpha. b1_compare.mac uses 0.20 rad as a
predeclared validation-only value, not a fit, and keeps identical optical
primary directions between states. Experimental-order testing and 511 keV
gamma interactions belong to later stages.

B2 is the validated optical-only roughness/position scan. Its single source of
truth is ../../config/b2_scan.json. Run it from the repository root with:

  python analysis/run_b2_scan.py \
    --executable build/gagg_surface_study \
    --config config/b2_scan.json --output-dir results/b2

The runner writes one inspectable macro per point under results/b2/macros and
executes each in an isolated Geant4 process. This prevents scan-order history
from entering the first event of a rebuilt ground surface. B2 does not select
or fit sigma_alpha and does not contain gamma interactions.

The physical Na-22 energy-deposition validation is intentionally non-optical.
Run it only with:

  ./build/gagg_surface_study --decay-only \
    build/macros/stage_b/na22_spectrum_100k.mac

It starts every event from one stationary GPS Na22 ion at a macro-controlled
distance from the +z GAGG face. Geant4 RadioactiveDecayPhysics and EM transport
produce all decay products. The event CSV contains total GAGG Edep in keV.
