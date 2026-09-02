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
fits. The GAGG faces are all polished in B0.

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

B7.1 validates the 2.5 mm x 2.5 mm effective source-face position sampler:

  ../validation/b7_face_source.mac

The `/gagg/source/faceSize 2.5 mm` command samples x and y uniformly around
the configured source centre. The validation macro uses a single 1 keV
fixed-direction gamma only to test positions. It does not yet implement the
back-to-back 511 keV, 4pi pair-axis source planned for B7.2.

B7.2 validates that effective pair source with:

  ../validation/b7_annihilation_pair_source.mac

Use `/gagg/source/particle annihilationPair`, `mode isotropic`, zero
`beamRadius`, and the validated 2.5 mm `faceSize`. Each event then has one
vertex and two exactly back-to-back 511 keV gammas. The validation macro writes
an independent source-audit CSV; it does not yet select 511 keV full-energy
GAGG events or report a B4-style light-output ratio.

B7.3 generates its production macro from the locked JSON configuration:

  python analysis/run_b7_3.py --executable build/gagg_surface_study \
    --config config/b7_3_full_energy_response.json \
    --output-dir results/b7_3_full_energy_100k

It runs 100000 all-polished events in the nominal estimated geometry and
selects Edep_GAGG=511.0+/-0.5 keV during analysis. N_PMT counts optical
photons transmitted from the bottom air layer into the PMT window. B7.3 does
not scan or fit sigma_alpha.

B7.4 generates isolated macros under the selected results directory using:

  python analysis/run_b7_4.py --executable build/gagg_surface_study \
    --config config/b7_4_sigma_scan.json \
    --output-dir results/b7_4_sigma_scan_20k --jobs 4

It scans one shared sigma_alpha for all rough faces, reuses one all-polished
reference and forbids per-face fitting. Generated macros are run artifacts;
the locked inputs live in config/b7_4_sigma_scan.json.

B7.5 generates bottom_rough, top_rough and top_bottom_rough macros at
sigma_alpha=0.70 rad:

  python analysis/run_b7_5.py --executable build/gagg_surface_study \
    --config config/b7_5_endface_sigma070.json \
    --output-dir results/b7_5_endface_sigma070_100k --jobs 3

Each state uses 100000 paired events. The validator reuses the B7.3
all-polished reference and writes numerical CSV summaries only; B7.5 does not
create a plot. To reuse validated single-end controls and run only the added
state, append `--state top_bottom_rough`.

B7.6 enables a separate photon-audit CSV while leaving the established event
CSV unchanged. Production macros are generated with:

  python analysis/run_b7_6.py --executable build/gagg_surface_study \
    --config config/b7_6_photon_fate_audit.json \
    --output-dir results/b7_6_photon_fate_audit_100k --jobs 5

The audit output is enabled by `/gagg/output/photonAuditCsv <path>`. It records
event-aggregate path and PMT-arrival diagnostics and is inactive when the path
is empty. `../validation/b7_6_photon_audit.mac` provides the low-statistics
schema and count-matching test.
