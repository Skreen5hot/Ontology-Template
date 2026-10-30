# Stage standards

One standard for each stage this project runs (`config/stages.yaml`), written before the
stage starts and approved by the person who holds its gate (`docs/process/METHOD.md`, §3).
Copy [`stage-standard.md`](stage-standard.md) to `<stage id>.md` and answer every section;
then name the file as the stage's `standard` in `config/stages.yaml`.

`python tools/stages.py` refuses a stage that has started without a standard, or that names
a file that does not exist. It does not read the standard. Whether the standard is right,
and whether a gate's conditions were met, is for the person who holds the gate.

A standard is changed like an approved model: by a new, reviewed version, recorded as a
decision. A stage that has started under one version is finished under it, or the change
says what happens to the work already done.
