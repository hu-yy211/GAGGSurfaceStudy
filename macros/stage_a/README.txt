A4 is the first Stage A comparison macro:

  a4_compare.mac

It runs polishedvm2000air, polishedtioair, groundvm2000air and groundtioair
in one executable process, with geometry reinitialization between finishes.
It then switches back to polishedvm2000air for fixed-seed reproducibility.

This macro still uses the A3 fixed-count isotropic optical source. It validates
LUT loading and switching only; it is not the A7 Fig. 4 production macro.

A5 scintillation-validation macros live in macros/validation because they are
controlled physics checks rather than paper-production runs. A6 adds the
fixed-seed 662 keV gamma and visualization macros there for the same reason:

  ../validation/a6_gamma.mac
  ../validation/a6_vis.mac

A6 validates full-energy events, scintillation yield and zero-deposit events
with polishedvm2000air only. A7 will add the final four-finish production
macro with identical statistics and full-energy selection.
