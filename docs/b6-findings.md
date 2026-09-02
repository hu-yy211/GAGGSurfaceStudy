# B6 location-resolved loss findings

## Full-energy photon budget at shared sigma_alpha = 0.20 rad

The table reports fractions of generated scintillation photons in the 28
event-paired 511 keV full-energy events.

| State | PMT receiver | GAGG self-absorption | Top ESR absorption | Black-structure absorption |
|---|---:|---:|---:|---:|
| all polished | 0.1260 | 0.5646 | 0.0019 | 0.2954 |
| bottom rough | 0.2832 | 0.1885 | 0.0064 | 0.4905 |
| top rough | 0.3585 | 0.1613 | 0.0038 | 0.4439 |
| side rough | 0.1146 | 0.0342 | 0.0020 | 0.8370 |
| bottom polished, others rough | 0.1135 | 0.0345 | 0.0019 | 0.8373 |
| top polished, others rough | 0.1015 | 0.0344 | 0.0021 | 0.8499 |

Every row closes to one when the small remaining terminal channels are
included. The five surface-absorption location counters close exactly to the
pre-existing aggregate surface-absorption count.

## Mechanism supported by the counters

The all-polished geometry traps photons for many reflections: it records
67.10 side interactions per generated photon. Bottom-rough and top-rough
reduce that burden to 23.16 and 19.60; the side/multiple-rough states reduce it
to about 3.9. This path shortening strongly reduces GAGG self-absorption.

For bottom rough and top rough, self-absorption falls by 0.3761 and 0.4032
relative to all polished. Black-structure absorption simultaneously rises by
0.1951 and 0.1485, while PMT collection rises by 0.1571 and 0.2325. Thus the
simulated end-face enhancement is a redistribution of photons that would
otherwise be lost on long trapped paths. The top/bottom asymmetry introduced
by the air-separated ESR and PMT stack is now large enough to reverse the
measured end-face ordering.

For side rough and the two multiple-rough states, black-structure absorption
rises by 0.5416--0.5545 and is the dominant change. Reduced self-absorption
almost compensates this loss, leaving net PMT reductions of only
0.0115--0.0245. The model therefore supports a direct explanation for the
broad experimental trend: rough sides release total-internally-reflected light
into the side air region, where the surrounding black structure absorbs it.

## What this rules in and out

The black boundary already has zero reflectivity and acts as an ideal
absorber. Making it darker cannot produce the missing experimental
suppression. The remaining magnitude gap must instead change how many photons
reach that boundary, how many reach the PMT, or how transmitted photons are
converted to measured charge.

The highest-value next checks are:

1. Replace the 0.1 mm bottom-gap placeholder with a measured coupling stack
   and PMT angular/spectral detection response. The current score treats every
   photon transmitted into the PMT window equally, even though rough surfaces
   change incidence angles.
2. Measure or bound the top ESR air spacing and product response. This
   controls whether light released by an end roughness is redirected toward
   the PMT or toward the side absorber.
3. Replace the centered pencil beam with the measured 22Na capsule and support
   geometry after source coordinates are available.
4. Obtain surface profilometry before extending UNIFIED parameters. Same-
   process rough faces must continue to share the same parameter set.

These are hypotheses for the next controlled sensitivity stages, not fitted
explanations of the current data.
