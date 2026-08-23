# Validation log

## 2026-08-23 - Inputs and environment

- The target directory existed and contained empty code directories plus the
  two reference files.
- All 6 PDF pages and all 8 PPTX slides were read and visually inspected.
- Fig. 3/Fig. 4 geometry and line ordering were checked.
- Slide 6 peak positions were read as 10.065, 9.685, 6.279, 2.445, 2.443 and
  2.003 nV s.
- Conda environment "hep" contains Geant4 11.2.2, CMake 3.30.2, CLHEP
  2.4.6.2, Qt 5.15.8 and real-surface data 2.2.
- Apple Clang 21.0.0 and Xcode command-line tools are available.

## 2026-08-23 - A0 optical smoke test

- CMake found Geant4 11.2.2 at
  "/opt/homebrew/Caskroom/miniconda/base/envs/hep/lib/cmake/Geant4".
- The project compiled and linked with conda Clang 16.0.6 and no compiler
  warnings.
- Geant4 reported "Checking overlaps for volume GAGG ... OK".
- The run header reported 550 nm = 2.25426 eV and an absorption length of
  64.5161 cm.
- Ten fixed-seed events ran. All ten photons had world_exit=1,
  bulk_absorption=0 and unclassified=0.
- CTest result: 1/1 passed.

Status: validation gate A0 passed. No Stage A reflector, LUT surface,
scintillation source or gamma source has been added.

## 2026-08-23 - A0 visualization, CSV and plots

- CMake now requires the installed Geant4 UI and visualization components.
- The Qt/OpenGL viewer opened successfully with the paper-sized yellow GAGG
  cylinder, coordinate axes and a green optical-photon trajectory.
- Event output is configurable at runtime with `/gagg/output/csv`; no rebuild
  is needed to change the destination.
- The CSV validator checks the exact schema, contiguous event IDs, one
  generated photon, one terminal outcome and zero unclassified photons for
  every event.
- A fixed-seed 1000-event presentation run produced 975 world exits, 25 bulk
  absorptions and zero unclassified photons. Independent CSV accounting
  validation passed.
- The plotting script produced a terminal-outcome bar chart and cumulative
  photon-accounting closure plot. Both images were visually inspected.

Status: the extended A0 diagnostics passed. The reported 97.5% world-exit
fraction is a transport sanity check, not a PMT collection efficiency.

## 2026-08-23 - A1 materials and units

- The GAGG density is 6.63 g/cm3 and its refractive index is 1.91.
- 550 nm converted to 2.25426 eV.
- 0.0155 cm^-1 converted to an absorption length of 64.5161 cm.
- The future reflector thickness is 1 mm and its refractive index is 1.35.
- The future reflector assumption 100 cm^-1 converted to 0.1 mm.
- The optical energy grid is strictly increasing and covers 550 nm.
- The complete suite passed: 5/5 CTest tests (`smoke`, `a0_csv_export`,
  `a0_csv_validate`, `a0_plot`, and `a1_material_units`).

Status: validation gate A1 passed. The 1 mm reflector, its refractive index and
its absorption length are centralized and unit-tested constants only. No A2
reflector geometry has been implemented.
