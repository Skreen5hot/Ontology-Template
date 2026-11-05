# Communications

The record of what this repository has said to, and heard from, the teams it depends on
or that depend on it. One folder per team; inside it, `incoming/` and `outgoing/`.

This record follows the communications protocol, version 1.1:
Skreen5hot/communications, PROTOCOL.md at 05068d800506bae6bbf66f6cb11d4eccc6adb312, sha256
fb3a06309eb5ecd5920a7737789df524000e5447f86c008ec16fee6203d9d74d.

That file is the only copy of the rules with authority: what a message is, its header,
the rules, team codes, and alerts on the board. It was the protocol this file used to
hold, generalized (its version 1.0). It is not repeated here, so it cannot drift. Adopting
a later version is a commit that changes the lines above.

```text
communications/
  README.md                 this file: the version followed, and the rules added here
  <team>/README.md          who the team is and where its repository lives
  <team>/incoming/          messages received, copied verbatim with their source
  <team>/outgoing/          messages sent
```

Nothing here is published on the site.

## How this record holds it

- **Codes.** The teams are the `correspondents` in `config/project.yaml`, by the code this
  record uses for each; a new project has none. The shared list of codes is
  `correspondents.yaml` in the protocol's repository, and a new project uses the codes it
  lists. This record keeps the aliases it already used before the protocol had codes: it
  calls itself `EXAMPLE` (the board's code for it is `OT`) and the BPO Testing Team
  `BPOTEST` (`BPOT`), as each team's README says.
- **The check.** `python tools/communications.py` checks every message against the
  protocol and lists the threads still open; `tests/test_communications.py` runs the same
  checks on every push. It also checks the version statement above and that
  `.gitattributes` has `communications/** -text` (Rule 7).
- **Decisions.** The decision record Rule 4 names is `docs/template/DECISIONS.md` for the
  template's own decisions, and `docs/decisions/` in a project made from it.
- **Alerts.** After an outgoing message is committed and pushed, its alert is printed with
  `python tools/communications.py --alert communications/<team>/outgoing/<file>.md` and
  posted to the board, a new Discussion or a comment as the tool says. Posting is the
  architect's call, like sending.
- **The inbox.** `python tools/communications.py --inbox --code OT` lists the board's
  alerts addressed to this record whose message no `incoming/` copy holds yet. Run it when
  a session starts: an agent gets no notifications.
- **Messages from before the board** (everything dated before 2026-11-04) need no alert.

## Adding a team

Create `communications/<team>/README.md` naming the team and its repository, and add the
team's code to `correspondents` in `config/project.yaml`. The checker refuses a message
folder for a team it does not know. A team new to the protocol is also added to
`correspondents.yaml` in the protocol's repository.
