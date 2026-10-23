# SPDX-License-Identifier: MIT
"""Vendor the parts of the pinned upstream ontologies this repository names.

    python tools/ontology/vendor_upstream.py            # offline verify
    python tools/ontology/vendor_upstream.py --rebuild  # fetch and rewrite
    python tools/ontology/vendor_upstream.py --confirm  # fetch and compare

Written in the Application Requirement Ontology and carried through the
Business Capability Ontology, which added three things: the serialiser's
prefixes come from the pins, a source whose artifact states no licence
may name a pinned licence file instead, and a specification is read for
seeds. The template adds: a source may be vendored whole, a source may be
several files at one commit, and every source gets a register.

WHY THIS EXISTS

Shapes ask reachability questions: does this class reach obo:BFO_0000001
through rdfs:subClassOf, does this CCO act reach obo:BFO_0000015. Without
the upstream in scope the chain stops at the first upstream parent and
the answer is "no" for every subject. In ARO that was 202 violations
reported in a voice that sounded like defects in the ontology, and every
one described the scope.

WHAT IS SELECTED

  all       for a source pinned with `select: all`, every term in its
            namespace that its own file describes. BFO is vendored this
            way: it is small, and a realist ontology answers to all of it.

  seeds     every upstream term named by the authored ontology or by
            the shapes, including the ones that appear only inside SPARQL
            text -- a constraint naming a class in a query depends on it
            exactly as much as one naming it as an IRI.

  spec      every upstream term a component with the role
            `specification` names, written as `prefix:local` with a prefix
            from the pins. A weaker kind of seed: a draft specification
            also names terms the project will mint and terms from files
            that are not vendored. So a spec term no pinned file
            describes is recorded in the manifest rather than refused,
            and the record is itself useful -- it is the list of what the
            design cites and nothing here can resolve. A project with no
            specification component has no spec seeds.

  closure   the transitive named ancestors and relatives of those seeds
            along rdfs:subClassOf, rdfs:subPropertyOf, owl:inverseOf,
            rdfs:domain and rdfs:range. This is what gives the shapes a
            chain to walk.

  stubs     any other upstream term mentioned by a copied triple, given a
            type declaration and a label and nothing else. Without this
            the extract would reference terms it does not describe, and
            the check for unresolved vocabulary would still fire -- on
            the extract's own annotations.

THE REGISTER

Beside each extract, a JSON register of every term the source's pinned
files describe in its namespace -- not only the ones selected -- with its
labels, its OWL types and whether it is deprecated. The extract answers
"what does this term reach"; the register answers "is there such a term,
and what is it called", which is what the IRI linter needs to tell a
mistyped opaque id from a readable name and to suggest the right IRI,
offline. It carries the upstream's own labels, so it is the upstream's
content under the upstream's licence, like the extract.

DISJOINTNESS, DERIVED

BFO states the disjointness a realist check leans on hardest --
independent, specifically dependent and generically dependent continuant;
process, process boundary, temporal and spatiotemporal region -- as
owl:AllDisjointClasses, whose members are an RDF list of blank nodes. The
extract drops blank nodes, so without more those axioms are gone, and a
shape refusing a class under two disjoint categories would never see the
commonest case. A source pinned with `disjointness:` therefore gets a
second file: each AllDisjointClasses axiom over vendored terms, written as
the pairwise owl:disjointWith triples it is equivalent to. It is derived,
not copied, and its header says so. An axiom asserted by several pinned
files (CCO's merged file repeats BFO's) is credited to the first whose
namespace holds all its members.

WHAT IS NOT SELECTED, AND WHAT THAT COSTS

Every axiom whose object is a blank node is dropped: OWL restrictions,
equivalent-class expressions, and the domain and range declarations
written as unions. That is a deliberate narrowing and it has a
consequence worth stating plainly, because the failure mode is a check
that certifies more than it proves:

    A reasoner over this repository plus these extracts derives strictly
    less than one over this repository plus the full upstream. It cannot
    be used to claim the ontology is consistent with the upstream. It
    supports the subClassOf reachability the shapes ask about, and that
    is the claim these files are good for.

The count of dropped axioms is recorded in the manifest rather than
described here, so the size of the omission is a number that moves.

DETERMINISM

The serialiser is written out here rather than delegated, because the
extract's byte digest is recorded and a serialiser that reorders or
re-escapes between library versions would make that digest a measurement
of the library. Triples are sorted, blank nodes are absent by
construction, and literals are escaped by a function in this file. The
round trip is checked on every build: the emitted text is parsed back and
required to carry the same triples that went in.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import layout  # noqa: E402
import project  # noqa: E402

FORMAT_VERSION = 1
GENERATOR = "tools/ontology/vendor_upstream.py"
PINS = "config/upstream-sources.yaml"
MANIFEST = "config/upstream-extracts.json"
NOTICE = "vendor/NOTICE.md"
CACHE = ".upstream-cache"

RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
OWL = "http://www.w3.org/2002/07/owl#"
DCTERMS = "http://purl.org/dc/terms/"
SKOS = "http://www.w3.org/2004/02/skos/core#"

#: Edges the closure follows. These are the ones a shape can walk or a
#: reader needs in order to place a term; annotation predicates are
#: copied but not followed, or the closure would be the whole ontology.
STRUCTURAL = (
    RDFS + "subClassOf", RDFS + "subPropertyOf", OWL + "inverseOf",
    RDFS + "domain", RDFS + "range",
)

#: Copied for a stub term. A stub says what kind of thing it is and what
#: it is called, which is enough for the reference to resolve and not
#: enough to imply the extract describes it.
STUB_PREDICATES = (RDF + "type", RDFS + "label")

#: The W3C prefixes. The upstream ones are read from the pins, so a new
#: source cannot be vendored with its IRIs written out longhand because
#: somebody forgot to add a line here.
BASE_PREFIXES = (
    ("rdf", RDF), ("rdfs", RDFS), ("owl", OWL), ("skos", SKOS),
    ("dcterms", DCTERMS),
    ("xsd", "http://www.w3.org/2001/XMLSchema#"),
)

#: How much of a source is vendored. `named`: the terms this repository
#: names and their structural ancestry. `all`: every term the source's own
#: file describes in its namespace.
SELECT_MODES = ("named", "all")


def extract_base() -> str:
    """Where the extracts' own owl:Ontology IRIs live: under the project.

    A function rather than a constant, because it is read from the
    project file, and init changes the project file.
    """
    return project.iri_base() + "/vendor/"

#: The role whose files are read for spec seeds. A role rather than a
#: path, so superseding a specification is a change to the layout
#: contract and the superseded version stops seeding on the same commit.
SPECIFICATION_ROLE = "specification"

_LOCAL = re.compile(r"^[A-Za-z_][A-Za-z0-9_\-]*$")


class Refused(SystemExit):
    """Raised rather than vendoring something unverified."""


# ------------------------------------------------------------- pins


def sources() -> list[dict]:
    import yaml

    root = layout.repository_root()
    raw = yaml.safe_load((root / PINS).read_text(encoding="utf-8")) or {}
    declared = raw.get("sources") or []
    if not declared:
        raise Refused(PINS + " declares no sources")
    for entry in declared:
        for required in ("id", "commit", "namespace", "prefix", "extract",
                         "register", "licence"):
            if not entry.get(required):
                raise Refused("a source in %s declares no %r: %r"
                              % (PINS, required, entry.get("id", entry)))
        entry["files"] = files_of(entry)
        entry.setdefault("disjointness", None)
        entry.setdefault("select", "named")
        if entry["select"] not in SELECT_MODES:
            raise Refused("%s declares select %r; the modes are %s"
                          % (entry["id"], entry["select"],
                             ", ".join(SELECT_MODES)))
        statement = entry["licence"].get("statement_url")
        if statement:
            if entry["commit"] not in statement:
                raise Refused(
                    "%s states its licence in %s, which does not name the "
                    "pinned commit %s -- the licence would be read from "
                    "whatever that url serves today"
                    % (entry["id"], statement, entry["commit"]))
            if not entry["licence"].get("statement_sha256"):
                raise Refused(
                    "%s names a licence statement_url and no "
                    "statement_sha256" % entry["id"])
    prefixes = [entry["prefix"] for entry in declared]
    if len(prefixes) != len(set(prefixes)):
        raise Refused("two sources in %s share a prefix: %s"
                      % (PINS, prefixes))
    return declared


def files_of(entry: dict) -> list[dict]:
    """The pinned files of one source, as [{url, sha256}].

    A source is one file (`url` and `sha256`) or several (`files`, each
    with both) -- never both spellings, because then which one is pinned
    would depend on which this tool read first. Every url must name the
    source's commit, so all of a source's files come from one state of
    its repository.
    """
    single = entry.get("url") or entry.get("sha256")
    listed = entry.get("files")
    if single and listed:
        raise Refused(
            "%s declares both url/sha256 and files; a source is one file or "
            "a list of them" % entry["id"])
    if listed:
        files = [dict(f) for f in listed]
    elif entry.get("url") and entry.get("sha256"):
        files = [{"url": entry["url"], "sha256": entry["sha256"]}]
    else:
        raise Refused("%s declares no url and sha256, and no files"
                      % entry["id"])
    for number, pinned in enumerate(files, 1):
        if not (pinned.get("url") and pinned.get("sha256")):
            raise Refused("%s: file %d declares no url or no sha256"
                          % (entry["id"], number))
        if entry["commit"] not in pinned["url"]:
            raise Refused(
                "%s pins commit %s but its url %s does not name it, so the "
                "url is not pinned to that commit"
                % (entry["id"], entry["commit"], pinned["url"]))
    urls = [f["url"] for f in files]
    if len(urls) != len(set(urls)):
        raise Refused("%s pins the same url twice" % entry["id"])
    return files


def prefixes() -> tuple:
    return BASE_PREFIXES + tuple((entry["prefix"], entry["namespace"])
                                 for entry in sources())


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_pinned(source_id: str, url: str, sha256: str, cache: Path,
                 name: str) -> bytes:
    """Pinned bytes, from the cache or the network, digest checked.

    The url names a commit, so what it serves cannot change. The digest
    is checked anyway: a proxy, a corporate TLS appliance or a partial
    download are all things that produce different bytes from the same
    url, and none of them announce themselves.
    """
    cache.mkdir(parents=True, exist_ok=True)
    local = cache / name
    if local.is_file():
        data = local.read_bytes()
        if sha256_of(data) == sha256:
            return data
        local.unlink()

    with urllib.request.urlopen(url, timeout=180) as response:
        data = response.read()
    got = sha256_of(data)
    if got != sha256:
        raise Refused(
            "%s: %s served %d bytes digesting to %s, but %s pins %s. "
            "Refusing to vendor bytes that are not the pinned ones."
            % (source_id, url, len(data), got, PINS, sha256))
    local.write_bytes(data)
    return data


def cache_name(source: dict, number: int) -> str:
    """`<id>.ttl` for a one-file source -- the name every earlier cache
    used -- and `<id>.<n>.ttl` for each file of a larger one."""
    if len(source["files"]) == 1:
        return source["id"] + ".ttl"
    return "%s.%d.ttl" % (source["id"], number)


def fetch(source: dict, cache: Path) -> list[bytes]:
    """Every pinned file of a source, in pin order, each digest checked."""
    return [fetch_pinned(source["id"], pinned["url"], pinned["sha256"],
                         cache, cache_name(source, number))
            for number, pinned in enumerate(source["files"], 1)]


# --------------------------------------------------------- selection


def seed_terms(namespaces: tuple) -> set:
    """Upstream IRIs the corpus and the shapes name.

    The shapes are read twice, as a graph and as text. A SPARQL
    constraint that filters on cco:ont00001921 mentions that term inside
    a string literal, so a graph-only sweep does not see it and the
    extract would silently omit exactly the terms the constraints run on.
    """
    import rdflib

    found = set()

    def harvest(graph):
        for triple in graph:
            for term in triple:
                if (isinstance(term, rdflib.URIRef)
                        and str(term).startswith(namespaces)):
                    found.add(str(term))

    data = rdflib.Graph()
    for path in layout.ontology_files():
        data.parse(path, format="turtle")
    for entry in layout.components("example-data"):
        for path in entry.members("*.ttl"):
            data.parse(path, format="turtle")
    harvest(data)

    for entry in layout.components("ontology-validation"):
        path = entry.resolve()
        shapes = rdflib.Graph()
        shapes.parse(path, format="turtle")
        harvest(shapes)
        found |= named_in_text(path.read_text(encoding="utf-8"))

    # A competency question names its terms in SPARQL, which is text: the
    # terms it depends on must be vendored for the question to be asked.
    for entry in layout.components("competency-question"):
        for path in entry.members("*.yaml"):
            found |= named_in_text(path.read_text(encoding="utf-8"))
    return found


def named_in_text(text: str) -> set:
    """Upstream IRIs written in text: in full, or as `prefix:local` with a
    pinned prefix. Shape SPARQL and competency queries use prefixed names
    (`obo:BFO_0000001`), which a scan for full IRIs alone misses -- the
    shape scan here did, until competency questions made it matter."""
    found = set()
    for source in sources():
        found.update(re.findall(
            re.escape(source["namespace"]) + r"[A-Za-z0-9_]+", text))
        pattern = (r"(?<![A-Za-z0-9_/#:<])" + re.escape(source["prefix"])
                   + r":([A-Za-z_][A-Za-z0-9_]*)")
        found.update(source["namespace"] + local
                     for local in re.findall(pattern, text))
    return found


def spec_terms() -> set:
    """Upstream IRIs the current specification names.

    The spec is Markdown, so it is read as text: `prefix:local` with a
    prefix from the pins, and full IRIs under a pinned namespace.
    Markdown escapes an underscore as `\\_`, and a name read up to the
    backslash would be a different, shorter name -- so escapes are undone
    first.

    Only components whose role is `specification` are read. The
    superseded v0.3 is `documentation`, so a term it names and v0.4
    dropped does not keep getting vendored.
    """
    declared = sources()
    found = set()
    for entry in layout.components(SPECIFICATION_ROLE):
        text = entry.resolve().read_text(encoding="utf-8")
        text = text.replace(chr(92) + "_", "_")
        for source in declared:
            pattern = (r"(?<![A-Za-z0-9_/#:])" + re.escape(source["prefix"])
                       + r":([A-Za-z_][A-Za-z0-9_]*)")
            found.update(source["namespace"] + local
                         for local in re.findall(pattern, text))
            found.update(re.findall(
                re.escape(source["namespace"]) + r"[A-Za-z0-9_]+", text))
    return found


def recorded_unresolvable_spec_terms() -> set:
    """What the last build recorded as named by the spec and described by
    no pinned file. Offline verification excuses exactly these and
    nothing else."""
    path = layout.repository_root() / MANIFEST
    if not path.is_file():
        return set()
    record = json.loads(path.read_text(encoding="utf-8"))
    return {iri for entry in record.get("extracts", {}).values()
            for iri in entry.get(
                "named_by_specification_described_by_no_pinned_file", [])}


def whole_source_terms(declared: list, per_source: dict) -> set:
    """Every term a `select: all` source describes in its own namespace.

    Read from that source's own file rather than from the merged
    upstream graph. CCO's merged file carries BFO terms too; asking the
    merged graph would make "all of BFO" mean "all of BFO, plus whatever
    CCO says is in BFO's namespace".

    The source's own owl:Ontology header is not a term, and is left out.
    BFO's (obo:bfo.owl) sits in BFO's namespace, and selecting it put a
    second owl:Ontology into the extract beside the extract's own, along
    with an owl:versionIRI naming a file nothing describes -- which the
    offline check then reported as a dangling reference.
    """
    import rdflib

    ontology = rdflib.URIRef(OWL + "Ontology")
    found = set()
    for entry in declared:
        if entry["select"] != "all":
            continue
        graph = per_source[entry["id"]]
        mine = {str(subject) for subject in graph.subjects()
                if isinstance(subject, rdflib.URIRef)
                and str(subject).startswith(entry["namespace"])
                and (subject, rdflib.RDF.type, ontology) not in graph}
        if not mine:
            raise Refused(
                "%s is pinned with select: all and its file describes no "
                "term in %s, so the namespace or the pin is wrong"
                % (entry["id"], entry["namespace"]))
        found |= mine
    return found


def select(upstream, seeds: set, namespaces: tuple):
    """Seeds, their structural closure, and the stubs that follow.

    Returns (full, stubs, dropped) where `full` are terms whose ground
    description is copied whole and `stubs` are terms mentioned by those
    descriptions and given a declaration only.
    """
    import rdflib

    def is_upstream(term):
        return (isinstance(term, rdflib.URIRef)
                and str(term).startswith(namespaces))

    described = {s for s in seeds
                 if list(upstream.predicate_objects(rdflib.URIRef(s)))}
    undescribed = sorted(seeds - described)
    if undescribed:
        raise Refused(
            "%d term(s) are referenced here but described by no pinned "
            "upstream, so vendoring cannot resolve them:\n  %s"
            % (len(undescribed), "\n  ".join(undescribed)))

    full = set(described)
    frontier = set(full)
    while frontier:
        nxt = set()
        for iri in frontier:
            subject = rdflib.URIRef(iri)
            for predicate in STRUCTURAL:
                for obj in upstream.objects(subject,
                                            rdflib.URIRef(predicate)):
                    if is_upstream(obj) and str(obj) not in full:
                        nxt.add(str(obj))
            for other in upstream.subjects(rdflib.URIRef(OWL + "inverseOf"),
                                           subject):
                if is_upstream(other) and str(other) not in full:
                    nxt.add(str(other))
        full |= nxt
        frontier = nxt

    dropped = 0
    mentioned = set()
    for iri in full:
        for predicate, obj in upstream.predicate_objects(rdflib.URIRef(iri)):
            if isinstance(obj, rdflib.BNode):
                dropped += 1
                continue
            for term in (predicate, obj):
                if is_upstream(term):
                    mentioned.add(str(term))

    return full, sorted(mentioned - full), dropped


def triples_for(upstream, full: set, stubs: list) -> list:
    """Ground triples only. Blank nodes are dropped, and counted above."""
    import rdflib

    out = []
    for iri in sorted(full):
        subject = rdflib.URIRef(iri)
        for predicate, obj in upstream.predicate_objects(subject):
            if isinstance(obj, rdflib.BNode):
                continue
            out.append((subject, predicate, obj))
    for iri in stubs:
        subject = rdflib.URIRef(iri)
        for predicate in STUB_PREDICATES:
            for obj in upstream.objects(subject, rdflib.URIRef(predicate)):
                if not isinstance(obj, rdflib.BNode):
                    out.append((subject, rdflib.URIRef(predicate), obj))
    return out


# ------------------------------------------------------- serialising


def qname(iri: str) -> str:
    for prefix, namespace in prefixes():
        if iri.startswith(namespace):
            local = iri[len(namespace):]
            if _LOCAL.match(local):
                return prefix + ":" + local
    return "<" + iri + ">"


def escape(text: str) -> str:
    """Turtle string escaping, written here rather than borrowed.

    The extract's digest is recorded, so the escaping has to be a
    property of this file and not of whichever rdflib is installed. Every
    literal is emitted on one line in the short form; a newline inside a
    definition becomes a backslash-n rather than a triple-quoted block.
    """
    out = text.replace(chr(92), chr(92) * 2).replace('"', chr(92) + '"')
    return (out.replace(chr(13), chr(92) + "r")
               .replace(chr(10), chr(92) + "n")
               .replace(chr(9), chr(92) + "t"))


def term_text(term) -> str:
    import rdflib

    if isinstance(term, rdflib.URIRef):
        return qname(str(term))
    if isinstance(term, rdflib.Literal):
        body = '"' + escape(str(term)) + '"'
        if term.language:
            return body + "@" + term.language
        if term.datatype:
            return body + "^^" + qname(str(term.datatype))
        return body
    raise Refused("a blank node reached the serialiser: %r" % (term,))


def serialise(triples: list, header: list) -> str:
    lines = ["# " + line if line else "#" for line in header]
    lines.append("")
    for prefix, namespace in prefixes():
        lines.append("@prefix %-8s <%s> ." % (prefix + ":", namespace))
    lines.append("")

    rows = sorted({(term_text(s), term_text(p), term_text(o))
                   for s, p, o in triples})
    current = None
    for subject, predicate, obj in rows:
        if subject != current:
            if current is not None:
                lines.append("")
            current = subject
        lines.append("%s %s %s ." % (subject, predicate, obj))
    return chr(10).join(lines) + chr(10)


def sortable(obj) -> str:
    import rdflib

    if isinstance(obj, rdflib.Literal):
        return "L%s|%s|%s" % (obj.language or "", obj.datatype or "", obj)
    return str(obj)


def round_trip(text: str, triples: list) -> None:
    """The emitted file must carry the triples that went into it."""
    import rdflib

    back = rdflib.Graph()
    back.parse(data=text, format="turtle")
    want = {(str(s), str(p), sortable(o)) for s, p, o in triples}
    got = {(str(s), str(p), sortable(o)) for s, p, o in back}
    if want != got:
        missing = sorted(want - got)[:3]
        extra = sorted(got - want)[:3]
        raise Refused(
            "the serialised extract does not reparse to what was "
            "selected: %d missing, %d unexpected. e.g. missing %r, "
            "unexpected %r" % (len(want - got), len(got - want),
                               missing, extra))


# ------------------------------------------------------------ header


def licence_as_stated(upstream, source: dict, cache: Path) -> str:
    """What the source itself says its licence is.

    The SPDX identifier in the pins file is a claim by whoever wrote it.
    This is the same claim checked against the artifact: the substring
    the pin declares must appear in the upstream's own dcterms:license.

    Some sources state no licence in their Turtle (the Business Process
    Ontology is one); their repository's LICENSE does. A
    source may therefore name `statement_url` -- a file at the same
    pinned commit, digest-checked like the ontology itself -- and the
    substring is required there instead. It is never both and never
    neither: a source with a statement_url is not also allowed to fall
    back to a dcterms:license that says something else.
    """
    import rdflib

    licence = source["licence"]
    needle = licence["licence_statement_contains"]
    if licence.get("statement_url"):
        text = fetch_pinned(source["id"], licence["statement_url"],
                            licence["statement_sha256"], cache,
                            source["id"] + ".licence").decode("utf-8")
        lines = [line.strip() for line in text.splitlines()
                 if needle in line]
        if not lines:
            raise Refused(
                "%s: %s does not contain %r, which %s declares. Refusing "
                "to vendor under a licence the source does not state."
                % (source["id"], licence["statement_url"], needle, PINS))
        return "%s (%s)" % (lines[0], licence["statement_url"])

    predicate = rdflib.URIRef(DCTERMS + "license")
    stated = sorted({str(o) for _s, o in upstream.subject_objects(predicate)})
    matching = [value for value in stated if needle in value]
    if not matching:
        raise Refused(
            "%s: the pinned source states its licence as %s, and none of "
            "those contains %r, which %s declares. Refusing to vendor "
            "under a licence the artifact does not state."
            % (source["id"], stated or "nothing", needle, PINS))
    return matching[0]


def header_lines(source: dict, stated: str, counts: dict) -> list:
    licence = source["licence"]
    return [
        "Generated by %s -- do not edit." % GENERATOR,
        "",
        "A partial extract of %s, pinned." % source["project"],
        "",
        "  release     %s" % source["release"],
        "  commit      %s" % source["commit"],
    ] + [line for pinned in source["files"] for line in (
        "  source      %s" % pinned["url"],
        "  sha256      %s" % pinned["sha256"],
    )] + [
        "  licence     %s (%s)" % (licence["spdx"], licence["url"]),
        "  as stated   %s" % stated,
        "",
        licence["attribution"].strip(),
        "",
        "This is not %s. It carries %d terms described in full and %d"
        % (source["project"], counts["full"], counts["stubs"]),
        "declared as stubs, selected because this repository names them or",
        "because a selected term's ancestry passes through them.",
        "",
        "%d axioms about the selected terms were dropped: every one whose"
        % counts["dropped"],
        "object is an anonymous class expression. A reasoner over this file",
        "therefore derives less than one over the upstream, and it cannot be",
        "used to claim consistency with %s." % source["project"],
    ]


def ontology_triples(source: dict, stated: str, counts: dict) -> list:
    import rdflib

    iri = rdflib.URIRef(extract_base() + Path(source["extract"]).stem)
    licence = source["licence"]
    return [
        (iri, rdflib.URIRef(RDF + "type"), rdflib.URIRef(OWL + "Ontology")),
        (iri, rdflib.URIRef(OWL + "versionInfo"),
         rdflib.Literal("%s %s, partial extract for %s"
                        % (source["project"], source["release"],
                           project.load()["title"]), lang="en")),
    ] + [
        (iri, rdflib.URIRef(DCTERMS + "source"), rdflib.URIRef(pinned["url"]))
        for pinned in source["files"]
    ] + [
        (iri, rdflib.URIRef(DCTERMS + "license"),
         rdflib.URIRef(licence["url"])),
        (iri, rdflib.URIRef(RDFS + "comment"),
         rdflib.Literal(
             "Partial extract, not the upstream ontology. %d axioms whose "
             "object is an anonymous class expression were dropped, so a "
             "reasoner over this file derives less than one over %s and "
             "cannot be used to claim consistency with it. Upstream "
             "licence as stated by the source: %s"
             % (counts["dropped"], source["project"], stated), lang="en")),
        (rdflib.URIRef(DCTERMS + "source"), rdflib.URIRef(RDF + "type"),
         rdflib.URIRef(OWL + "AnnotationProperty")),
        (rdflib.URIRef(DCTERMS + "license"), rdflib.URIRef(RDF + "type"),
         rdflib.URIRef(OWL + "AnnotationProperty")),
    ]


# ------------------------------------------------------------- build


def build(cache: Path) -> dict:
    import rdflib

    declared = sources()
    namespaces = tuple(entry["namespace"] for entry in declared)

    upstream = rdflib.Graph()
    per_source = {}
    for entry in declared:
        graph = rdflib.Graph()
        for data in fetch(entry, cache):
            graph.parse(data=data.decode("utf-8"), format="turtle")
        per_source[entry["id"]] = graph
        for triple in graph:
            upstream.add(triple)

    strict = seed_terms(namespaces)
    whole = whole_source_terms(declared, per_source)
    spec = spec_terms()
    spec_described = {iri for iri in spec
                      if list(upstream.predicate_objects(rdflib.URIRef(iri)))}
    spec_unresolved = spec - spec_described
    seeds = strict | spec_described | whole
    full, stubs, dropped = select(upstream, seeds, namespaces)
    selected = triples_for(upstream, full, stubs)

    def owner(triple) -> str:
        """The source a selected triple is attributed to.

        By subject namespace when that source's own file asserts it, and
        otherwise by the file that does. ARO partitioned by subject
        namespace alone, and CCO's merged file carries its own
        annotations on BFO terms: four skos:scopeNote triples present
        only in CCO were written into the BFO extract, under BFO's
        licence and attribution, with a header naming bfo-core.ttl as
        their source. Measured 2026-10-23 against these pins.
        """
        for entry in declared:
            if (str(triple[0]).startswith(entry["namespace"])
                    and triple in per_source[entry["id"]]):
                return entry["id"]
        for entry in declared:
            if triple in per_source[entry["id"]]:
                return entry["id"]
        raise Refused("a selected triple is asserted by no pinned source: "
                      "%r" % (triple,))

    owners = {triple: owner(triple) for triple in selected}
    groups = disjoint_groups(declared, per_source, full)

    built = {}
    for entry in declared:
        namespace = entry["namespace"]
        mine = [t for t in selected if owners[t] == entry["id"]]
        my_full = sorted(i for i in full if i.startswith(namespace))
        my_stubs = sorted(i for i in stubs if i.startswith(namespace))
        my_dropped = sum(
            1 for iri in my_full
            for _p, o in upstream.predicate_objects(rdflib.URIRef(iri))
            if isinstance(o, rdflib.BNode))
        counts = {"full": len(my_full), "stubs": len(my_stubs),
                  "dropped": my_dropped}
        stated = licence_as_stated(per_source[entry["id"]], entry, cache)
        mine = mine + ontology_triples(entry, stated, counts)
        text = serialise(mine, header_lines(entry, stated, counts))
        round_trip(text, mine)
        register = register_of(entry, per_source[entry["id"]], stated)
        mine_groups = groups.get(entry["id"], [])
        if mine_groups and not entry["disjointness"]:
            raise Refused(
                "%s asserts %d owl:AllDisjointClasses axiom(s) over vendored "
                "terms and declares no `disjointness:` file to derive them "
                "into; without it the extract silently loses them"
                % (entry["id"], len(mine_groups)))
        disjointness = (disjointness_text(entry, stated, mine_groups)
                        if entry["disjointness"] else None)
        built[entry["id"]] = {
            "source": entry,
            "disjointness_text": disjointness,
            "disjointness_axioms": len(mine_groups),
            "disjointness_pairs": sum(len(g) * (len(g) - 1) // 2
                                      for g in mine_groups),
            "text": text,
            "register_text": register_bytes(register).decode("utf-8"),
            "register_terms": len(register["terms"]),
            "counts": counts,
            "stated_licence": stated,
            "seeds": sorted(s for s in seeds if s.startswith(namespace)),
            "seeds_from_corpus_and_shapes": sorted(
                s for s in strict if s.startswith(namespace)),
            "select": entry["select"],
            "spec_unresolved": sorted(
                s for s in spec_unresolved if s.startswith(namespace)),
            "triples": len(mine),
        }

    built["_totals"] = {"seeds": len(seeds),
                        "seeds_from_corpus_and_shapes": len(strict),
                        "seeds_from_whole_sources": len(whole),
                        "seeds_from_specification": len(spec_described),
                        "spec_terms_unresolved": len(spec_unresolved),
                        "full": len(full),
                        "stubs": len(stubs), "dropped": dropped}
    return built


# -------------------------------------------------------- disjointness


def disjoint_groups(declared: list, per_source: dict, full: set) -> dict:
    """{source id: [sorted member IRIs, ...]} from owl:AllDisjointClasses.

    Only members vendored here count; an axiom left with fewer than two
    is nothing to say. Each distinct member set is credited once: to the
    first pinned source whose namespace holds every member and whose
    file asserts it, else to the first source that asserts it.
    """
    import rdflib
    from rdflib.collection import Collection

    kind = rdflib.URIRef(OWL + "AllDisjointClasses")
    members_of = rdflib.URIRef(OWL + "members")
    asserted: dict[frozenset, list[str]] = {}
    for entry in declared:
        graph = per_source[entry["id"]]
        for axiom in graph.subjects(rdflib.RDF.type, kind):
            head = graph.value(axiom, members_of)
            if head is None:
                continue
            members = frozenset(str(m) for m in Collection(graph, head)
                                if isinstance(m, rdflib.URIRef)
                                and str(m) in full)
            if len(members) >= 2:
                asserted.setdefault(members, [])
                if entry["id"] not in asserted[members]:
                    asserted[members].append(entry["id"])
    out: dict[str, list] = {}
    order = [entry["id"] for entry in declared]
    namespace = {entry["id"]: entry["namespace"] for entry in declared}
    for members, sources in sorted(asserted.items(),
                                   key=lambda kv: sorted(kv[0])):
        home = [s for s in order if s in sources
                and all(m.startswith(namespace[s]) for m in members)]
        owner = home[0] if home else min(sources, key=order.index)
        out.setdefault(owner, []).append(sorted(members))
    return out


def disjointness_text(source: dict, stated: str, groups: list) -> str:
    import rdflib

    iri = rdflib.URIRef(extract_base() + Path(source["disjointness"]).stem)
    disjoint = rdflib.URIRef(OWL + "disjointWith")
    triples = [
        (iri, rdflib.RDF.type, rdflib.URIRef(OWL + "Ontology")),
        (iri, rdflib.URIRef(RDFS + "comment"), rdflib.Literal(
            "Derived, not copied: the owl:AllDisjointClasses axioms of %s "
            "%s over the terms vendored here, as the pairwise "
            "owl:disjointWith triples each is equivalent to. Upstream "
            "licence as stated by the source: %s"
            % (source["project"], source["release"], stated), lang="en")),
        (iri, rdflib.URIRef(DCTERMS + "license"),
         rdflib.URIRef(source["licence"]["url"])),
        (rdflib.URIRef(DCTERMS + "license"), rdflib.RDF.type,
         rdflib.URIRef(OWL + "AnnotationProperty")),
    ]
    pairs = 0
    for members in groups:
        for i, a in enumerate(members):
            for b in members[i + 1:]:
                triples.append((rdflib.URIRef(a), disjoint, rdflib.URIRef(b)))
                pairs += 1
    header = [
        "Generated by %s -- do not edit." % GENERATOR,
        "",
        "Disjointness DERIVED from %s, pinned." % source["project"],
        "",
        "  release     %s" % source["release"],
        "  commit      %s" % source["commit"],
    ] + ["  source      %s" % pinned["url"] for pinned in source["files"]] + [
        "  licence     %s (%s)" % (source["licence"]["spdx"],
                                   source["licence"]["url"]),
        "",
        source["licence"]["attribution"].strip(),
        "",
        "The source states these as %d owl:AllDisjointClasses axiom(s), whose"
        % len(groups),
        "member lists are blank nodes and so are absent from the extract. Each",
        "is written here as its %d pairwise owl:disjointWith triple(s):" % pairs,
        "AllDisjointClasses(A, B, C) holds exactly when every pair is",
        "disjoint, so this says what the source says, in a form the source",
        "does not use. Only members vendored here are included.",
    ]
    text = serialise(triples, header)
    round_trip(text, triples)
    return text


# ------------------------------------------------------------ register


#: The OWL kinds a register records for a term. Others (rdf:Property,
#: skos:Concept) are recorded too, but these are the ones a linter asks
#: about, so they are what `types` is guaranteed to hold if present.
REGISTER_TYPES = (OWL + "Class", OWL + "ObjectProperty",
                  OWL + "DatatypeProperty", OWL + "AnnotationProperty",
                  OWL + "NamedIndividual")


def register_of(source: dict, graph, stated: str) -> dict:
    """Every term the source's pinned files describe in its namespace.

    The whole source, not the selection: the register is how a linter
    knows that cco:ont00001180 exists and is called "Organization" before
    anything here names it. The source's own owl:Ontology is left out,
    as from a whole-source extract.
    """
    import rdflib

    ontology = rdflib.URIRef(OWL + "Ontology")
    deprecated = rdflib.URIRef(OWL + "deprecated")
    terms = {}
    for subject in set(graph.subjects()):
        if not (isinstance(subject, rdflib.URIRef)
                and str(subject).startswith(source["namespace"])):
            continue
        if (subject, rdflib.RDF.type, ontology) in graph:
            continue
        labels = sorted({(str(o), o.language or "")
                         for o in graph.objects(subject, rdflib.RDFS.label)
                         if isinstance(o, rdflib.Literal)})
        types = sorted({str(o) for o in graph.objects(subject, rdflib.RDF.type)
                        if isinstance(o, rdflib.URIRef)})
        flagged = any(str(o).lower() == "true"
                      for o in graph.objects(subject, deprecated))
        terms[str(subject)] = {
            "labels": [{"value": v, "lang": lang} for v, lang in labels],
            "types": types,
            "deprecated": flagged,
        }
    if not terms:
        raise Refused("%s: its pinned files describe no term in %s, so the "
                      "register would be empty" % (source["id"],
                                                   source["namespace"]))
    return {
        "format_version": FORMAT_VERSION,
        "generated_by": GENERATOR,
        "source": source["id"],
        "project": source["project"],
        "release": source["release"],
        "commit": source["commit"],
        "files": source["files"],
        "namespace": source["namespace"],
        "licence": source["licence"]["spdx"],
        "licence_as_stated_by_source": stated,
        "attribution": " ".join(source["licence"]["attribution"].split()),
        "note": (
            "Every term the pinned files describe in this namespace, not "
            "only the ones vendored: what exists, and what it is called. "
            "Generated -- do not edit. The labels are the upstream's, "
            "under the upstream's licence."),
        "terms": terms,
    }


def register_bytes(register: dict) -> bytes:
    """Deterministic: sorted keys, one indentation, LF, trailing newline."""
    return (json.dumps(register, indent=1, sort_keys=True,
                       ensure_ascii=False).encode("utf-8") + b"\n")


def manifest_of(built: dict) -> dict:
    root = layout.repository_root()
    extracts = {}
    for key, record in sorted(built.items()):
        if key.startswith("_"):
            continue
        entry = record["source"]
        path = root / entry["extract"]
        data = record["text"].encode("utf-8")
        register_path = root / entry["register"]
        register_data = record["register_text"].encode("utf-8")
        extracts[key] = {
            "extract": entry["extract"],
            "project": entry["project"],
            "release": entry["release"],
            "select": entry["select"],
            "commit": entry["commit"],
            "source_files": entry["files"],
            "licence_spdx": entry["licence"]["spdx"],
            "licence_url": entry["licence"]["url"],
            "licence_as_stated_by_source": record["stated_licence"],
            "namespace": entry["namespace"],
            "seed_terms": record["seeds"],
            "seed_terms_from_corpus_and_shapes":
                record["seeds_from_corpus_and_shapes"],
            "named_by_specification_described_by_no_pinned_file":
                record["spec_unresolved"],
            "terms_described_in_full": record["counts"]["full"],
            "terms_declared_as_stubs": record["counts"]["stubs"],
            "axioms_dropped_anonymous_object": record["counts"]["dropped"],
            "triples": record["triples"],
            "extract_sha256": sha256_of(data),
            "extract_on_disk_matches": (
                path.is_file()
                and sha256_of(path.read_bytes()) == sha256_of(data)),
            "disjointness": entry["disjointness"],
            "disjointness_axioms": record["disjointness_axioms"],
            "disjointness_pairs": record["disjointness_pairs"],
            "disjointness_sha256": (
                sha256_of(record["disjointness_text"].encode("utf-8"))
                if record["disjointness_text"] is not None else None),
            "disjointness_on_disk_matches": (
                record["disjointness_text"] is None
                or ((root / entry["disjointness"]).is_file()
                    and (root / entry["disjointness"]).read_bytes()
                    == record["disjointness_text"].encode("utf-8"))),
            "register": entry["register"],
            "register_terms": record["register_terms"],
            "register_sha256": sha256_of(register_data),
            "register_on_disk_matches": (
                register_path.is_file()
                and register_path.read_bytes() == register_data),
        }
    return {
        "format_version": FORMAT_VERSION,
        "generated_by": GENERATOR,
        "pins": PINS,
        "totals": built["_totals"],
        "extracts": extracts,
        "not_covered": not_covered(),
    }


def not_covered() -> list:
    """What the extracts do not support, in words a reader can act on."""
    projects = " or ".join(entry["project"] for entry in sources())
    return [
        "Axioms whose object is an anonymous class expression are "
        "dropped. OWL restrictions, equivalent-class expressions and "
        "union domains and ranges are therefore absent, and a reasoner "
        "over these extracts derives less than one over the upstream.",
        "These extracts cannot be used to claim the ontology is "
        "consistent with %s. They support the subClassOf reachability "
        "the shapes ask about." % projects,
        "A `select: named` source carries only the terms this repository "
        "names, and their structural ancestry. A new upstream reference "
        "in the corpus is not covered until this is rebuilt; "
        "tests/test_upstream_vendoring.py fails when that happens.",
        "Specification seeds, when a specification component exists, "
        "are read from its text. A term it names that no pinned file "
        "describes is recorded, not refused: it may be a term the "
        "project will mint, a term from an unvendored file, or a typo. "
        "Which is which is not decided here.",
        "owl:imports is not emitted. Validation is offline by design, "
        "so nothing resolves over the network at check time.",
    ]


def notice_of(built: dict) -> str:
    """The attribution every upstream licence here requires.

    Generated rather than written, because an attribution file is exactly
    the kind of document that is correct on the day it is added and
    silently wrong after the next source is vendored. What keeps that
    honest is not this function -- it is the licensing tool, which reads
    the pins and requires each declared attribution to appear here.
    """
    lines = [
        "# Third-party notices",
        "",
        "This repository redistributes partial extracts of the ontologies",
        "below. Each licence requires attribution, and this file is that",
        "attribution. It is generated by `" + GENERATOR + "`",
        "from `" + PINS + "`; the licensing check reads the same pins and",
        "fails if an attribution declared there is missing here.",
        "",
        "The extracts are not the upstream ontologies. Each carries the terms",
        "this repository names plus their structural ancestry (or, for a",
        "source pinned `select: all`, every term it describes), and drops",
        "every axiom whose object is an anonymous class expression. The",
        "registers list every term each source describes, with its labels.",
        "See the header of each extract, and `" + MANIFEST + "`.",
        "",
    ]
    for key, record in sorted(built.items()):
        if key.startswith("_"):
            continue
        entry = record["source"]
        lines += [
            "## " + entry["project"] + " " + entry["release"],
            "",
            entry["licence"]["attribution"].strip(),
            "",
            "- extract: `" + entry["extract"] + "`",
            "- register: `" + entry["register"] + "`",
        ] + ["- source: " + pinned["url"] for pinned in entry["files"]] + [
            "- commit: `" + entry["commit"] + "`",
            "- licence: " + entry["licence"]["spdx"] + " -- "
            + entry["licence"]["url"],
            "- as stated by the source: " + record["stated_licence"],
            "- %d terms in full, %d stubs, %d axioms dropped"
            % (record["counts"]["full"], record["counts"]["stubs"],
               record["counts"]["dropped"]),
            "",
        ]
    return chr(10).join(lines)


# ------------------------------------------------------------ verify


def verify() -> dict:
    """Offline: are the extracts on disk sufficient and self-consistent?

    Deliberately does not need the network, because this is what runs on
    every push. Rebuilding from upstream is a separate mode -- see
    --confirm -- and it is the one that proves these files are derived
    rather than merely present.
    """
    import rdflib

    root = layout.repository_root()
    declared = sources()
    namespaces = tuple(entry["namespace"] for entry in declared)
    manifest_path = root / MANIFEST
    if not manifest_path.is_file():
        raise Refused(MANIFEST + " is missing; run with --rebuild")
    recorded = json.loads(manifest_path.read_text(encoding="utf-8"))

    vendored = rdflib.Graph()
    findings = []
    if not (root / NOTICE).is_file():
        findings.append(
            NOTICE + " is missing. Every upstream licence here requires "
            "attribution, and redistributing an extract without it is a "
            "breach whatever the header of the extract says.")
    for entry in declared:
        path = root / entry["extract"]
        if not path.is_file():
            findings.append("%s: %s is missing"
                            % (entry["id"], entry["extract"]))
            continue
        data = path.read_bytes()
        digest = sha256_of(data)
        want = recorded["extracts"].get(entry["id"], {}).get("extract_sha256")
        if digest != want:
            findings.append(
                "%s: %s digests to %s but %s records %s"
                % (entry["id"], entry["extract"], digest[:16], MANIFEST,
                   (want or "nothing")[:16]))
        vendored.parse(data=data.decode("utf-8"), format="turtle")

        if entry["disjointness"]:
            derived = root / entry["disjointness"]
            want = recorded["extracts"].get(entry["id"], {}).get(
                "disjointness_sha256")
            if not derived.is_file():
                findings.append("%s: %s is missing"
                                % (entry["id"], entry["disjointness"]))
            else:
                data = derived.read_bytes()
                if sha256_of(data) != want:
                    findings.append(
                        "%s: %s digests to %s but %s records %s"
                        % (entry["id"], entry["disjointness"],
                           sha256_of(data)[:16], MANIFEST,
                           (want or "nothing")[:16]))
                vendored.parse(data=data.decode("utf-8"), format="turtle")

        register = root / entry["register"]
        want = recorded["extracts"].get(entry["id"], {}).get("register_sha256")
        if not register.is_file():
            findings.append("%s: %s is missing" % (entry["id"],
                                                  entry["register"]))
        elif sha256_of(register.read_bytes()) != want:
            findings.append(
                "%s: %s digests to %s but %s records %s"
                % (entry["id"], entry["register"],
                   sha256_of(register.read_bytes())[:16], MANIFEST,
                   (want or "nothing")[:16]))
        else:
            pinned = json.loads(register.read_text(encoding="utf-8"))
            if pinned.get("commit") != entry["commit"]:
                findings.append(
                    "%s: %s describes commit %s, and the pin is %s"
                    % (entry["id"], entry["register"], pinned.get("commit"),
                       entry["commit"]))

    # Spec terms the last build recorded as unresolvable are excused; any
    # other spec term is held to the same standard as a corpus term. A
    # spec revision that names a new CCO class therefore fails here until
    # the extracts are rebuilt, which is when somebody looks at it.
    excused = recorded_unresolvable_spec_terms()
    seeds = seed_terms(namespaces) | (spec_terms() - excused)
    unresolved = sorted(
        iri for iri in seeds
        if not list(vendored.predicate_objects(rdflib.URIRef(iri))))
    if unresolved:
        findings.append(
            "%d upstream term(s) named here are not described by any "
            "extract, so a shape walking through them still has no chain: "
            "%s" % (len(unresolved), ", ".join(unresolved[:6])))

    dangling = set()
    for triple in vendored:
        for term in triple:
            if (isinstance(term, rdflib.URIRef)
                    and str(term).startswith(namespaces)
                    and not list(vendored.predicate_objects(term))):
                dangling.add(str(term))
    dangling = sorted(dangling)
    if dangling:
        findings.append(
            "%d term(s) are mentioned by an extract and described by no "
            "extract: %s" % (len(dangling), ", ".join(dangling[:6])))

    return {
        "seeds": len(seeds),
        "vendored_triples": len(vendored),
        "unresolved_seeds": unresolved,
        "dangling_references": dangling,
        "findings": findings,
        "ok": not findings,
    }


# --------------------------------------------------------------- cli


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild", action="store_true",
                    help="fetch the pinned upstreams and rewrite the "
                         "extracts and the manifest")
    ap.add_argument("--confirm", action="store_true",
                    help="fetch and rebuild in memory, then require the "
                         "files on disk to be byte-identical. This is what "
                         "shows the extracts are derived from the pins "
                         "rather than edited by hand")
    ap.add_argument("--cache", default=None)
    args = ap.parse_args(argv)

    root = layout.repository_root()
    cache = Path(args.cache) if args.cache else (root / CACHE)

    if not (args.rebuild or args.confirm):
        record = verify()
        print("  %d seed term(s), %d vendored triple(s)"
              % (record["seeds"], record["vendored_triples"]))
        for finding in record["findings"]:
            print("  FINDING: %s" % finding)
        if record["ok"]:
            print("  extracts present, digests match, every reference "
                  "resolves")
        return 0 if record["ok"] else 1

    built = build(cache)
    totals = built["_totals"]
    print("  %d seed(s) -> %d term(s) in full, %d stub(s), %d axiom(s) "
          "dropped" % (totals["seeds"], totals["full"], totals["stubs"],
                       totals["dropped"]))
    print("    %d from the corpus and shapes, %d from the specification; "
          "%d spec term(s) described by no pinned file"
          % (totals["seeds_from_corpus_and_shapes"],
             totals["seeds_from_specification"],
             totals["spec_terms_unresolved"]))

    manifest = manifest_of(built)
    differing = [record["extract"]
                 for record in manifest["extracts"].values()
                 if not record["extract_on_disk_matches"]]
    differing += [record["register"]
                  for record in manifest["extracts"].values()
                  if not record["register_on_disk_matches"]]
    differing += [record["disjointness"]
                  for record in manifest["extracts"].values()
                  if not record["disjointness_on_disk_matches"]]

    for key, record in sorted(manifest["extracts"].items()):
        print("    %-4s %-40s %6d triple(s)  %s"
              % (key, record["extract"], record["triples"],
                 "same" if record["extract_on_disk_matches"] else "DIFFERS"))
        print("    %-4s %-40s %6d term(s)    %s"
              % ("", record["register"], record["register_terms"],
                 "same" if record["register_on_disk_matches"]
                 else "DIFFERS"))

    notice = notice_of(built)
    notice_path = root / NOTICE
    if not (notice_path.is_file()
            and notice_path.read_bytes() == notice.encode("utf-8")):
        differing.append(NOTICE)
        print("    %-4s %-40s %6s          DIFFERS" % ("", NOTICE, ""))

    if args.confirm:
        if differing:
            print()
            print("  FINDING: %d extract(s) on disk are not what rebuilding "
                  "from the pinned sources produces: %s"
                  % (len(differing), ", ".join(sorted(differing))))
            return 1
        print("  every extract, register and the notice are byte-identical "
              "to a fresh build from the pinned upstreams")
        return 0

    for key, record in sorted(built.items()):
        if key.startswith("_"):
            continue
        target = root / record["source"]["extract"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(record["text"].encode("utf-8"))
        print("  wrote %s" % record["source"]["extract"])
        if record["disjointness_text"] is not None:
            derived = root / record["source"]["disjointness"]
            derived.write_bytes(record["disjointness_text"].encode("utf-8"))
            print("  wrote %s (%d pairs from %d axioms)"
                  % (record["source"]["disjointness"],
                     record["disjointness_pairs"],
                     record["disjointness_axioms"]))
        register = root / record["source"]["register"]
        register.parent.mkdir(parents=True, exist_ok=True)
        register.write_bytes(record["register_text"].encode("utf-8"))
        print("  wrote %s (%d terms)" % (record["source"]["register"],
                                         record["register_terms"]))

    notice_path.parent.mkdir(parents=True, exist_ok=True)
    notice_path.write_bytes(notice.encode("utf-8"))
    print("  wrote %s" % NOTICE)

    manifest = manifest_of(built)
    (root / MANIFEST).write_bytes(
        json.dumps(manifest, indent=2, sort_keys=True,
                   ensure_ascii=False).encode("utf-8") + b"\n")
    print("  wrote %s" % MANIFEST)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
