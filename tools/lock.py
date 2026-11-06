# SPDX-License-Identifier: MIT
"""The Python dependency lock: every distribution the checks install.

    python tools/lock.py              # offline: is the lock current and whole?
    python tools/lock.py --write      # online: resolve it again, with uv
    python tools/lock.py --verify     # online: resolve it in a scratch
                                      # directory and compare, byte for byte
    python tools/lock.py --bootstrap  # install the pinned pip (stdlib only)

WHY THIS EXISTS

requirements-dev.txt pins the six packages the tools import. They pull in
ten more, owlrl among them -- pyshacl runs it -- and until v0.3.0 nothing
pinned those: two runs of one commit could run different code, depending
on what PyPI held that day (the BPO Testing Team's P-A1). And CI upgraded
pip itself to whatever was newest.

So requirements-lock.txt is generated from three inputs:

  requirements-dev.txt   the direct pins, each one justified
  requirements-pip.txt   the pip that installs the rest
  config/tooling.yaml    the uv that resolves the lock, by version and
                         checksum; the interpreter; and a cutoff instant,
                         after which no release is taken

uv resolves it once for every platform, keeping the environment markers
(colorama, on Windows only), with the sha256 of every file PyPI has for
each version. pip installs from it with --require-hashes, which refuses
any distribution the lock does not list: an incomplete lock fails the
install. uv is used for this and nothing else (template decision 32).

The cutoff is what makes --verify mean something: the same inputs resolve
to the same lock on any later day, so a lock nobody edited by hand is one
a scratch resolution reproduces.

WHAT THE OFFLINE CHECK REFUSES

  - a lock whose recorded digest is not that of its three inputs: one
    changed, and the lock was not written again;
  - a direct pin, or the pip pin, missing from the lock or at another
    version;
  - an entry without a hash, or not pinned with ==.

THE BOOTSTRAP

The pip that first runs in a fresh environment came with the interpreter,
and cannot be pinned. --bootstrap has it install only the pinned pip,
from the lock's own lines and hashes, then prints the interpreter and
both pip versions, so a run records what it ran on. It imports nothing
outside the standard library, because it runs before anything else is
installed.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import platform
import re
import subprocess
import sys
import tempfile
from pathlib import Path

DIRECT = "requirements-dev.txt"
PIP = "requirements-pip.txt"
TOOLING = "config/tooling.yaml"
LOCK = "requirements-lock.txt"
INPUTS = (DIRECT, PIP, TOOLING)

COMMAND = "python tools/lock.py --write"
INDEX = "https://pypi.org/simple"
DIGEST_LINE = re.compile(r"^# inputs-sha256: ([0-9a-f]{64})$", re.M)
PINNED = re.compile(r"^([A-Za-z0-9_.-]+)==([^\s;]+)\s*(?:;\s*(.+?))?$")
HASH = re.compile(r"--hash=sha256:([0-9a-f]{64})")


class Refused(SystemExit):
    """Raised rather than writing, or installing, something unchecked."""


def repository_root() -> Path:
    return Path(__file__).resolve().parent.parent


def normalized(name: str) -> str:
    """PEP 503: uv writes `pyyaml` for requirements-dev.txt's `PyYAML`."""
    return re.sub(r"[-_.]+", "-", name).lower()


# ---------------------------------------------------------------- read


def inputs_digest(root: Path) -> str:
    rows = "\n".join("%s %s" % (name, hashlib.sha256(
        (root / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest())
        for name in INPUTS)
    return hashlib.sha256(rows.encode("utf-8")).hexdigest()


def pins_in(text: str) -> dict:
    """{normalized name: version} for every `name==version` line."""
    out = {}
    for line in text.splitlines():
        match = PINNED.match(line.split("#", 1)[0].strip())
        if match:
            out[normalized(match.group(1))] = match.group(2)
    return out


def entries(text: str) -> list[dict]:
    """The lock's requirements, each with its marker and hashes.

    A requirement is one logical line: its continuations (a trailing
    backslash) carry the hashes, and `# via` comments between entries are
    the resolver's notes, not requirements.
    """
    logical, current = [], ""
    for line in text.splitlines():
        stripped = line.strip()
        if not current and (not stripped or stripped.startswith("#")):
            continue
        current += " " + stripped.rstrip("\\").strip()
        if not stripped.endswith("\\"):
            logical.append(current.strip())
            current = ""
    if current:
        logical.append(current.strip())

    out = []
    for line in logical:
        head = line.split("--hash=", 1)[0].strip()
        match = PINNED.match(head)
        out.append({
            "line": head,
            "name": normalized(match.group(1)) if match else None,
            "version": match.group(2) if match else None,
            "marker": match.group(3) if match else None,
            "hashes": HASH.findall(line),
        })
    return out


# --------------------------------------------------------------- check


def problems(root: Path | None = None) -> list[str]:
    root = root or repository_root()
    path = root / LOCK
    if not path.is_file():
        return ["%s is missing: run %s" % (LOCK, COMMAND)]
    text = path.read_bytes().decode("utf-8")
    out = []

    recorded = DIGEST_LINE.search(text)
    expected = inputs_digest(root)
    if not recorded:
        out.append("%s records no inputs digest, so nothing says what it "
                   "was resolved from" % LOCK)
    elif recorded.group(1) != expected:
        out.append("%s is stale: %s, %s or %s changed after it was "
                   "written (recorded %s, now %s). Run %s"
                   % (LOCK, DIRECT, PIP, TOOLING, recorded.group(1)[:16],
                      expected[:16], COMMAND))

    locked = {}
    for entry in entries(text):
        if entry["name"] is None:
            out.append("%s: %r is not pinned with ==" % (LOCK, entry["line"]))
            continue
        if not entry["hashes"]:
            out.append("%s: %s has no hash, so pip's hash-checking mode "
                       "refuses the whole lock" % (LOCK, entry["line"]))
        locked.setdefault(entry["name"], set()).add(entry["version"])

    for source in (DIRECT, PIP):
        for name, version in pins_in(
                (root / source).read_text(encoding="utf-8")).items():
            if name not in locked:
                out.append("%s pins %s==%s, and %s does not list it"
                           % (source, name, version, LOCK))
            elif locked[name] != {version}:
                out.append("%s pins %s==%s, and %s has %s"
                           % (source, name, version, LOCK,
                              ", ".join(sorted(locked[name]))))
    return out


# --------------------------------------------------------------- write


def tooling(root: Path) -> dict:
    import yaml

    uv = (yaml.safe_load((root / TOOLING).read_text(encoding="utf-8"))
          or {}).get("uv") or {}
    for key in ("version", "python", "exclude_newer", "sha256"):
        if not uv.get(key):
            raise Refused("%s: uv.%s is not set" % (TOOLING, key))
    bad = [name for name, value in uv["sha256"].items()
           if not re.fullmatch(r"[0-9a-f]{64}", str(value))]
    if bad:
        raise Refused("%s: not a sha256 for %s" % (TOOLING, ", ".join(bad)))
    return uv


def venv_python(venv: Path) -> Path:
    return venv / ("Scripts/python.exe" if sys.platform == "win32"
                   else "bin/python")


def run(command: list, cwd: Path | None = None) -> None:
    result = subprocess.run([str(c) for c in command], cwd=cwd,
                            capture_output=True)
    if result.returncode:
        raise Refused("%s failed:\n%s" % (" ".join(map(str, command[:4])),
                                          (result.stdout + result.stderr)
                                          .decode("utf-8", "replace")[-2000:]))


def resolve(root: Path, out: Path) -> None:
    """Install the pinned uv into a scratch environment, checking its
    checksum, and have it write the lock to `out`."""
    uv = tooling(root)
    with tempfile.TemporaryDirectory(prefix="lock-") as scratch:
        scratch = Path(scratch)
        requirement = scratch / "uv.txt"
        requirement.write_bytes(("uv==%s %s\n" % (uv["version"], " ".join(
            "--hash=sha256:%s" % value for value in sorted(
                uv["sha256"].values())))).encode("utf-8"))
        run([sys.executable, "-m", "venv", scratch / "venv"])
        python = venv_python(scratch / "venv")
        run([python, "-m", "pip", "install", "--quiet",
             "--disable-pip-version-check", "--require-hashes",
             "--index-url", INDEX, "-r", requirement])
        resolved = scratch / "resolved.txt"
        run([python, "-m", "uv", "pip", "compile", "--quiet", "--no-config",
             "--universal", "--generate-hashes",
             "--python-version", uv["python"],
             "--exclude-newer", uv["exclude_newer"],
             "--default-index", INDEX,
             "--custom-compile-command", COMMAND,
             "--output-file", resolved, DIRECT, PIP], cwd=root)
        body = resolved.read_bytes().decode("utf-8").replace("\r\n", "\n")
    header = ("# GENERATED by %s from %s, %s and\n"
              "# %s. Never edited: change an input and write it again.\n"
              "# inputs-sha256: %s\n"
              % (COMMAND, DIRECT, PIP, TOOLING, inputs_digest(root)))
    out.write_bytes((header + body).encode("utf-8"))


# ------------------------------------------------------------ bootstrap


def pip_version(python: str) -> str:
    result = subprocess.run([python, "-m", "pip", "--version"],
                            capture_output=True)
    words = result.stdout.decode("utf-8", "replace").split()
    return words[1] if result.returncode == 0 and len(words) > 1 else "none"


def bootstrap(root: Path, python: str = sys.executable) -> int:
    pinned = pins_in((root / PIP).read_text(encoding="utf-8")).get("pip")
    if not pinned:
        raise Refused("%s pins no pip" % PIP)
    lock = (root / LOCK).read_bytes().decode("utf-8")
    [entry] = [e for e in entries(lock) if e["name"] == "pip"] or [None]
    if entry is None or entry["version"] != pinned or not entry["hashes"]:
        raise Refused("%s has no hashed pip==%s line; run python "
                      "tools/lock.py" % (LOCK, pinned))
    before = pip_version(python)
    with tempfile.TemporaryDirectory(prefix="pip-") as scratch:
        requirement = Path(scratch) / "pip.txt"
        requirement.write_bytes(("pip==%s %s\n" % (pinned, " ".join(
            "--hash=sha256:" + h for h in entry["hashes"]))).encode("utf-8"))
        run([python, "-m", "pip", "install", "--quiet",
             "--disable-pip-version-check", "--require-hashes", "--no-deps",
             "--index-url", INDEX, "-r", requirement])
    after = pip_version(python)
    print("  interpreter %s (%s, %s)" % (
        platform.python_version(), platform.python_implementation(),
        platform.platform()))
    print("  pip %s installed pip %s from %s" % (before, after, LOCK))
    if after != pinned:
        print("  FAIL: pip is %s, and %s pins %s" % (after, PIP, pinned))
        return 1
    return 0


# ----------------------------------------------------------------- main


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true",
                      help="resolve the lock again (network)")
    mode.add_argument("--verify", action="store_true",
                      help="resolve in a scratch directory and compare "
                           "(network)")
    mode.add_argument("--bootstrap", action="store_true",
                      help="install the pinned pip from the lock")
    args = ap.parse_args(argv)
    root = repository_root()

    if args.bootstrap:
        return bootstrap(root)

    if args.write:
        resolve(root, root / LOCK)
        print("  wrote %s: %d distribution(s)" % (
            LOCK, len(entries((root / LOCK).read_text(encoding="utf-8")))))

    if args.verify:
        with tempfile.TemporaryDirectory(prefix="verify-") as scratch:
            again = Path(scratch) / LOCK
            resolve(root, again)
            fresh = again.read_bytes().decode("utf-8")
        held = (root / LOCK).read_bytes().decode("utf-8")
        if fresh != held:
            print("  FAIL: resolving %s, %s and %s again gives a different "
                  "lock:" % (DIRECT, PIP, TOOLING))
            sys.stdout.writelines(list(difflib.unified_diff(
                held.splitlines(True), fresh.splitlines(True),
                LOCK, "resolved again"))[:200])
            return 1
        print("  resolved again, byte for byte the same as %s" % LOCK)

    found = problems(root)
    for problem in found:
        print("  FAIL: %s" % problem)
    if found:
        return 1
    locked = entries((root / LOCK).read_text(encoding="utf-8"))
    print("  %s: %d distribution(s), every one pinned and hashed; current "
          "with %s, %s and %s" % (LOCK, len(locked), DIRECT, PIP, TOOLING))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
