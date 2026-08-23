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

## 2026-08-23 - A7 entered; Fig. 4 ordering gate failed

- Fig. 4 and its surrounding text were re-read from the reference PDF. The
  required peak-position order remains `groundtioair > polishedtioair >
  polishedvm2000air > groundvm2000air`; the figure also shows a much lower
  absolute output scale than the initial A7 prescan.
- The initial axial pencil-beam prescan did not reproduce the order. The
  paper's phrase "parallel gamma beam incident on the crystal end face" was
  then implemented as a macro-controlled uniform disk with radius 12.7 mm.
  Every sampled `(x,y)` lies inside the crystal face and is stored in CSV.
- Resetting only the run seed was insufficient for a paired comparison because
  optical surface transport consumed the shared random stream and changed
  later gamma events. A7 now optionally reseeds by event ID and defers
  scintillation tracks until non-optical transport completes. With these
  controls, all four finishes have exactly matching source positions, Edep,
  generated counts and full-energy event IDs.
- The Geant4 11.2 boundary implementation was audited against the official
  source. The legacy LBNL LUT supplies the reflected angular distribution;
  `G4OpBoundaryProcess` uses the surface `REFLECTIVITY`, whose default is one.
  The paper states ESR reflectivity above 98% and TiO2 reflectivity above 95%,
  so 0.98 and 0.95 are now explicit centralized literature lower-bound
  proxies. The complementary fraction is transmitted to the reflector volume,
  where the existing 0.1 mm absorption length classifies the terminal loss.
- A 25-event paired prescan with the explicit reflectivities still failed the
  order. A ten-times-shorter GAGG absorption-length diagnostic, representing a
  possible cm/mm reciprocal error, failed both with explicit reflectivities
  and with LUT-default unit reflectivity. The validated 64.516 cm length was
  retained.
- The formal comparison used 100 primaries per finish and selected the same 33
  events in the 661.5-662.5 keV full-energy gate. Every selected and rejected
  event closed exact optical accounting with zero unclassified photons.
- Event-level means (95% CI) were 0.80963 (0.80168-0.81758), 0.71835
  (0.70296-0.73374), 0.82768 (0.82107-0.83430) and 0.72919
  (0.71544-0.74295) for polished VM2000, polished TiO, ground VM2000 and ground
  TiO respectively. Mean output counts were 28942.7, 25679.6, 29588.0 and
  26067.2.
- The paired difference `groundtioair - polishedtioair` was positive, 0.01084
  with 95% CI 0.00601-0.01567. The required `polishedtioair -
  polishedvm2000air` and `polishedvm2000air - groundvm2000air` differences
  were negative with confidence intervals fully below zero. More statistics
  cannot plausibly reverse those two comparisons.
- The confidence-interval plot, full-energy output distributions and summary
  CSV were generated and visually inspected. `validate_a7.py` intentionally
  exits with status 1 after all structural checks because the ordering gate
  fails.
- The existing A0-A6 regression suite still passed 20/20 tests in 42.66 s.

Status: A7 is not passed. No arbitrary adjustment was made, no A7 CTest was
registered as passing, and no `a7` tag or remote push is allowed at this
point. The next investigation must identify a documented geometry/scoring/LUT
implementation difference or obtain the authors' Geant4 configuration.

## 2026-08-23 - A7 bounded scoring/interface audit

- Added independent runtime controls for `firstArrival` and true
  `transmitted` output scoring. The latter accepts only
  `FresnelRefraction`, `Transmission` or `SameMaterial` boundary
  statuses; volume-name inspection alone was shown to count reflected
  boundary arrivals.
- Added direct and explicit-air Stage A interface modes. The explicit
  0.1 mm air separation is a centralized diagnostic placeholder, not a paper
  measurement or fitted parameter.
- Four paired 50-primary runs used identical event seeding and selected 17
  full-energy events for the direct models and 16 for the air models. Every
  model passed analytic geometry, overlap, LUT assignment, paired
  source/Edep/generated and exact terminal-accounting checks.
- The two first-arrival models retained
  `ground VM > polished VM > ground TiO > polished TiO`.
- The two transmitted models gave
  `ground VM > ground TiO > polished TiO > polished VM`.
  For direct transmission the full-energy efficiencies were 0.18362,
  0.27827, 0.41116 and 0.28999 for polished VM, polished TiO, ground VM and
  ground TiO, with mean output counts 6564, 9948, 14698 and 10367.
- Explicit air changed each corresponding efficiency by only a few
  (10^{-3}). It did not resolve the stable ground-VM reversal and was not
  scanned further.

Status: structural audit passed; Fig. 4 ordering failed in all four models.
A7 remains untagged. The audit improved the interpretation and absolute scale
without introducing an arbitrary fit.

## 2026-08-23 - B0 experiment geometry and optical baseline

- Added runtime `experiment` geometry mode with the measured
  5.75 mm x 5.75 mm x 20 mm3 GAGG crystal. The convention is top ESR at +z
  and PMT window at -z.
- Added an explicit side-air subtraction volume, surrounding black
  subtraction volume, top ESR and bottom PMT receiver window. Runtime
  defaults are 0.1 mm side gap, 1.0 mm black thickness, 0.1 mm ESR thickness
  and 0.5 mm PMT-window thickness. These are labeled unmeasured B0
  placeholders and are not fits.
- ESR reflectivity 0.98 and ideal-black reflectivity zero use UNIFIED polished
  dielectric-metal boundaries. No rough GAGG surface or `sigma_alpha` is
  active in B0.
- Geometry validation passed analytic volumes, five navigator probes, five
  overlap checks, the two UNIFIED boundary assignments and PMT-window
  refractive index 1.52. Boolean-solid volume estimates use a documented 0.2%
  numerical tolerance; ordinary box volumes retain strict checks.
- The optical baseline transported 100 isotropic center-origin photons in
  each of 50 events. Of 5000 photons, 1845 transmitted into the PMT window,
  1492 were absorbed in GAGG, 1662 at ESR/black surfaces and one exited
  elsewhere. Thus `N_PMT/N_generated = 0.369`; accounting closed exactly
  with zero unclassified photons.
- The 5000-direction sample passed isotropy checks. The complete A0-A6+B0
  regression suite passed 23/23 tests in 44.05 s.

Status: B0 validation gate passed. B1 will add the six runtime-selectable
GAGG face states and one shared rough-surface `sigma_alpha`; it must not tune
individual faces.

## 2026-08-23 - B1 six runtime surface states

- Added the six experimental surface states as runtime messenger choices. A
  state change rebuilds the experiment geometry; no recompilation is needed.
- Added one shared `/gagg/stageB/sigmaAlpha` parameter. Top, bottom and side
  rough faces all read this same value; there are no independent per-face
  tuning controls. Runtime switching from 0.20 to 0.25 rad and back passed the
  structural surface validator.
- Added explicit UNIFIED GAGG-to-ESR, GAGG-to-PMT-window and GAGG-to-side-air
  borders. Structural validation checks each state's expected polished/ground
  assignments, dielectric type, model, shared roughness and all four border
  surfaces including the air-to-black absorber.
- Extended each event row with surface-state and shared-roughness metadata plus
  independent top, bottom and side boundary-interaction counters. Terminal
  photon accounting remains independent of these diagnostic counters.
- Used 50 events of 100 isotropic center-origin 550 nm photons per state. The
  event seed base was held fixed, so primary directions were identical for all
  states. The exact repeated all-polished run also reproduced every event.
- At the predeclared validation-only `sigma_alpha = 0.20 rad`, total
  `N_PMT/N_generated` was 0.3816, 0.5518, 0.5392, 0.1138, 0.1182 and 0.1180
  for all polished, bottom rough, top rough, side rough, bottom polished with
  others rough, and top polished with others rough. Normalized values were
  1.000, 1.446, 1.413, 0.298, 0.310 and 0.309.
- B0/B1 targeted regression passed 6/6 tests. The complete A0-B1 regression
  passed 26/26 tests in 51.98 s.

Status: B1 validation gate passed. This result validates state mapping,
shared roughness, counting and reproducibility. The 0.20 rad value was not
fitted, the source was optical-only, and no experimental-order gate or 511 keV
gamma response is claimed. B2 will scan a predeclared roughness grid and
multiple source positions before B3 introduces 511 keV gamma interactions.

## 2026-08-24 - B2 optical-only roughness/position scan

- Locked the scan before inspecting B2 results in `config/b2_scan.json`:
  shared `sigma_alpha = 0, 0.05, 0.10, 0.20, 0.30 rad`; axial source
  positions -8, 0 and +8 mm; all six states; 50 events of 100 isotropic
  550 nm photons per point. The grid contains 90 analysis points and does not
  use the experimental order as a fit target.
- The first validation attempt used a 0.01 minimum response span at every
  state/position combination. It failed for bottom rough at +8 mm. Review of
  all points showed that requiring a distant surface to produce a resolved
  response at every source position is not a valid universal condition. The
  numerical threshold was retained but correctly applied per state: at least
  one of the three predeclared positions must resolve the roughness response.
  The grid and adjacent-jump limit were not changed.
- That review also found top rough to be exactly invariant with sigma. The
  direct dielectric-metal ESR surface had no UNIFIED reflection-component
  constants, so ground reflection fell through to a sigma-independent
  Lambertian branch. Fixed `SPECULARLOBECONSTANT=1`, spike=0 and backscatter=0.
  This makes the shared sigma_alpha the only angular-width parameter for a
  rough top ESR reflection; the constants are fixed model choices, not fits.
- A same-process repeat then differed only in event 0 while events 1-49 and
  aggregate primary-direction diagnostics were identical. Gaussian-cache,
  seed-list and navigator-reset hypotheses did not remove the effect. Two
  consecutive comparison runs were internally repeatable, indicating a
  bounded run-history dependence when UNIFIED ground surfaces were repeatedly
  rebuilt. The scan therefore runs every point, including the repeat, in an
  independent Geant4 process. This is stricter than ignoring an event and
  removes ordering/history from the analysis sample.
- Startup now records the active `MixMaxRng` engine. Deterministic event
  seeding supplies an explicit two-seed count and a zero-terminated seed list;
  this hardens the engine contract but was not claimed as the cause of the
  same-process history effect.
- The isolated 91-process scan passed exact repeatability. All-polished was
  event-for-event invariant across all five sigma values at each position.
  Every point had exact terminal accounting, nonzero PMT collection and active
  top/bottom/side counters.
- Across all rough-state position curves, the largest adjacent absolute
  efficiency jump was 0.0608, below the predeclared 0.20 discontinuity guard.
  At sigma=0.20 rad the normalized results for -8/0/+8 mm were bottom rough
  1.227/1.223/1.205, top rough 1.187/1.192/1.205, side rough
  0.913/0.596/0.809, bottom polished with others rough 0.912/0.515/0.686,
  and top polished with others rough 0.890/0.528/0.778.
- B0/B1 targeted regression passed 6/6 tests. Full A0-B2 regression passed
  29/29 tests in 64.33 s; the isolated B2 subset passed 3/3.

Status: B2 validation gate passed. No `sigma_alpha` value was selected, no
experimental ranking gate was applied and no 511 keV interaction was used.
B3 may now add a controlled 511 keV gamma response while retaining this
surface/position scan as the optical-transport baseline.

## 2026-08-24 - B3 controlled 511 keV gamma response

- Locked the controlled run in `config/b3_gamma.json`: 100 normally incident
  511 keV pencil-beam events from z=+14.7 mm, all-polished Stage B geometry,
  deterministic event seed base 830001 and a 510.5--511.5 keV full-energy
  gate. The stored `sigma_alpha=0.20 rad` is inactive for all-polished faces.
- Enabled deferred scintillation-track processing. Gamma/electron transport
  therefore completes before optical transport, establishing the event-paired
  random-stream contract needed by B4 without changing the physical event
  record.
- The sample contained 30 zero-deposit, 42 partial-energy and 28 full-energy
  events. Every zero-deposit event generated zero light; all events closed
  terminal accounting with no unclassified photons.
- The all-depositing and full-energy light yields were 53999.924 and
  53999.860 photons/MeV, relative errors 1.40e-6 and 2.59e-6 from the
  literature value. The full-energy collection efficiency was 0.37140028.
- The energy-deposition histogram and scintillation-yield plot were visually
  inspected. The B3 subset passed 3/3 tests and full A0--B3 regression passed
  32/32 tests.

Status: B3 validation gate passed. B4 may reuse the exact gamma/event seeds in
isolated processes for all six surface states and must require identical
event-level source position, Edep, N_generated and full-energy IDs before
comparing relative light output.

## 2026-08-24 - B4 six-state 511 keV comparison

- Locked the comparison in `config/b4_comparison.json`. The six B1 states use
  the B3 100-event 511 keV pencil beam, event seed base 830001, 510.5--511.5
  keV full-energy gate and one shared `sigma_alpha=0.20 rad`. The preliminary
  measured ratios are stored as comparison data and never passed to Geant4.
- Ran each state in an independent process to retain the B2 process-isolation
  rule. All six states had exactly matching source position, Edep,
  N_generated and full-energy event IDs. The all-polished result was an exact
  event-level repeat of B3; all optical accounting closed.
- The 28 paired full-energy events produced normalized predictions
  1.0000, 1.2003, 1.1970, 0.6846, 0.6321 and 0.6538. Paired 95% bootstrap
  intervals were respectively 1.0000, 1.1963--1.2043, 1.1909--1.2046,
  0.6508--0.7197, 0.5965--0.6711 and 0.6212--0.6880.
- Compared with preliminary measured values 1.00, 1.60, 1.54, 0.39, 0.39 and
  0.32, the model reproduces the broad enhanced/suppressed groups but the
  response magnitude is too weak. It also predicts bottom-polished/others-
  rough below top-polished/others-rough, the reverse of the measured order.
- The B4 subset passed 3/3 tests. Experimental agreement was explicitly not a
  pass condition, and no face-specific parameter or roughness fit was added.

Status: B4 comparison gate passed; this is not a claim of quantitative
agreement. B5 must test whether the conclusions survive statistical/event-
selection and shared-roughness sensitivity, then separate established model
limitations from hypotheses needing measured setup parameters.

## 2026-08-24 - B5 shared-roughness robustness and interpretation

- Locked `sigma_alpha=0.10, 0.20, 0.30 rad`, all six states and full-energy
  half-widths 0.25, 0.5 and 1.0 keV in `config/b5_robustness.json`. The B4
  0.20-rad point is reused; twelve isolated 100-event processes provide the
  two new roughness values. No best-fit sigma or per-face sigma is calculated.
- The first validation attempt required every rough state to span at least
  0.01 over the grid. It failed because bottom rough spans only 0.00299. That
  requirement incorrectly treated a scientifically meaningful weak response
  as a corrupt scan. The numerical threshold was retained as a reporting
  threshold, and the structural gate now requires at least one rough state to
  respond above it. Four of five do. This criterion correction does not use
  experimental agreement and does not change the grid or simulation output.
- All sigma/state points have exact event-level gamma-history pairing and
  terminal accounting. All-polished transport is event-for-event invariant
  to the unused roughness parameter. The three full-energy windows select the
  same 28 events in this ideal, resolution-free detector model.
- Simulation envelopes over the grid are bottom rough 1.200--1.203, top rough
  1.170--1.207, side rough 0.630--0.745, bottom polished/others rough
  0.567--0.724 and top polished/others rough 0.581--0.731. All five
  corresponding preliminary measurements lie outside these envelopes.
- The first sequential run passed all 12 Geant4 jobs but took 693.9 s. The
  runner now keeps each job in a separate process while allowing four jobs in
  parallel. The repeated B5 subset passed 3/3 in 135.62 s with identical
  validated event records.
- The final A0--B5 regression passed 38/38 tests in 802.90 s. B2 and B4 were
  slower than their earlier targeted runs under the current machine load, but
  all deterministic records and scientific summaries were unchanged.
- `docs/b5-findings.md` separates established conclusions from unverified
  explanations involving optical coupling, PMT response, ESR placement and
  properties, black structure, surface metrology and source/setup realism.

Status: B5 robustness gate passed. Within the tested shared-roughness range,
neither statistical uncertainty, ideal full-energy selection nor sigma choice
is sufficient to explain the experimental magnitudes. Further model changes
should wait for measured setup/interface inputs rather than introduce
face-specific fit parameters.
