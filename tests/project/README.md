# The project's own tests

What this project's decisions require of its ontology, beyond what the template checks:
a property that must stay an annotation property, a mapping that must be derivable, a
source every module must cite. Put each such test here, beside the decision it holds.

- **Collected by the suite.** `python -m pytest tests/ -q -p no:randomly` runs these with
  the rest, and the fixtures in `tests/conftest.py` (`repo`, `project`, `layout`, ...)
  are available.
- **Not template-owned.** `tests/` is the template's, so a file added there is reported by
  `tools/template_status.py` as divergence. A file here is the project's, and is not.
- **Give each file a name no file in `tests/` has.** The suite has no `__init__.py`, so
  pytest imports each test file by its basename, and two files with one basename are an
  import error. `tests/test_template.py` refuses a clash with a message naming both.
