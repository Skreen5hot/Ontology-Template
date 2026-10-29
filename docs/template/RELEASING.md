# Releasing the template

A template release is a tag on `main` that projects are made from and measured against.
Template-only: init removes `docs/template/`, and a project releases its ontology with
`tools/release.py` instead (`docs/DEVELOPMENT.md`, "Releasing").

## Checklist

Each item is done, or recorded as not done with its reason, before the tag.

1. **Every pin is checked (T19, decision 16).** The template runs no Dependabot and updates
   nothing by itself, so a release ships its pins as they are, into every project made from
   it. Check each pin `docs/DEVELOPMENT.md` lists under "Pins": take the update, with the manifest
   re-recorded, or keep the pin and say why in the release's ROADMAP entry.

2. **The suite passes**, and the Checks, Reasoning and Scale workflows are green on the
   commit to be tagged.
3. **A full init, rebuild included, runs in a fresh copy** (`tests/test_init_project.py`
   runs it with `--offline`; the rebuild needs the network), and its suite passes.
4. **The manifest is recorded with the release's label**, in its own commit:

   ```bash
   python tools/template_status.py --record --label vX.Y.Z
   ```

   `template_commit` is then the commit before it, and the tag goes on the commit that
   carries the manifest.
5. **The ROADMAP says what the release contains** and what is still open.
6. **Tag and push**, with the architect's say-so:

   ```bash
   git tag -a vX.Y.Z -m "Ontology Template vX.Y.Z"
   git push origin vX.Y.Z
   ```
