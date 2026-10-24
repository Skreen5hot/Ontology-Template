# Research

The project's own notes: summaries of sources, comparisons of how other ontologies model
something, the reasoning behind a modelling choice before it becomes a decision. Written
here, in this project's words, under its licence.

## What goes here, and what does not

- **Here:** Markdown notes, tables (`.tsv`, `.csv`), bibliographies (`.bib`), small YAML.
  Cite a source by title, author and where to find it; quote a passage short enough to be
  a quotation.
- **Not here:** the sources themselves. A standard, a paper, a framework, a spreadsheet
  someone else made is somebody else's work. It goes in `docs/Reference/`, which the layout
  contract declares `tracked: false`: it may sit on your disk, and it is never committed.

The suite enforces the second half: a file in `research/` with a suffix other than the
ones above is refused, and so is any file whose bytes are those of a file in
`docs/Reference/` -- a copy is a copy whatever it is called.

A note that settles something becomes a decision (`docs/decisions/`) or a change to the
ontology; the note stays as the record of how it was reached.
