# GAGGSurfaceStudy

This project studies how GAGG:Ce surface treatment changes optical-photon
collection.

- Stage A reproduces the qualitative ordering in Fig. 4 of the paper with
  four Geant4 LUT finishes.
- Stage B models the six experimental surface states for a
  5.75 mm x 5.75 mm x 20 mm crystal with the UNIFIED model and one shared
  rough-surface sigma_alpha.

The current validated milestone is A5. A0 provides a one-photon optical
transport baseline, Qt/OpenGL view, event-level CSV output, accounting checks
and reproducible plots. A1 validates the literature parameters and their
Geant4 unit conversions. A2 adds the paper's 1 mm Teflon-assumption side
sleeve and top cap while leaving the -z crystal output face open. A3 adds a
fixed-count isotropic 550 nm source at controlled positions and records the
first crossing of that open face as `N_output`. A4 attaches the four paper
LBNL LUT finishes to the GAGG-to-side/top borders and switches them at runtime
through geometry reinitialization. A5 adds Geant4 scintillation with a narrow
550 nm component and validates its 54000 photons/MeV yield using controlled
electron energy deposits.

There is no gamma source, PMT, or fitting yet. A5 validates scintillation
production independently of gamma interactions. Fig. 4 ordering is still
deferred until A7, after the A6 662 keV gamma and full-energy-event gate.

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

The fixed A4 functional run returned 0.8818, 0.8586, 0.8826 and 0.8657 for
`polishedvm2000air`, `polishedtioair`, `groundvm2000air` and `groundtioair`,
respectively. This is not the paper's order and is not treated as an A4
failure: the source is still a point-like fixed-count optical source rather
than 662 keV gamma-induced scintillation. No parameter was tuned.

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

## Directory design

~~~text
GAGG/
├── app/                    executable entry point
├── include/GAGG/           interfaces and central defaults
├── src/                    Geant4 implementation
├── macros/
│   ├── validation/         deterministic checks
│   ├── stage_a/            paper-reproduction runs
│   └── stage_b/            real-experiment runs, future
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
| absorption coefficient | 0.0155 cm^-1 | literature | paper |
| absorption length | 64.516 cm | derived | reciprocal |
| reflector | 1 mm, n=1.35 | literature | A2 geometry active in `paper` mode |
| reflector density | 2.2 g/cm3, Teflon assumption | literature | A2 validated |
| reflector absorption | 100 cm^-1 = 0.1 mm length | literature model assumption | A2 bulk property active |
| Stage A LUT data | RealSurface 2.2 | installed Geant4 dataset | A4 active |
| Stage A finishes | four named LBNL LUT finishes | literature model choice | A4 runtime-selectable |
| Stage B crystal | 5.75 x 5.75 x 20 mm3 | measured/setup | slides |
| rough sigma_alpha | unset | free parameter | one shared value |

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
passes. See "docs/git-workflow.md" for the A0-A7 push convention.
