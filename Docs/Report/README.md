# PromptBench — Project Report

This folder contains the UCS 318 Software Engineering semester-evaluation report for
PromptBench, written in LaTeX.

## Contents

- `main.tex` — report source
- `images/logo-000.png` — Thapar Institute logo used on the title page
- `images/er_diagram.png` — Entity-Relationship diagram
- `PromptBench_Report.pdf` — pre-built PDF (regenerate after edits, see below)

## Building the PDF

Requires a standard TeX distribution (TeX Live / MiKTeX) with `pdflatex` and the
`tikz`, `booktabs`, `enumitem`, `titlesec`, `hyperref`, `fancyhdr`, and `parskip` packages
(all included in a full TeX Live install).

```bash
cd report
pdflatex main.tex
pdflatex main.tex   # run twice so the table of contents/page numbers resolve
```

The output is `main.pdf`.

## Editing

- Diagrams (use-case, activity, swimlane, DFDs, class diagram) are drawn with TikZ directly
  in `main.tex` — no external image files, so they scale cleanly and are easy to edit.
- The ER diagram is a static image at `images/er_diagram.png`; regenerate/replace that file
  and rerun `pdflatex` if the schema changes.
