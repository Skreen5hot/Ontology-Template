# SPDX-License-Identifier: MIT
"""Turn a fresh copy of the template into a project of its own.

    python tools/init_project.py --id widget --title "Widget Ontology" \\
        --description "What widgets are and what they are for." \\
        --repository owner/Widget-Ontology

    python tools/init_project.py ... --dry-run     # say what would change
    python tools/init_project.py ... --offline     # every generator but the
                                                   # vendoring rebuild
    python tools/init_project.py ... --no-regenerate
                                                   # skip the generators
                                                   # (they need the network
                                                   # or a warm cache)

Run once, in a clean checkout of a repository made with "Use this
template", before the first commit of the project's own.

WHAT IT DOES

  1. Writes config/project.yaml: the new id, code, title, description,
     namespace, prefix and repository, and `template: false`.
  2. Rewrites the namespace and the prefix inside the authored Turtle --
     the module, the shapes and the fixtures -- because the SPARQL in a
     shape cannot read the project file, and a filter on the template's
     namespace would select nothing and report success.
  3. Renames ontology/example.ttl to ontology/<id>.ttl, in the file
     system and in the layout contract.
  4. Renders README.md, CLAUDE.md and docs/HANDOFF.md from the skeletons
     in docs/template/skeletons, and sets the copyright line in LICENSE.
  5. Removes everything that describes only the template: the
     components declared `template: only`, their files, and their block
     in the layout contract.
  6. Regenerates every generated file, because each one names the
     project: the extracts' headers carry its IRI and title, and the
     digest and baseline describe its module.

Files declared `template: owned` are not touched. They are what
tools/template_status.py compares against the template, and editing
them here would make every project look diverged on day one.

WHY A SCRIPT RATHER THAN SEARCH AND REPLACE

The template's placeholder is the word `example`, which also occurs in
prose, in `example.org`, and in the names of fixtures. A replacement
across the tree would rewrite comments explaining why example.org is
reserved. This changes the strings it knows the location of, and then
checks that the old namespace survives nowhere a tool would read it.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import layout  # noqa: E402
import project  # noqa: E402

IRI_PATTERN = "https://fandaws.com/ontology/%s"
SKELETONS = "docs/template/skeletons"

#: Skeleton -> where it is rendered.
RENDERED = {
    "README.md": "README.md",
    "CLAUDE.md": "CLAUDE.md",
    "HANDOFF.md": "docs/HANDOFF.md",
    "CITATION.cff": "CITATION.cff",
}

#: Roles whose Turtle carries the namespace or the prefix.
TURTLE_ROLES = ("ontology-module", "ontology-module-set",
                "ontology-validation", "test-fixture", "example-data")

MARK_BEGIN = "  # >>> template-only"
MARK_END = "  # <<< template-only"

#: The one generator that needs the network (or a warm cache): the
#: extracts' headers name the project, so it runs at init, but --offline
#: leaves it for later and runs everything else.
NETWORK_GENERATORS = (("tools/ontology/vendor_upstream.py", "--rebuild"),)

GENERATORS = (
    ("tools/ontology/vocabulary.py",),
    ("tools/ontology/vendor_upstream.py", "--rebuild"),
    ("tools/ontology/profile_shapes.py",),
    ("tools/ontology/protege.py",),
    ("tools/ontology/corpus_digest.py", "-o", "config/corpus-digest.json"),
    ("tools/ontology/validate.py", "--record"),
)


class Refused(SystemExit):
    """Raised before anything is written."""


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=str(root),
                            capture_output=True)
    if result.returncode:
        raise Refused("git %s failed: %s" % (
            " ".join(args), result.stderr.decode("utf-8", "replace")[-300:]))
    return result.stdout.decode("utf-8")


def values_of(args, old: dict) -> dict:
    """The new project file's values, refused if they do not hold."""
    code = args.code or args.id.replace("-", "").upper()
    prefix = args.prefix or args.id.replace("-", "_")
    iri_base = args.iri_base or IRI_PATTERN % args.id
    new = dict(old)
    new.update({
        "template": False,
        "id": args.id,
        "code": code,
        "title": args.title,
        "description": args.description,
        "namespace": iri_base + "#",
        "prefix": prefix,
        "iri_base": iri_base,
        "repository": args.repository,
        "licence_holder": args.licence_holder or old["licence_holder"],
        "correspondents": [],
    })
    problems = project.problems_of(new)
    if prefix in ("rdf", "rdfs", "owl", "xsd", "skos", "dcterms", "sh",
                  "obo", "cco", "wf"):
        problems.append("prefix %r is already used for another vocabulary"
                        % prefix)
    if problems:
        raise Refused("the project values do not hold:\n  "
                      + "\n  ".join(problems))
    return new


# ------------------------------------------------------- rewriting


def yaml_scalar(value: str) -> str:
    """A one-line YAML scalar, quoted when it would not survive bare."""
    import json

    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 ._/:#-]*", value) and \
            not value.endswith(":") and ": " not in value and " #" not in value:
        return value
    return json.dumps(value, ensure_ascii=False)


def project_file(text: str, new: dict) -> str:
    """config/project.yaml with each value replaced where it is written.

    Line by line rather than re-dumped, so the comments explaining each
    field survive.
    """
    out = []
    lines = text.split("\n")
    i = 0
    seen = set()
    while i < len(lines):
        line = lines[i]
        match = re.match(r"^([a-z_]+):(.*)$", line)
        if not match or match.group(1) not in new:
            out.append(line)
            i += 1
            continue
        key = match.group(1)
        seen.add(key)
        if key == "description":
            out.append("description: >-")
            words, row = new[key].split(), "  "
            for word in words:
                if len(row) + len(word) + 1 > 74 and row.strip():
                    out.append(row.rstrip())
                    row = "  "
                row += word + " "
            out.append(row.rstrip())
            i += 1
            while i < len(lines) and lines[i].startswith("  "):
                i += 1
            continue
        value = new[key]
        if isinstance(value, bool):
            rendered = "true" if value else "false"
        elif isinstance(value, list):
            rendered = "[" + ", ".join(value) + "]"
        else:
            rendered = yaml_scalar(str(value))
        out.append("%s: %s" % (key, rendered))
        i += 1
    missing = set(project.REQUIRED) - seen
    if missing:
        raise Refused("config/project.yaml does not write %s on a line of "
                      "its own, so init cannot set it" % sorted(missing))
    return "\n".join(out)


def turtle(text: str, old: dict, new: dict) -> str:
    """The namespace, the prefix, and the module's title and comment."""
    text = text.replace(old["iri_base"], new["iri_base"])
    text = re.sub(r"(?<![A-Za-z0-9_/#.\-])" + re.escape(old["prefix"]) + ":",
                  new["prefix"] + ":", text)
    text = text.replace('"%s"' % old["title"], '"%s"' % new["title"])
    text = text.replace("# %s --" % old["title"], "# %s --" % new["title"])
    text = text.replace('"%s"' % old["description"],
                        '"%s"' % new["description"].replace('"', "'"))
    text = text.replace('dcterms:creator "%s"' % old["licence_holder"],
                        'dcterms:creator "%s"'
                        % new["licence_holder"].replace('"', "'"))
    return text


def render(text: str, new: dict, module: str, template: str) -> str:
    values = {
        "id": new["id"], "code": new["code"], "title": new["title"],
        "description": new["description"], "namespace": new["namespace"],
        "prefix": new["prefix"], "iri_base": new["iri_base"],
        "repository": new["repository"], "module": module,
        "date": dt.date.today().isoformat(),
        "template_url": "https://github.com/" + template,
        "licence_holder": new["licence_holder"],
    }
    for key, value in values.items():
        text = text.replace("{{%s}}" % key, value)
    left = sorted(set(re.findall(r"\{\{([a-z_]+)\}\}", text)))
    if left:
        raise Refused("a skeleton names placeholders init does not fill: %s"
                      % left)
    return text


def licence(text: str, holder: str) -> str:
    year = dt.date.today().year
    new, count = re.subn(r"^Copyright \(c\) .*$",
                         "Copyright (c) %d %s" % (year, holder), text,
                         count=1, flags=re.M)
    if count != 1:
        raise Refused("LICENSE has no 'Copyright (c) ...' line to set")
    return new


def without_template_block(text: str) -> str:
    begin = text.find(MARK_BEGIN + "\n")
    end = text.find(MARK_END + "\n")
    if begin == -1 or end == -1 or end < begin:
        raise Refused("the layout contract has no template-only block "
                      "between %r and %r" % (MARK_BEGIN.strip(),
                                             MARK_END.strip()))
    return text[:begin] + text[end + len(MARK_END) + 1:]


# --------------------------------------------------------------- plan


def plan(root: Path, old: dict, new: dict) -> tuple[dict, list, list]:
    """(writes, renames, removals) -- computed in full before any is made.

    writes:   {relative path: new bytes}
    renames:  [(old relative, new relative)]
    removals: [relative path]
    """
    writes: dict[str, bytes] = {}
    renames: list[tuple[str, str]] = []

    def read(relative: str) -> str:
        return (root / relative).read_bytes().decode("utf-8")

    module = layout.component("ontology.main")
    module_new = "ontology/%s.ttl" % new["id"]
    if module.path != module_new:
        renames.append((module.path, module_new))

    for role in TURTLE_ROLES:
        for entry in layout.components(role):
            for path in entry.members("*.ttl"):
                relative = path.relative_to(root).as_posix()
                before = read(relative)
                after = turtle(before, old, new)
                if after != before:
                    writes[relative] = after.encode("utf-8")

    contract = read(layout.CONTRACT)
    contract = contract.replace("    path: %s\n" % module.path,
                                "    path: %s\n" % module_new)
    contract = without_template_block(contract)
    writes[layout.CONTRACT] = contract.encode("utf-8")

    writes[project.CONFIG] = project_file(
        read(project.CONFIG), new).encode("utf-8")

    for skeleton, target in RENDERED.items():
        source = "%s/%s" % (SKELETONS, skeleton)
        if not (root / source).is_file():
            raise Refused("the skeleton %s is missing" % source)
        writes[target] = render(read(source), new, module_new,
                                old["repository"]).encode("utf-8")

    writes["LICENSE"] = licence(read("LICENSE"),
                                new["licence_holder"]).encode("utf-8")

    removals = [c.path for c in layout.components()
                if c.template == "only"]
    if not removals:
        raise Refused("no component is declared template: only, so this "
                      "is not the template, or the contract has changed")

    owned = {c.path for c in layout.components() if c.template == "owned"}
    for relative in writes:
        for path in owned:
            if relative == path or relative.startswith(path + "/"):
                raise Refused(
                    "init would write %s, which the template owns. Owned "
                    "files must not name the project" % relative)
    return writes, renames, removals


def generated_paths() -> set:
    """Every file a component with a generator holds. The generators
    rewrite them after this check, so the template's IRI base in them is
    expected here and gone afterwards."""
    out = set()
    for entry in layout.components():
        if entry.generator and entry.exists():
            out |= {p.resolve() for p in entry.members("*")}
    return out


def leftovers(root: Path, old: dict) -> list[str]:
    """Turtle in which the template's namespace survives.

    Every .ttl in the tree except what a generator rewrites next (the
    extracts, the Protégé edit file, the profile shapes) -- deliberately
    not the TURTLE_ROLES the rewrite walked. Asking the same list twice would make this check blind
    exactly where the rewrite was: with the shapes' role dropped from
    that list, both skipped the shapes, init reported success, and the
    shapes went on filtering on a namespace nothing used.
    """
    regenerated = generated_paths()
    found = []
    for path in sorted(root.rglob("*.ttl")):
        relative = path.relative_to(root).as_posix()
        if relative.startswith((".git/", ".venv/", ".upstream-cache/")):
            continue
        if path.resolve() in regenerated:
            continue
        if old["iri_base"] in path.read_bytes().decode("utf-8"):
            found.append(relative)
    return found


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--id", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--description", required=True)
    ap.add_argument("--repository", required=True, help="owner/name")
    ap.add_argument("--code", default=None,
                    help="default: the id, uppercase, hyphens removed")
    ap.add_argument("--prefix", default=None,
                    help="default: the id, hyphens as underscores")
    ap.add_argument("--iri-base", default=None,
                    help="default: " + IRI_PATTERN % "<id>")
    ap.add_argument("--licence-holder", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-regenerate", action="store_true")
    ap.add_argument("--offline", action="store_true",
                    help="run every generator but the vendoring rebuild, "
                         "which needs the network or a warm cache")
    ap.add_argument("--allow-dirty", action="store_true",
                    help="run with uncommitted changes in the tree")
    args = ap.parse_args(argv)

    root = layout.repository_root()
    old = dict(project.load())
    if not old["template"]:
        raise Refused("config/project.yaml says template: false -- this "
                      "repository is already a project")
    new = values_of(args, old)

    if not args.allow_dirty and git(root, "status", "--porcelain").strip():
        raise Refused("the working tree has uncommitted changes. init "
                      "rewrites files across the tree; run it from a clean "
                      "checkout so `git diff` shows exactly what it did")

    writes, renames, removals = plan(root, old, new)

    print("  %s -> %s" % (old["namespace"], new["namespace"]))
    for source, target in renames:
        print("  rename  %s -> %s" % (source, target))
    for relative in sorted(writes):
        print("  write   %s" % relative)
    for relative in removals:
        print("  remove  %s" % relative)
    if args.dry_run:
        print("  (dry run: nothing written)")
        return 0

    for relative, data in writes.items():
        (root / relative).parent.mkdir(parents=True, exist_ok=True)
        (root / relative).write_bytes(data)
    for source, target in renames:
        (root / source).rename(root / target)
    for relative in removals:
        target = root / relative
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()

    layout._load.cache_clear()
    project.load.cache_clear()
    stray = leftovers(root, old)
    if stray:
        raise Refused("the template namespace %s survives in %s"
                      % (old["iri_base"], stray))

    if args.no_regenerate:
        print()
        print("  generators not run. Before the first commit, run:")
        for command in GENERATORS:
            print("    python " + " ".join(command))
        return 0

    commands = [c for c in GENERATORS
                if not (args.offline and c in NETWORK_GENERATORS)]
    print(flush=True)
    for command in commands:
        # Flushed, or the generator's output -- written straight to the
        # terminal -- lands above the lines that introduced it.
        print("  $ python " + " ".join(command), flush=True)
        result = subprocess.run([sys.executable, *command], cwd=str(root))
        if result.returncode:
            print("  FAILED: %s exited %d. The rewrite is done; fix what it "
                  "reports and run the remaining generators by hand."
                  % (command[0], result.returncode))
            return 1
    print()
    print("  %s is set up. Review `git status` and `git diff`, run the "
          "suite, and commit." % new["title"])
    print("  Then enable GitHub Pages (Settings > Pages > Source: GitHub "
          "Actions): the site is published from the first push to main, and "
          "that push fails until Pages is enabled.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
