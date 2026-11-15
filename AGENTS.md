# Repository Guidelines & Design Decisions (`tutorials`)

This file records the standing architectural, pedagogical, visualization, and verification decisions for creating and maintaining tutorials in this repository.

---

## 1. Repository & Tutorial Layout

- **Directory Structure:** Each tutorial lives in a self-contained top-level directory (`<topic>-tutorial/`) and is cataloged in the root [README.md](./README.md).
- **Chapter Numbering Convention:**
  - `00-<index>.md` and `README.md`: Keep `<topic>-tutorial/README.md` and `<topic>-tutorial/00-*.md` **identical** so browsing the directory directly on GitHub presents the complete index, system model, and notation/glossary.
  - `01-*.md` through `0N-*.md`: Sequential chapters starting with self-contained prerequisites (`01-*.md`) and progressing through theory/mechanics to end-to-end comparison/error-handling synthesis.
  - `99-solutions-and-references.md`: Complete step-by-step solutions to every end-of-chapter exercise plus an annotated bibliography or spec reference.
- **Cross-File Sync:** Whenever a chapter summary, key figure, numerical bound, or structural convention changes, propagate the update consistently across the root `README.md`, `<topic>-tutorial/README.md`, `<topic>-tutorial/00-*.md`, affected chapters, and `99-solutions-and-references.md`.

---

## 2. Pedagogical & Content Standards

- **Concrete Running Anchor:** Every tutorial anchors all derivations, state machines, and experiments to a single concrete system model introduced in Chapter 00 (e.g., $N = 1024, M = 256, r = 0.25$ gradient compression blocks; multi-million-IOPS NVMe HIL controller).
- **Four-Stage Exposition Flow:** Present major concepts in the sequence:
  `Intuition -> Statement / Spec -> Derivation / State Machine -> Worked Example`, concluding each chapter with Check-Your-Understanding exercises.
- **Explicit Separation of Rigor vs. Heuristics:** Clearly distinguish proven mathematical theorems and official hardware/protocol specifications from practical engineering heuristics, approximations, and empirical modeling assumptions.

---

## 3. Visualizations & Diagrams

Choose the representation strictly by what is being illustrated:

1. **Mathematical, Geometric & Empirical Plots → Vector SVG (`figures/*.svg`):**
   - **Never use ASCII art** for coordinate systems, vector-space decompositions, norm balls ($\ell_1 / \ell_2$), function plots, phase transitions, convergence trajectories, or benchmark charts.
   - Generate all plots reproducibly via a Python/Matplotlib script at `<topic>-tutorial/scripts/generate_figures.py` and commit the resulting `.svg` assets under `<topic>-tutorial/figures/` (embedded in Markdown with relative links `![...](./figures/<name>.svg)`).
   - **Theme & Renderer Portability:** Configure Matplotlib with opaque white backgrounds (`figure.facecolor = "#FFFFFF"`, `axes.facecolor = "#FFFFFF"`, `savefig.facecolor = "#FFFFFF"`) and vectorized text/math paths (`svg.fonttype = "path"`, `mathtext.fontset = "dejavusans"`) so equations and dark labels render cleanly across GitHub, VS Code, Obsidian, and PDF viewers in both light and dark modes.
   - **Visual Quality & Parity:** Use a consistent, colorblind-safe semantic palette, include figures for both conceptual geometry and empirical verification scripts/worked examples, and visually inspect rendered previews (stored temporarily outside the repo) before committing to catch overlapping labels, clipped annotations, or arrow collisions.
2. **System Architectures, State Machines & Protocol Sequences → Mermaid:**
   - Use fenced `mermaid` blocks (`flowchart`, `stateDiagram-v2`, `sequenceDiagram`) for SoC/system block diagrams, firmware state machines, and host-controller interaction sequences.
3. **Bit/Byte Layouts & Aligned Hardware Structures → Monospace Code Blocks:**
   - Reserve plain monospace ASCII blocks strictly for bit/byte-accurate packet or register layouts (e.g., `SQE`, `CQE`), memory pointer maps (e.g., `PRP` lists), and short aligned execution traces where fixed-width column alignment is intrinsic to the content.

---

## 4. Technical, Mathematical & Spec Verification

- **Dependency-Light Runnable Verification:** Pair every chapter's core claims or protocols with a self-contained Python verification script (standard library or `numpy`) that executes cleanly without heavy external frameworks.
- **Quantitative Alignment:** Verify all worked counterexamples, analytical formulas, Monte Carlo figures, and prose claims directly against script execution so prose, tables, code, and plotted figures match exactly (e.g., verifying null-space residuals, exact asymptotic phase-transition curves, and empirical error ratios).
- **Specification & Binary Layout Verification:** Verify hardware register offsets, status code names, and bitfields against official specifications, and verify C struct sizes and padding explicitly using compiler checks (e.g., `gcc -Wpadded -Werror`).
