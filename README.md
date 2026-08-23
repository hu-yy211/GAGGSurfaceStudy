# GAGGSurfaceStudy

This project studies how GAGG:Ce surface treatment changes optical-photon
collection.

- Stage A reproduces the qualitative ordering in Fig. 4 of the paper with
  four Geant4 LUT finishes.
- Stage B models the six experimental surface states for a
  5.75 mm x 5.75 mm x 20 mm crystal with the UNIFIED model and one shared
  rough-surface sigma_alpha.

The current validated milestone is A3. A0 provides a one-photon optical
transport baseline, Qt/OpenGL view, event-level CSV output, accounting checks
and reproducible plots. A1 validates the literature parameters and their
Geant4 unit conversions. A2 adds the paper's 1 mm Teflon-assumption side
sleeve and top cap while leaving the -z crystal output face open. A3 adds a
fixed-count isotropic 550 nm source at controlled positions and records the
first crossing of that open face as `N_output`.

There is no LUT optical surface, scintillation production, gamma source, PMT,
or fitting yet. The current `N_output/N_generated` values validate transport
and accounting only and must not be compared with the paper's Fig. 4 yet.

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
            + N_other_absorption + N_other_world_exit + N_unclassified
~~~

For the fixed A3 validation seed, each scan point contains 20,000 photons.
The center efficiency is 0.17065, and disabling GAGG self-absorption gives
0.17800. The axial scan at z = -10, -5, 0, 5 and 10 mm gives 0.40250,
0.25870, 0.17065, 0.17735 and 0.17155. The small center-to-+5 mm reversal is
1.767 standard deviations and therefore not statistically significant.

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
| light yield | 54000 photons/MeV | literature | inactive |
| refractive index | 1.91 | literature | paper |
| emission wavelength | 550 nm | literature simplification | paper |
| absorption coefficient | 0.0155 cm^-1 | literature | paper |
| absorption length | 64.516 cm | derived | reciprocal |
| reflector | 1 mm, n=1.35 | literature | A2 geometry active in `paper` mode |
| reflector density | 2.2 g/cm3, Teflon assumption | literature | A2 validated |
| reflector absorption | 100 cm^-1 = 0.1 mm length | literature model assumption | A2 bulk property active |
| Stage B crystal | 5.75 x 5.75 x 20 mm3 | measured/setup | slides |
| rough sigma_alpha | unset | free parameter | one shared value |

The bulk composition is stoichiometric Gd3Al2Ga3O12. Ce concentration was not
provided and is omitted from mass composition; supplied density and optical
constants are used directly.

For A2 the side sleeve directly touches the crystal and spans only the crystal
length. The top cap covers the full 13.7 mm outer radius and directly touches
both crystal and sleeve. The paper gives no finite air-gap thickness, so none
is invented. These solids do not yet define the LUT boundary response.

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
