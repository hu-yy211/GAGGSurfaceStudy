# GAGGSurfaceStudy

This project studies how GAGG:Ce surface treatment changes optical-photon
collection.

- Stage A reproduces the qualitative ordering in Fig. 4 of the paper with
  four Geant4 LUT finishes.
- Stage B models the six experimental surface states for a
  5.75 mm x 5.75 mm x 20 mm crystal with the UNIFIED model and one shared
  rough-surface sigma_alpha.

The current validated milestone is A1. One 550 nm optical photon is launched
per event from the center of the paper-sized GAGG cylinder. A0 provides a
Qt/OpenGL view, event-level CSV output, accounting checks and reproducible
plots. A1 validates the literature parameters and their Geant4 unit
conversions. Optical physics plus the minimum standard electromagnetic support
required for valid process-manager initialization is active.

There is no gamma source, reflector geometry, LUT surface, scintillation
production, PMT, or fitting yet. In particular, A2 has not started.

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

The CSV columns are `event_id`, `generated`, `world_exit`,
`bulk_absorption`, and `unclassified`. A0 requires exactly one generated
photon and one classified terminal outcome per event, with zero unclassified
photons.

Run only the A1 material/unit check:

~~~sh
./build/gagg_surface_study --validate-materials
~~~

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
| reflector | 1 mm, n=1.35 | literature | A1 validated, geometry inactive |
| reflector absorption | 100 cm^-1 = 0.1 mm length | literature assumption | A1 validated, geometry inactive |
| Stage B crystal | 5.75 x 5.75 x 20 mm3 | measured/setup | slides |
| rough sigma_alpha | unset | free parameter | one shared value |

The bulk composition is stoichiometric Gd3Al2Ga3O12. Ce concentration was not
provided and is omitted from mass composition; supplied density and optical
constants are used directly.

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
