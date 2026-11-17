# AGENTS.md

## Project

Self-contained engineering tutorials (`<topic>-tutorial/`) pairing rigorous derivations or hardware specs with runnable Python verification and vector SVG/Mermaid diagrams.

## Layout

- `README.md` — Root catalog and repository overview (one summary per tutorial; no chapter lists, which live in each tutorial index).
- `<topic>-tutorial/README.md` & `00-*.md` — Byte-identical index, running system model, and notation/glossary.
- `<topic>-tutorial/01-*.md`..`0N-*.md` — Sequential chapters (`01` prerequisites through synthesis) + `99-solutions-and-references.md` (worked solutions and annotated references).
- `<topic>-tutorial/scripts/generate_figures.py` & `figures/*.svg` — Reproducible Matplotlib plot generator and committed vector SVGs.

## Rules

- **Pedagogy:** Anchor every tutorial to one system model in `00-*.md`; structure concepts as `Intuition -> Statement / Spec -> Derivation / State Machine -> Worked Example` plus exercises; clearly separate proven theorems/official specs from heuristics and approximations.
- **Parity & Sync:** Keep `<topic>-tutorial/README.md` byte-identical to `00-*.md`, and sync changed summaries, bounds, or conventions across root `README.md`, `00-*.md`, chapters, and `99-solutions-and-references.md`.
- **Plots (SVG):** Never use ASCII art for math, geometry, norm balls, phase transitions, convergence, or benchmarks. Generate `figures/*.svg` via `scripts/generate_figures.py` with `#FFFFFF` (`figure.facecolor`, `axes.facecolor`, `savefig.facecolor`), `svg.fonttype = "path"`, `mathtext.fontset = "dejavusans"`, a colorblind-safe palette, and relative `./figures/<name>.svg` links; cover both conceptual geometry and empirical plots, and visually inspect temporary previews outside the repo before committing.
- **Diagrams & Layouts:** Use fenced `mermaid` (`flowchart`, `stateDiagram-v2`, `sequenceDiagram`) for architectures, state machines, and protocol sequences; reserve monospace ASCII strictly for bit/byte packet or register layouts (`SQE`, `CQE`), pointer maps (`PRP`), and short aligned execution traces.
- **Verification:** Pair core claims with dependency-light Python verification (standard library or `numpy`; `matplotlib` allowed in `generate_figures.py`) and ensure prose, tables, code, and plots match executed output. Check hardware offsets, status codes, and bitfields against official specs, and verify C struct layout/padding with `gcc -Wpadded -Werror`.

## Commands

- Regenerate CS tutorial SVGs (`numpy`, `matplotlib`):
  `python3 cs-decoder-tutorial/scripts/generate_figures.py`
- Verify `00-*.md` / `README.md` parity:
  `diff -u cs-decoder-tutorial/README.md cs-decoder-tutorial/00-index-and-notation.md`
  `diff -u nvme-ssd-frontend-tutorial/README.md nvme-ssd-frontend-tutorial/00-index-and-architecture.md`

## More

- Catalog & philosophy: `README.md`
- CS running model & notation: `cs-decoder-tutorial/00-index-and-notation.md`
- NVMe running model & glossary: `nvme-ssd-frontend-tutorial/00-index-and-architecture.md`
- SVG styling & palette reference: `cs-decoder-tutorial/scripts/generate_figures.py`
