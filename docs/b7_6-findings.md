# B7.6 photon-fate audit findings

## Scope

B7.6 changes no optical transport parameter. It uses the B7.5 geometry,
effective annihilation-pair source, 510.5--511.5 keV event-total GAGG gate and
shared `sigma_alpha=0.70 rad`. Five states were run with 100000 events each:
all polished, bottom rough, top rough, top plus bottom rough, and side rough.
The same 187 full-energy histories and 5,160,063 generated scintillation
photons were selected in every state.

The stable event CSV schema retains the terminal-location counters. A separate
optional audit CSV records event-aggregate optical path length and, for photons
entering the PMT window, path length, crystal-face interaction counts and PMT
incidence-angle sum. It avoids an impractical multi-million-row per-photon
file. The audit is inactive unless `/gagg/output/photonAuditCsv` is set.

## Terminal budget

Fractions below are relative to generated light in the selected full-energy
events. `Other` contains the remaining exact terminal channels.

| State | PMT | GAGG absorption | Black structure | Top/ESR surface | Other |
|---|---:|---:|---:|---:|---:|
| all polished | 0.09554 | 0.56295 | 0.29433 | 0.00171 | 0.04547 |
| bottom rough | 0.19907 | 0.14699 | 0.51147 | 0.00543 | 0.13704 |
| top rough | 0.29259 | 0.13274 | 0.44687 | 0.00378 | 0.12403 |
| top + bottom rough | 0.19131 | 0.11670 | 0.57167 | 0.00394 | 0.11638 |
| side rough | 0.08696 | 0.03812 | 0.80783 | 0.00272 | 0.06437 |

All terminal and state-minus-reference budgets close. Bottom- and side-surface
absorption are exactly zero: the current rough GAGG-air dielectric boundaries
redirect photons but do not represent a lossy damaged surface layer.

## Transport burden

| State | Total path/generated (mm) | Path/PMT photon (mm) | Face hits/PMT photon | Mean PMT angle (deg) |
|---|---:|---:|---:|---:|
| all polished | 366.29 | 26.04 | 3.28 | 24.30 |
| bottom rough | 102.08 | 113.54 | 22.83 | 27.33 |
| top rough | 91.41 | 106.81 | 20.86 | 24.90 |
| top + bottom rough | 82.50 | 94.18 | 18.19 | 25.34 |
| side rough | 31.29 | 35.30 | 5.69 | 21.50 |

Roughness releases many photons from long-lived polished trapping, sharply
reducing the average path over all generated photons and therefore GAGG
self-absorption. The subset that reaches the PMT in the end-rough states is
different: it typically undergoes many side encounters and has a longer path
than the prompt PMT subset in the all-polished state.

## Mechanism conclusions

- Compared with all polished, top rough gains 0.19705 of generated light at
  the PMT. GAGG absorption falls by 0.43021, while black-structure absorption
  rises by 0.15254. The current model converts part of trapped/self-absorbed
  light into collected light very efficiently.
- Top rough exceeds bottom rough mainly because its black-structure loss is
  lower by 0.06460 of generated light. The difference in GAGG absorption is
  only 0.01425. Geometry-dependent black interception, rather than intrinsic
  roughness strength, drives the simulated top/bottom asymmetry.
- Adding top roughness to bottom rough reduces GAGG absorption by another
  0.03029 but raises black absorption by 0.06020. This explains why the
  top-plus-bottom state is 3.90% dimmer than bottom rough.
- Side rough sends 0.80783 of generated photons to the black structure. Its
  PMT fraction is nevertheless 0.08696, only 8.99% below the all-polished
  value and far above the experimental normalized trend of about 0.39.
- PMT mean incidence angles span only 21.50--27.33 degrees. An angle-dependent
  photocathode response may matter, but this modest shift alone is unlikely to
  account for the large response discrepancies.

The audit supports a model-structure conclusion: `sigma_alpha` only changes
direction in the current GAGG-air implementation. A physically constrained,
shared loss mechanism for processed surfaces or non-ideal air-gap/contact
geometry should be tested before any further sigma fitting. Per-face sigma
fitting is not justified.
