"""Generate clean SVG figures for the Compressive Sensing Decoders tutorial.

Usage:
    python3 cs-decoder-tutorial/scripts/generate_figures.py

All figures are saved as vector SVGs under `cs-decoder-tutorial/figures/` with
opaque white backgrounds and vectorized text paths so they render identically
across GitHub, VS Code, Obsidian, and PDF viewers in both light and dark modes.
"""

import math
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/mpl_cache")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import numpy as np


# ---------------------------------------------------------------------------
# Global Palette & Style
# ---------------------------------------------------------------------------
BLUE = "#2563EB"       # Pseudo-inverse / row(Phi) / L2
BLUE_LIGHT = "#DBEAFE"
ORANGE = "#EA580C"     # L1 / Basis Pursuit / FISTA
ORANGE_LIGHT = "#FFEDD5"
PURPLE = "#7C3AED"     # ISTA / LASSO
GREEN = "#059669"      # True signal x / Exact recovery zone
GREEN_LIGHT = "#D1FAE5"
RED = "#DC2626"        # Null space erased component / Failure / DT threshold
RED_LIGHT = "#FEE2E2"
TEAL = "#0F766E"       # Affine solution space H_y
SLATE = "#334155"
MUTED = "#64748B"
GRID = "#E2E8F0"
DARK = "#0F172A"

SCRIPT_DIR = Path(__file__).resolve().parent
TUTORIAL_DIR = SCRIPT_DIR.parent
FIG_DIR = TUTORIAL_DIR / "figures"


def configure_style() -> None:
    plt.rcParams.update({
        "figure.facecolor": "#FFFFFF",
        "axes.facecolor": "#FFFFFF",
        "savefig.facecolor": "#FFFFFF",
        "savefig.edgecolor": "none",
        "svg.fonttype": "path",
        "mathtext.fontset": "dejavusans",
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
        "font.size": 10,
        "axes.titlesize": 11.2,
        "axes.titleweight": "bold",
        "axes.labelsize": 10.2,
        "axes.edgecolor": "#CBD5E1",
        "axes.linewidth": 0.9,
        "xtick.color": SLATE,
        "ytick.color": SLATE,
        "text.color": DARK,
        "legend.frameon": True,
        "legend.facecolor": "#FFFFFF",
        "legend.edgecolor": "#CBD5E1",
        "legend.framealpha": 0.96,
    })


def save_fig(fig: plt.Figure, name: str, preview_dir: Path | None = None) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    svg_path = FIG_DIR / f"{name}.svg"
    fig.savefig(svg_path, format="svg", bbox_inches="tight", pad_inches=0.14)
    if preview_dir is not None:
        preview_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(preview_dir / f"{name}.png", format="png", dpi=160, bbox_inches="tight", pad_inches=0.14)
    plt.close(fig)
    print(f"Saved {svg_path}")


def draw_right_angle(ax: plt.Axes, origin: np.ndarray, u_dir: np.ndarray, v_dir: np.ndarray,
                     size: float = 0.22, color: str = MUTED) -> None:
    u = u_dir / np.linalg.norm(u_dir) * size
    v = v_dir / np.linalg.norm(v_dir) * size
    pts = np.vstack([origin + u, origin + u + v, origin + v])
    ax.plot(pts[:, 0], pts[:, 1], color=color, lw=1.1, zorder=4)


# ---------------------------------------------------------------------------
# Figure 1: Ch 2 Section 2.2 — Subspace Geometry
# ---------------------------------------------------------------------------
def make_ch2_subspace_geometry(preview_dir: Path | None = None) -> None:
    fig, ax = plt.subplots(figsize=(10.2, 5.7))
    ax.set_aspect("equal")
    ax.axis("off")

    # Orthonormal subspace basis (row(Phi), null(Phi)) rotated relative to standard axes (z1, z2):
    # Phi = [1, -2]/sqrt(5) => r_hat = [1, -2]/sqrt(5), n_hat = [2, 1]/sqrt(5).
    s5 = math.sqrt(5.0)
    e1 = np.array([1.0 / s5, 2.0 / s5])
    e2 = np.array([-2.0 / s5, 1.0 / s5])

    u_R = 2.6
    v_x = 1.85
    v_l1 = -1.3  # exact intersection of H_y (u = u_R) with -e2 axis!
    r_l1 = u_R * s5 / 2.0

    # Light rotated standard coordinate axes (z1, z2), labeled on the unobstructed left side
    for vec, lbl, pos_scale, ha_val in [
        (e1, r"Coordinate axis $z_1$", -2.65, "right"),
        (e2, r"Coordinate axis $z_2$", 2.65, "right"),
    ]:
        p_neg = -3.05 * vec
        p_pos = 3.15 * vec
        ax.plot([p_neg[0], p_pos[0]], [p_neg[1], p_pos[1]],
                color="#94A3B8", ls=(0, (4, 3)), lw=1.0, zorder=1)
        tip = pos_scale * vec
        ax.text(tip[0] - 0.10, tip[1], lbl,
                fontsize=8.5, color="#64748B", ha=ha_val, va="center",
                bbox=dict(boxstyle="round,pad=0.14", fc="#FFFFFF", ec="none", alpha=0.88))

    # L2 ball centered at 0 tangent to H_y at x_R
    theta = np.linspace(0, 2 * np.pi, 360)
    ax.fill(u_R * np.cos(theta), u_R * np.sin(theta), color=BLUE_LIGHT, alpha=0.30, zorder=1)
    ax.plot(u_R * np.cos(theta), u_R * np.sin(theta), color=BLUE, ls="--", lw=1.2, alpha=0.8, zorder=2)

    # Rotated L1 diamond expanded until its -e2 corner touches H_y at (u_R, -1.3)
    diamond_pts = np.array([r_l1 * e1, r_l1 * e2, -r_l1 * e1, -r_l1 * e2])
    ax.add_patch(Polygon(diamond_pts, closed=True, facecolor=ORANGE_LIGHT, edgecolor=ORANGE,
                         lw=1.3, ls="-.", alpha=0.42, zorder=2))

    # Orthogonal subspace axes: row(Phi) horizontal, null(Phi) vertical
    ax.annotate("", xy=(5.15, 0), xytext=(-3.25, 0),
                arrowprops=dict(arrowstyle="-|>,head_length=0.5,head_width=0.28", lw=1.5, color=SLATE), zorder=3)
    ax.annotate("", xy=(0, 3.05), xytext=(0, -2.55),
                arrowprops=dict(arrowstyle="-|>,head_length=0.5,head_width=0.28", lw=1.5, color=SLATE), zorder=3)
    draw_right_angle(ax, np.array([0.0, 0.0]), np.array([1.0, 0.0]), np.array([0.0, 1.0]), size=0.22, color=SLATE)

    ax.text(5.25, 0.16, r"$\mathrm{row}(\Phi)\;\;(\dim = M = 256)$",
            fontsize=9.8, fontweight="bold", color=DARK, va="bottom", ha="left")
    ax.text(0.0, 3.16, r"$\mathrm{null}(\Phi)\;\;(\dim = N - M = 768)$",
            fontsize=9.8, fontweight="bold", color=DARK, va="bottom", ha="center")
    ax.text(-0.18, -0.22, r"$0$", fontsize=10, fontweight="bold", color=DARK, ha="right", va="top")

    # Affine solution space H_y = x_R + null(Phi)
    ax.plot([u_R, u_R], [-2.45, 2.90], color=TEAL, lw=2.4, zorder=4)
    draw_right_angle(ax, np.array([u_R, 0.0]), np.array([-1.0, 0.0]), np.array([0.0, 1.0]), size=0.20, color=TEAL)
    ax.text(u_R + 0.18, 2.95,
            r"$\mathcal{H}_y = x_{\mathcal{R}} + \mathrm{null}(\Phi)$" + "\n" +
            r"Every $z \in \mathcal{H}_y$ satisfies $\Phi z = y$",
            fontsize=9.0, color=TEAL, fontweight="bold", va="top", ha="left",
            bbox=dict(boxstyle="round,pad=0.24", fc="#F0FDFA", ec="#99F6E4", lw=0.8))

    # Decomposition vectors: x_R along row(Phi), x_N along H_y, and x from 0
    ax.annotate("", xy=(u_R, 0), xytext=(0, 0),
                arrowprops=dict(arrowstyle="-|>,head_length=0.55,head_width=0.3", lw=2.3, color=BLUE), zorder=5)
    ax.text(u_R * 0.50, -0.24, r"$x_{\mathcal{R}} = P_{\mathcal{R}}x$" + "\n(preserved by $y=\\Phi x$)",
            fontsize=8.6, color=BLUE, fontweight="bold", ha="center", va="top",
            bbox=dict(boxstyle="round,pad=0.16", fc="#FFFFFF", ec="none", alpha=0.88))

    ax.annotate("", xy=(u_R, v_x), xytext=(u_R, 0),
                arrowprops=dict(arrowstyle="-|>,head_length=0.55,head_width=0.3", lw=2.0, color=RED, ls="--"), zorder=5)
    ax.text(u_R + 0.14, v_x * 0.45, r"$x_{\mathcal{N}} \in \mathrm{null}(\Phi)$" + "\n(erased by $\\Phi$)",
            fontsize=8.6, color=RED, fontweight="bold", ha="left", va="center")

    # Hypotenuse arrow from 0 to x
    ax.annotate("", xy=(u_R, v_x), xytext=(0, 0),
                arrowprops=dict(arrowstyle="-|>,head_length=0.5,head_width=0.26", lw=1.6, color=GREEN, alpha=0.85), zorder=5)

    # Key solution points
    ax.scatter([u_R], [v_x], s=140, marker="*", color=GREEN, edgecolors=DARK, linewidths=0.7, zorder=7)
    ax.annotate(r"True signal $x = x_{\mathcal{R}} + x_{\mathcal{N}}$",
                xy=(u_R, v_x), xytext=(u_R + 0.70, 1.85),
                fontsize=9.2, fontweight="bold", color=GREEN,
                arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.0),
                bbox=dict(boxstyle="round,pad=0.22", fc="#ECFDF5", ec="#6EE7B7", lw=0.8), zorder=8)

    ax.scatter([u_R], [0], s=85, marker="o", color=BLUE, edgecolors="#FFFFFF", linewidths=1.2, zorder=7)
    ax.annotate(r"$\hat{x}_{\mathrm{raw}} = x_{\mathcal{R}} = \Phi^+ y$" + "\n" +
                r"Min $\ell_2$-norm point on $\mathcal{H}_y$" + "\n(closest to origin $0$)",
                xy=(u_R, 0), xytext=(u_R + 0.88, -0.68),
                fontsize=8.6, color=BLUE, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.1, connectionstyle="arc3,rad=-0.12"),
                bbox=dict(boxstyle="round,pad=0.24", fc="#EFF6FF", ec="#93C5FD", lw=0.8), zorder=8)

    ax.scatter([u_R], [v_l1], s=85, marker="D", color=ORANGE, edgecolors="#FFFFFF", linewidths=1.1, zorder=7)
    ax.annotate(r"$\hat{x}_{\ell_1}$ (Min $\ell_1$-norm solution)" + "\n" +
                r"Expanding $\ell_1$ diamond touches" + "\n" +
                r"$\mathcal{H}_y$ at a coordinate-axis corner",
                xy=(u_R, v_l1), xytext=(u_R + 0.88, -1.92),
                fontsize=8.6, color=ORANGE, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.1, connectionstyle="arc3,rad=0.1"),
                bbox=dict(boxstyle="round,pad=0.24", fc="#FFF7ED", ec="#FDBA74", lw=0.8), zorder=8)

    # Small ball labels inside shapes
    ax.text(-1.25, 1.85, r"$\ell_2$ ball" + "\n" + r"$\|z\|_2 \leq \|x_{\mathcal{R}}\|_2$",
            fontsize=8.4, color=BLUE, ha="center", va="center", alpha=0.95)
    ax.text(-0.92, -0.95, r"$\ell_1$ diamond" + "\n" + r"$\|z\|_1 \leq \|\hat{x}_{\ell_1}\|_1$",
            fontsize=8.4, color=ORANGE, ha="center", va="center", alpha=0.95)

    ax.set_xlim(-3.7, 7.6)
    ax.set_ylim(-2.65, 3.65)
    ax.set_title("Orthogonal Subspace Geometry of Underdetermined Linear Measurements ($y = \\Phi x,\\; M < N$)",
                 pad=10, fontsize=11.5)
    save_fig(fig, "ch2_subspace_geometry", preview_dir)


# ---------------------------------------------------------------------------
# Figure 2: Ch 2 Sections 2.3 & 2.4 — Hand-Worked Examples 1 & 2
# ---------------------------------------------------------------------------
def make_ch2_worked_examples(preview_dir: Path | None = None) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(15.4, 4.8), gridspec_kw={"wspace": 0.34})

    # --- Panel (a): Example 1 (N=2, M=1) ---
    ax = axes[0]
    ax.set_aspect("equal")
    ax.grid(True, color=GRID, lw=0.7, zorder=0)
    ax.axhline(0, color="#94A3B8", lw=0.9, zorder=1)
    ax.axvline(0, color="#94A3B8", lw=0.9, zorder=1)

    r2 = math.sqrt(7.2)
    th = np.linspace(0, 2 * np.pi, 360)
    ax.fill(r2 * np.cos(th), r2 * np.sin(th), color=BLUE_LIGHT, alpha=0.35, zorder=1)
    ax.plot(r2 * np.cos(th), r2 * np.sin(th), color=BLUE, ls="--", lw=1.1, zorder=2)

    d_pts = np.array([[3, 0], [0, 3], [-3, 0], [0, -3]])
    ax.add_patch(Polygon(d_pts, closed=True, facecolor=ORANGE_LIGHT, edgecolor=ORANGE,
                         lw=1.2, ls="-.", alpha=0.38, zorder=2))

    t_r = np.linspace(-1.4, 1.9, 100)
    ax.plot(t_r * 1.0, t_r * 2.0, color=BLUE, ls=":", lw=1.2, alpha=0.85, label=r"$\mathrm{row}(\Phi)=\mathrm{span}([1,2]^T)$", zorder=2)
    t_n = np.linspace(-1.3, 2.3, 100)
    ax.plot(t_n * (-2.0), t_n * 1.0, color=MUTED, ls=":", lw=1.1, alpha=0.85, label=r"$\mathrm{null}(\Phi)=\mathrm{span}([-2,1]^T)$", zorder=2)
    draw_right_angle(ax, np.array([0.0, 0.0]), np.array([1.0, 2.0]), np.array([-2.0, 1.0]), size=0.35, color=MUTED)

    z1_line = np.linspace(-2.5, 6.7, 100)
    z2_line = 3.0 - 0.5 * z1_line
    ax.plot(z1_line, z2_line, color=TEAL, lw=2.3, label=r"$\mathcal{H}_y: z_1 + 2z_2 = 6$", zorder=4)

    ax.annotate("", xy=(1.2, 2.4), xytext=(0, 0),
                arrowprops=dict(arrowstyle="-|>,head_length=0.45,head_width=0.25", lw=2.0, color=BLUE), zorder=5)
    ax.annotate("", xy=(0, 3.0), xytext=(1.2, 2.4),
                arrowprops=dict(arrowstyle="-|>,head_length=0.45,head_width=0.25", lw=1.8, color=RED, ls="--"), zorder=5)
    ax.text(0.88, 1.05, r"$x_{\mathcal{R}}$", fontsize=9, fontweight="bold", color=BLUE)
    ax.text(0.55, 2.86, r"$x_{\mathcal{N}}$", fontsize=9, fontweight="bold", color=RED)

    ax.scatter([1.2], [2.4], s=65, color=BLUE, edgecolors="#FFFFFF", lw=1.0, zorder=7)
    ax.annotate(r"$\Phi^+ y = [1.2, 2.4]^T$", xy=(1.2, 2.4), xytext=(1.95, 2.15),
                fontsize=8.2, fontweight="bold", color=BLUE,
                arrowprops=dict(arrowstyle="->", color=BLUE, lw=0.9),
                bbox=dict(boxstyle="round,pad=0.18", fc="#EFF6FF", ec="#93C5FD", lw=0.7), zorder=8)

    ax.scatter([0.0], [3.0], s=120, marker="*", color=GREEN, edgecolors=DARK, lw=0.6, zorder=7)
    ax.annotate(r"$x = \hat{x}_{\ell_1} = [0, 3]^T$", xy=(0.0, 3.0), xytext=(-2.65, 3.95),
                fontsize=8.2, fontweight="bold", color=GREEN,
                arrowprops=dict(arrowstyle="->", color=GREEN, lw=0.9),
                bbox=dict(boxstyle="round,pad=0.18", fc="#ECFDF5", ec="#6EE7B7", lw=0.7), zorder=8)

    ax.scatter([6.0], [0.0], s=42, color=MUTED, zorder=6)
    ax.text(5.85, 0.35, r"$[6,0]^T$", fontsize=8, color=MUTED, ha="center")

    ax.set_xlim(-2.9, 6.8)
    ax.set_ylim(-2.9, 5.1)
    ax.set_xlabel(r"$z_1$")
    ax.set_ylabel(r"$z_2$")
    ax.set_title(r"(a) Example 1: $N=2, M=1$ ($\Phi=[1,2],\, y=6$)", pad=8, fontsize=10.5)
    ax.legend(loc="upper right", fontsize=7.5)

    # --- Panel (b): Example 2 (N=3, M=2) Sparse x = [0, 0, 3]^T ---
    ax = axes[1]
    ax.grid(True, color=GRID, lw=0.7, zorder=0)
    ts = np.linspace(-0.8, 3.3, 400)
    l1_sparse = 2.0 * np.abs(ts) + np.abs(3.0 - ts)
    l2sq_sparse = 3.0 * (ts - 1.0) ** 2 + 6.0

    ax.plot(ts, l1_sparse, color=ORANGE, lw=2.3, label=r"$\|z(t)\|_1 = 2|t| + |3-t|$", zorder=4)
    ax.plot(ts, l2sq_sparse, color=BLUE, lw=2.3, label=r"$\|z(t)\|_2^2 = 3(t-1)^2 + 6$", zorder=4)

    ax.axvline(0.0, color=GREEN, ls=":", lw=1.1, alpha=0.75)
    ax.scatter([0.0], [3.0], s=110, marker="*", color=GREEN, edgecolors=DARK, lw=0.6, zorder=7)
    ax.annotate(r"$\hat{x}_{\ell_1} = x = [0,0,3]^T$" + "\n" + r"($t=0,\; \|z\|_1=3$)",
                xy=(0.0, 3.0), xytext=(0.25, 0.8),
                fontsize=8.2, fontweight="bold", color=GREEN,
                arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.0),
                bbox=dict(boxstyle="round,pad=0.18", fc="#ECFDF5", ec="#6EE7B7", lw=0.7), zorder=8)

    ax.scatter([1.0], [6.0], s=65, color=BLUE, edgecolors="#FFFFFF", lw=1.0, zorder=7)
    ax.annotate(r"$\Phi^+ y = [1,1,2]^T$" + "\n" + r"($t=1,\; \|z\|_2^2=6$)",
                xy=(1.0, 6.0), xytext=(1.42, 7.6),
                fontsize=8.2, fontweight="bold", color=BLUE,
                arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.0),
                bbox=dict(boxstyle="round,pad=0.18", fc="#EFF6FF", ec="#93C5FD", lw=0.7), zorder=8)

    ax.set_xlim(-0.8, 3.3)
    ax.set_ylim(0.0, 15.2)
    ax.set_xlabel(r"Position $t$ along $\mathcal{H}_y$: $z(t) = [t,\; t,\; 3-t]^T$")
    ax.set_ylabel(r"Objective value along $\mathcal{H}_y$")
    ax.set_title(r"(b) Example 2: Sparse $x=[0,0,3]^T$", pad=8, fontsize=10.5)
    ax.legend(loc="upper left", fontsize=7.9)

    # --- Panel (c): Example 2 (N=3, M=2) Dense x = [1.1, 0.9, 1.9]^T ---
    ax = axes[2]
    ax.grid(True, color=GRID, lw=0.7, zorder=0)
    ts_d = np.linspace(-0.4, 2.3, 400)
    l1_dense = np.abs(ts_d) + np.abs(ts_d - 0.2) + np.abs(3.0 - ts_d)
    l2sq_dense = ts_d ** 2 + (ts_d - 0.2) ** 2 + (3.0 - ts_d) ** 2
    sq_err_dense = 3.0 * (ts_d - 1.1) ** 2

    ax.plot(ts_d, l1_dense, color=ORANGE, lw=2.2, label=r"$\|z(t)\|_1$", zorder=4)
    ax.plot(ts_d, l2sq_dense, color=BLUE, lw=2.2, label=r"$\|z(t)\|_2^2$", zorder=4)
    ax.plot(ts_d, sq_err_dense, color=RED, lw=2.0, ls="--", label=r"$\mathrm{Sq.\ Error}\; \|z(t)-x_{\mathrm{dense}}\|_2^2$", zorder=5)

    t_pinv = 1.0 + 0.2 / 3.0
    t_l1 = 0.2
    t_true = 1.1

    ax.axvline(t_true, color=GREEN, ls=":", lw=1.3, zorder=3)
    ax.scatter([t_true], [0.0], s=110, marker="*", color=GREEN, edgecolors=DARK, lw=0.6, zorder=7)
    ax.annotate(r"True $x_{\mathrm{dense}}$ ($t=1.1$)",
                xy=(t_true + 0.03, 0.04), xytext=(1.36, 0.52),
                fontsize=8.0, fontweight="bold", color=GREEN,
                arrowprops=dict(arrowstyle="->", color=GREEN, lw=0.9),
                bbox=dict(boxstyle="round,pad=0.14", fc="#ECFDF5", ec="#6EE7B7", lw=0.6), zorder=8)

    ax.scatter([t_pinv], [0.0033], s=58, color=BLUE, edgecolors="#FFFFFF", lw=0.9, zorder=7)
    ax.annotate(r"$\Phi^+ y$ ($t=1.067$)" + "\n" + r"Err $= 0.0033$",
                xy=(t_pinv, 0.08), xytext=(1.12, 2.35),
                fontsize=8.0, fontweight="bold", color=BLUE,
                arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.0),
                bbox=dict(boxstyle="round,pad=0.18", fc="#EFF6FF", ec="#93C5FD", lw=0.7), zorder=8)

    ax.scatter([t_l1], [2.43], s=65, marker="D", color=RED, edgecolors="#FFFFFF", lw=0.9, zorder=7)
    ax.scatter([t_l1], [3.0], s=55, marker="o", color=ORANGE, edgecolors="#FFFFFF", lw=0.9, zorder=7)
    ax.annotate(r"$\hat{x}_{\ell_1}$ snaps to kink $t=0.2$" + "\n" +
                r"Err $= 2.43$ ($729\times$ worse!)",
                xy=(t_l1, 2.48), xytext=(0.05, 4.45),
                fontsize=8.0, fontweight="bold", color=RED,
                arrowprops=dict(arrowstyle="->", color=RED, lw=1.0),
                bbox=dict(boxstyle="round,pad=0.18", fc="#FEF2F2", ec="#FCA5A5", lw=0.7), zorder=8)

    ax.set_xlim(-0.4, 2.3)
    ax.set_ylim(-0.35, 10.6)
    ax.set_xlabel(r"Position $t$ along $\mathcal{H}_y$: $z(t) = [t,\; t-0.2,\; 3-t]^T$")
    ax.set_ylabel("Norm / Squared error")
    ax.set_title(r"(c) Example 2: Dense $x_{\mathrm{dense}}=[1.1,0.9,1.9]^T$", pad=8, fontsize=10.5)
    ax.legend(loc="upper right", fontsize=7.8)

    save_fig(fig, "ch2_worked_examples", preview_dir)


# ---------------------------------------------------------------------------
# Figure 3: Ch 4 Section 4.3 — L2 Sphere vs. L1 Diamond
# ---------------------------------------------------------------------------
def make_ch4_l2_vs_l1_geometry(preview_dir: Path | None = None) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 5.0), gridspec_kw={"wspace": 0.20})

    z1_line = np.linspace(-3.5, 6.8, 200)
    z2_line = 3.0 - 0.5 * z1_line

    for ax in axes:
        ax.set_aspect("equal")
        ax.grid(True, color=GRID, lw=0.7, zorder=0)
        ax.axhline(0, color="#94A3B8", lw=1.0, zorder=1)
        ax.axvline(0, color="#94A3B8", lw=1.0, zorder=1)
        ax.plot(z1_line, z2_line, color=TEAL, lw=2.4, label=r"$\mathcal{H}_y:\; \Phi z = y\;\;(z_1 + 2z_2 = 6)$", zorder=4)
        ax.scatter([0.0], [3.0], s=135, marker="*", color=GREEN, edgecolors=DARK, lw=0.6, zorder=8)
        ax.set_xlim(-3.6, 6.4)
        ax.set_ylim(-3.3, 4.4)
        ax.set_xlabel(r"$z_1$")
        ax.set_ylabel(r"$z_2$")

    # Left: L2 sphere
    ax = axes[0]
    th = np.linspace(0, 2 * np.pi, 360)
    for rad, alpha_val, ls_val in [(1.5, 0.14, ":"), (math.sqrt(7.2), 0.36, "-")]:
        if ls_val == "-":
            ax.fill(rad * np.cos(th), rad * np.sin(th), color=BLUE_LIGHT, alpha=alpha_val, zorder=2)
        ax.plot(rad * np.cos(th), rad * np.sin(th), color=BLUE, ls=ls_val, lw=1.8 if ls_val == "-" else 1.1, zorder=3)

    ax.annotate("", xy=(1.2, 2.4), xytext=(0, 0),
                arrowprops=dict(arrowstyle="-|>,head_length=0.45,head_width=0.25", lw=1.8, color=BLUE), zorder=5)
    draw_right_angle(ax, np.array([1.2, 2.4]), np.array([-1.2, -2.4]), np.array([2.0, -1.0]), size=0.35, color=BLUE)
    ax.scatter([1.2], [2.4], s=80, color=BLUE, edgecolors="#FFFFFF", lw=1.1, zorder=8)
    ax.annotate(r"$\hat{x}_{\mathrm{raw}} = \Phi^+ y = [1.2, 2.4]^T$" + "\n(Dense interior tangency!)",
                xy=(1.2, 2.4), xytext=(1.9, 3.15),
                fontsize=8.6, fontweight="bold", color=BLUE,
                arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.0),
                bbox=dict(boxstyle="round,pad=0.2", fc="#EFF6FF", ec="#93C5FD", lw=0.8), zorder=9)
    ax.text(-2.95, 3.45, r"True sparse $x = [0, 3]^T$" + "\n(missed by $\\ell_2$!)",
            fontsize=8.4, color=GREEN, fontweight="bold")
    ax.text(0.0, -2.05, r"$\ell_2$ ball $\|z\|_2 \leq \sqrt{7.2}$", fontsize=8.8, color=BLUE,
            ha="center", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.16", fc="#FFFFFF", ec="none", alpha=0.86), zorder=6)
    ax.set_title(r"Pseudo-Inverse: Expanding $\ell_2$ Sphere", pad=8)
    ax.legend(loc="lower right", fontsize=8.2)

    # Right: L1 diamond
    ax = axes[1]
    for rad, fill_a, ls_val in [(1.6, 0.0, ":"), (3.0, 0.36, "-")]:
        pts = np.array([[rad, 0], [0, rad], [-rad, 0], [0, -rad]])
        if fill_a > 0:
            ax.add_patch(Polygon(pts, closed=True, facecolor=ORANGE_LIGHT, edgecolor=ORANGE, lw=1.9, alpha=fill_a, zorder=2))
        ax.plot(np.append(pts[:, 0], pts[0, 0]), np.append(pts[:, 1], pts[0, 1]),
                color=ORANGE, ls=ls_val, lw=1.9 if ls_val == "-" else 1.1, zorder=3)

    ax.scatter([1.2], [2.4], s=50, color=BLUE, alpha=0.75, zorder=6)
    ax.text(1.42, 2.55, r"$\Phi^+ y$ ($\|z\|_1=3.6 > 3$)", fontsize=8.0, color=BLUE)

    ax.annotate(r"$\hat{x}_{\mathrm{BP}} = x = [0, 3]^T$" + "\n(Sharp corner touches $\\mathcal{H}_y$!)",
                xy=(0.0, 3.0), xytext=(1.55, 3.35),
                fontsize=8.6, fontweight="bold", color=ORANGE,
                arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.0),
                bbox=dict(boxstyle="round,pad=0.2", fc="#FFF7ED", ec="#FDBA74", lw=0.8), zorder=9)
    ax.text(0.0, -2.05, r"$\ell_1$ diamond $|z_1| + |z_2| \leq 3$", fontsize=8.8, color=ORANGE,
            ha="center", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.16", fc="#FFFFFF", ec="none", alpha=0.86), zorder=6)
    ax.text(4.05, 2.15, r"Slope of $\mathcal{H}_y$: $-\frac{1}{2}$" + "\n(flatter than diamond $\\pm 1$)",
            fontsize=8.1, color=TEAL, ha="center",
            bbox=dict(boxstyle="round,pad=0.18", fc="#F0FDFA", ec="#99F6E4", lw=0.7), zorder=6)
    ax.set_title(r"Basis Pursuit: Expanding $\ell_1$ Diamond", pad=8)
    ax.legend(loc="lower right", fontsize=8.2)

    save_fig(fig, "ch4_l2_vs_l1_geometry", preview_dir)


# ---------------------------------------------------------------------------
# Figure 4: Ch 4 Sections 4.7 & 4.9 — Donoho-Tanner Phase Transition
# ---------------------------------------------------------------------------
def dt_point(t: float) -> tuple[float, float]:
    phi = math.exp(-0.5 * t * t) / math.sqrt(2.0 * math.pi)
    phi_m = 0.5 * (1.0 + math.erf(-t / math.sqrt(2.0)))
    ratio = 2.0 * (phi - t * phi_m) / t
    gamma = ratio / (1.0 + ratio)
    delta = gamma * (1.0 + t * t) + 2.0 * (1.0 - gamma) * ((1.0 + t * t) * phi_m - t * phi)
    rho = gamma / delta
    return delta, rho


def fista_basis_pursuit(Phi: np.ndarray, y: np.ndarray, lam_final: float = 1e-4,
                        stages: int = 5, iter_per_stage: int = 120) -> np.ndarray:
    _, N = Phi.shape
    L = np.linalg.norm(Phi, ord=2) ** 2
    alpha = 1.0 / L
    lam_start = 0.2 * np.max(np.abs(Phi.T @ y))
    lams = np.geomspace(lam_start, lam_final, stages)
    z = np.zeros(N)
    for lam in lams:
        tau = alpha * lam
        w = z.copy()
        t = 1.0
        for _ in range(iter_per_stage):
            grad = Phi.T @ (Phi @ w - y)
            u = w - alpha * grad
            z_next = np.sign(u) * np.maximum(np.abs(u) - tau, 0.0)
            t_next = 0.5 * (1.0 + np.sqrt(1.0 + 4.0 * t * t))
            w = z_next + ((t - 1.0) / t_next) * (z_next - z)
            z, t = z_next, t_next
    return z


def make_ch4_donoho_tanner(preview_dir: Path | None = None) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(14.8, 4.5), gridspec_kw={"wspace": 0.27})

    # --- Panel (a): Theoretical Donoho-Tanner Phase Diagram ---
    ax = axes[0]
    ts = np.geomspace(0.03, 4.2, 250)
    pts = np.array([dt_point(float(t)) for t in ts])
    order = np.argsort(pts[:, 0])
    deltas = pts[order, 0]
    rhos = pts[order, 1]

    ax.fill_between(deltas, 0, rhos, color=GREEN_LIGHT, alpha=0.55, label=r"Exact $\ell_1$ recovery ($\mathrm{Prob}\to 1$)")
    ax.fill_between(deltas, rhos, 1.0, color=RED_LIGHT, alpha=0.50, label=r"$\ell_1$ recovery fails ($\mathrm{Prob}\to 1$)")
    ax.plot(deltas, rhos, color=DARK, lw=2.4, label=r"Phase boundary $\rho_W(\delta)$")

    ax.axvline(0.25, color=RED, ls="--", lw=1.3, zorder=3)
    for d_val, r_val, k_txt in [
        (0.10, 0.1894, None),
        (0.25, 0.2674, r"$r=0.25:\;\rho_W\approx 0.267$" + "\n" + r"($k_{\max}\approx 68$ at $N=1024$)"),
        (0.50, 0.3857, None),
        (0.75, 0.5337, None),
    ]:
        ms = 115 if abs(d_val - 0.25) < 1e-6 else 45
        col = RED if abs(d_val - 0.25) < 1e-6 else DARK
        mk = "*" if abs(d_val - 0.25) < 1e-6 else "o"
        ax.scatter([d_val], [r_val], s=ms, marker=mk, color=col, zorder=6)
        if k_txt:
            ax.annotate(k_txt, xy=(d_val, r_val), xytext=(0.31, 0.10),
                        fontsize=8.2, fontweight="bold", color=RED,
                        arrowprops=dict(arrowstyle="->", color=RED, lw=1.0),
                        bbox=dict(boxstyle="round,pad=0.22", fc="#FEF2F2", ec="#FCA5A5", lw=0.8), zorder=7)

    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.grid(True, color=GRID, lw=0.6)
    ax.set_xlabel(r"Undersampling ratio $\delta = M/N$")
    ax.set_ylabel(r"Sparsity / measurement ratio $\rho = k/M$")
    ax.set_title("(a) Donoho–Tanner Phase Diagram", pad=8)
    ax.legend(loc="upper left", fontsize=7.8)

    # --- Run Section 4.9 sweep (N=256, M=64, r=0.25) with 100 trials for smooth empirical curve ---
    rng = np.random.default_rng(7)
    N, M = 256, 64
    ks = [4, 6, 8, 10, 12, 14, 15, 16, 18, 20, 24, 32, 48, 64]
    succ_rates, l1_means, pinv_means = [], [], []
    trials = 100
    for k in ks:
        l1_errs, pinv_errs, successes = [], [], 0
        for _ in range(trials):
            Phi = rng.normal(0.0, 1.0 / np.sqrt(M), size=(M, N))
            x = np.zeros(N)
            supp = rng.choice(N, size=k, replace=False)
            x[supp] = rng.standard_normal(k)
            y = Phi @ x
            x_l1 = fista_basis_pursuit(Phi, y, lam_final=1e-4)
            x_raw = np.linalg.pinv(Phi) @ y
            rel_l1 = np.linalg.norm(x_l1 - x) / np.linalg.norm(x)
            rel_pinv = np.linalg.norm(x_raw - x) / np.linalg.norm(x)
            l1_errs.append(rel_l1)
            pinv_errs.append(rel_pinv)
            if rel_l1 < 1e-2:
                successes += 1
        succ_rates.append(100.0 * successes / trials)
        l1_means.append(float(np.mean(l1_errs)))
        pinv_means.append(float(np.mean(pinv_errs)))

    k_arr = np.array(ks)
    rho_arr = k_arr / M
    rho_crit = 0.2674
    k_crit_theory = rho_crit * M  # ~17.1

    # --- Panel (b): Success Rate Cliff ---
    ax = axes[1]
    ax.grid(True, color=GRID, lw=0.7, zorder=0)
    ax.axvspan(0, k_crit_theory, color=GREEN_LIGHT, alpha=0.25, zorder=1)
    ax.axvspan(k_crit_theory, 66, color=RED_LIGHT, alpha=0.20, zorder=1)
    ax.axvline(k_crit_theory, color=RED, ls="--", lw=1.5, zorder=3)
    ax.plot(k_arr, succ_rates, color=ORANGE, lw=2.3, marker="o", ms=5.0, zorder=5,
            label=r"$\ell_1$ Basis Pursuit ($N=256, M=64$)")
    ax.annotate(r"Asymptotic DT limit" + "\n" + r"$k_{\max} \approx 0.267M \approx 17.1$",
                xy=(k_crit_theory, 84), xytext=(24, 80),
                fontsize=8.1, fontweight="bold", color=RED,
                arrowprops=dict(arrowstyle="->", color=RED, lw=1.0),
                bbox=dict(boxstyle="round,pad=0.2", fc="#FEF2F2", ec="#FCA5A5", lw=0.7), zorder=7)
    ax.set_xlim(0, 66)
    ax.set_ylim(-5, 108)
    ax.set_xlabel(r"True Sparsity $k$ (at $M=64, N=256$)")
    ax.set_ylabel(r"Exact Recovery Rate ($\mathrm{rel\ err} < 10^{-2}$, %)")
    ax.set_title("(b) Sharp $\\ell_1$ Recovery Cliff ($r = 0.25$)", pad=8)
    ax.legend(loc="center right", fontsize=7.9)

    # --- Panel (c): Relative Error Comparison ---
    ax = axes[2]
    ax.grid(True, color=GRID, lw=0.7, zorder=0)
    ax.axvline(rho_crit, color=RED, ls="--", lw=1.5, zorder=2, label=r"DT limit $\rho_W(0.25)\approx 0.267$")
    ax.axhline(math.sqrt(1.0 - M / N), color=BLUE, ls=":", lw=1.4, alpha=0.85,
               label=r"Pinv theory $\sqrt{1-r}\approx 0.866$")
    ax.plot(rho_arr, l1_means, color=ORANGE, lw=2.3, marker="o", ms=4.8, zorder=5, label=r"$\ell_1$ Basis Pursuit")
    ax.plot(rho_arr, pinv_means, color=BLUE, lw=2.1, marker="s", ms=4.3, zorder=4, label=r"Raw Pseudo-Inverse $\Phi^+ y$")

    ax.set_xlim(0.0, 1.04)
    ax.set_ylim(-0.04, 1.02)
    ax.set_xlabel(r"Measurement load $\rho = k/M$")
    ax.set_ylabel(r"Mean Relative $\ell_2$ Error $\|\hat{x}-x\|_2 / \|x\|_2$")
    ax.set_title("(c) Reconstruction Error Across Transition", pad=8)
    ax.legend(loc="lower right", fontsize=7.8)

    save_fig(fig, "ch4_donoho_tanner_phase_transition", preview_dir)


# ---------------------------------------------------------------------------
# Figure 5: Ch 5 Section 5.2 — Soft-Thresholding Operator
# ---------------------------------------------------------------------------
def make_ch5_soft_thresholding(preview_dir: Path | None = None) -> None:
    fig, ax = plt.subplots(figsize=(7.4, 5.2))
    ax.set_aspect("equal")
    ax.grid(True, color=GRID, lw=0.7, zorder=0)

    u = np.linspace(-3.2, 3.2, 600)
    s_tau = np.sign(u) * np.maximum(np.abs(u) - 1.0, 0.0)

    ax.axvspan(-1.0, 1.0, color=ORANGE_LIGHT, alpha=0.45, zorder=1, label=r"Deadzone $[-\tau, +\tau]$ (exact $0$)")
    ax.axhline(0, color="#94A3B8", lw=1.0, zorder=2)
    ax.axvline(0, color="#94A3B8", lw=1.0, zorder=2)

    ax.plot(u, u, color=MUTED, ls="--", lw=1.6, zorder=3, label=r"Identity $z_j = u_j$")
    ax.plot(u, s_tau, color=ORANGE, lw=3.0, zorder=5, label=r"Soft-Thresholding $\mathcal{S}_\tau(u_j)$")

    for x_pos, y_curve, y_id, lbl_pos in [(2.2, 1.2, 2.2, (2.32, 1.7)), (-2.2, -1.2, -2.2, (-2.88, -1.7))]:
        ax.annotate("", xy=(x_pos, y_curve), xytext=(x_pos, y_id),
                    arrowprops=dict(arrowstyle="<->", color=BLUE, lw=1.5), zorder=6)
        ax.text(lbl_pos[0], lbl_pos[1], r"$\tau = \alpha\lambda$", fontsize=9.5, fontweight="bold",
                color=BLUE, va="center")

    ax.plot([-1.0, 1.0], [0.0, 0.0], color=ORANGE, lw=4.5, zorder=6)
    ax.scatter([-1.0, 1.0], [0.0, 0.0], s=50, color=ORANGE, zorder=7)

    ax.annotate("Deadzone $[-\\tau, +\\tau]$:\nsnapped to exact $0$",
                xy=(0.0, 0.05), xytext=(-0.05, 1.15), ha="center",
                fontsize=8.8, fontweight="bold", color=ORANGE,
                arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.1),
                bbox=dict(boxstyle="round,pad=0.22", fc="#FFF7ED", ec="#FDBA74", lw=0.8), zorder=8)

    ax.text(2.15, 0.65, "Slope $= 1$\n($u_j - \\tau$)", fontsize=8.8, color=DARK, fontweight="bold", ha="left")
    ax.text(-2.95, -0.55, "Slope $= 1$\n($u_j + \\tau$)", fontsize=8.8, color=DARK, fontweight="bold", ha="left")

    ticks = [-3, -2, -1, 0, 1, 2, 3]
    tick_labels = [r"$-3\tau$", r"$-2\tau$", r"$-\tau$", r"$0$", r"$\tau$", r"$2\tau$", r"$3\tau$"]
    ax.set_xticks(ticks)
    ax.set_xticklabels(tick_labels)
    y_ticks = [-2, -1, 0, 1, 2]
    y_labels = [r"$-2\tau$", r"$-\tau$", r"$0$", r"$\tau$", r"$2\tau$"]
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels)

    ax.set_xlim(-3.2, 3.2)
    ax.set_ylim(-2.6, 2.6)
    ax.set_xlabel(r"Forward gradient input $u_j$")
    ax.set_ylabel(r"Thresholded output $\mathcal{S}_\tau(u_j)$")
    ax.set_title(r"Soft-Thresholding Proximal Operator $\mathcal{S}_\tau(u_j) = \mathrm{sign}(u_j)\max(|u_j| - \tau, 0)$", pad=10)
    ax.legend(loc="upper left", fontsize=8.6)

    save_fig(fig, "ch5_soft_thresholding", preview_dir)


# ---------------------------------------------------------------------------
# Figure 6: Ch 5 Section 5.7 — ISTA vs. FISTA Convergence
# ---------------------------------------------------------------------------
def make_ch5_ista_vs_fista(preview_dir: Path | None = None) -> None:
    rng = np.random.default_rng(42)
    N, M, k = 1024, 256, 32
    Phi = rng.normal(0.0, 1.0 / np.sqrt(M), size=(M, N))
    x_true = np.zeros(N)
    supp = rng.choice(N, size=k, replace=False)
    x_true[supp] = rng.standard_normal(k)
    y = Phi @ x_true

    lam_max = np.max(np.abs(Phi.T @ y))
    L = np.linalg.norm(Phi, ord=2) ** 2
    alpha = 1.0 / L

    def soft_thresh(u: np.ndarray, tau: float) -> np.ndarray:
        return np.sign(u) * np.maximum(np.abs(u) - tau, 0.0)

    def lasso_obj(z: np.ndarray, lam: float) -> float:
        return float(0.5 * np.sum((Phi @ z - y) ** 2) + lam * np.sum(np.abs(z)))

    lam = 0.02 * lam_max
    tau = alpha * lam
    max_iters = 300

    z_ref = np.zeros(N)
    w_ref = np.zeros(N)
    t_ref = 1.0
    for _ in range(2000):
        z_next = soft_thresh(w_ref - alpha * (Phi.T @ (Phi @ w_ref - y)), tau)
        t_next = 0.5 * (1.0 + np.sqrt(1.0 + 4.0 * t_ref * t_ref))
        w_ref = z_next + ((t_ref - 1.0) / t_next) * (z_next - z_ref)
        z_ref, t_ref = z_next, t_next
    F_star = lasso_obj(z_ref, lam)

    z_ista = np.zeros(N)
    z_fista = np.zeros(N)
    w_fista = np.zeros(N)
    t_fista = 1.0

    iters = np.arange(1, max_iters + 1)
    gaps_ista, gaps_fista = [], []
    errs_ista, errs_fista = [], []
    x_norm = np.linalg.norm(x_true)

    for _ in iters:
        z_ista = soft_thresh(z_ista - alpha * (Phi.T @ (Phi @ z_ista - y)), tau)
        z_next = soft_thresh(w_fista - alpha * (Phi.T @ (Phi @ w_fista - y)), tau)
        t_next = 0.5 * (1.0 + np.sqrt(1.0 + 4.0 * t_fista * t_fista))
        w_fista = z_next + ((t_fista - 1.0) / t_next) * (z_next - z_fista)
        z_fista, t_fista = z_next, t_next

        gaps_ista.append(max(lasso_obj(z_ista, lam) - F_star, 1e-12))
        gaps_fista.append(max(lasso_obj(z_fista, lam) - F_star, 1e-12))
        errs_ista.append(np.linalg.norm(z_ista - x_true) / x_norm)
        errs_fista.append(np.linalg.norm(z_fista - x_true) / x_norm)

    x_raw = np.linalg.pinv(Phi) @ y
    err_pinv = np.linalg.norm(x_raw - x_true) / x_norm
    err_lasso_star = np.linalg.norm(z_ref - x_true) / x_norm

    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.7), gridspec_kw={"wspace": 0.25})

    # --- Panel (a): Objective Gap (log-log) ---
    ax = axes[0]
    ax.grid(True, which="both", color=GRID, lw=0.6, zorder=0)
    ax.loglog(iters, gaps_ista, color=PURPLE, lw=2.3, label=r"ISTA ($O(1/k)$ rate)", zorder=4)
    ax.loglog(iters, gaps_fista, color=ORANGE, lw=2.3, label=r"FISTA ($O(1/k^2)$ rate)", zorder=5)

    k_ref = np.array([10.0, 250.0])
    ax.loglog(k_ref, 22.0 / k_ref, color=PURPLE, ls="--", lw=1.1, alpha=0.65, label=r"Reference slope $\propto 1/k$")
    ax.loglog(k_ref, 200.0 / (k_ref ** 2), color=ORANGE, ls="--", lw=1.1, alpha=0.65, label=r"Reference slope $\propto 1/k^2$")

    ax.axvline(50, color=MUTED, ls=":", lw=1.2, zorder=3)
    ax.scatter([50, 50], [gaps_ista[49], gaps_fista[49]], s=55, color=[PURPLE, ORANGE], edgecolors="#FFFFFF", lw=0.9, zorder=7)
    ax.annotate(f"Iter 50:\nFISTA = {gaps_fista[49]:.2e}\nISTA  = {gaps_ista[49]:.2e}",
                xy=(50, gaps_fista[49]), xytext=(7.5, 5e-4),
                fontsize=8.2, fontweight="bold", color=DARK,
                arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.0),
                bbox=dict(boxstyle="round,pad=0.22", fc="#FFF7ED", ec="#FDBA74", lw=0.8), zorder=8)

    ax.set_xlim(1, 320)
    ax.set_ylim(1e-10, 40)
    ax.set_xlabel(r"Iteration $k$ (log scale)")
    ax.set_ylabel(r"LASSO Optimality Gap $F(z^{(k)}) - F^*$ (log scale)")
    ax.set_title(r"(a) Objective Convergence ($N=1024, M=256, k=32$)", pad=8)
    ax.legend(loc="lower left", fontsize=7.9)

    # --- Panel (b): Signal Recovery Error ---
    ax = axes[1]
    ax.grid(True, color=GRID, lw=0.7, zorder=0)
    ax.axhline(err_pinv, color=BLUE, ls=":", lw=1.5, label=rf"Raw Pseudo-Inverse ($\approx {err_pinv:.2f}$)", zorder=2)
    ax.axhline(err_lasso_star, color=GREEN, ls="--", lw=1.3, label=rf"LASSO fixed-point floor ($z^*$: {err_lasso_star:.3f})", zorder=2)
    ax.plot(iters, errs_ista, color=PURPLE, lw=2.3, label="ISTA", zorder=4)
    ax.plot(iters, errs_fista, color=ORANGE, lw=2.3, label="FISTA", zorder=5)
    ax.axvline(50, color=MUTED, ls=":", lw=1.2, zorder=3)

    ax.annotate("Non-monotone ripple\n(momentum overshoot\nnear $k=50$)",
                xy=(52, errs_fista[51]), xytext=(142, 0.56),
                fontsize=8.1, color=ORANGE, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.0, connectionstyle="arc3,rad=-0.12"),
                bbox=dict(boxstyle="round,pad=0.2", fc="#FFF7ED", ec="#FDBA74", lw=0.7), zorder=8)

    ax.set_xlim(0, 305)
    ax.set_ylim(0.0, 1.02)
    ax.set_xlabel(r"Iteration $k$")
    ax.set_ylabel(r"Relative Recovery Error $\|z^{(k)} - x\|_2 / \|x\|_2$")
    ax.set_title(r"(b) Signal Recovery Trajectory ($\lambda = 0.02\lambda_{\max}$)", pad=8)
    ax.legend(loc="upper right", fontsize=8.0)

    save_fig(fig, "ch5_ista_vs_fista", preview_dir)


# ---------------------------------------------------------------------------
# Figure 7: Ch 6 Section 6.7 — Full Head-to-Head Benchmark
# ---------------------------------------------------------------------------
def make_ch6_decoder_benchmark(preview_dir: Path | None = None) -> None:
    rng = np.random.default_rng(2026)
    N, M = 1024, 256
    r = M / N
    scale = N / M

    Phi = rng.normal(0.0, 1.0 / np.sqrt(M), size=(M, N))
    Phi_pinv = Phi.T @ np.linalg.inv(Phi @ Phi.T)
    L = np.linalg.norm(Phi, ord=2) ** 2
    alpha = 1.0 / L

    def fista_decode(y: np.ndarray, eta_lam: float, max_iter: int = 100) -> np.ndarray:
        lam = eta_lam * np.max(np.abs(Phi.T @ y))
        tau = alpha * lam
        z = np.zeros(N)
        w = np.zeros(N)
        t = 1.0
        for _ in range(max_iter):
            u = w - alpha * (Phi.T @ (Phi @ w - y))
            z_next = np.sign(u) * np.maximum(np.abs(u) - tau, 0.0)
            t_next = 0.5 * (1.0 + np.sqrt(1.0 + 4.0 * t * t))
            w = z_next + ((t - 1.0) / t_next) * (z_next - z)
            z, t = z_next, t_next
        return z

    def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        return float(np.dot(a, b) / (na * nb)) if na > 0 and nb > 0 else 0.0

    x_k32 = np.zeros(N)
    x_k32[rng.choice(N, 32, replace=False)] = rng.standard_normal(32)
    x_k128 = np.zeros(N)
    x_k128[rng.choice(N, 128, replace=False)] = rng.standard_normal(128)
    x_lap = rng.laplace(0.0, 1.0, size=N)
    x_gauss = rng.standard_normal(N)

    signals = [
        ("Sparse\n(k=32)", x_k32),
        ("Sparse\n(k=128)", x_k128),
        ("Laplace\nBlock", x_lap),
        ("Gaussian\nBlock", x_gauss),
    ]

    k_effs, top68_pcts = [], []
    cos_pinv, cos_bp, cos_lasso = [], [], []
    mse_raw, mse_bp, mse_lasso = [], [], []

    for _, x in signals:
        k_effs.append(float((np.sum(np.abs(x)) ** 2) / np.sum(x ** 2)))
        top68_idx = np.argsort(np.abs(x))[-68:]
        top68_pcts.append(float(100.0 * np.sum(x[top68_idx] ** 2) / np.sum(x ** 2)))

        y = Phi @ x
        x_raw = Phi_pinv @ y
        x_pinv = scale * x_raw
        x_bp = fista_decode(y, eta_lam=0.005, max_iter=100)
        x_la = fista_decode(y, eta_lam=0.10, max_iter=100)

        cos_pinv.append(cosine_sim(x_pinv, x))
        cos_bp.append(cosine_sim(x_bp, x))
        cos_lasso.append(cosine_sim(x_la, x))

        x_sq = float(np.sum(x ** 2))
        mse_raw.append(float(np.sum((x_raw - x) ** 2) / x_sq))
        mse_bp.append(float(np.sum((x_bp - x) ** 2) / x_sq))
        mse_lasso.append(float(np.sum((x_la - x) ** 2) / x_sq))

    labels = [s[0] for s in signals]
    idx = np.arange(len(labels))
    w_bar = 0.25

    fig, axes = plt.subplots(1, 3, figsize=(15.0, 4.8), gridspec_kw={"wspace": 0.27})

    # --- Panel (a): Effective Sparsity vs. Donoho-Tanner Ceiling ---
    ax = axes[0]
    ax.grid(True, axis="y", color=GRID, lw=0.7, zorder=0)
    bar_colors = [GREEN, ORANGE, RED, RED]
    bars = ax.bar(idx, k_effs, width=0.52, color=bar_colors, alpha=0.85, edgecolor=DARK, lw=0.6, zorder=3)
    ax.axhline(68, color=RED, ls="--", lw=1.6, zorder=4, label=r"Donoho–Tanner limit $k_{\max}\approx 68$")
    for i, b in enumerate(bars):
        lbl = f"$k_{{\\mathrm{{eff}}}}={k_effs[i]:.1f}$\n(Top68: {top68_pcts[i]:.0f}%)"
        if i == 0:
            ax.annotate(lbl, xy=(b.get_x() + b.get_width() / 2, b.get_height()),
                        xytext=(b.get_x() + b.get_width() / 2, 225),
                        ha="center", va="bottom", fontsize=7.5, fontweight="bold", color=DARK,
                        arrowprops=dict(arrowstyle="->", color=MUTED, lw=0.9),
                        bbox=dict(boxstyle="round,pad=0.14", fc="#FFFFFF", ec="#CBD5E1", lw=0.6), zorder=6)
        else:
            y_pos = max(b.get_height() + 18, 96)
            ax.text(b.get_x() + b.get_width() / 2, y_pos, lbl,
                    ha="center", va="bottom", fontsize=7.5, fontweight="bold", color=DARK,
                    bbox=dict(boxstyle="round,pad=0.1", fc="#FFFFFF", ec="none", alpha=0.85), zorder=6)
    ax.set_xticks(idx)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 790)
    ax.set_ylabel(r"Effective Sparsity $k_{\mathrm{eff}} = (\|x\|_1/\|x\|_2)^2$")
    ax.set_title("(a) Gradient Sparsity vs. $k_{\\max} \\approx 68$", pad=8)
    ax.legend(loc="upper left", fontsize=8.0)

    # --- Panel (b): Cosine Similarity ---
    ax = axes[1]
    ax.grid(True, axis="y", color=GRID, lw=0.7, zorder=0)
    b1 = ax.bar(idx - w_bar, cos_pinv, width=w_bar, color=BLUE, edgecolor=DARK, lw=0.5, label=r"Pseudo-Inverse", zorder=3)
    b2 = ax.bar(idx, cos_bp, width=w_bar, color=ORANGE, edgecolor=DARK, lw=0.5, label=r"FISTA (BP, $\eta=0.005$)", zorder=3)
    b3 = ax.bar(idx + w_bar, cos_lasso, width=w_bar, color=PURPLE, edgecolor=DARK, lw=0.5, label=r"FISTA (LASSO, $\eta=0.10$)", zorder=3)
    ax.axhline(math.sqrt(r), color=BLUE, ls="--", lw=1.3, zorder=4, label=r"Pinv theory $\sqrt{r} = 0.50$")
    for grp in [b1, b2, b3]:
        for b in grp:
            h = b.get_height()
            ax.text(b.get_x() + b.get_width() / 2, h + 0.018, f"{h:.2f}",
                    ha="center", va="bottom", fontsize=7.1, rotation=90,
                    bbox=dict(boxstyle="square,pad=0.04", fc="#FFFFFF", ec="none", alpha=0.85), zorder=6)
    ax.set_xticks(idx)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1.24)
    ax.set_ylabel(r"Cosine Similarity $\cos(\hat{x}, x)$ (Higher = Better)")
    ax.set_title("(b) Directional Alignment Across Regimes", pad=8)
    ax.legend(loc="upper right", fontsize=7.5)

    # --- Panel (c): Normalized Single-Block MSE ---
    ax = axes[2]
    ax.grid(True, axis="y", color=GRID, lw=0.7, zorder=0)
    m1 = ax.bar(idx - w_bar, mse_raw, width=w_bar, color=BLUE, edgecolor=DARK, lw=0.5, label=r"Raw Pinv $\Phi^+ y$", zorder=3)
    m2 = ax.bar(idx, mse_bp, width=w_bar, color=ORANGE, edgecolor=DARK, lw=0.5, label=r"FISTA (BP, $\eta=0.005$)", zorder=3)
    m3 = ax.bar(idx + w_bar, mse_lasso, width=w_bar, color=PURPLE, edgecolor=DARK, lw=0.5, label=r"FISTA (LASSO, $\eta=0.10$)", zorder=3)
    ax.axhline(1.0 - r, color=BLUE, ls="--", lw=1.3, zorder=4, label=r"Raw Pinv theory $1 - r = 0.75$")
    for grp in [m1, m2, m3]:
        for b in grp:
            h = b.get_height()
            ax.text(b.get_x() + b.get_width() / 2, h + 0.018, f"{h:.2f}",
                    ha="center", va="bottom", fontsize=7.1, rotation=90,
                    bbox=dict(boxstyle="square,pad=0.04", fc="#FFFFFF", ec="none", alpha=0.85), zorder=6)
    ax.set_xticks(idx)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1.24)
    ax.set_ylabel(r"Relative MSE $\|\hat{x} - x\|_2^2 / \|x\|_2^2$ (Lower = Better)")
    ax.set_title("(c) Single-Block Reconstruction Error", pad=8)
    ax.legend(loc="upper left", fontsize=7.5)

    save_fig(fig, "ch6_decoder_benchmark", preview_dir)


def main() -> None:
    configure_style()
    preview_env = os.environ.get("PREVIEW_PNG_DIR")
    preview_dir = Path(preview_env) if preview_env else None

    make_ch2_subspace_geometry(preview_dir)
    make_ch2_worked_examples(preview_dir)
    make_ch4_l2_vs_l1_geometry(preview_dir)
    make_ch4_donoho_tanner(preview_dir)
    make_ch5_soft_thresholding(preview_dir)
    make_ch5_ista_vs_fista(preview_dir)
    make_ch6_decoder_benchmark(preview_dir)


if __name__ == "__main__":
    main()
