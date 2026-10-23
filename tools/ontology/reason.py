# SPDX-License-Identifier: MIT
"""Reason over the ontology with the full pinned upstreams: consistency, and
unsatisfiable classes.

    python tools/ontology/reason.py               # modules + full upstreams,
                                                  # then the examples too
    python tools/ontology/reason.py -o report.json

Exit codes: 0 consistent, nothing unsatisfiable; 1 an unsatisfiable class
or an inconsistency; 2 the reasoner could not be run -- no Java, a jar
that is not the pinned one, an upstream that could not be fetched.

WHY THE FULL UPSTREAMS

The extracts drop every axiom whose object is an anonymous class
expression, so a reasoner over them derives less than one over BFO and
CCO, and could not say the ontology is consistent with either. Here the
pinned upstream files themselves are fetched (the vendoring cache) and
merged with the authored modules. The shapes check what is asserted; this
is what finds a class no instance can have because of what follows.

TWO PASSES

The terminology first -- modules and upstreams -- for unsatisfiable
classes. Then, when there are examples, the same with the example
instance data, for consistency only: an individual typed with two
disjoint classes makes the whole graph inconsistent, and reported in one
pass it would read as a defect of the ontology.

READING ROBOT

ROBOT exits non-zero on either problem and names unsatisfiable classes in
its log, one `unsatisfiable: <IRI>` line each, after a line giving their
number. Both are read, and a run where they disagree is refused rather
than reported: a change in ROBOT's log format would otherwise read as
"nothing unsatisfiable".
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import layout  # noqa: E402
import project  # noqa: E402

CONFIG = "config/reasoning.yaml"
TOOL_CACHE = ".tool-cache"
UPSTREAM_CACHE = ".upstream-cache"


class Unrunnable(Exception):
    """Exit 2: the question could not be asked."""


def config(root: Path | None = None) -> dict:
    import yaml

    root = root or layout.repository_root()
    raw = yaml.safe_load((root / CONFIG).read_text(encoding="utf-8")) or {}
    robot = raw.get("robot") or {}
    for key in ("version", "url", "sha256", "tag_commit", "licence"):
        if not robot.get(key):
            raise Unrunnable("%s declares no robot.%s" % (CONFIG, key))
    if "v%s" % robot["version"] not in robot["url"]:
        raise Unrunnable("%s pins ROBOT %s and its url %s names another "
                         "release" % (CONFIG, robot["version"], robot["url"]))
    if not re.fullmatch(r"[0-9a-f]{64}", str(robot["sha256"])):
        raise Unrunnable("%s: robot.sha256 is not 64 lowercase hex" % CONFIG)
    if raw.get("reasoner", "").lower() not in ("elk", "hermit"):
        raise Unrunnable("%s: reasoner %r is not ELK or HermiT"
                         % (CONFIG, raw.get("reasoner")))
    return raw


def fetch_jar(robot: dict, cache: Path) -> Path:
    """The pinned jar, from the cache or the network, digest checked."""
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / ("robot-%s.jar" % robot["version"])
    if path.is_file():
        if hashlib.sha256(path.read_bytes()).hexdigest() == robot["sha256"]:
            return path
        path.unlink()
    try:
        with urllib.request.urlopen(robot["url"], timeout=300) as response:
            data = response.read()
    except OSError as error:
        raise Unrunnable("cannot fetch ROBOT from %s: %s" % (robot["url"],
                                                             error))
    got = hashlib.sha256(data).hexdigest()
    if got != robot["sha256"]:
        raise Unrunnable(
            "%s served %d bytes digesting to %s, and %s pins %s. Refusing to "
            "run a reasoner that is not the pinned one."
            % (robot["url"], len(data), got, CONFIG, robot["sha256"]))
    path.write_bytes(data)
    return path


def java() -> str:
    found = shutil.which("java")
    if not found:
        raise Unrunnable("no `java` on the PATH. The reasoning job installs "
                         "one (config/reasoning.yaml, `java`); locally, "
                         "install a JDK 11 or later")
    return found


def upstream_files(root: Path) -> list[Path]:
    """The pinned upstream files themselves, through the vendoring cache."""
    vendoring = _vendoring()
    cache = root / UPSTREAM_CACHE
    out = []
    for source in vendoring.sources():
        try:
            vendoring.fetch(source, cache)
        except (OSError, SystemExit) as error:
            raise Unrunnable("cannot fetch %s: %s" % (source["id"], error))
        out.extend(cache / vendoring.cache_name(source, n)
                   for n in range(1, len(source["files"]) + 1))
    return out


def _vendoring():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "reason_vendoring",
        layout.repository_root() / "tools/ontology/vendor_upstream.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


UNSAT_COUNT = re.compile(r"There (?:are|is) (\d+) unsatisfiable class")
UNSAT_CLASS = re.compile(r"unsatisfiable: (\S+)")
INCONSISTENT = "The ontology is inconsistent"


def read_robot(code: int, log: str) -> dict:
    """What ROBOT said, refused when it is not one of the known answers.
    Pure, so each branch is tested without a JVM."""
    classes = sorted(set(UNSAT_CLASS.findall(log)))
    counted = [int(n) for n in UNSAT_COUNT.findall(log)]
    if code == 0:
        if classes or counted:
            raise Unrunnable("ROBOT exited 0 and named unsatisfiable classes")
        return {"consistent": True, "unsatisfiable": []}
    if INCONSISTENT in log:
        return {"consistent": False, "unsatisfiable": []}
    if counted:
        if counted[0] != len(classes):
            raise Unrunnable(
                "ROBOT reported %d unsatisfiable classes and named %d; its "
                "log format may have changed, so the list cannot be trusted"
                % (counted[0], len(classes)))
        return {"consistent": True, "unsatisfiable": classes}
    raise Unrunnable("ROBOT exited %d without saying why:\n%s"
                     % (code, log.strip()[-1500:]))


def run_robot(jar: Path, reasoner: str, inputs: list[Path]) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        command = [java(), "-jar", str(jar), "merge"]
        for path in inputs:
            command += ["--input", str(path)]
        command += ["reason", "--reasoner", reasoner,
                    "--dump-unsatisfiable", str(Path(tmp) / "unsat.ttl")]
        result = subprocess.run(command, capture_output=True)
    log = (result.stdout + result.stderr).decode("utf-8", "replace")
    return read_robot(result.returncode, log)


def reason(modules: list[Path] | None = None,
           examples: list[Path] | None = None) -> dict:
    root = layout.repository_root()
    settings = config(root)
    jar = fetch_jar(settings["robot"], root / TOOL_CACHE)
    upstream = upstream_files(root)
    modules = list(modules if modules is not None else layout.ontology_files())
    if examples is None:
        examples = []
        for entry in layout.components("example-data"):
            examples.extend(entry.members("*.ttl"))
    namespace = project.namespace()

    terminology = run_robot(jar, settings["reasoner"], upstream + modules)
    unsat = terminology["unsatisfiable"]
    record = {
        "robot": settings["robot"]["version"],
        "reasoner": settings["reasoner"],
        "upstream_files": [p.name for p in upstream],
        "modules": [p.as_posix() for p in modules],
        "consistent": terminology["consistent"],
        "unsatisfiable_authored": [c for c in unsat if c.startswith(namespace)],
        "unsatisfiable_upstream": [c for c in unsat
                                   if not c.startswith(namespace)],
        "examples": [p.as_posix() for p in examples],
        "examples_consistent": None,
    }
    if examples and terminology["consistent"] and not unsat:
        with_data = run_robot(jar, settings["reasoner"],
                              upstream + modules + list(examples))
        record["examples_consistent"] = with_data["consistent"]
    record["ok"] = (record["consistent"] and not unsat
                    and record["examples_consistent"] is not False)
    return record


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("-o", "--out", default=None)
    args = ap.parse_args(argv)
    try:
        record = reason()
    except Unrunnable as error:
        print("  CANNOT REASON: %s" % error, file=sys.stderr)
        return 2
    print("  ROBOT %s, %s, over %d module(s) and %s"
          % (record["robot"], record["reasoner"], len(record["modules"]),
             ", ".join(record["upstream_files"])))
    if not record["consistent"]:
        print("  INCONSISTENT: the modules and the upstreams together have "
              "no model")
    for iri in record["unsatisfiable_authored"]:
        print("  UNSATISFIABLE  %s" % iri)
    for iri in record["unsatisfiable_upstream"]:
        print("  UNSATISFIABLE (upstream)  %s" % iri)
    if record["examples_consistent"] is False:
        print("  INCONSISTENT WITH THE EXAMPLES: an example individual has "
              "types nothing can have together")
    if record["ok"]:
        print("  consistent; nothing unsatisfiable%s"
              % ("; the examples are consistent with it"
                 if record["examples_consistent"] else ""))
    if args.out:
        Path(args.out).write_bytes(json.dumps(record, indent=2,
                                              sort_keys=True).encode("utf-8")
                                   + b"\n")
    return 0 if record["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
