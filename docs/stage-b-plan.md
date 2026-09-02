# Stage B implementation plan

## Conventions and parameter classes

- Crystal: measured 5.75 mm x 5.75 mm x 20 mm3 GAGG.
- +z: top face covered by ESR.
- -z: bottom face coupled toward the PMT receiver.
- `N_PMT`: photons transmitted from the bottom air gap into the PMT receiver
  volume.
- Measured/setup, literature, assumed placeholder and free parameters remain
  explicitly separated.
- All rough faces produced by the same process share one `sigma_alpha`.

## B0 - Experiment geometry and optical baseline - PASSED

Build the measured crystal, explicit air volumes on all six faces, black
surrounding structure, top ESR and bottom PMT window. Keep every GAGG face
polished and do not fit roughness.

Pass: analytic dimensions/volumes, navigator probes, no overlaps, UNIFIED
ESR/black boundaries, PMT refractive index, isotropic optical transport,
nonzero `N_PMT` and exact event-level photon accounting.

Status: revised and passed on 2026-08-26. The six-face-air 5000-photon
baseline gave `N_PMT/N_generated = 0.1236`. The side, top and bottom gaps are
all 0.1 mm placeholders; the 1.0 mm black thickness, 0.1 mm ESR thickness and
0.5 mm PMT-window thickness are also explicitly unmeasured placeholders.

## B1 - Six runtime surface states - PASSED

Create six macro-selectable states without recompilation:

1. all polished
2. bottom rough, others polished
3. top rough, others polished
4. side rough, top/bottom polished
5. bottom polished, others rough
6. top polished, others rough

Use UNIFIED GAGG-to-air dielectric-dielectric interfaces on the top, bottom
and sides. The outer top-air-to-ESR interface is dielectric-metal and the
bottom-air-to-PMT-window interface is dielectric-dielectric. One shared
runtime `sigma_alpha` controls every rough crystal face. Validate face
assignment with independent top, bottom and side boundary counters before
comparing yields.

Status: passed on 2026-08-23. The six states are selected with
`/gagg/stageB/surfaceState`; `/gagg/stageB/sigmaAlpha` changes the single value
used by every rough face and triggers geometry reinitialization. Structural
validation checks each face's expected finish, model, type and shared value.
The revised deterministic center-source run used 5000 optical photons per
state and a predeclared validation-only `sigma_alpha = 0.20 rad`. Normalized
collection was 1.000, 2.146, 2.795, 0.774, 0.791 and 0.688 in the order listed above. The
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
0.0362 against the predeclared 0.20 guard. Roughness is applied only at the
three GAGG-to-air surface classes; the ESR uses a separate polished UNIFIED
specular-lobe reflector boundary. Neither the model choice nor scan grid was
fitted.

## B3 - 511 keV gamma response - PASSED

Replace the optical source with a controlled 511 keV gamma beam and validate
zero-, partial- and full-energy event classes. Retain per-event Edep,
N_generated, N_PMT and loss locations.

Status: revised and passed on 2026-08-26. The locked all-polished pencil-beam run used
100 gammas at 511 keV, a source at z=+14.7 mm and deterministic event seeds.
Scintillation photons were deferred until non-optical transport completed so
later surface comparisons can preserve paired gamma histories. The sample
contained 28 zero-deposit, 40 partial-energy and 32 full-energy events. The
full-energy gate was 510.5--511.5 keV, the measured light yield was
53999.88 photons/MeV and all optical accounting closed.

## B4 - Experimental relative-light comparison - PASSED AS COMPARISON GATE

For one documented geometry/parameter set, report
`N_PMT/N_generated` and normalize all six states to all polished. Compare
with experiment while distinguishing predictions, measured inputs and free
parameters. Do not tune faces independently.

Status: revised and passed on 2026-08-26 as a comparison/reporting gate, not an agreement
claim. Six isolated 100-event runs reused the exact B3 gamma histories and one
shared `sigma_alpha=0.20 rad`. The normalized predictions are 1.000, 2.247,
2.844, 0.909, 0.901 and 0.805, versus preliminary measured values 1.000,
1.600, 1.540, 0.390, 0.390 and 0.320. The broad enhancement/suppression
groups are reproduced, but end-face enhancement is too strong, top and bottom
rough are reversed, and side suppression remains too weak. Experimental agreement was explicitly not a validation pass
condition; no parameter was tuned.

## B5 - Robustness and interpretation gate - PASSED

Quantify statistical uncertainty and sensitivity to the full-energy event
selection and the single shared roughness parameter. Compare prediction and
measurement without promoting placeholder dimensions or per-face parameters
to fitted values. Record which discrepancies are established by the model and
which explanations remain hypotheses requiring measured optical/setup inputs.

Status: revised and passed on 2026-08-26. The 511 keV comparison was evaluated at shared
`sigma_alpha=0.10, 0.20, 0.30 rad`; the middle point reuses B4 and 12 new
isolated runs cover the other values. All histories paired exactly and the
0.25/0.5/1.0 keV full-energy half-widths selected the same 32 events. All five
rough states exceeded the 0.01 response-reporting threshold. All five non-reference measurements lay
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

Status: revised and passed on 2026-08-26. At sigma=0.20 rad, end-face
roughness reduces GAGG self-absorption by 0.376--0.403 of generated light and
increases black loss by 0.149--0.195, leaving net PMT gains of 0.157 and
0.232. Side/multiple roughness increases black-structure absorption by
0.542--0.554, producing net PMT losses of 0.011--0.025. All 18 sigma/state budgets and every differential
budget close exactly. Final A0--B6 regression passed 40/40 tests. See
`docs/b6-findings.md`.
