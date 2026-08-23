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

