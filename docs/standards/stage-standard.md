# Standard: (stage id), (stage name)

**Version:** 0.1, draft. **Approved:** not yet (the decision record, when it is).
**Holder of the gate:** who, and in what capacity.

The skeleton for a stage standard (`docs/process/METHOD.md`, §3). Copy it to
`docs/standards/<stage id>.md`, replace each paragraph with the stage's answer, and keep
every heading: a question that does not apply is answered "none", with why.

## 1. Purpose

What the stage decides or produces, in a sentence, and which stage or lane of the method it
is (`config/stages.yaml`).

## 2. Inputs

What the stage takes in, and the state each must be in first: approved, ratified, rights
recorded. Name each by its record, not by a description.

## 3. Outputs

What the stage produces, where it lives (the layout components), and in what form.

## 4. Rules

What every output must satisfy. Mark each rule as held by a check (name the check) or by a
reviewer. Use MUST and SHOULD as RFC 2119 does, and only where a reviewer could tell
whether the rule was met.

## 5. Where it joins the decision path

For a lane: which gates on the path its work waits on, and which it may run ahead of. For
a path stage: what it hands to the next stage. A finding that belongs to another stage is
raised there as an open issue, not settled here.

## 6. The gate

The conditions under which the stage is done, stated before the stage starts. For each:
who decides it, in what capacity (ontologist, domain practitioner, architect, rights), and
the record that shows it was met. A condition only a person can state is recorded by that
person, never ticked by a tool.

## 7. Out of scope

What this stage does not do, and which stage does.

## 8. Not covered

What this standard does not yet say, and what would close each gap.
