# Releasing the template

A template release is a tag on `main` that projects are made from and measured against.
Template-only: init removes `docs/template/`, and a project releases its ontology with
`tools/release.py` instead (`docs/DEVELOPMENT.md`, "Releasing").

## Checklist

Each item is done, or recorded as not done with its reason, before the tag.

1. **Every open Dependabot update is taken or ignored on the record (T19).** A new project
   copies `.github/dependabot.yml` and the pins as they are, so an update left open here
   becomes a pull request in every project made from this release, on its first day.
   - Taken: merged, with the manifest re-recorded (the Dependabot manifest workflow does it
     on the pull request).
   - Held: an `ignore` entry in `.github/dependabot.yml` for that dependency and version,
     with a comment giving the reason and the date it is looked at again. The hold then
     travels with the release, and projects inherit the decision instead of the pull
     request.

   ```bash
   gh pr list --author app/dependabot --state open
   ```

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
