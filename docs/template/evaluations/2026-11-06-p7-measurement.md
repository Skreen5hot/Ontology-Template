# P7: the propagation check measured on BCO

**Date:** 2026-11-06. **Under:** decision 38, which approved the read-only measurement of
the design's section 6: BCO's DP-1 and DP-2 records, their `carries_into` written in memory
as BCO's specification, checked against the specification. BCO's repository was read, not
modified (its working tree was the same before and after the run), and none of its content
is recorded here: counts only.

**How BCO was read.** BCO's records have no front matter. For DP-1 and DP-2 the block was
supplied in memory, each listing the specification as its one target, and each was checked
with the template's exact match (`tools/decisions.py`, `cites`) against each specification
version BCO keeps. The rest of the check ran on BCO's tracked files with the template's
default settings.

## DP-1 and DP-2

| Specification | DP-1 | DP-2 |
|---|---|---|
| v0.4.0-draft.1 | owed | owed |
| v0.5.0-draft.1 | carried | carried |
| v0.5.0-draft.2 | carried | carried |
| v0.5.0-draft.3 (as it stands) | carried | carried |

v0.4.0-draft.1 cites neither record: that is the debt BCO found by reading, and the check
lists it. From v0.5.0-draft.1 the specification cites both records by name, so the check
passes them. It says nothing more: whether draft.3 says what DP-1 and DP-2 decided is
BCO's "faithful" column, a person's judgement.

## BCO's records, as a project adopting P7 would see them

| | |
|---|---|
| Decision records (README excluded) | 42 |
| With a front matter block | 0 |
| Not named `YYYY-MM-DD-<slug>.md` | 0 |
| Refused with `required_from` unset | 42 |
| Listed as not declaring with `required_from` set to the adoption date | 42, none refused |
| Naming a tracked file outside `docs/decisions/` in prose | 41 |
| Path-form citations of a record that does not exist | 18: 16 in trial fixtures, 2 in proposals |

## What this says

- **The check finds the case it was designed for.** Against the specification that owed
  DP-1 and DP-2 it lists both; against the one that carries them it passes both.
- **`required_from` is what makes adoption possible.** Unset, every one of BCO's 42 records
  is refused; set to the adoption date, none is, and all are listed. That is decision 38's
  backward compatibility, as designed.
- **BCO's records already name what they change.** 41 of 42 name a tracked file in prose,
  so writing the blocks is transcription, not new analysis. The count shows a file is
  named, not that it is a target.
- **Fixtures need excluding.** 16 of the 18 unresolved citations are trial fixtures that
  cite invented records, which is what `scan_exclude` is for; `config/decisions.yaml` says
  so. The other 2 are proposals citing a record that does not exist; whether they are a
  forward reference or a slip is BCO's to read.

The figures describe BCO's records on 2026-11-06, not projects in general.
