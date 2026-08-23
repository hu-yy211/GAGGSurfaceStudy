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

## 2026-08-23 - A4 LUT switching by messenger

- `/gagg/stageA/surface` accepts `none` plus the four required LBNL LUT
  finishes. The four active finishes are switched at PreInit or Idle without
  recompilation.
- At Idle, a finish change clears the old logical-border table and requests
  `ReinitializeGeometry(true)`. The comparison macro explicitly initializes
  the new geometry before validating or running it.
- The active finish is assigned to the directional GAGG-to-side-reflector and
  GAGG-to-top-reflector borders. Both borders share one `G4OpticalSurface`
  configured as `model=LUT` and `type=dielectric_LUT`; the -z output face has
  no LUT surface.
- `G4REALSURFACEDATA` resolved to RealSurface 2.2. Geant4 successfully read
  `PolishedVM2000.z`, `PolishedTiO.z`, `GroundVM2000.z` and `GroundTiO.z`.
  The A4 surface validator confirmed the expected file, finish, model, type
  and exactly two border surfaces after every initialization.
- The event CSV now records `stage_a_surface`, `surface_absorption` and
  `lut_interactions`. A0/A3 require these LUT diagnostics to be inactive;
  A4 requires a nonzero interaction count. Terminal accounting includes
  surface absorption and remained exact with zero unclassified photons.
- Each finish used 50 events with 200 fixed-count isotropic 550 nm photons per
  event. `polishedvm2000air`, `polishedtioair`, `groundvm2000air` and
  `groundtioair` produced efficiencies 0.8818, 0.8586, 0.8826 and 0.8657 and
  31,234, 41,232, 32,989 and 38,783 LUT interactions, respectively.
- LBNL LUT non-reflections entered the 0.1 mm bulk-absorption reflector in
  this geometry; boundary-process `surface_absorption` was zero and is not
  required to be positive. No parameter was changed in response.
- Resetting the seed after switching back to `polishedvm2000air` reproduced
  the original 50 CSV event rows exactly.
- The efficiency/error-bar plot and normalized terminal-outcome plot were
  generated and visually inspected. The Qt/OpenGL A4 macro opened with the
  `groundtioair` LUT loaded, two validated borders and 20 green trajectories;
  its single event closed with 46 LUT interactions and zero unclassified
  photons.
- The complete A0-A4 regression suite passed 13/13 CTest tests.

Status: validation gate A4 passed. The observed functional comparison does
not match the paper's Fig. 4 ordering, but A4 deliberately does not test that
ordering. Scintillation, a 662 keV gamma source, full-energy event selection
and the Fig. 4 validation criterion remain A5-A7 work.

## 2026-08-23 - A5 scintillation validation

- The GAGG material now has a three-point
  `SCINTILLATIONCOMPONENT1` spectrum at 545, 550 and 555 nm with relative
  intensities 0, 1 and 0. The narrow spectrum is a documented simplification
  of the paper's 550 nm peak rather than a fitted emission curve.
- `SCINTILLATIONYIELD` is 54000 photons/MeV, `SCINTILLATIONYIELD1` is 1 and
  `RESOLUTIONSCALE` is zero. The zero resolution scale deliberately removes
  yield fluctuations from the slope validation; the paper's 2% intrinsic
  resolution remains disabled until its simulation role is defined.
- The default one-component decay constant is the paper's 62.53 ns fast
  value. `/gagg/optics/scintillationTimeConstant` permits a PreInit change;
  190.89 ns, the paper's slow value, is used only as the A5 timing control.
  No two-component time profile has been introduced.
- `/gagg/optics/validateScintillation` read back the material table and
  confirmed the yield, component fraction, resolution scale, selected time
  constant, increasing three-point energy grid and 550 nm peak.
- `G4Scintillation` is enabled and Cerenkov production is explicitly disabled.
  A new stacking action counts only optical secondaries whose creator process
  is `Scintillation`; A0-A4 retain explicit optical primary sources and require
  zero scintillation photons.
- `/gagg/source/particle optical|electron` and
  `/gagg/source/kineticEnergy` add a controlled electron validation source.
  A5 uses exactly one center-origin electron per event and does not add a
  gamma source.
- Event output now includes `source_particle`, `source_energy_keV`,
  `edep_keV` and `scintillation`. `edep_keV` counts non-optical energy deposits
  in GAGG only, preventing later optical self-absorption from being counted a
  second time as primary deposited energy.
- Twenty events each at 10, 20 and 40 keV deposited exactly 200, 400 and
  800 keV in total and generated 10,800, 21,600 and 43,200 scintillation
  photons. This is exactly 540, 1080 and 2160 photons per event and gives a
  through-origin slope of 54000 photons/MeV with zero relative error.
- Every A5 event satisfied exact photon terminal accounting with zero
  unclassified photons and had nonzero LBNL LUT boundary interactions.
- At 20 keV, changing the decay constant from 62.53 ns to 190.89 ns changed
  the integrated count from 21,600 to 21,599 photons. The relative difference
  is 4.63e-5, within the predefined 1e-4 integer-generation tolerance. The
  output efficiencies differed by 0.150 combined standard deviations.
- The scintillation-linearity plot and timing-control plot were generated and
  visually inspected. The Qt/OpenGL scene opened successfully with one red
  1 keV electron and its green optical trajectories; the event deposited
  1 keV, generated 54 scintillation photons, recorded 194 LUT interactions,
  produced 49 output photons and closed with zero unclassified photons.
- The complete A0-A5 regression suite passed 17/17 CTest tests.

Status: validation gate A5 passed. The model now validates optical transport,
LUT boundaries and scintillation production separately. A 662 keV gamma
source, full-energy selection and Fig. 4 ordering remain A6-A7 work.

## 2026-08-23 - A6 662 keV gamma response

- `/gagg/source/particle` now accepts `gamma` in addition to the existing
  `optical` and `electron` modes. One gamma is generated per event with its
  macro-selected kinetic energy; gamma primaries in fixed mode travel along
  -z while existing optical/electron behavior remains unchanged.
- The paper gamma energy is centralized as 662 keV. The validation source is
  at `(0, 0, 14.7 mm)`, one millimetre above the outer top-reflector face, and
  is constrained to remain inside the world and aimed at the crystal.
- `G4EmStandardPhysics`, already used for the controlled A5 electrons, is the
  minimum electromagnetic constructor for A6. It provides gamma photoelectric
  and Compton interactions plus charged-secondary transport. No radioactive
  decay physics was added.
- The fixed seeds are 271828 and 314159. Of 100 events, 42 lay in the
  predefined `661.5 <= Edep <= 662.5 keV` full-energy gate, 30 had partial
  energy deposition and 28 had exactly zero GAGG energy deposition.
- The full-energy events deposited 27,804 keV and generated 1,501,410
  scintillation photons, giving 53999.784 photons/MeV and a relative error of
  4.00e-6 from the A5 yield. Across all depositing events the result was
  53999.839 photons/MeV, a relative error of 2.98e-6.
- Every zero-deposit event generated and transported zero scintillation
  photons. Every event satisfied exact optical terminal accounting with zero
  unclassified photons.
- The energy-deposition histogram and generated-light scatter plot were
  generated and visually inspected. The latter follows the 54000 photons/MeV
  reference line across zero, partial and full-energy events.
- The Qt/OpenGL A6 scene opened successfully. Its fixed first event deposited
  all 662 keV and generated 35,748 photons. A gamma-only trajectory filter
  displayed the normally incident magenta gamma without drawing the optical
  tracks; the optical photons were still transported and their accounting
  closed.
- The complete A0-A6 regression suite passed 20/20 CTest tests in 46.04 s.

Status: validation gate A6 passed. The sharp full-energy entries validate
energy conservation and scintillation yield; they are not an experimental
peak-width prediction because resolution scale, radioactive decay,
electronics and PMT response are not modeled. The four-finish Fig. 4
production comparison remains A7 work.
