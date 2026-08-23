A4 is the first Stage A comparison macro:

  a4_compare.mac

It runs polishedvm2000air, polishedtioair, groundvm2000air and groundtioair
in one executable process, with geometry reinitialization between finishes.
It then switches back to polishedvm2000air for fixed-seed reproducibility.

This macro still uses the A3 fixed-count isotropic optical source. It validates
LUT loading and switching only; it is not the A7 Fig. 4 production macro.
