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
with polishedvm2000air only. A7 has added:

  a7_compare.mac

It runs 100 paired gamma events per finish with a uniform face beam and
event-level random-stream isolation. The current ordering fails the predefined
Fig. 4 gate, so this is a diagnostic production macro rather than a validated
milestone. ../validation/a7_prescan.mac and
../validation/a7_absorption_diagnostic.mac retain the bounded checks that
ruled out pencil-beam sampling and a cm/mm absorption-length interpretation.

The output-face/interface audit is reproduced by:

  ../validation/a7_model_direct_transmitted.mac
  ../validation/a7_model_direct_first_arrival.mac
  ../validation/a7_model_airgap_transmitted.mac
  ../validation/a7_model_airgap_first_arrival.mac

The 0.1 mm explicit air separation is a diagnostic placeholder, not a paper
measurement. None of the four combinations passes the complete Fig. 4 order.
