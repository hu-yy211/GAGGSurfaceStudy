# B6 location-resolved loss findings

## Full-energy photon budget at shared sigma_alpha = 0.20 rad

The table reports fractions of generated scintillation photons in the 28
event-paired 511 keV full-energy events.

| State | PMT receiver | GAGG self-absorption | Top ESR absorption | Black-structure absorption |
|---|---:|---:|---:|---:|
| all polished | 0.3714 | 0.2959 | 0.0383 | 0.2932 |
| bottom rough | 0.4458 | 0.1343 | 0.0143 | 0.4032 |
| top rough | 0.4446 | 0.1418 | 0.0153 | 0.3971 |
| side rough | 0.2543 | 0.0305 | 0.0055 | 0.7061 |
| bottom polished, others rough | 0.2348 | 0.0296 | 0.0055 | 0.7261 |
| top polished, others rough | 0.2428 | 0.0309 | 0.0055 | 0.7169 |

Every row closes to one when the small remaining terminal channels are
included. The five surface-absorption location counters close exactly to the
pre-existing aggregate surface-absorption count.

## Mechanism supported by the counters

The all-polished geometry traps photons for many reflections: it records
40.17 side interactions per generated photon. Bottom-rough and top-rough
reduce that burden to 18.63 and 19.78; the side/multiple-rough states reduce it
to about 3.4. This path shortening strongly reduces GAGG self-absorption.

For bottom rough and top rough, self-absorption falls by 0.1616 and 0.1541
relative to all polished. Black-structure absorption simultaneously rises by
0.1101 and 0.1039, so only 0.0744 and 0.0732 emerge as additional PMT
collection. Thus the simulated end-face enhancement is a redistribution of
photons that would otherwise be lost on long trapped paths; much of the
recovered light is redirected to the black structure instead of the PMT.

For side rough and the two multiple-rough states, black-structure absorption
rises by 0.4129--0.4330 and is the dominant change. Reduced self-absorption
partly compensates this loss, leaving the net PMT reductions at
0.1171--0.1366. The model therefore supports a direct explanation for the
broad experimental trend: rough sides release total-internally-reflected light
into the side air region, where the surrounding black structure absorbs it.

## What this rules in and out

The black boundary already has zero reflectivity and acts as an ideal
absorber. Making it darker cannot produce the missing experimental
suppression. The remaining magnitude gap must instead change how many photons
reach that boundary, how many reach the PMT, or how transmitted photons are
converted to measured charge.

The highest-value next checks are:

1. Add a measured bottom coupling stack and PMT angular/spectral detection
   response. The current score treats every photon transmitted into the PMT
   window equally, even though rough surfaces change incidence angles.
2. Measure or bound the top ESR contact/air spacing and product response. This
   controls whether light released by an end roughness is redirected toward
   the PMT or toward the side absorber.
3. Replace the centered pencil beam with the measured 22Na capsule and support
   geometry after source coordinates are available.
4. Obtain surface profilometry before extending UNIFIED parameters. Same-
   process rough faces must continue to share the same parameter set.

These are hypotheses for the next controlled sensitivity stages, not fitted
explanations of the current data.
