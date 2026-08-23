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

## 2026-08-23 - A2 paper geometry

- The paper geometry is selectable with `/gagg/geometry/mode bare|paper`
  before initialization; all A0 macros explicitly retain `bare` mode.
- `paper` mode adds a 1 mm side annulus from radius 12.7 to 13.7 mm over the
  25.4 mm crystal length and a 1 mm top disk of radius 13.7 mm.
- The reflector uses `G4_TEFLON`, matching the paper's Teflon assumption and
  stated density of 2.2 g/cm3. Its A1 refractive index and absorption length
  are attached as bulk optical properties; the material table was read back
  at 550 nm and returned 1.35 and 0.1 mm.
- The side sleeve and top cap directly touch the crystal. The -z output face
  remains open because the paper does not provide a finite air-gap thickness.
- Geant4 overlap checks reported OK for GAGG, SideReflector and TopReflector;
  the independent A2 check reported zero overlaps.
- Computed volumes were 12870.4 mm3 for GAGG, 2106.63 mm3 for the side sleeve
  and 589.646 mm3 for the top cap, all matching their analytic values.
- Navigator probes returned `GAGG`, `SideReflector`, `TopReflector` and
  `World` at the center, side, top and immediately below the output face.
- The Qt/OpenGL A2 scene opened successfully with separate colors for the
  crystal, side sleeve and top cap.
- The complete regression suite passed 6/6 tests, including all A0/A1 tests
  and `a2_paper_geometry`.

Status: validation gate A2 passed. No LUT surface, optical collection metric,
scintillation, gamma source or PMT has been added.

## 2026-08-23 - A3 optical transport before scintillation

- `/gagg/source/mode fixed|isotropic`, `/gagg/source/photonsPerEvent` and the
  dimensioned `/gagg/source/position x y z unit` command configure the source
  without recompiling. A0 macros explicitly retain their fixed +z source.
- Isotropic directions use uniform azimuth and uniform cosine of polar angle;
  polarization is randomized in the plane normal to each direction.
- Each A3 validation run used 100 events with 200 photons per event at 550 nm.
  Direction means were within 0.01 of zero and second moments within 0.003 of
  1/3, passing the predefined 0.02 tolerance.
- A photon is counted as output on its first GAGG-to-world crossing through
  the open -z face and is then killed. Absorptions are classified separately
  in GAGG, the side/top reflector and any other material.
- The event CSV includes source coordinates, detailed terminal categories,
  legacy world-exit/bulk-absorption subtotals and an unclassified remainder.
  Every tested event satisfied exact photon accounting with zero unclassified
  photons.
- Repeating the center run after resetting seeds produced 100 CSV rows that
  were exactly identical field by field.
- At the center, 20,000 photons produced 3,413 output photons, 500 GAGG
  absorptions, 16,076 reflector absorptions and 11 other world exits, giving
  `N_output/N_generated = 0.17065`.
- Disabling only GAGG bulk absorption produced zero GAGG absorptions and an
  output efficiency of 0.17800, so collection did not decrease. The
  on/off difference is within the recorded three-sigma comparison interval.
- The z = -10, -5, 0, 5 and 10 mm scan returned 0.40250, 0.25870, 0.17065,
  0.17735 and 0.17155. No adjacent upward reversal exceeded 3 sigma; the
  largest was 1.767 sigma, and the near-output efficiency exceeded the far-end
  efficiency.
- Three plots were generated and visually inspected: the axial position scan,
  center terminal outcomes and bulk-absorption control. The Qt/OpenGL scene
  also opened successfully with 20 isotropic photon trajectories.
- The complete A0-A3 regression suite passed 10/10 CTest tests.

Status: validation gate A3 passed. These results use only Fresnel transport
and reflector bulk absorption; no LUT optical surface, scintillation, gamma
source or PMT exists, so the efficiencies are not Fig. 4 predictions.
