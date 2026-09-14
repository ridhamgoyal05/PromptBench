# PromptBench — Project Report

This folder contains the LaTeX source for the Software Engineering project report.

- `PromptBench_Report.tex` — LaTeX source
- `PromptBench_Report.pdf` — pre-compiled PDF (open this directly if you just want to read it)
- `images/` — logo and ER diagram used by the report

## Compiling from source

**Option A — Overleaf (easiest, no install needed)**
1. Create a new blank project on [overleaf.com](https://overleaf.com).
2. Upload `PromptBench_Report.tex` and the whole `images/` folder into it.
3. Click **Recompile**.

**Option B — Locally**
Requires a TeX distribution (e.g. TeX Live / MiKTeX) with `pdflatex`.
```bash
pdflatex PromptBench_Report.tex
pdflatex PromptBench_Report.tex   # run twice for the table of contents
```

## Editing

All placeholder brackets like `[Describe relevant project experience]` in the Software
Bid table should be filled in before final submission.
