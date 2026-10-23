# Communications

The record of what this repository has said to, and heard from, the teams it depends on
or that depend on it. One folder per team; inside it, `incoming/` and `outgoing/`.

```text
communications/
  README.md                 this protocol
  <team>/README.md          who the team is and where its repository lives
  <team>/incoming/          messages received, copied verbatim with their source
  <team>/outgoing/          messages sent
```

The teams are the `correspondents` in `config/project.yaml`; a new project has none.

`tools/communications.py` checks every message against this protocol and lists the
threads still open. `tests/test_communications.py` runs the same checks on every push.
Nothing here is published on the site.

---

## A message

One Markdown file: a YAML header between `---` lines, then the body.

**Filename** — `YYYY-MM-DD-<slug>.md`, the date the message was sent or received, and a
short lowercase slug (`a-z`, `0-9`, `-`). The folder says the team and the direction.

**Header** -- a real example, from the Business Capability Ontology (`BCO`) to the
Business Process Ontology (`BPO`).

```yaml
---
id: BCO-BPO-2026-10-23-vendoring-pin   # <FROM>-<TO>-<date>-<slug>; must match the path
from: BCO
to: BPO
date: 2026-10-23                        # must match the filename
type: request                           # request | finding | answer | notice | acknowledgment
subject: One line, what this is about
in_reply_to: null                       # the id of the message this answers, or null
refs:                                   # what the message is about, bound by digest
  - repo: Skreen5hot/BusinessProcessOntology
    commit: 66131945b525c54f44e4962f32bb1f52dfa0cd12
    path: ontology/apqc-ext.ttl
    sha256: 1b9a9375cb7303003556004effd712b63913d6aa4935dbf604a653aec65cab4b
author: Aaron Damiano                   # a person, or an agent named as an agent
requires_act: false                     # true when only the architect can answer it
---
```

Incoming messages carry one more field, `source`, saying where the original lives:

```yaml
source:
  repo: Skreen5hot/BusinessProcessOntology
  commit: <the commit the original was read at>
  path: <its path there>
  sha256: <SHA-256 of the original file's bytes>
```

and the body below the header is that original, byte for byte. The checker recomputes the
digest of the body and requires it to equal `source.sha256`, so a copy that has been
"tidied" fails rather than quietly standing in for what was sent.

## Rules

1. **A committed message never changes.** A correction is a new message whose `in_reply_to`
   names the one it corrects. The checker reads git history and refuses a message file
   that more than one commit has touched.
2. **Status is derived, not written.** A `request` or `finding` is *open* until a later
   message answers it (`in_reply_to` its id) with type `answer` or `acknowledgment`. There
   is no status field to forget to update; `python tools/communications.py` lists what is
   open.
3. **Every ref is digest-bound.** A path without a commit and a SHA-256 names whatever is
   there today. A ref into this repository is recomputed from `git show <commit>:<path>`;
   a ref into another repository is checked for shape here and can be verified there.
4. **A message is not a decision.** It can ask for one (`requires_act: true`). The act
   itself is the architect's and goes in `docs/decisions/`, citing the message by id.
5. **Agents are named as agents.** A message drafted by an agent says so in `author`, and
   whose direction it was drafted at.
6. **Sending is outside the repository.** An outgoing message here is the record of what
   was said; it reaches the other team however that team receives things (an issue, a
   file in their repository, a conversation). The record does not claim delivery.

## Adding a team

Create `communications/<team>/README.md` naming the team and its repository, and add the
team's code to `correspondents` in `config/project.yaml`. The checker refuses a message
folder for a team it does not know.
