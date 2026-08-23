# Stage B implementation plan

## Conventions and parameter classes

- Crystal: measured 5.75 mm x 5.75 mm x 20 mm3 GAGG.
- +z: top face covered by ESR.
- -z: bottom face coupled toward the PMT receiver.
- `N_PMT`: photons transmitted into the PMT receiver volume.
- Measured/setup, literature, assumed placeholder and free parameters remain
  explicitly separated.
- All rough faces produced by the same process share one `sigma_alpha`.

## B0 - Experiment geometry and optical baseline - PASSED

Build the measured crystal, side air volume, black surrounding structure, top
ESR and bottom PMT window. Keep every GAGG face polished and do not fit
roughness.

Pass: analytic dimensions/volumes, navigator probes, no overlaps, UNIFIED
ESR/black boundaries, PMT refractive index, isotropic optical transport,
nonzero `N_PMT` and exact event-level photon accounting.

Status: passed on 2026-08-23. The 5000-photon baseline gave
`N_PMT/N_generated = 0.369`; 23/23 full regression tests passed. The 0.1 mm
side gap, 1.0 mm black thickness, 0.1 mm ESR thickness and 0.5 mm PMT-window
thickness are explicitly labeled unmeasured B0 placeholders.

## B1 - Six runtime surface states - PASSED

Create six macro-selectable states without recompilation:

1. all polished
2. bottom rough, others polished
3. top rough, others polished
4. side rough, top/bottom polished
5. bottom polished, others rough
6. top polished, others rough

Use UNIFIED GAGG interfaces: the idealized top ESR is dielectric-metal, while
the bottom PMT-window and side-air interfaces are dielectric-dielectric. One
shared runtime `sigma_alpha` controls every rough face. Validate face
assignment with independent top, bottom and side boundary counters before
comparing yields.

Status: passed on 2026-08-23. The six states are selected with
`/gagg/stageB/surfaceState`; `/gagg/stageB/sigmaAlpha` changes the single value
used by every rough face and triggers geometry reinitialization. Structural
validation checks each face's expected finish, model, type and shared value.
The deterministic center-source run used 5000 optical photons per state and a
predeclared validation-only `sigma_alpha = 0.20 rad`. Normalized collection was
1.000, 1.446, 1.413, 0.298, 0.310 and 0.309 in the order listed above. The
all-polished repeat was exact and full regression passed 26/26 tests. These
values validate switching and diagnostics only; no 511 keV source or
experimental-order acceptance test is active in B1.

## B2 - Optical-only roughness scan

Use fixed-count isotropic optical sources at several crystal positions. Scan
a predeclared, physically plausible `sigma_alpha` grid without using the
experimental ranking as a fit target. Require photon accounting, seed
reproducibility and smooth parameter response.

## B3 - 511 keV gamma response

Replace the optical source with a controlled 511 keV gamma beam and validate
zero-, partial- and full-energy event classes. Retain per-event Edep,
N_generated, N_PMT and loss locations.

## B4 - Experimental relative-light comparison

For one documented geometry/parameter set, report
`N_PMT/N_generated` and normalize all six states to all polished. Compare
with experiment while distinguishing predictions, measured inputs and free
parameters. Do not tune faces independently.
