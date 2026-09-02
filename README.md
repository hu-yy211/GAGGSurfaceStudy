# GAGGSurfaceStudy

This project studies how GAGG:Ce surface treatment changes optical-photon
collection.

- Stage A attempts the qualitative ordering in Fig. 4 of the paper with four
  Geant4 LUT finishes; the A7 ordering gate is currently not passed.
- Stage B models the six experimental surface states for a
  5.75 mm x 5.75 mm x 20 mm crystal with the UNIFIED model and one shared
  rough-surface sigma_alpha.

The current validated milestone is B2. A0 provides a one-photon optical
transport baseline, Qt/OpenGL view, event-level CSV output, accounting checks
and reproducible plots. A1 validates the literature parameters and their
Geant4 unit conversions. A2 adds the paper's 1 mm Teflon-assumption side
sleeve and top cap while leaving the -z crystal output face open. A3 adds a
fixed-count isotropic 550 nm source at controlled positions and records the
first crossing of that open face as `N_output`. A4 attaches the four paper
LBNL LUT finishes to the GAGG-to-side/top borders and switches them at runtime
through geometry reinitialization. A5 adds Geant4 scintillation with a narrow
550 nm component and validates its 54000 photons/MeV yield using controlled
electron energy deposits. A6 adds the minimum standard electromagnetic
physics application: one normally incident 662 keV gamma per event, a
full-energy event gate and zero-deposit controls.

There is no radioactive-decay source, detector energy resolution, PMT, or
fitting yet. A6 validates gamma energy deposition and scintillation production.
A7 has not passed its Fig. 4 ordering gate; four controlled interface/scoring
models are retained as diagnosed mismatches rather than tuned into agreement.
Following that bounded audit, B0 starts the experimental geometry and B1 adds
the six runtime-selectable UNIFIED surface states with one shared roughness
parameter. B1 is an optical-only switching validation, not an experimental
fit. B2 scans a locked roughness/position grid with isolated Geant4 processes
so that no point inherits optical-boundary state from another point.

## Build and run

Validated toolchain:

- conda Clang 16.0.6 used by CMake
- host Apple Clang 21.0.0 also available
- Geant4 11.2.2 in conda environment "hep"
- CMake 3.30.2 in the same environment
- G4 real-surface data 2.2 installed

~~~sh
source /opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh
conda activate hep
cmake -S . -B build
cmake --build build -j
ctest --test-dir build --output-on-failure
~~~

Direct run:

~~~sh
./build/gagg_surface_study ./build/macros/validation/smoke.mac
~~~

Interactive Qt/OpenGL visualization:

~~~sh
./build/gagg_surface_study --interactive \
  ./build/macros/validation/a0_vis.mac
~~~

The yellow cylinder is GAGG and the green line is the 550 nm optical-photon
trajectory. Rotate and zoom in the Qt viewer; on macOS, use Shift-Command-4 to
capture a presentation image. Close the Qt window to end the program.

Validate and visualize the A2 paper geometry:

~~~sh
./build/gagg_surface_study \
  ./build/macros/validation/a2_geometry.mac
./build/gagg_surface_study --interactive \
  ./build/macros/validation/a2_vis.mac
~~~

The yellow cylinder is GAGG, the blue annulus is the 1 mm side reflector and
the pale-blue disk is the 1 mm top cap. Geometry mode is selected before
initialization without recompiling:

~~~text
/gagg/geometry/mode bare
/gagg/geometry/mode paper
~~~

The implemented A2 cross-section is:

~~~text
                       +z
            ┌─────────────────────┐
            │ 1 mm top reflector  │  radius 13.7 mm
        ┌───┴─────────────────────┴───┐
        │ 1 mm │                  │ 1 mm
        │ side │  GAGG cylinder   │ side
        │      │  R=12.7, L=25.4  │
        └──────┴──────────────────┴──────
                       -z output open
~~~

Generate a 1000-event CSV and the two A0 validation plots from the project
root:

~~~sh
./build/gagg_surface_study \
  ./build/macros/validation/a0_export.mac
python analysis/validate_a0_csv.py \
  --input results/a0_events.csv --expect-events 1000
MPLCONFIGDIR=results/.mplconfig python analysis/plot_a0.py \
  --input results/a0_events.csv --output-dir results/a0
~~~

This creates:

- `results/a0_events.csv`
- `results/a0/a0_terminal_outcomes.png`
- `results/a0/a0_photon_accounting.png`

The CSV retains `generated`, `world_exit`, `bulk_absorption` and
`unclassified`, and now also records source position, `output`, GAGG
absorption, reflector absorption, other absorption and other world exit. A0
requires exactly one generated photon and one classified terminal outcome per
event, with zero unclassified photons.

B6 adds location subtotals for `surface_absorption`: top ESR, bottom PMT
interface, side-air interface, outer black structure and other configured
surfaces. These are diagnostic subtotals, not additional terminal outcomes;
their sum is required to equal `surface_absorption` for every event.

Run only the A1 material/unit check:

~~~sh
./build/gagg_surface_study --validate-materials
~~~

Run the A3 fixed-seed transport suite and create its plots:

~~~sh
./build/gagg_surface_study \
  ./build/macros/validation/a3_transport.mac
./build/gagg_surface_study \
  ./build/macros/validation/a3_no_absorption.mac
python analysis/validate_a3.py \
  --center-a results/a3/center_a.csv \
  --center-b results/a3/center_b.csv \
  --no-absorption results/a3/center_no_absorption.csv \
  --z-m10 results/a3/z_m10.csv --z-m5 results/a3/z_m5.csv \
  --z-p5 results/a3/z_p5.csv --z-p10 results/a3/z_p10.csv
MPLCONFIGDIR=results/.mplconfig python analysis/plot_a3.py \
  --input-dir results/a3 --output-dir results/a3/figures
~~~

Interactive A3 trajectories:

~~~sh
./build/gagg_surface_study --interactive \
  ./build/macros/validation/a3_vis.mac
~~~

The source is controlled without recompiling:

~~~text
/gagg/source/mode fixed|isotropic
/gagg/source/photonsPerEvent 200
/gagg/source/position 0 0 -5 mm
/gagg/optics/gaggBulkAbsorption true|false
~~~

A photon is counted once when it crosses from GAGG through the open -z face
into the world, then the track is killed. The A3 event accounting identity is:

~~~text
N_generated = N_output + N_GAGG_absorption + N_reflector_absorption
            + N_surface_absorption + N_other_absorption
            + N_other_world_exit + N_unclassified
~~~

For the fixed A3 validation seed, each scan point contains 20,000 photons.
The center efficiency is 0.17065, and disabling GAGG self-absorption gives
0.17800. The axial scan at z = -10, -5, 0, 5 and 10 mm gives 0.40250,
0.25870, 0.17065, 0.17735 and 0.17155. The small center-to-+5 mm reversal is
1.767 standard deviations and therefore not statistically significant.

## A4 LUT switching and plots

Run all four LBNL LUT finishes in one executable process. The macro resets the
random seed for each 10,000-photon run and finally switches back to
`polishedvm2000air` for an exact event-row reproducibility check:

~~~sh
./build/gagg_surface_study \
  ./build/macros/stage_a/a4_compare.mac
python analysis/validate_a4.py --input-dir results/a4
MPLCONFIGDIR=results/.mplconfig python analysis/plot_a4.py \
  --input-dir results/a4 --output-dir results/a4/figures
~~~

This creates one event CSV per finish plus:

- `results/a4/figures/a4_surface_summary.csv`
- `results/a4/figures/a4_surface_efficiency.png`
- `results/a4/figures/a4_terminal_outcomes.png`

Open the A4 `groundtioair` scene with 20 green optical-photon trajectories:

~~~sh
./build/gagg_surface_study --interactive \
  ./build/macros/validation/a4_vis.mac
~~~

The active surface is selected without recompilation:

~~~text
/gagg/stageA/surface polishedvm2000air
/gagg/stageA/surface polishedtioair
/gagg/stageA/surface groundvm2000air
/gagg/stageA/surface groundtioair
~~~

When changing the finish after initialization, the command requests geometry
reinitialization. Use `/run/initialize` before `/gagg/stageA/validate` (or let
the next `/run/beamOn` initialize it). The validator confirms two directional
borders, `model=LUT`, `type=dielectric_LUT`, the exact finish, the required
RealSurface file and a nonzero `lut_interactions` count.

With the explicit paper reflectivity lower bounds added during the A7 audit,
the fixed A4 functional run returns 0.8300, 0.7109, 0.8238 and 0.7268 for
`polishedvm2000air`, `polishedtioair`, `groundvm2000air` and `groundtioair`,
respectively. This is not the paper's order and is not treated as an A4
failure: the source is still a point-like fixed-count optical source rather
than 662 keV gamma-induced scintillation. The published `a4` tag preserves the
earlier LUT-loading-only baseline; no parameter was adjusted to force an order.

## A5 scintillation validation

A5 uses one controlled electron at the crystal center to deposit 10, 20 or
40 keV without introducing a gamma source. Run the linearity and timing
controls, validate the CSV files and create the plots:

~~~sh
./build/gagg_surface_study \
  ./build/macros/validation/a5_linearity.mac
./build/gagg_surface_study \
  ./build/macros/validation/a5_slow_time.mac
python analysis/validate_a5.py --input-dir results/a5
MPLCONFIGDIR=results/.mplconfig python analysis/plot_a5.py \
  --input-dir results/a5 --output-dir results/a5/figures
~~~

This creates:

- `results/a5/energy_10kev.csv`, `energy_20kev.csv` and `energy_40kev.csv`
- `results/a5/energy_20kev_slow.csv`
- `results/a5/figures/a5_scintillation_summary.csv`
- `results/a5/figures/a5_scintillation_linearity.png`
- `results/a5/figures/a5_timing_control.png`

Open a Qt/OpenGL event with one red 1 keV electron and its green
scintillation-photon trajectories:

~~~sh
./build/gagg_surface_study --interactive \
  ./build/macros/validation/a5_vis.mac
~~~

The source and single-component decay time are macro-controlled:

~~~text
/gagg/source/particle optical|electron
/gagg/source/kineticEnergy 20 keV
/gagg/optics/scintillationTimeConstant 62.53 ns
/gagg/optics/validateScintillation
~~~

The scintillation spectrum is the narrow three-point simplification 545,
550 and 555 nm with its peak at 550 nm. `SCINTILLATIONYIELD` is 54000/MeV,
`SCINTILLATIONYIELD1` is 1, and `RESOLUTIONSCALE` is zero for the isolated
linearity test. Cerenkov production is explicitly disabled, so `generated`
contains primary optical photons in A0-A4 or Scintillation-created photons in
A5, but no mixed optical source.

The event CSV now records `source_particle`, `source_energy_keV`, `edep_keV`
and `scintillation`. `edep_keV` excludes later optical-photon absorption and
contains only non-optical energy deposited in GAGG. The three fast-component
runs produced exactly 540, 1080 and 2160 photons per event at 10, 20 and
40 keV, giving a fitted slope of exactly 54000 photons/MeV. Changing the
single decay constant from the paper's 62.53 ns fast value to its 190.89 ns
slow value changed the integrated yield by only 4.63e-5 relative; the output
fractions differed by 0.150 standard deviations. All photon accounting closed.

## A6 662 keV gamma validation

A6 uses one 662 keV gamma per event at `(0, 0, 14.7 mm)`, which is 1 mm above
the outer face of the top reflector. In `fixed` mode, gamma primaries travel
along -z and enter the paper geometry normally. `G4EmStandardPhysics` supplies
the photoelectric, Compton and charged-secondary transport needed at this
energy; optical production and transport remain those validated in A3-A5.

Run the fixed-seed 100-event sample, validate it and create the two plots:

~~~sh
./build/gagg_surface_study \
  ./build/macros/validation/a6_gamma.mac
python analysis/validate_a6.py \
  --input results/a6/gamma_662kev.csv --expect-events 100
MPLCONFIGDIR=results/.mplconfig python analysis/plot_a6.py \
  --input results/a6/gamma_662kev.csv \
  --output-dir results/a6/figures
~~~

This creates:

- `results/a6/gamma_662kev.csv`
- `results/a6/figures/a6_gamma_summary.csv`
- `results/a6/figures/a6_energy_deposition.png`
- `results/a6/figures/a6_gamma_light_yield.png`

Open the A6 Qt/OpenGL scene:

~~~sh
./build/gagg_surface_study --interactive \
  ./build/macros/validation/a6_vis.mac
~~~

The scene filters out optical trajectories and shows the normally incident
gamma in magenta, so the detector geometry is not obscured by tens of
thousands of scintillation tracks. The underlying optical photons are still
fully transported and counted.

The A6 full-energy gate is `661.5 <= Edep <= 662.5 keV`. With seeds 271828 and
314159, 100 events gave 28 zero-deposit events, 30 partial-energy events and
42 full-energy events. The full-energy subset produced 1,501,410 photons from
27,804 keV deposited, or 53999.784 photons/MeV. All 28 zero-deposit events
generated zero scintillation photons, and every event closed its optical
terminal accounting with zero unclassified photons.

The sharp simulated 662 keV entries are an energy-conservation validation,
not a prediction of the experimental peak width. `RESOLUTIONSCALE=0` remains
the A5 validation setting, and no electronics or intrinsic detector-energy
resolution has been applied. The source is a monoenergetic particle gun, not
a simulated radioactive decay.

## A7 Fig. 4 comparison - ordering gate not passed

A7 interprets the paper's normally incident gamma beam as a uniform circular
parallel beam over the 12.7 mm crystal radius. Four surfaces use the same 100
primary events and deterministic event seed base 730001. Scintillation tracks
are deferred until non-optical transport completes, so each event ID has the
same source position, Edep and N_generated for every finish. This removes a
random-stream coupling in which surface transport changed later gamma events.

Run the current comparison, validator and diagnostic plots:

~~~sh
./build/gagg_surface_study \
  ./build/macros/stage_a/a7_compare.mac
python analysis/validate_a7.py \
  --input-dir results/a7/production --expect-events 100
MPLCONFIGDIR=results/.mplconfig python analysis/plot_a7.py \
  --input-dir results/a7/production \
  --output-dir results/a7/figures --expect-events 100
~~~

The validator intentionally exits nonzero while the Fig. 4 order is wrong.
It still verifies the CSV schema, source disk, paired event selection,
scintillation yield, LUT activity and exact optical terminal accounting before
testing the order. The fixed sample contains the same 33 full-energy events
for all four finishes and gives event-level means with 95% confidence
intervals:

| Surface | Mean N_output/N_generated | 95% CI | Mean N_output |
|---|---:|---:|---:|
| polishedvm2000air | 0.80963 | 0.80168-0.81758 | 28942.7 |
| polishedtioair | 0.71835 | 0.70296-0.73374 | 25679.6 |
| groundvm2000air | 0.82768 | 0.82107-0.83430 | 29588.0 |
| groundtioair | 0.72919 | 0.71544-0.74295 | 26067.2 |

Thus the observed order is:

~~~text
groundvm2000air
  > polishedvm2000air
  > groundtioair
  > polishedtioair
~~~

Only `groundtioair > polishedtioair` agrees with the target. The other two
required pair differences have 95% confidence intervals entirely in the
wrong direction, so more events alone cannot repair the result.

The A7 audit found that the legacy LBNL LUT files provide reflected angular
distributions while Geant4's boundary process defaults absolute reflectivity
to one unless a surface property is supplied. The paper separately states
reflectivity above 98% for ESR and above 95% for TiO2. The current model uses
the conservative literature lower bounds 0.98 and 0.95, with the remainder
transmitted into the modeled reflector and absorbed according to its 0.1 mm
bulk absorption length. A diagnostic using the LUT default and another using
a ten-times-shorter GAGG absorption length both failed to recover Fig. 4, so
neither parameter was adopted as a fit.

A7 remains unvalidated. Do not create or move the `a7` tag until a documented
model difference explains the mismatch and the predefined ordering gate
passes.

The output-face audit also separated two definitions that had previously
looked identical:

- `firstArrival` counts and terminates a photon at its first geometrical
  arrival at the -z crystal face. This is the formal Stage A interpretation
  of the paper phrase "arriving at the output face".
- `transmitted` inspects `G4OpBoundaryProcess` and counts only
  `FresnelRefraction`, `Transmission` or `SameMaterial` into the receiver.
  Reflected photons continue transporting.

Four 50-primary paired diagnostics crossed direct/explicit-air interfaces
with both scoring definitions. All geometry, pairing and accounting checks
passed, but no model reproduced the complete Fig. 4 order:

| Model | Observed order | Fig. 4 |
|---|---|---|
| direct + first arrival | ground VM > polished VM > ground TiO > polished TiO | FAIL |
| 0.1 mm air + first arrival | ground VM > polished VM > ground TiO > polished TiO | FAIL |
| direct + transmitted | ground VM > ground TiO > polished TiO > polished VM | FAIL |
| 0.1 mm air + transmitted | ground VM > ground TiO > polished TiO > polished VM | FAIL |

The transmitted direct model reduced the full-energy mean counts to about
6564, 9948, 14698 and 10367 for polished VM, polished TiO, ground VM and
ground TiO. It therefore recovered `ground TiO > polished TiO > polished VM`
and moved the absolute scale toward Fig. 4, but `ground VM` remained highest
instead of lowest. Adding the explicit diagnostic air volume changed the
efficiencies by only a few (10^{-3}), so its thickness was not tuned.

Run and summarize the bounded model grid:

~~~sh
./build/gagg_surface_study \
  ./build/macros/validation/a7_model_direct_transmitted.mac
./build/gagg_surface_study \
  ./build/macros/validation/a7_model_direct_first_arrival.mac
./build/gagg_surface_study \
  ./build/macros/validation/a7_model_airgap_transmitted.mac
./build/gagg_surface_study \
  ./build/macros/validation/a7_model_airgap_first_arrival.mac
python analysis/summarize_a7_models.py \
  --input-dir results/a7/models --expect-events 50 \
  --output results/a7/models/model_summary.csv
~~~

## B0 experimental geometry and optical baseline

B0 is validated independently of the failed A7 ordering. It establishes the
measured 5.75 x 5.75 x 20 mm3 GAGG crystal, an explicit side air volume,
surrounding black absorber, top ESR and a bottom PMT receiver window. The
convention is +z top/ESR and -z bottom/PMT.

~~~text
                     +z
              ┌─────────────┐
              │  top ESR    │
        ┌─────┴─────────────┴─────┐
        │ black │  side air │ black│
        │       │ ┌───────┐ │      │
        │       │ │ GAGG  │ │      │  20 mm
        │       │ │5.75 mm│ │      │
        │       │ └───────┘ │      │
        └───────┴─────┬─────┴──────┘
                      │ PMT window
                     -z
~~~

The ESR and ideal black absorber use UNIFIED polished boundaries in B0. The
GAGG faces remain geometrically polished; no rough `sigma_alpha` and no
six-state surface switch are introduced until B1. B0 counts only photons that
actually transmit into `PMTWindow`, stored in the existing `output` column.

Run the geometry and 5000-photon optical baseline:

~~~sh
./build/gagg_surface_study \
  ./build/macros/validation/b0_geometry.mac
./build/gagg_surface_study \
  ./build/macros/validation/b0_transport.mac
python analysis/validate_b0.py \
  --input results/b0/b0_transport.csv \
  --expect-events 50 --photons-per-event 100
./build/gagg_surface_study --interactive \
  ./build/macros/validation/b0_vis.mac
~~~

The validated baseline delivered 1845/5000 photons to the PMT window,
`N_PMT/N_generated = 0.369`. All 5000 photons had exactly one terminal
classification, the direction sample passed isotropy checks, all analytic
geometry/position/overlap checks passed, and the full suite passed 23/23
CTest tests in 44.05 s.

## B1 six runtime surface states

B1 assigns independent UNIFIED borders to the GAGG top, bottom and sides. The
top ESR is represented as dielectric-metal; the bottom PMT-window and side-air
interfaces are dielectric-dielectric. The `/gagg/stageB/surfaceState` messenger
switches all six experimental states without recompilation. Every rough face
uses the same `/gagg/stageB/sigmaAlpha`; separate per-face roughness parameters
do not exist. The CSV records the active state and shared value together with
independent top, bottom and side boundary-interaction counters.

Run the deterministic six-state optical-only comparison and make the figures:

~~~sh
./build/gagg_surface_study \
  ./build/macros/stage_b/b1_compare.mac
python analysis/validate_b1.py \
  --input-dir results/b1 --expect-events 50 \
  --photons-per-event 100 --sigma-alpha 0.20
MPLCONFIGDIR=results/.mplconfig python analysis/plot_b1.py \
  --input-dir results/b1 --output-dir results/b1/figures \
  --expect-events 50 --photons-per-event 100 --sigma-alpha 0.20
./build/gagg_surface_study --interactive \
  ./build/macros/validation/b1_vis.mac
~~~

The B1 validation source emits 100 isotropic 550 nm photons at the crystal
center in each of 50 events, with identical primary directions for every
state. At the predeclared validation-only `sigma_alpha = 0.20 rad`, the current
B2 surface implementation gives:

| State | N_PMT / N_generated | Normalized to all polished |
|---|---:|---:|
| all polished | 0.3816 | 1.000 |
| bottom rough | 0.4562 | 1.195 |
| top rough | 0.4522 | 1.185 |
| side rough | 0.2070 | 0.542 |
| bottom polished, others rough | 0.1916 | 0.502 |
| top polished, others rough | 0.1968 | 0.516 |

This is a surface-assignment and transport diagnostic. The value 0.20 rad was
not fitted, no 511 keV interaction is present, and B1 does not claim an
experimental prediction. The exact all-polished repeat, runtime state and
roughness changes, shared-roughness checks, photon accounting, face counters
and plot export all passed. The `b1` tag retains the original B1 diagnostic;
B2 corrected the top ESR UNIFIED reflection components so a ground top face
actually responds to `sigma_alpha`.

## B2 optical-only roughness/position scan

B2 locks all scan inputs in `config/b2_scan.json`: shared
`sigma_alpha = 0, 0.05, 0.10, 0.20, 0.30 rad`, axial source positions
`z = -8, 0, +8 mm`, 50 events and 100 isotropic 550 nm photons per point.
All six B1 states are evaluated, for 90 analysis points plus one exact repeat.
No grid point is selected from the experimental ranking.

The runner generates one inspectable Geant4 macro per point and launches every
point in a fresh process. This isolation is required because a bounded audit
found one history-dependent event when ground UNIFIED surfaces were repeatedly
rebuilt in a single process. The active random engine (`MixMaxRng`) is printed
at startup, and event seeds use an explicit two-seed count.

~~~sh
python analysis/run_b2_scan.py \
  --executable build/gagg_surface_study \
  --config config/b2_scan.json --output-dir results/b2
python analysis/validate_b2.py \
  --input-dir results/b2 --config config/b2_scan.json
MPLCONFIGDIR=results/.mplconfig python analysis/plot_b2.py \
  --input-dir results/b2 --output-dir results/b2/figures \
  --config config/b2_scan.json
~~~

For orientation only, the normalized optical collection at the grid point
`sigma_alpha = 0.20 rad` is:

| State | z=-8 mm | z=0 mm | z=+8 mm |
|---|---:|---:|---:|
| all polished | 1.000 | 1.000 | 1.000 |
| bottom rough | 1.227 | 1.223 | 1.205 |
| top rough | 1.187 | 1.192 | 1.205 |
| side rough | 0.913 | 0.596 | 0.809 |
| bottom polished, others rough | 0.912 | 0.515 | 0.686 |
| top polished, others rough | 0.890 | 0.528 | 0.778 |

All 90 points closed photon accounting. The repeated point was identical at
event level, all-polished results were identical across the unused roughness
parameter, and the largest adjacent efficiency jump was 0.0608, below the
predeclared 0.20 discontinuity guard. These are optical-source diagnostics,
not 511 keV predictions or an experimental fit. Full A0-B2 regression passed
29/29 tests in 64.33 s.

## B3 controlled 511 keV gamma response

B3 fixes all run inputs in `config/b3_gamma.json` and introduces gamma
interactions into the Stage B geometry without yet comparing rough states.
The validation source is a normally incident 511 keV pencil beam at
`z=+14.7 mm`; the surface state is all polished and the B2 reference value
`sigma_alpha=0.20 rad` is recorded but inactive on polished faces.
Scintillation photons are deferred until non-optical event transport is
complete, which preserves the gamma history for the paired B4 comparison.

~~~sh
python analysis/run_b3.py \
  --executable build/gagg_surface_study \
  --config config/b3_gamma.json --output-dir results/b3
python analysis/validate_b3.py \
  --input results/b3/gamma_511kev_all_polished.csv \
  --config config/b3_gamma.json
MPLCONFIGDIR=results/.mplconfig python analysis/plot_b3.py \
  --input results/b3/gamma_511kev_all_polished.csv \
  --output-dir results/b3/figures --config config/b3_gamma.json
~~~

The 100-event locked sample contains 30 zero-deposit, 42 partial-energy and
28 full-energy events. The 510.5--511.5 keV full-energy subset gives
53999.86 generated photons/MeV and `N_PMT/N_generated=0.371400`; every event
closes terminal photon accounting. The energy spectrum and light-yield plot
were visually checked, and full A0--B3 regression passed 32/32 tests.

## B4 six-state 511 keV comparison

B4 reuses the exact B3 source, gamma histories and full-energy gate in six
separate Geant4 processes. Only `/gagg/stageB/surfaceState` changes. Every
rough face reads the one shared `sigma_alpha=0.20 rad`; the value remains the
predeclared B1/B2 reference and was not selected from the experimental data.
`config/b4_comparison.json` stores the preliminary measured ratios separately
from simulation inputs.

~~~sh
python analysis/run_b4.py \
  --executable build/gagg_surface_study \
  --config config/b4_comparison.json --output-dir results/b4
python analysis/validate_b4.py \
  --input-dir results/b4 \
  --b3-reference results/b3/gamma_511kev_all_polished.csv \
  --config config/b4_comparison.json
MPLCONFIGDIR=results/.mplconfig python analysis/plot_b4.py \
  --input-dir results/b4 --output-dir results/b4/figures \
  --config config/b4_comparison.json
~~~

The 28 paired full-energy events give:

| State | N_PMT/N_generated | Simulation, normalized | Paired 95% CI | Experiment |
|---|---:|---:|---:|---:|
| all polished | 0.371400 | 1.000 | 1.000--1.000 | 1.00 |
| bottom rough | 0.445774 | 1.200 | 1.196--1.204 | 1.60 |
| top rough | 0.444558 | 1.197 | 1.191--1.205 | 1.54 |
| side rough | 0.254264 | 0.685 | 0.651--0.720 | 0.39 |
| bottom polished, others rough | 0.234767 | 0.632 | 0.596--0.671 | 0.39 |
| top polished, others rough | 0.242808 | 0.654 | 0.621--0.688 | 0.32 |

The current model therefore reproduces the broad separation between the two
single-end rough states (enhanced) and the three side/multiple-rough states
(suppressed). It underpredicts both enhancements, underpredicts the amount of
suppression, and reverses the last two states. The comparison gate passes
because pairing, accounting, uncertainty calculation and parameter
provenance pass; agreement with experiment is deliberately not a pass test.

## B5 robustness and interpretation

B5 varies only the one shared roughness parameter across the B2-predeclared
`sigma_alpha=0.10, 0.20, 0.30 rad` subset. The B4 0.20-rad files are reused;
the runner creates 12 additional isolated samples for 0.10 and 0.30 rad.
Up to four independent Geant4 processes run concurrently, which preserves
process isolation while reducing the validated scan time from 694.8 s to
135.6 s on the development machine.

~~~sh
python analysis/run_b5.py \
  --executable build/gagg_surface_study \
  --config config/b5_robustness.json --output-dir results/b5
python analysis/validate_b5.py \
  --input-dir results/b5 --b4-input-dir results/b4 \
  --config config/b5_robustness.json
MPLCONFIGDIR=results/.mplconfig python analysis/plot_b5.py \
  --input-dir results/b5 --b4-input-dir results/b4 \
  --output-dir results/b5/figures --config config/b5_robustness.json
~~~

| State | Shared-sigma prediction envelope | Experiment | Covered? |
|---|---:|---:|---:|
| all polished | 1.000--1.000 | 1.00 | yes, normalization |
| bottom rough | 1.200--1.203 | 1.60 | no |
| top rough | 1.170--1.207 | 1.54 | no |
| side rough | 0.630--0.745 | 0.39 | no |
| bottom polished, others rough | 0.567--0.724 | 0.39 | no |
| top polished, others rough | 0.581--0.731 | 0.32 | no |

Changing the full-energy half-width among 0.25, 0.5 and 1.0 keV retained the
same 28 ideal full-energy events. Four of five rough states changed by at
least the retained 0.01 reporting threshold; bottom rough changed by only
0.003. Thus the current discrepancy is larger than Monte Carlo uncertainty
and cannot be removed by the tested peak window or by selecting another
single shared sigma within this range. Unknown coupling, PMT response, ESR
placement/properties, black structure and surface metrology remain hypotheses,
not fitted explanations. The evidence boundary and required measurements are
recorded in `docs/b5-findings.md`.

The B5 subset passed 3/3 tests in 135.62 s after parallelization. The final
A0--B5 regression passed 38/38 tests in 802.90 s; the longer full-suite time
reflects variable optical-transport load and does not change the event-level
results.

## B6 location-resolved loss budget

B6 does not change any optical parameter. It extends each event record with
five surface-absorption locations, then decomposes the event-paired B4/B5
full-energy samples into PMT collection, GAGG self-absorption, ESR loss,
black-structure loss and small remaining outcomes.

~~~sh
python analysis/validate_b6.py \
  --input-dir results/b5 --b4-input-dir results/b4 \
  --config config/b6_diagnostics.json
MPLCONFIGDIR=results/.mplconfig python analysis/plot_b6.py \
  --input-dir results/b5 --b4-input-dir results/b4 \
  --output-dir results/b6/figures --config config/b6_diagnostics.json
~~~

At shared `sigma_alpha=0.20 rad`, the main terminal fractions are:

| State | PMT | GAGG absorption | Top ESR | Black structure |
|---|---:|---:|---:|---:|
| all polished | 0.3714 | 0.2959 | 0.0383 | 0.2932 |
| bottom rough | 0.4458 | 0.1343 | 0.0143 | 0.4032 |
| top rough | 0.4446 | 0.1418 | 0.0153 | 0.3971 |
| side rough | 0.2543 | 0.0305 | 0.0055 | 0.7061 |
| bottom polished, others rough | 0.2348 | 0.0296 | 0.0055 | 0.7261 |
| top polished, others rough | 0.2428 | 0.0309 | 0.0055 | 0.7169 |

End-face roughness shortens trapped paths and reduces crystal self-absorption,
but redirects much of that recovered light to the black structure; the net PMT
gain is only about 0.074. Side/multiple roughness drives black absorption up
by 0.413--0.433 and is therefore the direct cause of the simulated light
suppression. Since the black boundary is already an ideal zero-reflectivity
absorber, the remaining experiment/model gap cannot be solved by making it
darker. Detailed evidence and next measurements are in `docs/b6-findings.md`.

The B3--B6 targeted suite passed 11/11 tests in 152.98 s. Final A0--B6
regression passed 40/40 tests in 214.37 s.

## B7 effective annihilation-source face

B7.1 adds a backward-compatible square gamma-source position sampler. The
existing point and circular beam remain active when `/gagg/source/faceSize`
is zero. The B7 effective-source value is 2.5 mm, centred at `(0,0,30) mm`:

~~~sh
./build/gagg_surface_study build/macros/validation/b7_face_source.mac
MPLCONFIGDIR=build/.mplconfig python analysis/validate_b7_face_source.py \
  --input results/b7_1_face_source/positions.csv \
  --output-dir results/b7_1_face_source/figures \
  --expect-events 5000 --face-size-mm 2.5
~~~

The 5000-event deterministic validation sampled x in
`[-1.248967, 1.249723] mm` and y in `[-1.249803, 1.249929] mm`. The means
were 0.01460 and 0.00652 mm; the variances were 0.52133 and 0.52252 mm2,
compared with the uniform-square expectation 0.52083 mm2. The 5x5-grid
reduced chi-square was 1.36375 and every predeclared range, moment,
correlation, edge-coverage and grid-uniformity check passed.

This B7.1 macro deliberately uses one fixed-direction 1 keV gamma only to
make the position test inexpensive. It is not a source-physics result.

B7.2 adds `/gagg/source/particle annihilationPair`. Every event now contains
one primary vertex at the validated square-face position and two 511 keV
gammas. One pair axis is sampled uniformly over 4pi and the second gamma is
assigned the exactly opposite direction. Source kinematics are written to a
separate audit CSV so the locked A0--B6 event schema remains unchanged:

~~~sh
./build/gagg_surface_study \
  build/macros/validation/b7_annihilation_pair_source.mac
MPLCONFIGDIR=build/.mplconfig \
python analysis/validate_b7_annihilation_pair.py \
  --input results/b7_2_annihilation_pair/source_audit.csv \
  --output-dir results/b7_2_annihilation_pair/figures \
  --expect-events 10000 --face-size-mm 2.5
~~~

All 10000 events had one vertex, two primaries and two 511 keV energies. The
sampled first-axis component means were (-0.00927, 0.00906, -0.00124), and
second moments were (0.33651, 0.33412, 0.32937), consistent with isotropy.
The cos(theta) range was [-0.999886, 0.999877], the 12-bin phi reduced
chi-square was 1.75818, and every pair had a direction dot product of -1.
The source is an effective unpolarized gamma model; positron transport,
source encapsulation and annihilation-polarization correlations are not
represented.

The B7.2 validation transported the particles through the optical model and
closed all photon accounting, but its aggregate light totals are not a
511 keV full-energy selection. That event gate and PMT-light estimator belong
to B7.3.

B7.3 migrates the schematic experiment geometry used after B6: 5.75 mm side
air clearance, 1.15 mm top and bottom air gaps, 4.0 mm black structure,
upper/lower shoulders, an 11.5 x 11.5 x 0.1 mm3 ESR sheet and a 25 mm diameter
x 1 mm PMT window. These are image-based estimates, not measured dimensions
or fit parameters. The top and bottom roughness surfaces now act at the
GAGG-air boundaries; fixed polished interfaces connect the air layers to ESR
and PMT. `N_PMT` is counted only when an optical photon transmits from the
bottom air layer into the PMT window.

The locked all-polished run uses 100000 annihilation-pair events and applies
the event-level gate `510.5 <= Edep_GAGG <= 511.5 keV`. This does not select
511 keV optical photons: it selects 511 keV gamma full-energy events and then
counts their approximately 2.25 eV scintillation photons at the PMT window.

~~~sh
python analysis/run_b7_3.py --executable build/gagg_surface_study \
  --config config/b7_3_full_energy_response.json \
  --output-dir results/b7_3_full_energy_100k
python analysis/validate_b7_3.py \
  --input results/b7_3_full_energy_100k/annihilation_pair_all_polished.csv
MPLCONFIGDIR=build/.mplconfig python analysis/plot_b7_3.py \
  --input results/b7_3_full_energy_100k/annihilation_pair_all_polished.csv \
  --output-dir results/b7_3_full_energy_100k/figures
~~~

The actual sample contained 99400 zero-deposit, 413 partial-deposit and 187
full-energy events. The selected events generated 5,160,063 scintillation
photons and delivered 492,993 photons to the PMT window, giving
`sum(N_PMT)/sum(N_generated) = 0.0955401`. Mean `N_PMT` was
2636.33 +/- 9.93 (standard error), and the selected-event light yield was
53999.84 photons/MeV. All optical terminal accounting closed. B7.3 validates
the source-to-response statistic only.

B7.4 scans one shared UNIFIED `sigma_alpha` over
`0, 0.02, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50, 0.70 rad`. Each of the
five rough-surface states uses exactly the same sigma at a scan point; no
per-face fit is permitted. One all-polished reference is reused, and all 51
points use exactly paired source positions, gamma histories, GAGG deposits
and scintillation yields.

~~~sh
python analysis/run_b7_4.py --executable build/gagg_surface_study \
  --config config/b7_4_sigma_scan.json \
  --output-dir results/b7_4_sigma_scan_20k --jobs 4
python analysis/validate_b7_4.py \
  --config config/b7_4_sigma_scan.json \
  --input-dir results/b7_4_sigma_scan_20k
~~~

Every 20000-event point contained the same 38 full-energy events. The
predeclared five-state RMSE is minimized mathematically at `sigma_alpha=0`
with RMSE 0.79278. Among positive candidates it is minimized at the scanned
upper boundary, `0.70 rad`, with RMSE 0.79688. At 0.70 rad the normalized
responses for bottom rough and top rough are 2.08496 and 3.07435, compared
with preliminary experimental values 1.60 and 1.54. Side/multiple-rough
states also remain too bright. B7.4 therefore validates the scan machinery
but rejects shared `sigma_alpha` alone as an adequate explanation of all six
experimental responses.

B7.5 isolates the two single-end-face states at the B7.4 positive-grid
candidate `sigma_alpha=0.70 rad`. It runs 100000 events for `bottom_rough`
and `top_rough`, reuses the paired B7.3 all-polished reference, and writes
event CSVs plus numerical summaries only; no new plot is generated.

~~~sh
python analysis/run_b7_5.py --executable build/gagg_surface_study \
  --config config/b7_5_endface_sigma070.json \
  --output-dir results/b7_5_endface_sigma070_100k --jobs 2
python analysis/validate_b7_5.py \
  --config config/b7_5_endface_sigma070.json \
  --input-dir results/b7_5_endface_sigma070_100k \
  --reference results/b7_3_full_energy_100k/annihilation_pair_all_polished.csv
~~~

All three samples selected the same 187 full-energy events. Bottom rough gave
mean `N_PMT=5493.25`, collection efficiency 0.199075 and normalized response
2.08368. Top rough gave mean `N_PMT=8073.69`, efficiency 0.292589 and
normalized response 3.06248. The paired bottom/top photon ratio is 0.680389
(95% bootstrap interval 0.676611--0.684050), while the preliminary experiment
gives 1.60/1.54=1.03896. Thus the current model predicts a strong top-rough
advantage, whereas the experiment shows a small bottom-rough advantage.

## Directory design

~~~text
GAGG/
├── app/                    executable entry point
├── config/                 locked scan grids and validation parameters
├── include/GAGG/           interfaces and central defaults
├── src/                    Geant4 implementation
├── macros/
│   ├── validation/         deterministic checks
│   ├── stage_a/            paper-reproduction runs
│   └── stage_b/            real-experiment runs
├── analysis/               reduction and plotting
├── docs/                   plans, decisions, validation log
├── reference/              source PDF/PPTX, read-only
├── results/                generated output
└── build/                  out-of-source build
~~~

Runtime commands will use the "/gagg/" namespace. Surface states will be
selected by macro/messenger without recompiling. Active defaults are
centralized in "include/GAGG/SimulationConfig.hh".

## Parameter provenance

| Parameter | Value | Class | Source/status |
|---|---:|---|---|
| Stage A crystal | diameter 25.4 mm, length 25.4 mm | literature | paper |
| density | 6.63 g/cm3 | literature | paper |
| light yield | 54000 photons/MeV | literature | A5 active and validated |
| refractive index | 1.91 | literature | paper |
| emission spectrum | narrow 545/550/555 nm, peak 550 nm | literature simplification | A5 active |
| fast decay time | 62.53 ns | literature | A5 single-component default |
| slow decay time | 190.89 ns | literature | A5 timing-control value |
| resolution scale | 0 | validation setting | disables yield fluctuations in A5 |
| Stage A gamma energy | 662 keV | literature | A6 monoenergetic source active |
| A6 gamma source | z=+14.7 mm, direction -z | validation geometry | 1 mm above top reflector |
| absorption coefficient | 0.0155 cm^-1 | literature | paper |
| absorption length | 64.516 cm | derived | reciprocal |
| reflector | 1 mm, n=1.35 | literature | A2 geometry active in `paper` mode |
| reflector density | 2.2 g/cm3, Teflon assumption | literature | A2 validated |
| reflector absorption | 100 cm^-1 = 0.1 mm length | literature model assumption | A2 bulk property active |
| Stage A LUT data | RealSurface 2.2 | installed Geant4 dataset | A4 active |
| Stage A finishes | four named LBNL LUT finishes | literature model choice | A4 runtime-selectable |
| VM2000 reflectivity | 0.98 | literature lower-bound proxy | A7 explicit surface property |
| TiO2 reflectivity | 0.95 | literature lower-bound proxy | A7 explicit surface property |
| A7 beam radius | 12.7 mm | documented interpretation | uniform parallel beam over crystal face |
| A7 event seed base | 730001 | validation control | pairs source/Edep/generated across finishes |
| Stage B crystal | 5.75 x 5.75 x 20 mm3 | measured/setup | slides |
| B0 side air gap | 0.1 mm | unmeasured placeholder | runtime-selectable; not fitted |
| B0 black structure thickness | 1.0 mm | unmeasured placeholder | runtime-selectable; ideal absorber |
| B0 top ESR thickness | 0.1 mm | unmeasured placeholder | runtime-selectable |
| B0 PMT window thickness/index | 0.5 mm / 1.52 | model placeholder | direct contact in B0 |
| B1 rough sigma_alpha | 0.20 rad | free validation parameter | predeclared diagnostic value; one shared value; not fitted |
| B2 sigma_alpha grid | 0, 0.05, 0.10, 0.20, 0.30 rad | free validation grid | locked before B2 results; no selected value |
| B2 optical source positions | z=-8, 0, +8 mm | validation geometry | axial points, 2 mm from each end at extremes |
| B3 gamma energy / source | 511 keV / z=+14.7 mm pencil beam | validation control | Stage B gamma-response gate |
| B3 full-energy gate | 510.5--511.5 keV | analysis definition | locked before B4 comparison |
| B3/B4 event seed base | 830001 | validation control | supports event-paired surface comparisons |
| B4 measured ratios | 1.00, 1.60, 1.54, 0.39, 0.39, 0.32 | measured/preliminary | comparison only; never supplied to Geant4 |
| B4 bootstrap | 5000 paired resamples, seed 840001 | analysis control | 95% confidence intervals |
| B5 shared sigma grid | 0.10, 0.20, 0.30 rad | free validation grid | B2-predeclared subset; no point selected |
| B5 full-energy half-widths | 0.25, 0.5, 1.0 keV | analysis robustness grid | identical 28-event ideal sample |
| B6 surface-loss locations | top, bottom, side, black, other | diagnostic counters | exact subtotals; no physics change |
| B7 effective source face | 2.5 x 2.5 mm2, centred at (0,0,30) mm | explicit model assumption | B7.1 uniform x-y sampling validated; directions deferred to B7.2 |
| B7 effective annihilation emission | two 511 keV gammas, one vertex, exactly back-to-back | explicit model assumption | B7.2 pair axis sampled uniformly over 4pi; unpolarized |
| B7 nominal side/top/bottom air gaps | 5.75 / 1.15 / 1.15 mm | image-based estimate | not measured and not fitted |
| B7 nominal black/ESR/PMT geometry | 4.0 mm black; 11.5 x 11.5 x 0.1 mm3 ESR; 25 mm diameter x 1 mm PMT window | image-based estimate | includes upper/lower shoulders |
| B7.3 full-energy gate | 510.5--511.5 keV event-total GAGG Edep | analysis definition | PMT counts remain optical scintillation photons |
| ESR specular-lobe fraction | 1.0 | UNIFIED model choice | fixed, not fitted; makes ground ESR reflection sigma-driven |

The bulk composition is stoichiometric Gd3Al2Ga3O12. Ce concentration was not
provided and is omitted from mass composition; supplied density and optical
constants are used directly.

For the Stage A paper geometry, the side sleeve directly touches the crystal
and spans only the crystal length. The top cap covers the full 13.7 mm outer
radius and directly touches both crystal and sleeve. The paper gives no finite
air-gap thickness, so none is invented. A4 and later stages assign the selected
LUT as directional GAGG-to-reflector border surfaces on the side and top only;
the -z output face remains open.

The Stage A qualitative target read from Fig. 4 is:

~~~text
groundtioair
  > polishedtioair
  > polishedvm2000air
  > groundvm2000air
~~~

See "docs/stage-a-plan.md" and "docs/validation-log.md".

Git commits and annotated tags are created only after a validation gate
passes. A7 remains untagged; B0, B1 and B2 are independently validated
checkpoints.
See "docs/git-workflow.md" for the push convention.
