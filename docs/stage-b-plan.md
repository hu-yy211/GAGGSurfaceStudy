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

## B2 - Optical-only roughness scan - PASSED

Use fixed-count isotropic optical sources at several crystal positions. Scan
a predeclared, physically plausible `sigma_alpha` grid without using the
experimental ranking as a fit target. Require photon accounting, seed
reproducibility and smooth parameter response.

Status: passed on 2026-08-24. The locked grid contains five shared roughness
values from 0 to 0.30 rad, three axial positions at -8, 0 and +8 mm, all six
states and 5000 photons per point. Each of the 90 points runs in an isolated
Geant4 process, and a 91st process repeats one point exactly. This isolation
was introduced after an audit showed a one-event history dependence when
ground surfaces were repeatedly rebuilt within one process. All-polished was
exactly invariant across sigma, the repeat matched every event, accounting
closed for every point and the largest adjacent absolute efficiency jump was
0.0608 against the predeclared 0.20 guard. The top ESR uses a fixed UNIFIED
specular-lobe fraction of one so its shared sigma_alpha is active; this model
choice and the scan grid were not fitted. Full regression passed 29/29 tests.

## B3 - 511 keV gamma response - PASSED

Replace the optical source with a controlled 511 keV gamma beam and validate
zero-, partial- and full-energy event classes. Retain per-event Edep,
N_generated, N_PMT and loss locations.

Status: passed on 2026-08-24. The locked all-polished pencil-beam run used
100 gammas at 511 keV, a source at z=+14.7 mm and deterministic event seeds.
Scintillation photons were deferred until non-optical transport completed so
later surface comparisons can preserve paired gamma histories. The sample
contained 30 zero-deposit, 42 partial-energy and 28 full-energy events. The
full-energy gate was 510.5--511.5 keV, the measured light yield was
53999.86 photons/MeV and all optical accounting closed. Full regression
passed 32/32 tests.

## B4 - Experimental relative-light comparison - PASSED AS COMPARISON GATE

For one documented geometry/parameter set, report
`N_PMT/N_generated` and normalize all six states to all polished. Compare
with experiment while distinguishing predictions, measured inputs and free
parameters. Do not tune faces independently.

Status: passed on 2026-08-24 as a comparison/reporting gate, not an agreement
claim. Six isolated 100-event runs reused the exact B3 gamma histories and one
shared `sigma_alpha=0.20 rad`. The normalized predictions were 1.000, 1.200,
1.197, 0.685, 0.632 and 0.654, versus preliminary measured values 1.000,
1.600, 1.540, 0.390, 0.390 and 0.320. The broad enhancement/suppression
groups are reproduced, but the magnitude is too weak and the final two states
are reversed. Experimental agreement was explicitly not a validation pass
condition; no parameter was tuned.

## B5 - Robustness and interpretation gate - PASSED

Quantify statistical uncertainty and sensitivity to the full-energy event
selection and the single shared roughness parameter. Compare prediction and
measurement without promoting placeholder dimensions or per-face parameters
to fitted values. Record which discrepancies are established by the model and
which explanations remain hypotheses requiring measured optical/setup inputs.

Status: passed on 2026-08-24. The 511 keV comparison was evaluated at shared
`sigma_alpha=0.10, 0.20, 0.30 rad`; the middle point reuses B4 and 12 new
isolated runs cover the other values. All histories paired exactly and the
0.25/0.5/1.0 keV full-energy half-widths selected the same 28 events. Four of
five rough states exceeded the 0.01 response-reporting threshold; bottom rough
was nearly insensitive (span 0.003). All five non-reference measurements lay
outside their shared-sigma prediction envelopes. This rules out statistical
uncertainty, the tested peak window and a shared sigma choice in the scanned
range as sufficient explanations, but does not identify which unmeasured
setup parameter is responsible. See `docs/b5-findings.md`.

## B6 - Location-resolved loss budget - PASSED

Extend the event schema with top, bottom, side, black-structure and other
surface-absorption subtotals while preserving the original terminal category.
For the event-paired B4/B5 full-energy samples, require exact surface-subtotal,
terminal-budget and state-minus-reference closure. Report the loss channel
that dominates each surface-state response without adding optical parameters.

Status: passed on 2026-08-24. At sigma=0.20 rad, end-face roughness reduces
GAGG self-absorption by 0.154--0.162 of generated light and increases black
loss by 0.104--0.110, leaving a net PMT gain near 0.074. Side/multiple
roughness increases black-structure absorption by 0.413--0.433, producing a
net PMT loss of 0.117--0.137. All 18 sigma/state budgets and every differential
budget close exactly. Final A0--B6 regression passed 40/40 tests. See
`docs/b6-findings.md`.

## B7 - Effective source and revised response baseline - IN PROGRESS

B7.1 validated uniform sampling on a 2.5 x 2.5 mm2 face at z=+30 mm. B7.2
validated one same-vertex, exactly back-to-back pair of 511 keV gammas with a
uniform 4pi pair axis. This is an effective annihilation source, not a Na-22
decay or positron-transport model.

B7.3 uses the estimated six-air-face experimental geometry and validates the
event-level 511 keV response definition before any roughness fit. Only events
with `510.5 <= Edep_GAGG <= 511.5 keV` enter the PMT-light estimator. The
actual 100000-event all-polished sample selected 187 events and gave
`sum(N_PMT)/sum(N_generated)=0.0955401`, with mean `N_PMT=2636.33 +/- 9.93`
(standard error). Geometry, surface and photon-accounting checks passed.

Status: B7.3 passed on 2026-09-02. B7.4 may run the six states in isolated
processes over one shared `sigma_alpha` grid. No per-face roughness fitting is
allowed.
