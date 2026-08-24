# Git milestone workflow

The repository is pushed only after a validation gate passes. A milestone
commit must include:

- source and macro changes;
- the updated README when model assumptions changed;
- an entry in "docs/validation-log.md";
- tests passing locally;
- no generated build, log, CSV, ROOT, or bulk result files.

Recommended commit and annotated-tag names:

| Gate | Commit message | Tag |
|---|---|---|
| A0 | milestone(A0): validate optical smoke test | a0 |
| A1 | milestone(A1): validate optical material parameters | a1 |
| A2 | milestone(A2): validate paper geometry | a2 |
| A3 | milestone(A3): validate optical photon accounting | a3 |
| A4 | milestone(A4): validate LUT surface switching | a4 |
| A5 | milestone(A5): validate scintillation production | a5 |
| A6 | milestone(A6): validate 662 keV gamma response | a6 |
| A7 | milestone(A7): reproduce Fig. 4 qualitative ordering | a7 |
| B0 | milestone(B0): validate experiment geometry baseline | b0 |
| B1 | milestone(B1): validate six surface states | b1 |
| B2 | milestone(B2): validate optical roughness scan | b2 |
| B3 | milestone(B3): validate 511 keV gamma response | b3 |
| B4 | milestone(B4): compare six-state relative light | b4 |
| B5 | milestone(B5): validate robustness and interpretation | b5 |
| B6 | milestone(B6): localize optical loss mechanisms | b6 |

If A7 remains scientifically unresolved while an independently validated B0
is authorized to proceed, retain the A7 failure evidence in the B0 checkpoint
but do not create or move the `a7` tag. The `b0` tag certifies only the B0
geometry/transport gates documented in `docs/stage-b-plan.md`.

Before each milestone commit:

~~~sh
cmake -S . -B build
cmake --build build --parallel
ctest --test-dir build --output-on-failure
git status --short
git diff --check
~~~

After validation:

~~~sh
git add .
git status --short
git commit -m "milestone(A1): validate optical material parameters"
git tag -a a1 -m "A1 validation passed"
git push origin main
git push origin a1
~~~

Replace A1/a1 with the gate that actually passed. Never move or reuse a
published milestone tag. Bug fixes after a published gate use a normal commit
or, if a corrected milestone must be identified, a new tag such as "a1.1".
