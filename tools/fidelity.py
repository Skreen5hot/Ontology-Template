# SPDX-License-Identifier: MIT
"""Conceptual fidelity: which element of an approved conceptual model each
authored term, shape and competency question formalizes, who reviewed
it, and which decision authorized each departure from the model.

    python tools/fidelity.py                 # check; exit 1 on a finding
    python tools/fidelity.py --json          # findings, debt and counts
    python tools/fidelity.py --digest TERM   # the axiom digest to review
    python tools/fidelity.py --pins          # model and upstream digests

METHOD section 4's formalization gate (P6, template decisions 42 and
43): each formal choice preserves the approved conceptual model's
meaning, or documents why it changes it, in a decision. This records the
trace between the two and holds what a person still owes it. It never
judges meaning: `preserves` is a reviewer's claim, a departure is the
architect's decision, and a matching digest shows only that what was
reviewed has not changed since.

THE MODELS, config/fidelity.yaml

  applicable    null, or false with decided_by: the decision record that
                says conceptual fidelity does not apply to this project.
                With no model registered and no such decision, the report
                says "not yet established", never that fidelity passed
  models        each approved model:
    id          CM-01 and the like, as references name it
    file        the model, in the repository
    approved_by the decision record that approved it, citing its id
    cover       the anchors that must each be traced, [kind:]path
                patterns (below). The architect's selection; the tool
                never takes it for the whole model
    prohibits   references to elements that forbid an inference: each
                row tracing one names a guard, or says why it has none
    anchors     for a model not in Markdown: its anchors, declared. They
                are reported as declared, never as verified in the file
  reviewers     the kinds that may sign a `preserves` row; each one a kind
                config/review.yaml declares (decision 43)
  stage         the stage the debt holds, formalization by default
  required_from, baseline_commit
                for a project adopting P6 with terms already authored:
                the adoption snapshot is baseline_commit, or else the
                last commit before required_from. A term the authored
                modules, by their current paths, declared at that
                snapshot predates adoption: it is listed, and not held.
                A term whose age cannot be established -- the baseline
                commit is not in the history, or a shallow clone cannot
                say which commit came before the date -- is uncertain,
                and held as debt: never exempted

AN ELEMENT REFERENCE is <model id>#<anchor>. In a Markdown model an
anchor is the text of a heading, up to an em dash ("P1", "DP-1",
"Organization"), with "§6" for a numbered section "6. ..."; the first
cell of a table row other than a header ("RL-01"); or the leading bold
text of a list item ("A-01"). Text in fenced code blocks is not read. A
reference must resolve to exactly one place; one that recurs is
qualified by the headings that enclose it, outermost first:
"§7/DP-1/Options". In a `cover` pattern, "/" separates those headings
and each part is a glob; a kind prefix (heading:, row:, item:) narrows
it: "row:§5/RL-*".

THE TRACE, ontology/trace.yaml

  models          {model id: the SHA-256 of its file when the trace was
                  reviewed}
  upstream_sha256 the digest of the pinned upstream context
                  (config/upstream-sources.yaml, parsed): BFO or CCO
                  re-pinned can change what a reviewed axiom entails
  rows            each:
    elements        element references, one or more
    formalized_as   {terms, shapes, questions}: authored IRIs (or
                    prefix:name in the project's prefix), node or
                    property shapes in a shape set, competency question
                    ids. Several of each, for a many-to-many mapping
    fidelity        preserves | changes | not-formalized. not-formalized
                    is not in OWL: it names no term, and may name a shape
                    or a question that represents the element
    decision        a decision record citing each of the row's
                    references, required for changes and not-formalized.
                    The citation is P7's (decision 38): the reference
                    written in the record, a longer one not counting
    reviewed_by     "<name> (<kind>)", required for preserves
    axioms_sha256   the digest of the terms' asserted axioms when the row
                    was reviewed, required when it names a term
    guards          competency question ids or shape IRIs that fail if a
                    prohibited inference is made, or
    no_guard        why there is none: one is required for a row tracing
                    an element in `prohibits`

THE AXIOM DIGEST is over a canonical form of the asserted axioms about
the row's terms, merged across every authored module: each RDF, RDFS and
OWL triple whose subject is the term, with the blank-node structures it
reaches (restrictions, class expressions, lists); each disjointness,
equivalence, inverse or identity axiom naming it from another IRI; each
anonymous axiom mentioning it (AllDisjointClasses, a general class
axiom); and its skos:definition. Labels, comments and other annotations
are not in it, nor reified axiom annotations. Members of set-valued lists
(unionOf, intersectionOf, oneOf, members, disjointUnionOf,
distinctMembers, hasKey) are taken as sets; a property chain keeps its
order. Blank nodes are labelled canonically (rdflib.compare), so neither
the order of a serialization nor the module an axiom sits in moves it.
The tool never writes a digest: --digest prints it for the reviewer,
who writes it into the row with the review (decision 42: never silently
regenerated).

WHAT IT REFUSES, in ordinary CI, each finding naming the row or file:
the schema of either file; a model that is missing, unapproved by a
decision record citing it, or neither Markdown nor declaring its
anchors; a reference that resolves to nothing or to more than one
place; a term outside the authored namespace or declared in no authored
module; a shape no shape set declares; a competency question that does
not exist, or a guard question that is not answerable; a row's fidelity
without what it requires; a reviewer not of an allowed kind; a malformed
or missing digest; a prohibiting element's row without a guard or a
reason.

WHAT IT LISTS, THE FIDELITY DEBT: an authored class or property no row
names; a covered or prohibiting element no row names; a row whose model,
upstream context or axioms have changed since its review (stale); a
term whose age cannot be established (uncertain). Debt fails nothing
here. It holds the stage named in `stage` marked done (tools/stages.py),
and a release (tools/release.py).

Exit codes: 0 no findings; 1 findings.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import decisions  # noqa: E402
import findings  # noqa: E402
import layout  # noqa: E402
import project  # noqa: E402

CONFIG = "config/fidelity.yaml"
TRACE = "ontology/trace.yaml"
UPSTREAM = "config/upstream-sources.yaml"
QUESTIONS = "competency-questions"
FORMATS = (1,)
FIDELITY = ("preserves", "changes", "not-formalized")
NEEDS_DECISION = ("changes", "not-formalized")
TOP_FIELDS = {"format_version", "models", "upstream_sha256", "rows"}
ROW_FIELDS = {"elements", "formalized_as", "fidelity", "decision",
              "reviewed_by", "axioms_sha256", "guards", "no_guard"}
TARGET_FIELDS = ("terms", "shapes", "questions")
MODEL_FIELDS = {"id", "file", "approved_by", "cover", "prohibits",
                "anchors"}
KINDS = ("heading", "row", "item", "declared")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
MODEL_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]*$")
QUESTION_ID = re.compile(r"^CQ-[0-9]+$")
MARKDOWN = (".md", ".markdown")

DEFAULTS = {
    "applicable": None,
    "decided_by": None,
    "models": [],
    "reviewers": ["ontologist", "domain-expert", "proxy-domain-expert"],
    "stage": "formalization",
    "required_from": None,
    "baseline_commit": None,
}

RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
OWL = "http://www.w3.org/2002/07/owl#"
SKOS = "http://www.w3.org/2004/02/skos/core#"
SH = "http://www.w3.org/ns/shacl#"
#: The authored kinds the formal side of coverage counts.
TERM_KINDS = ("Class", "ObjectProperty", "DatatypeProperty",
              "AnnotationProperty")
#: Annotations in the logical namespaces, which the digest leaves out.
NOT_AXIOMS = {RDFS + "label", RDFS + "comment", RDFS + "seeAlso",
              RDFS + "isDefinedBy", OWL + "versionInfo",
              OWL + "priorVersion", OWL + "backwardCompatibleWith",
              OWL + "incompatibleWith"}
#: The one annotation the digest keeps: a definition says what a term
#: means, and a changed one is a change for the reviewer.
DEFINITION = SKOS + "definition"
#: Axioms naming a term from another IRI that constrain the term itself.
SYMMETRIC = {OWL + "disjointWith", OWL + "equivalentClass",
             OWL + "equivalentProperty", OWL + "inverseOf",
             OWL + "propertyDisjointWith", OWL + "sameAs",
             OWL + "differentFrom"}
#: List-valued predicates whose lists are sets.
SET_LISTS = {OWL + "unionOf", OWL + "intersectionOf", OWL + "oneOf",
             OWL + "members", OWL + "disjointUnionOf",
             OWL + "distinctMembers", OWL + "hasKey"}
MEMBER = "urn:x-fidelity:member"

HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
NUMBERED = re.compile(r"^(\d+(?:\.\d+)*)\.?\s")
FENCE = re.compile(r"^\s*(```|~~~)")
SEPARATOR = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
ITEM = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+\*\*(.+?)\*\*")


class Unreadable(SystemExit):
    """A file this reads cannot be read as what it should be."""


# --------------------------------------------------------------- reading


def load_yaml(root: Path, name: str, empty):
    import yaml

    path = root / name
    if not path.is_file():
        return empty
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise Unreadable("%s cannot be read: %s" % (name, exc))
    raw = empty if raw is None else raw
    if not isinstance(raw, dict):
        raise Unreadable("%s is not a mapping" % name)
    return raw


def configuration(root: Path) -> dict:
    import datetime

    raw = load_yaml(root, CONFIG, {})
    unknown = sorted(set(raw) - set(DEFAULTS) - {"version"})
    if unknown:
        raise Unreadable("%s has unknown field(s): %s"
                         % (CONFIG, ", ".join(map(str, unknown))))
    settings = dict(DEFAULTS)
    settings.update({k: v for k, v in raw.items() if k != "version"})
    start = settings["required_from"]
    if start is not None and not isinstance(start, datetime.date):
        try:
            settings["required_from"] = datetime.date.fromisoformat(
                str(start))
        except ValueError:
            raise Unreadable("%s: required_from %r is not a date "
                             "(YYYY-MM-DD)" % (CONFIG, start))
    return settings


def trace(root: Path) -> dict:
    raw = load_yaml(root, TRACE, None)
    if raw is None:
        return {"format_version": 1, "models": {}, "rows": []}
    if raw.get("format_version") not in FORMATS:
        raise Unreadable("%s: format_version %r is not one of %s"
                         % (TRACE, raw.get("format_version"), FORMATS))
    return raw


def text_of(value) -> str:
    return str(value).strip() if isinstance(value, (str, int, float)) \
        else ""


def strings(value) -> list[str] | None:
    """A list of non-empty strings, or None if it is not one."""
    if value is None:
        return []
    if not isinstance(value, list) or not all(
            isinstance(v, str) and v.strip() for v in value):
        return None
    return [v.strip() for v in value]


def git(root: Path, *args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(root),
                          capture_output=True, text=True)


def tracked(root: Path) -> set[str]:
    result = git(root, "ls-files")
    return set(result.stdout.split()) if result.returncode == 0 else set()


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def upstream_digest(root: Path) -> str | None:
    """The pinned upstream context: config/upstream-sources.yaml, parsed,
    so a comment or a reflow does not move it."""
    import yaml

    path = root / UPSTREAM
    if not path.is_file():
        return None
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return hashlib.sha256(json.dumps(data, sort_keys=True, default=str)
                          .encode("utf-8")).hexdigest()


# --------------------------------------------------- the model's anchors


class Anchor:
    """One place in a model a reference can name."""

    def __init__(self, kind: str, names: list[str], path: list[list[str]],
                 line: int):
        self.kind = kind
        self.names = names        # what it is called, "§6" too for a section
        self.path = path          # the names of each enclosing heading
        self.line = line


def clean(cell: str) -> str:
    cell = cell.strip()
    for mark in ("**", "__", "`"):
        if cell.startswith(mark) and cell.endswith(mark) and \
                len(cell) > 2 * len(mark):
            cell = cell[len(mark):-len(mark)].strip()
    return cell


def heading_names(text: str) -> list[str]:
    name = text.split(" — ", 1)[0].strip()
    names = [name] if name else []
    number = NUMBERED.match(text)
    if number:
        names.append("§" + number.group(1))
    return names


def markdown_anchors(text: str) -> list[Anchor]:
    """Every heading, table row and bold list item, in order, each with
    the headings that enclose it."""
    out, stack, fenced = [], [], False
    lines = text.split("\n")
    for number, line in enumerate(lines, 1):
        if FENCE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        heading = HEADING.match(line)
        if heading:
            level = len(heading.group(1))
            while stack and stack[-1][0] >= level:
                stack.pop()
            names = heading_names(heading.group(2))
            if names:
                out.append(Anchor("heading", names, [s[1] for s in stack],
                                  number))
                stack.append((level, names))
            continue
        enclosing = [s[1] for s in stack]
        if line.lstrip().startswith("|"):
            if SEPARATOR.match(line):
                continue
            following = lines[number] if number < len(lines) else ""
            if SEPARATOR.match(following):
                continue                      # a header row
            cells = line.strip().strip("|").split("|")
            first = clean(cells[0]) if cells else ""
            if first:
                out.append(Anchor("row", [first], enclosing, number))
            continue
        item = ITEM.match(line)
        if item:
            name = item.group(1).strip().rstrip(".:").strip()
            if name:
                out.append(Anchor("item", [name], enclosing, number))
    return out


def within(prefix: str, path: list[list[str]], glob: bool = False) -> bool:
    """Whether the qualifier names enclosing headings, outermost first,
    each one once and in order."""
    if prefix == "":
        return True
    for index, names in enumerate(path):
        for name in names:
            if glob:
                head, _, rest = prefix.partition("/")
                if fnmatch.fnmatchcase(name, head) and \
                        within(rest, path[index + 1:], glob):
                    return True
            elif prefix == name:
                return True
            elif prefix.startswith(name + "/") and \
                    within(prefix[len(name) + 1:], path[index + 1:]):
                return True
    return False


def matches(anchor: Anchor, reference: str) -> bool:
    for name in anchor.names:
        if reference == name:
            return True
        if reference.endswith("/" + name) and within(
                reference[:-len(name) - 1], anchor.path):
            return True
    return False


def resolve(anchors: list[Anchor], reference: str) -> list[Anchor]:
    return [a for a in anchors if matches(a, reference)]


def covered_by(anchor: Anchor, pattern: str) -> bool:
    kind, sep, rest = pattern.partition(":")
    if sep and kind in KINDS:
        if anchor.kind != kind:
            return False
        pattern = rest
    head, sep, last = pattern.rpartition("/")
    if not sep:
        head, last = "", pattern
    return any(fnmatch.fnmatchcase(n, last) for n in anchor.names) and \
        within(head, anchor.path, glob=True)


def reference_for(anchors: list[Anchor], anchor: Anchor, model: str) -> str:
    """The shortest reference that names this anchor and nothing else."""
    candidates = [anchor.names[0]]
    for depth in range(1, len(anchor.path) + 1):
        qualifiers = [names[-1] if names[-1].startswith("§")
                      else names[0] for names in anchor.path[-depth:]]
        candidates.append("/".join(qualifiers + [anchor.names[0]]))
    for candidate in candidates:
        if resolve(anchors, candidate) == [anchor]:
            return "%s#%s" % (model, candidate)
    return "%s#%s (line %d)" % (model, anchor.names[0], anchor.line)


# ---------------------------------------------------------------- models


def banned(ident: str, model: dict) -> tuple[list[Anchor], list[str]]:
    """The elements a model's `prohibits` names, each resolved to one
    place, and what is wrong with the list."""
    found, out = [], []
    for reference in strings(model["entry"].get("prohibits")) or []:
        owner, sep, anchor = reference.partition("#")
        if not sep or owner != ident or not anchor:
            out.append("prohibits %s, which is not %s#<anchor>"
                       % (reference, ident))
            continue
        places = resolve(model["anchors"], anchor)
        if len(places) == 1:
            found.append(places[0])
        else:
            out.append("prohibits %s, which %s" % (
                reference, "names nothing in it" if not places
                else "names %d places; qualify it" % len(places)))
    return found, out


def model_problems(root: Path, settings: dict, known: set,
                   records: set) -> tuple[dict, list[str]]:
    """{id: {"entry", "anchors", "declared"}} and what is wrong."""
    out, models = [], {}
    entries = settings["models"]
    if not isinstance(entries, list):
        return {}, ["%s: models is not a list" % CONFIG]
    for number, entry in enumerate(entries, 1):
        if not isinstance(entry, dict):
            out.append("%s: model %d is not a mapping" % (CONFIG, number))
            continue
        ident = text_of(entry.get("id"))
        where = "%s: model %s" % (CONFIG, ident or number)
        unknown = sorted(set(entry) - MODEL_FIELDS)
        if unknown:
            out.append("%s has unknown field(s): %s"
                       % (where, ", ".join(map(str, unknown))))
        if not MODEL_ID.match(ident):
            out.append("%s: id %r is not a model identifier (letters, "
                       "digits, '.', '_', '-'; no '#')" % (where, ident))
            continue
        if ident in models:
            out.append("%s is registered twice" % where)
            continue
        name = text_of(entry.get("file"))
        path = root / name if name else None
        if not name or not path.is_file():
            out.append("%s: its file %r does not exist" % (where, name))
            continue
        approval = text_of(entry.get("approved_by"))
        if not approval or approval not in records or approval not in known:
            out.append("%s: approved_by %r is not a tracked decision record "
                       "(config/decisions.yaml records); a model is traced "
                       "once it is approved" % (where, approval or None))
        elif not decisions.cites((root / approval).read_text(
                encoding="utf-8", errors="replace"), ident):
            out.append("%s: %s, its approval, does not cite %s"
                       % (where, approval, ident))
        declared = entry.get("anchors")
        if declared is not None:
            names = strings(declared)
            if names is None:
                out.append("%s: anchors is not a list of names" % where)
                names = []
            seen = set()
            for anchor in names:
                if anchor in seen:
                    out.append("%s declares the anchor %s twice"
                               % (where, anchor))
                seen.add(anchor)
            anchors = [Anchor("declared", [a], [], 0) for a in sorted(seen)]
        elif path.suffix.lower() in MARKDOWN:
            anchors = markdown_anchors(path.read_bytes().decode(
                "utf-8", errors="replace"))
        else:
            out.append("%s: %s is not Markdown and declares no anchors; "
                       "the tool cannot read its elements" % (where, name))
            anchors = []
        for field in ("cover", "prohibits"):
            if strings(entry.get(field)) is None:
                out.append("%s: %s is not a list" % (where, field))
        models[ident] = {"entry": entry, "anchors": anchors,
                         "declared": declared is not None, "file": name}
    for ident, model in models.items():
        model["banned"], wrong = banned(ident, model)
        out += ["%s: model %s: %s" % (CONFIG, ident, w) for w in wrong]
    return models, out


# ----------------------------------------------------------------- terms


def merged(modules) -> "rdflib.Graph":
    import rdflib

    graph = rdflib.Graph()
    for module in modules:
        graph.parse(str(module), format="turtle")
    return graph


def authored_terms(graph, namespace: str) -> list[str]:
    import rdflib

    out = set()
    for kind in TERM_KINDS:
        for s in graph.subjects(rdflib.RDF.type, rdflib.URIRef(OWL + kind)):
            if isinstance(s, rdflib.URIRef) and str(s).startswith(namespace):
                out.add(str(s))
    return sorted(out)


def declared_terms(graph, namespace: str) -> set[str]:
    import rdflib

    return {str(s) for s in graph.subjects(rdflib.RDF.type, None)
            if isinstance(s, rdflib.URIRef) and str(s).startswith(namespace)}


def expand(value: str, namespace: str, prefix: str) -> str:
    if value.startswith(prefix + ":"):
        return namespace + value[len(prefix) + 1:]
    return value


def shape_iris(shapes) -> set[str]:
    import rdflib

    out = set()
    for path in shapes:
        graph = rdflib.Graph()
        graph.parse(str(path), format="turtle")
        for kind in ("NodeShape", "PropertyShape"):
            out |= {str(s) for s in graph.subjects(
                rdflib.RDF.type, rdflib.URIRef(SH + kind))
                if isinstance(s, rdflib.URIRef)}
    return out


def question(root: Path, ident: str):
    import yaml

    path = root / QUESTIONS / ("%s.yaml" % ident)
    if not QUESTION_ID.match(ident) or not path.is_file():
        return None
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return {}


# ------------------------------------------------------- axiom digests


def is_axiom(predicate) -> bool:
    name = str(predicate)
    if name == DEFINITION:
        return True
    if name in NOT_AXIOMS:
        return False
    return name.startswith((RDF, RDFS, OWL))


def list_items(graph, node) -> list:
    import rdflib

    items, seen = [], set()
    while node != rdflib.RDF.nil and node not in seen:
        seen.add(node)
        first = graph.value(node, rdflib.RDF.first)
        if first is None:
            break
        items.append(first)
        node = graph.value(node, rdflib.RDF.rest)
        if node is None:
            break
    return items


def copy_node(graph, node, out, done: set):
    """Every triple of a blank node and the structures it reaches into
    out, with a set-valued list kept as members."""
    import rdflib

    if not isinstance(node, rdflib.BNode) or node in done:
        return
    done.add(node)
    for p, o in graph.predicate_objects(node):
        add(graph, node, p, o, out, done)


def add(graph, s, p, o, out, done: set):
    import rdflib

    if str(p) in SET_LISTS and isinstance(o, rdflib.BNode):
        members = rdflib.BNode()
        out.add((s, p, members))
        for item in list_items(graph, o):
            out.add((members, rdflib.URIRef(MEMBER), item))
            copy_node(graph, item, out, done)
        return
    out.add((s, p, o))
    copy_node(graph, o, out, done)


def axioms_of(graph, iris) -> "rdflib.Graph":
    """The asserted axioms about these terms (the module docstring)."""
    import rdflib

    out, done = rdflib.Graph(), set()
    terms = {rdflib.URIRef(i) for i in iris}
    for term in sorted(terms):
        for p, o in graph.predicate_objects(term):
            if is_axiom(p):
                add(graph, term, p, o, out, done)
        for s, p in graph.subject_predicates(term):
            if str(p) in SYMMETRIC and isinstance(s, rdflib.URIRef):
                out.add((s, p, term))
    referenced = set(graph.objects())
    roots = [b for b in set(graph.subjects()) if isinstance(b, rdflib.BNode)
             and b not in referenced
             and (b, rdflib.RDF.type, rdflib.URIRef(OWL + "Axiom"))
             not in graph]
    for node in sorted(roots, key=str):
        piece, seen = rdflib.Graph(), set()
        copy_node(graph, node, piece, seen)
        if any(t in terms for triple in piece for t in triple):
            for triple in piece:
                out.add(triple)
    return out


def digest(graph) -> str:
    from rdflib.compare import to_canonical_graph

    canonical = to_canonical_graph(graph)
    lines = sorted("%s %s %s ." % (s.n3(), p.n3(), o.n3())
                   for s, p, o in canonical)
    return hashlib.sha256(("\n".join(lines) + "\n").encode("utf-8")) \
        .hexdigest()


def axiom_digest(graph, iris) -> str:
    return digest(axioms_of(graph, iris))


# ---------------------------------------------------------------- rows


def row_problems(root: Path, raw: dict, settings: dict, models: dict,
                 context: dict) -> tuple[list[dict], list[str]]:
    """Each row as read, its references resolved, and what is wrong."""
    out, rows = [], []
    unknown = sorted(set(raw) - TOP_FIELDS)
    if unknown:
        out.append("%s has unknown field(s): %s"
                   % (TRACE, ", ".join(map(str, unknown))))
    pinned = raw.get("models") or {}
    if not isinstance(pinned, dict):
        out.append("%s: models is not a mapping of model id to sha256"
                   % TRACE)
        pinned = {}
    for ident, value in pinned.items():
        if ident not in models:
            out.append("%s: models pins %s, which %s does not register"
                       % (TRACE, ident, CONFIG))
        elif not SHA256.match(text_of(value)):
            out.append("%s: models.%s is not 64 lowercase hex digits"
                       % (TRACE, ident))
    upstream = raw.get("upstream_sha256")
    if upstream is not None and not SHA256.match(text_of(upstream)):
        out.append("%s: upstream_sha256 is not 64 lowercase hex digits"
                   % TRACE)
    entries = raw.get("rows") or []
    if not isinstance(entries, list):
        return [], out + ["%s: rows is not a list" % TRACE]
    review_kinds = context["kinds"]
    for number, row in enumerate(entries, 1):
        where = "%s: row %d" % (TRACE, number)
        if not isinstance(row, dict):
            out.append("%s is not a mapping" % where)
            continue
        unknown = sorted(set(row) - ROW_FIELDS)
        if unknown:
            out.append("%s has unknown field(s): %s"
                       % (where, ", ".join(map(str, unknown))))
        read = {"number": number, "anchors": [], "models": set(),
                "terms": [], "fidelity": row.get("fidelity"),
                "axioms_sha256": text_of(row.get("axioms_sha256")),
                "references": []}
        references = strings(row.get("elements"))
        if not references:
            out.append("%s names no elements" % where)
            references = []
        prohibited = False
        for reference in references:
            ident, sep, anchor = reference.partition("#")
            if not sep or not anchor:
                out.append("%s: %s is not <model id>#<anchor>"
                           % (where, reference))
                continue
            if ident not in models:
                out.append("%s: %s names model %s, which %s does not "
                           "register" % (where, reference, ident, CONFIG))
                continue
            found = resolve(models[ident]["anchors"], anchor)
            if not found:
                out.append("%s: %s names nothing in %s"
                           % (where, reference, models[ident]["file"]))
                continue
            if len(found) > 1:
                out.append("%s: %s names %d places in %s (lines %s); "
                           "qualify it with the headings that enclose it"
                           % (where, reference, len(found),
                              models[ident]["file"],
                              ", ".join(str(a.line) for a in found)))
                continue
            read["anchors"].append((ident, found[0]))
            read["models"].add(ident)
            read["references"].append(reference)
            if found[0] in models[ident]["banned"]:
                prohibited = True
        for ident in sorted(read["models"] - set(pinned)):
            out.append("%s traces %s, whose digest %s does not pin "
                       "(models); tools/fidelity.py --pins prints it"
                       % (where, ident, TRACE))
        targets = row.get("formalized_as") or {}
        if not isinstance(targets, dict):
            out.append("%s: formalized_as is not a mapping" % where)
            targets = {}
        unknown = sorted(set(targets) - set(TARGET_FIELDS))
        if unknown:
            out.append("%s: formalized_as has unknown field(s): %s"
                       % (where, ", ".join(map(str, unknown))))
        lists = {}
        for field in TARGET_FIELDS:
            lists[field] = strings(targets.get(field))
            if lists[field] is None:
                out.append("%s: formalized_as.%s is not a list"
                           % (where, field))
                lists[field] = []
        for value in lists["terms"]:
            iri = expand(value, context["namespace"], context["prefix"])
            if not iri.startswith(context["namespace"]):
                out.append("%s: %s is not in the authored namespace %s; "
                           "an imported term has no model element"
                           % (where, value, context["namespace"]))
            elif iri not in context["declared"]:
                out.append("%s: %s is declared in no authored module"
                           % (where, value))
            else:
                read["terms"].append(iri)
        for value in lists["shapes"]:
            iri = expand(value, context["namespace"], context["prefix"])
            if iri not in context["shapes"]:
                out.append("%s: %s is not a shape any shape set declares"
                           % (where, value))
        for value in lists["questions"]:
            if question(root, value) is None:
                out.append("%s: %s is not a competency question in %s/"
                           % (where, value, QUESTIONS))
        fidelity = row.get("fidelity")
        if fidelity not in FIDELITY:
            out.append("%s: fidelity %r is not one of %s"
                       % (where, fidelity, ", ".join(FIDELITY)))
        if fidelity == "not-formalized" and lists["terms"]:
            out.append("%s is not-formalized and names terms; "
                       "not-formalized means not represented in OWL"
                       % where)
        if fidelity in ("preserves", "changes") and not any(lists.values()):
            out.append("%s is %s and names nothing that formalizes it"
                       % (where, fidelity))
        decision = text_of(row.get("decision"))
        if decision:
            if decision not in context["records"] or \
                    decision not in context["known"]:
                out.append("%s: decision %s is not a tracked decision "
                           "record (config/decisions.yaml records)"
                           % (where, decision))
            else:
                text = (root / decision).read_text(encoding="utf-8",
                                                   errors="replace")
                missing = [r for r in references
                           if not decisions.cites(text, r)]
                if missing:
                    out.append("%s: decision %s does not cite %s; it "
                               "references every element it authorizes "
                               "(P7's citation)" % (where, decision,
                                                    ", ".join(missing)))
        elif fidelity in NEEDS_DECISION:
            out.append("%s is %s and names no decision; a departure from "
                       "the model is the architect's, recorded"
                       % (where, fidelity))
        reviewer = text_of(row.get("reviewed_by"))
        match = findings.CLASSIFIED_BY.match(reviewer)
        if reviewer and not match:
            out.append("%s: reviewed_by %r is not '<name> (<kind>)'"
                       % (where, reviewer))
        elif match and match.group("kind") not in context["reviewers"]:
            out.append("%s: reviewed_by names the kind %s; %s allows %s"
                       % (where, match.group("kind"), CONFIG,
                          ", ".join(sorted(context["reviewers"]))))
        elif fidelity == "preserves" and not reviewer:
            out.append("%s is preserves and names no reviewer; a claim "
                       "that meaning is kept is signed" % where)
        if match and match.group("kind") not in review_kinds:
            out.append("%s: %s is not a kind config/review.yaml declares"
                       % (where, match.group("kind")))
        stated = row.get("axioms_sha256")
        if lists["terms"] and stated is None:
            out.append("%s names terms and no axioms_sha256; "
                       "tools/fidelity.py --digest prints it" % where)
        elif stated is not None and not SHA256.match(text_of(stated)):
            out.append("%s: axioms_sha256 is not 64 lowercase hex digits"
                       % where)
        elif stated is not None and not lists["terms"]:
            out.append("%s gives axioms_sha256 and names no term" % where)
        guards = strings(row.get("guards"))
        if guards is None:
            out.append("%s: guards is not a list" % where)
            guards = []
        for guard in guards:
            if QUESTION_ID.match(guard):
                found = question(root, guard)
                if found is None:
                    out.append("%s: guard %s is not a competency question"
                               % (where, guard))
                elif found.get("status") != "answerable":
                    out.append("%s: guard %s is %s, so "
                               "tools/ontology/competency.py does not run "
                               "it" % (where, guard, found.get("status")))
            elif expand(guard, context["namespace"],
                        context["prefix"]) not in context["shapes"]:
                out.append("%s: guard %s is neither a competency question "
                           "nor a shape any shape set declares"
                           % (where, guard))
        reason = text_of(row.get("no_guard"))
        if guards and reason:
            out.append("%s names guards and says why it has none" % where)
        if prohibited and not guards and not reason:
            out.append("%s traces an element that prohibits an inference, "
                       "and names no guard, nor why it has none (no_guard)"
                       % where)
        rows.append(read)
    if upstream is None and any(r["terms"] for r in rows):
        out.append("%s: rows name terms and upstream_sha256 is not set; "
                   "tools/fidelity.py --pins prints it" % TRACE)
    return rows, out


# ------------------------------------------------------------- the debt


def baseline(root: Path, settings: dict) -> str | None:
    """The adoption snapshot: baseline_commit, or else the last commit
    before required_from; None if the history cannot say which."""
    commit = text_of(settings["baseline_commit"])
    if commit:
        present = git(root, "cat-file", "-e", commit + "^{commit}")
        return commit if present.returncode == 0 else None
    found = git(root, "rev-list", "-1", "--before=%s 00:00:00"
                % settings["required_from"].isoformat(), "HEAD")
    shallow = git(root, "rev-parse", "--is-shallow-repository") \
        .stdout.strip() == "true"
    if found.returncode or not found.stdout.strip():
        return None if shallow else ""
    return found.stdout.strip()


def predating(root: Path, settings: dict, terms: list[str], modules,
              namespace: str) -> tuple[set, set]:
    """(terms that predate adoption, terms whose age cannot be told).
    A term predates adoption when the authored modules, by their current
    paths, declared it at the adoption snapshot."""
    import rdflib

    if settings["required_from"] is None or not terms:
        return set(), set()
    snapshot = baseline(root, settings)
    if snapshot is None:
        return set(), set(terms)
    if snapshot == "":
        return set(), set()                   # no commit before adoption
    graph = rdflib.Graph()
    for module in modules:
        name = Path(module).resolve().relative_to(root.resolve()).as_posix()
        shown = git(root, "show", "%s:%s" % (snapshot, name))
        if shown.returncode == 0:
            graph.parse(data=shown.stdout, format="turtle")
    then = declared_terms(graph, namespace)
    return {t for t in terms if t in then}, set()


def debt_of(models: dict, rows: list[dict], terms: list[str], pins: dict,
            now: dict, old: set, unsure: set) -> list[dict]:
    out = []
    named = {t for r in rows for t in r["terms"]}
    for term in terms:
        if term in named:
            continue
        if term in unsure:
            out.append({"kind": "uncertain", "item": term,
                        "why": "no row names it, and whether it predates "
                               "adoption cannot be established"})
        elif term not in old:
            out.append({"kind": "untraced", "item": term,
                        "why": "an authored term no row names"})
    traced = {(m, id(a)) for r in rows for m, a in r["anchors"]}
    for ident, model in sorted(models.items()):
        entry = model["entry"]
        selected = set()
        for pattern in strings(entry.get("cover")) or []:
            selected |= {id(a) for a in model["anchors"]
                         if covered_by(a, pattern)}
        selected |= {id(a) for a in model["banned"]}
        for anchor in model["anchors"]:
            if id(anchor) in selected and (ident, id(anchor)) not in traced:
                out.append({"kind": "untraced",
                            "item": reference_for(model["anchors"], anchor,
                                                  ident),
                            "why": "a covered element no row names"})
    for row in rows:
        moved = sorted(m for m in row["models"]
                       if pins.get(m) and pins[m] != now["models"].get(m))
        if moved:
            out.append({"kind": "stale", "item": "row %d" % row["number"],
                        "why": "%s changed since its review"
                               % ", ".join(moved)})
        if row["terms"] and now["upstream_pinned"] and \
                now["upstream_pinned"] != now["upstream"]:
            out.append({"kind": "stale", "item": "row %d" % row["number"],
                        "why": "the pinned upstream context changed since "
                               "its review"})
        if row["terms"] and row["axioms_sha256"] and \
                row["axioms_sha256"] != now["axioms"][row["number"]]:
            out.append({"kind": "stale", "item": "row %d" % row["number"],
                        "why": "the axioms of %s changed since its review"
                               % ", ".join(row["terms"])})
    return out


def tally(models: dict, rows: list[dict]) -> dict:
    """Decision 42's counts: elements traced, untraced, not formalized,
    preserving, changed."""
    by = {f: set() for f in FIDELITY}
    for row in rows:
        if row["fidelity"] in by:
            by[row["fidelity"]] |= {(m, id(a)) for m, a in row["anchors"]}
    traced = set().union(*by.values()) if by else set()
    covered = set()
    for ident, model in models.items():
        for pattern in strings(model["entry"].get("cover")) or []:
            covered |= {(ident, id(a)) for a in model["anchors"]
                        if covered_by(a, pattern)}
    return {"covered": len(covered), "traced": len(traced),
            "untraced_covered": len(covered - traced),
            "not_formalized": len(by["not-formalized"]),
            "preserves": len(by["preserves"]), "changes": len(by["changes"]),
            "rows": len(rows),
            "declared_models": sorted(i for i, m in models.items()
                                      if m["declared"])}


# ----------------------------------------------------------- where held


def stage_problems(stages: list[dict], debt: list[dict],
                   stage: str) -> list[str]:
    """The stage gate: the stage named in config/fidelity.yaml, marked
    done, holds every piece of applicable debt."""
    out = []
    for entry in stages:
        if entry.get("id") != stage or entry.get("status") != "done" or \
                entry.get("runs") is not True:
            continue
        for item in debt:
            out.append("%s: is done, but conceptual fidelity is owed: %s %s "
                       "(%s)" % (stage, item["kind"], item["item"],
                                 item["why"]))
    return out


def release_problems(debt: list[dict]) -> list[str]:
    return ["%s %s (%s)" % (d["kind"], d["item"], d["why"]) for d in debt]


# ----------------------------------------------------------------- main


def status_of(root: Path, settings: dict, records: set, known: set,
              problems: list) -> str:
    applicable = settings["applicable"]
    if applicable is False:
        decided = text_of(settings["decided_by"])
        if not decided or decided not in records or decided not in known:
            problems.append("%s: applicable is false, and decided_by %r is "
                            "not a tracked decision record; that fidelity "
                            "does not apply is a recorded decision"
                            % (CONFIG, decided or None))
        if settings["models"]:
            problems.append("%s: applicable is false and models are "
                            "registered" % CONFIG)
        return "not-applicable"
    if applicable not in (None, True):
        problems.append("%s: applicable %r is not null, true or false"
                        % (CONFIG, applicable))
    if settings["decided_by"] is not None:
        problems.append("%s: decided_by is set and applicable is not false"
                        % CONFIG)
    return "applicable" if settings["models"] else "not-established"


def check(root: Path | None = None, modules=None, shapes=None,
          namespace: str | None = None, prefix: str | None = None) -> dict:
    root = root or layout.repository_root()
    settings = configuration(root)
    raw = trace(root)
    known = tracked(root)
    records = set(decisions.records(root, decisions.configuration(root)))
    problems: list[str] = []
    status = status_of(root, settings, records, known, problems)
    kinds = set(findings.review_kinds(root))
    reviewers = strings(settings["reviewers"])
    if reviewers is None:
        problems.append("%s: reviewers is not a list of kinds" % CONFIG)
        reviewers = []
    for kind in reviewers:
        if kind not in kinds:
            problems.append("%s: reviewer kind %s is not a kind "
                            "config/review.yaml declares" % (CONFIG, kind))
    commit = settings["baseline_commit"]
    if commit is not None and not COMMIT.match(text_of(commit)):
        problems.append("%s: baseline_commit is not 40 lowercase hex digits"
                        % CONFIG)
    if commit is not None and settings["required_from"] is None:
        problems.append("%s: baseline_commit is set and required_from is "
                        "not" % CONFIG)
    result = {"status": status, "problems": problems, "debt": [],
              "counts": {}, "stage": settings["stage"]}
    if status != "applicable":
        if raw.get("rows"):
            problems.append("%s has rows and no approved model is "
                            "registered in %s" % (TRACE, CONFIG))
        return result
    modules = list(modules if modules is not None else layout.ontology_files())
    shapes = list(shapes if shapes is not None else
                  [c.resolve() for c in layout.components(
                      "ontology-validation")])
    namespace = namespace or project.namespace()
    prefix = prefix or project.prefix()
    graph = merged(modules)
    models, found = model_problems(root, settings, known, records)
    problems += found
    context = {"namespace": namespace, "prefix": prefix,
               "declared": declared_terms(graph, namespace),
               "shapes": shape_iris(shapes), "records": records,
               "known": known, "reviewers": set(reviewers), "kinds": kinds}
    rows, found = row_problems(root, raw, settings, models, context)
    problems += found
    pins = {k: text_of(v) for k, v in (raw.get("models") or {}).items()} \
        if isinstance(raw.get("models"), dict) else {}
    now = {"models": {i: sha256_of(root / m["file"])
                      for i, m in models.items()},
           "upstream": upstream_digest(root),
           "upstream_pinned": text_of(raw.get("upstream_sha256")) or None,
           "axioms": {r["number"]: axiom_digest(graph, r["terms"])
                      for r in rows if r["terms"]}}
    terms = authored_terms(graph, namespace)
    old, unsure = predating(root, settings, terms, modules, namespace)
    result["debt"] = debt_of(models, rows, terms, pins, now, old, unsure)
    result["predating"] = sorted(old)
    result["counts"] = dict(tally(models, rows), terms=len(terms))
    return result


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--digest", nargs="+", metavar="TERM",
                    help="print the axiom digest of these terms, for the "
                         "reviewer to write into the row")
    ap.add_argument("--pins", action="store_true",
                    help="print each model's digest and the upstream "
                         "context's, for the reviewer to write")
    args = ap.parse_args(argv)
    root = layout.repository_root()
    if args.digest or args.pins:
        if args.digest:
            namespace, prefix = project.namespace(), project.prefix()
            graph = merged(layout.ontology_files())
            iris = [expand(t, namespace, prefix) for t in args.digest]
            print("axioms_sha256: %s" % axiom_digest(graph, iris))
        if args.pins:
            for entry in configuration(root)["models"] or []:
                path = root / text_of((entry or {}).get("file"))
                if path.is_file():
                    print("%s: %s" % (entry.get("id"), sha256_of(path)))
            print("upstream_sha256: %s" % upstream_digest(root))
        print("Printed for a person to review and write; nothing was "
              "written.")
        return 0
    result = check(root)
    if args.json:
        print(json.dumps(result, indent=1, default=str))
        return 1 if result["problems"] else 0
    for problem in result["problems"]:
        print("  finding  " + problem)
    status = result["status"]
    if status == "not-applicable":
        print("  Conceptual fidelity: not applicable, by the decision "
              "config/fidelity.yaml names. Nothing was checked.")
    elif status == "not-established":
        print("  Conceptual fidelity: not yet established. No approved "
              "conceptual model is registered in config/fidelity.yaml, so "
              "nothing was traced, and nothing here says fidelity passed.")
    else:
        for item in result["debt"]:
            print("  %-10s %s: %s" % (item["kind"], item["item"],
                                      item["why"]))
        counts = result["counts"]
        print("\n  %d row(s); %d covered element(s), %d traced in all, %d "
              "covered and untraced; %d preserving, %d changed by a "
              "decision, %d not in OWL; %d authored term(s), %d predating "
              "adoption; %d debt item(s)" % (
                  counts["rows"], counts["covered"], counts["traced"],
                  counts["untraced_covered"], counts["preserves"],
                  counts["changes"], counts["not_formalized"],
                  counts["terms"], len(result["predating"]),
                  len(result["debt"])))
        if counts["declared_models"]:
            print("  Anchors declared, not read from the file: "
                  + ", ".join(counts["declared_models"]))
        if result["debt"]:
            print("  Debt fails nothing here; %s marked done, or a "
                  "release, is held for it." % result["stage"])
        print("  `cover` is the architect's selection, not the whole "
              "model. A trace says what was reviewed and decided; it does "
              "not show that the formalization is faithful.")
    return 1 if result["problems"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
