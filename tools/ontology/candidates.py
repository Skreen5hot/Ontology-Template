# SPDX-License-Identifier: MIT
"""Review candidates: where a defect no check can decide may be.

    python tools/ontology/candidates.py           # the candidates, by rule
    python tools/ontology/candidates.py --json    # every one, with evidence

WP6 found four kinds of defect in the BPO port that no validation check
decides, because whether each is a defect is a fact about what the
authors meant (template decisions 29 and 34, backlog item 12):

  over-claiming       a definition says more than the axioms do
  homonym             one IRI used for two kinds
  duplicate           two IRIs for one kind
  misclassification   a class placed under the wrong category

They were found by reading definitions against axioms and modules
against each other, which a machine can do. So a machine lists every
place one may be, with the evidence, and a person answers each
(config/review-register.yaml). Nothing here is a verdict, and nothing
here gates a commit: tools/stages.py refuses a stage marked done while a
candidate in its scope is unanswered, never because a candidate exists.

THE RULES

  necessity-without-axiom   a class whose definition uses necessity
                            wording ("requires", "must", ...) and which
                            has no existential restriction at all
  inverse-necessity         an object property declared the inverse of
                            another, whose definition uses that wording
  genus-differs             one IRI whose definitions, in one module or
                            across several, begin with different genera
  definitions-differ        one IRI with two different definitions under
                            one genus: a term copied into several modules
                            and edited in one, which may now mean two
                            things
  near-duplicate            two classes with the same label, or with
                            definitions whose content words mostly
                            coincide; and a class with the same label as
                            an upstream class, which it may duplicate
  category-in-differentia   a class whose definition says it includes, is
                            made of, or is also something from a BFO
                            category disjoint with its own, a mention no
                            restriction on the class accounts for (a
                            material artifact "that includes software",
                            say: WP6's case). A mention without such a
                            word -- "used in a process" -- is a relation,
                            not a constitution, and is not listed

The word list and the thresholds are config/candidates.yaml's. A
candidate is identified by its rule and the IRIs it is about, never by
its message, so rewording a message leaves its answer matched.

It reads the authored modules and the vendored registers, hierarchies and
disjointness, offline, and is deterministic: the same corpus gives the
same candidates.

Exit codes: 0 always, unless the corpus cannot be read (2).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import layout  # noqa: E402
import project  # noqa: E402

RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
OWL = "http://www.w3.org/2002/07/owl#"
SKOS = "http://www.w3.org/2004/02/skos/core#"
BFO = "http://purl.obolibrary.org/obo/BFO_"
CONFIG = "config/candidates.yaml"
PINS = "config/upstream-sources.yaml"

RULES = ("necessity-without-axiom", "inverse-necessity", "genus-differs",
         "definitions-differ", "near-duplicate", "category-in-differentia")
#: What ends a definition's genus phrase when no known label matches it.
GENUS_ENDS = re.compile(
    r"\s+(?:that|which|who|whose|where|when|in which|by which)\b|[,;:.(]")
ARTICLE = re.compile(r"^\s*(?:(?:a|an|the)\s+)?", re.I)
WORD = re.compile(r"[a-z0-9]+")
#: Words that carry no content, for the duplicate overlap.
STOPWORDS = frozenset("""a an and are as at be by for from has have in is it
its of on or that the their this to which who whose with""".split())


class Unreadable(SystemExit):
    """The corpus or the configuration cannot be read."""

    code = 2


# --------------------------------------------------------- configuration


DEFAULTS = {
    "necessity_words": ["requires", "required", "must", "always", "every",
                        "necessarily", "only if"],
    "duplicate_overlap": 0.8,
    "duplicate_min_words": 4,
    "constitution_words": ["includes", "including", "include", "comprises",
                           "comprising", "consists of", "consisting of",
                           "composed of", "made of", "made up of",
                           "contains", "containing", "is also"],
}
#: How many words before a mention a constitution word may stand.
CUE_WINDOW = 6


def configuration(root: Path) -> dict:
    """config/candidates.yaml, over the defaults it may leave out."""
    import yaml

    path = root / CONFIG
    raw = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}
           if path.is_file() else {})
    out = dict(DEFAULTS)
    out.update({k: v for k, v in raw.items() if k in DEFAULTS})
    unknown = sorted(set(raw) - set(DEFAULTS) - {"version"})
    if unknown:
        raise Unreadable("%s: unknown setting(s) %s" % (CONFIG,
                                                         ", ".join(unknown)))
    overlap = out["duplicate_overlap"]
    if not isinstance(overlap, (int, float)) or not 0 < overlap <= 1:
        raise Unreadable("%s: duplicate_overlap %r is not in (0, 1]"
                         % (CONFIG, overlap))
    return out


# ----------------------------------------------------------- the corpus


def normal(text: str) -> str:
    """A label or phrase compared as words: lower case, a trailing
    "(...)" dropped (T11), anything but letters and digits as one space."""
    text = re.sub(r"\s*\([^()]*\)\s*$", "", str(text).lower())
    return " ".join(WORD.findall(text))


def english(values) -> list[str]:
    return [str(v) for v in values
            if getattr(v, "language", None) in (None, "") or
            str(v.language).lower().startswith("en")]


class Corpus:
    """What the rules read: the authored modules, one graph each, and the
    upstreams' labels, parents and disjointness."""

    def __init__(self, modules, namespace, labels=None, parents=None,
                 disjoint=None):
        import rdflib

        self.modules = list(modules)              # [(name, graph)]
        self.namespace = namespace
        self.graph = rdflib.Graph()
        for _name, graph in self.modules:
            for triple in graph:
                self.graph.add(triple)
        self.labels = {k: list(v) for k, v in (labels or {}).items()}
        self.parents = {k: set(v) for k, v in (parents or {}).items()}
        self.disjoint = set(disjoint or ())
        self._ancestors: dict = {}
        g, U = self.graph, rdflib.URIRef
        for s, o in g.subject_objects(U(RDFS + "label")):
            if isinstance(s, U):
                for text in english([o]):
                    self.labels.setdefault(str(s), []).append(text)
        for s, o in g.subject_objects(U(RDFS + "subClassOf")):
            if isinstance(s, U) and isinstance(o, U):
                self.parents.setdefault(str(s), set()).add(str(o))
        for s, o in g.subject_objects(U(OWL + "disjointWith")):
            if isinstance(s, U) and isinstance(o, U):
                self.disjoint.add(frozenset((str(s), str(o))))
        self.by_label: dict = {}
        for iri, texts in self.labels.items():
            for text in texts:
                key = normal(text)
                if key:
                    self.by_label.setdefault(key, set()).add(iri)
        self.longest = max((len(k.split()) for k in self.by_label), default=0)

    def authored(self, kind: str) -> list[str]:
        import rdflib

        return sorted(str(s) for s in self.graph.subjects(
            rdflib.URIRef(RDF + "type"), rdflib.URIRef(OWL + kind))
            if str(s).startswith(self.namespace))

    def definitions(self, iri: str) -> list[tuple[str, str]]:
        """(module, definition) for each English or untagged definition,
        in every module that gives one."""
        import rdflib

        out = []
        for name, graph in self.modules:
            for value in english(graph.objects(rdflib.URIRef(iri),
                                               rdflib.URIRef(SKOS
                                                             + "definition"))):
                out.append((name, value))
        return sorted(set(out))

    def ancestors(self, iri: str) -> set:
        """The class and every named class above it."""
        if iri in self._ancestors:
            return self._ancestors[iri]
        seen, todo = {iri}, [iri]
        while todo:
            for parent in self.parents.get(todo.pop(), ()):
                if parent not in seen:
                    seen.add(parent)
                    todo.append(parent)
        self._ancestors[iri] = seen
        return seen

    def disjoint_pair(self, one: str, other: str):
        """A declared disjoint pair (a, b), a above `one` and b above
        `other`, or None."""
        mine, theirs = self.ancestors(one), self.ancestors(other)
        for pair in sorted(self.disjoint, key=sorted):
            a, b = sorted(pair)
            if a in mine and b in theirs:
                return a, b
            if b in mine and a in theirs:
                return b, a
        return None

    def restrictions(self, iri: str) -> list[tuple[str, str, str]]:
        """(kind, property, filler) for each restriction a class is under
        or equivalent to, directly or in an intersection."""
        import rdflib
        from rdflib.collection import Collection

        g, U = self.graph, rdflib.URIRef
        out, todo = [], []
        for p in ("subClassOf", "equivalentClass"):
            todo.extend(g.objects(U(iri), U((RDFS if p == "subClassOf"
                                             else OWL) + p)))
        seen = set()
        while todo:
            node = todo.pop()
            if node in seen or isinstance(node, U):
                continue
            seen.add(node)
            for item in g.objects(node, U(OWL + "intersectionOf")):
                todo.extend(Collection(g, item))
            prop = g.value(node, U(OWL + "onProperty"))
            if prop is None:
                continue
            for kind, key in (("some", "someValuesFrom"),
                              ("all", "allValuesFrom"),
                              ("value", "hasValue"),
                              ("some", "onClass")):
                for filler in g.objects(node, U(OWL + key)):
                    out.append((kind, str(prop), str(filler)))
            for key in ("minCardinality", "minQualifiedCardinality",
                        "cardinality", "qualifiedCardinality"):
                for n in g.objects(node, U(OWL + key)):
                    if int(n) >= 1:
                        out.append(("some", str(prop), ""))
        return sorted(set(out))

    def label(self, iri: str) -> str:
        texts = self.labels.get(iri) or []
        return texts[0] if texts else iri


def sources(root: Path) -> list[dict]:
    import yaml

    raw = yaml.safe_load((root / PINS).read_text(encoding="utf-8")) or {}
    return raw.get("sources") or []


def upstream(root: Path) -> tuple[dict, dict, set]:
    """Labels, parents and disjoint pairs from every vendored source."""
    import rdflib

    labels, parents, disjoint = {}, {}, set()
    for source in sources(root):
        register = root / source["register"]
        if register.is_file():
            terms = json.loads(register.read_text(encoding="utf-8"))["terms"]
            for iri, term in terms.items():
                texts = [t["value"] for t in term.get("labels") or []
                         if str(t.get("lang") or "en").startswith("en")]
                if texts:
                    labels[iri] = texts
        hierarchy = root / source["hierarchy"]
        if hierarchy.is_file():
            classes = json.loads(hierarchy.read_text(
                encoding="utf-8"))["classes"]
            for iri, entry in classes.items():
                parents[iri] = set(entry.get("superclasses") or [])
        if source.get("disjointness"):
            graph = rdflib.Graph()
            graph.parse(root / source["disjointness"], format="turtle")
            for s, o in graph.subject_objects(
                    rdflib.URIRef(OWL + "disjointWith")):
                disjoint.add(frozenset((str(s), str(o))))
    return labels, parents, disjoint


def corpus(root: Path | None = None) -> Corpus:
    import rdflib

    root = root or layout.repository_root()
    modules = []
    for path in layout.ontology_files():
        graph = rdflib.Graph()
        try:
            graph.parse(path, format="turtle")
        except Exception as exc:  # rdflib raises several types
            raise Unreadable("%s cannot be read: %s" % (path, exc))
        modules.append((path.relative_to(root).as_posix(), graph))
    labels, parents, disjoint = upstream(root)
    return Corpus(modules, project.namespace(), labels, parents, disjoint)


def corpus_digest(found: Corpus) -> str:
    """The modules the candidates were generated from, as one digest."""
    h = hashlib.sha256()
    for name, graph in found.modules:
        h.update(name.encode("utf-8") + b"\0")
        for line in sorted(graph.serialize(format="nt").splitlines()):
            h.update(line.encode("utf-8") + b"\n")
    return h.hexdigest()


# ------------------------------------------------------------ the rules


def candidate(rule: str, about, message: str, evidence: dict) -> dict:
    return {"rule": rule, "about": sorted(about), "message": message,
            "evidence": evidence}


def identity(record: dict) -> tuple:
    return (record["rule"], tuple(record["about"]))


def necessity(text: str, words) -> list[str]:
    lowered = text.lower()
    return sorted({w for w in words
                   if re.search(r"\b%s\b" % re.escape(w.lower()), lowered)})


def necessity_without_axiom(found: Corpus, settings: dict) -> list[dict]:
    out = []
    for iri in found.authored("Class"):
        if any(kind in ("some", "value")
               for kind, _p, _f in found.restrictions(iri)):
            continue
        for module, text in found.definitions(iri):
            words = necessity(text, settings["necessity_words"])
            if words:
                out.append(candidate(
                    "necessity-without-axiom", [iri],
                    "The definition of %s says %s, but the class has no "
                    "existential restriction: the axioms do not say what "
                    "the definition claims every instance has or does."
                    % (iri, ", ".join(repr(w) for w in words)),
                    {"module": module, "definition": text, "words": words,
                     "restrictions": []}))
                break
    return out


def inverse_necessity(found: Corpus, settings: dict) -> list[dict]:
    import rdflib

    g, U = found.graph, rdflib.URIRef
    out = []
    for iri in found.authored("ObjectProperty"):
        inverses = sorted({str(o) for o in g.objects(U(iri),
                                                     U(OWL + "inverseOf"))}
                          | {str(s) for s in g.subjects(U(OWL + "inverseOf"),
                                                        U(iri))})
        if not inverses:
            continue
        for module, text in found.definitions(iri):
            words = necessity(text, settings["necessity_words"])
            if words:
                out.append(candidate(
                    "inverse-necessity", [iri],
                    "%s is the inverse of %s, and its definition says %s: "
                    "an inverse states that the relation holds both ways, "
                    "not that either side needs the other."
                    % (iri, ", ".join(inverses),
                       ", ".join(repr(w) for w in words)),
                    {"module": module, "definition": text, "words": words,
                     "inverse_of": inverses}))
                break
    return out


def genus(found: Corpus, text: str) -> tuple[str, int]:
    """A definition's genus, read as the genus check reads it: after a
    leading article, the longest known label it begins with; failing
    that, the words before "that", "which", a comma and the like. With
    the number of words it took."""
    body = normal(ARTICLE.sub("", text, count=1))
    words = body.split()
    for n in range(min(found.longest, len(words)), 0, -1):
        phrase = " ".join(words[:n])
        if phrase in found.by_label:
            return phrase, n
    head = GENUS_ENDS.split(ARTICLE.sub("", text, count=1).lower(), 1)[0]
    phrase = " ".join(WORD.findall(head)[:6])
    return phrase, len(phrase.split())


def genus_differs(found: Corpus, settings: dict) -> list[dict]:
    out = []
    for iri in found.authored("Class"):
        read = [{"module": m, "definition": d, "genus": genus(found, d)[0]}
                for m, d in found.definitions(iri)]
        genera = sorted({r["genus"] for r in read if r["genus"]})
        if len(genera) > 1:
            out.append(candidate(
                "genus-differs", [iri],
                "%s has definitions with different genera (%s): one IRI "
                "may be used for two kinds." % (
                    iri, "; ".join(repr(g) for g in genera)),
                {"definitions": read}))
    return out


def definitions_differ(found: Corpus, settings: dict) -> list[dict]:
    out = []
    for iri in found.authored("Class"):
        read = [{"module": m, "definition": d, "genus": genus(found, d)[0]}
                for m, d in found.definitions(iri)]
        texts = {" ".join(normal(r["definition"]).split()) for r in read}
        genera = {r["genus"] for r in read if r["genus"]}
        if len(texts) > 1 and len(genera) <= 1:
            out.append(candidate(
                "definitions-differ", [iri],
                "%s has %d different definitions under one genus (%s): a "
                "copy edited in one place may now mean something else."
                % (iri, len(texts), ", ".join(sorted(genera)) or "unread"),
                {"definitions": read}))
    return out


def content(text: str) -> frozenset:
    return frozenset(w for w in WORD.findall(text.lower())
                     if w not in STOPWORDS)


def near_duplicate(found: Corpus, settings: dict) -> list[dict]:
    classes = found.authored("Class")
    out, seen = [], set()
    by_label: dict = {}
    for iri in classes:
        for text in found.labels.get(iri) or []:
            by_label.setdefault(normal(text), set()).add(iri)
    for key, iris in sorted(by_label.items()):
        for one in sorted(iris):
            for other in sorted(iris):
                if one < other and (one, other) not in seen:
                    seen.add((one, other))
                    out.append(candidate(
                        "near-duplicate", [one, other],
                        "%s and %s have the same label, %r: two IRIs may "
                        "name one kind." % (one, other, key),
                        {"same_label": key, "overlap": None,
                         "definitions": {i: [d for _m, d in
                                             found.definitions(i)]
                                         for i in (one, other)}}))
    upstream_labels: dict = {}
    for iri, texts in found.labels.items():
        if iri.startswith(found.namespace) or iri not in found.parents:
            continue
        for text in texts:
            upstream_labels.setdefault(normal(text), set()).add(iri)
    for key, iris in sorted(by_label.items()):
        for theirs in sorted(upstream_labels.get(key, ())):
            for one in sorted(iris):
                out.append(candidate(
                    "near-duplicate", [one, theirs],
                    "%s has the same label as the upstream class %s, %r: it "
                    "may duplicate it." % (one, theirs, key),
                    {"same_label": key, "overlap": None, "upstream": theirs,
                     "definitions": {one: [d for _m, d in
                                           found.definitions(one)]}}))
    threshold = settings["duplicate_overlap"]
    least = settings["duplicate_min_words"]
    words = []
    for iri in classes:
        for _module, text in found.definitions(iri):
            bag = content(text)
            if len(bag) >= least:
                words.append((len(bag), iri, bag, text))
    words.sort(key=lambda w: (w[0], w[1], w[3]))
    for i, (size, one, mine, my_text) in enumerate(words):
        for size2, other, theirs, their_text in words[i + 1:]:
            if size < threshold * size2:
                break
            if one == other:
                continue
            pair = tuple(sorted((one, other)))
            if pair in seen:
                continue
            overlap = len(mine & theirs) / len(mine | theirs)
            if overlap >= threshold:
                seen.add(pair)
                out.append(candidate(
                    "near-duplicate", list(pair),
                    "%s and %s have definitions whose content words "
                    "overlap %.2f: two IRIs may name one kind."
                    % (pair[0], pair[1], overlap),
                    {"same_label": None, "overlap": round(overlap, 2),
                     "definitions": {one: [my_text],
                                     other: [their_text]}}))
    return out


def mentions(found: Corpus, words: list[str]) -> list[tuple[str, set,
                                                              int]]:
    """Each known label among `words`, as a whole phrase, longest first
    where two overlap, with the index it starts at."""
    out, i = [], 0
    while i < len(words):
        for n in range(min(found.longest, len(words) - i), 0, -1):
            phrase = " ".join(words[i:i + n])
            if phrase in found.by_label:
                out.append((phrase, found.by_label[phrase], i))
                i += n
                break
        else:
            i += 1
    return out


def accounted(found: Corpus, iri: str, other: str) -> bool:
    """Whether a restriction on `iri` names `other`, or a class above or
    below it: the axioms then say what the mention says."""
    for _kind, _prop, filler in found.restrictions(iri):
        if filler and (filler in found.ancestors(other)
                       or other in found.ancestors(filler)):
            return True
    return False


def cued(words: list[str], start: int, cues: list[list[str]]) -> bool:
    """Whether a constitution word stands in the few words before
    `start`: the definition says the class includes or is the thing, not
    only that it is related to it."""
    before = words[max(0, start - CUE_WINDOW):start]
    for cue in cues:
        for i in range(len(before) - len(cue) + 1):
            if before[i:i + len(cue)] == cue:
                return True
    return False


def category_in_differentia(found: Corpus, settings: dict) -> list[dict]:
    out, seen = [], set()
    cues = [normal(c).split() for c in settings["constitution_words"]]
    for iri in found.authored("Class"):
        for module, text in found.definitions(iri):
            # The whole definition: a mention counts only after a
            # constitution word, so the genus, which opens it, never does.
            words = normal(ARTICLE.sub("", text, count=1)).split()
            for phrase, others, start in mentions(found, words):
                if not cued(words, start, cues):
                    continue
                for other in sorted(others):
                    pair = found.disjoint_pair(iri, other)
                    if (pair is None or (iri, other) in seen
                            or accounted(found, iri, other)):
                        continue
                    seen.add((iri, other))
                    out.append(candidate(
                        "category-in-differentia", [iri, other],
                        "The definition of %s says it includes or is %r "
                        "(%s), which falls "
                        "under %s; the class falls under %s, declared "
                        "disjoint with it, and no restriction on the class "
                        "accounts for the mention. The class may be "
                        "placed under the wrong category."
                        % (iri, phrase, other, found.label(pair[1]),
                           found.label(pair[0])),
                        {"module": module, "definition": text,
                         "mention": phrase, "mentioned": other,
                         "category": pair[0], "disjoint_with": pair[1]}))
    return out


GENERATORS = {
    "necessity-without-axiom": necessity_without_axiom,
    "inverse-necessity": inverse_necessity,
    "genus-differs": genus_differs,
    "definitions-differ": definitions_differ,
    "near-duplicate": near_duplicate,
    "category-in-differentia": category_in_differentia,
}


def generate(found: Corpus, settings: dict | None = None) -> list[dict]:
    """Every candidate, in a stable order."""
    settings = settings or dict(DEFAULTS)
    out = []
    for rule in RULES:
        out.extend(GENERATORS[rule](found, settings))
    return sorted(out, key=identity)


# ----------------------------------------------------------------- main


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true",
                    help="every candidate, with its evidence, and the "
                         "corpus digest it was generated from")
    args = ap.parse_args(argv)
    root = layout.repository_root()
    found = corpus(root)
    records = generate(found, configuration(root))
    if args.json:
        print(json.dumps({"corpus": corpus_digest(found),
                          "candidates": records}, indent=1,
                         ensure_ascii=False))
        return 0
    for rule in RULES:
        mine = [r for r in records if r["rule"] == rule]
        print("  %-24s %d" % (rule, len(mine)))
        for record in mine:
            print("    %s" % record["message"][:300])
    print("\n  %d candidate(s): each is a place to look, not a defect; a "
          "person answers it in config/review-register.yaml" % len(records))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
