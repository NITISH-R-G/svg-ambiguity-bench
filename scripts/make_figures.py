"""Generate publication figures from the live corpus.

One figure per completed subsystem. Every figure is regenerated from the corpus rather
than drawn by hand, so a figure that stops matching the data becomes a broken build
rather than a stale illustration.

This script lives in `scripts/` and not in `svgbench.reporting` on purpose. Figures need
the renderer; the reporting path must not import one, because Tier-1 and Tier-2
reproduction promise that every published number can be re-derived with no SVG toolchain
installed. A test enforces that boundary.

Usage:
    python scripts/make_figures.py
"""

from __future__ import annotations

import io
from collections import Counter
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import resvg_py
from PIL import Image

from svgbench.config import load_config
from svgbench.generation import generate_corpus
from svgbench.geometry import measure_document
from svgbench.groundtruth import build_corpus_ground_truth

# Headless: chosen after import but before any figure exists, which is supported and
# keeps every import at the top of the file.
matplotlib.use("Agg")

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT = REPO_ROOT / "assets" / "figures"
BASE = REPO_ROOT / "configs" / "base.yaml"

INK = "#1a1a1a"
MUTED = "#8a8a8a"
ACCENT = "#c0392b"
COOL = "#2c6fa8"
GRID = "#dcdcdc"

plt.rcParams.update(
    {
        "figure.dpi": 200,
        "savefig.dpi": 200,
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.edgecolor": MUTED,
        "axes.labelcolor": INK,
        "axes.titlesize": 10,
        "axes.titleweight": "bold",
        "text.color": INK,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "axes.axisbelow": True,
    }
)


def _render(svg_text: str, size: int) -> np.ndarray:
    png = bytes(resvg_py.svg_to_bytes(svg_string=svg_text))
    return np.asarray(Image.open(io.BytesIO(png)).convert("RGBA"))


def figure_one_ambiguity(corpus, truths) -> None:  # type: ignore[no-untyped-def]
    """The phenomenon itself: the picture has an answer, the markup does not."""
    sample = next(s for s in corpus if s.k == 4)
    measured = measure_document(sample.resolved_svg, sample.canvas_size, scale=1)
    members = {e.element_id for e in sample.ambiguity_elements}

    fig, (left, right) = plt.subplots(1, 2, figsize=(9.5, 4.4))

    left.imshow(_render(sample.resolved_svg, sample.canvas_size))
    for element_id in members:
        geometry = measured[element_id]
        x, y = geometry.centroid
        x0, y0, x1, y1 = geometry.analytic.bbox
        # Size the ring to the shape it marks. A fixed radius swamps the small members
        # and is overflowed by the large ones, which reads as sloppy annotation and,
        # worse, visually misrepresents the size differences the ordinal family uses.
        radius = 0.5 * max(x1 - x0, y1 - y0) + 10
        left.add_patch(
            plt.Circle((x, y), radius, fill=False, color=ACCENT, linewidth=1.5, linestyle="--")
        )
    left.set_title("What the instruction refers to", loc="left")
    left.set_xticks([])
    left.set_yticks([])
    left.grid(False)
    left.text(
        0.5,
        -0.06,
        f"the {len(members)} circled shapes share one fill",
        transform=left.transAxes,
        ha="center",
        color=MUTED,
        fontsize=8,
    )

    lines = [ln for ln in sample.model_visible_svg.splitlines() if "<path" in ln]
    right.set_title("What the model receives", loc="left")
    right.axis("off")
    for i, line in enumerate(lines):
        is_member = any(m in line for m in members)
        right.text(
            0.0,
            0.93 - i * 0.085,
            line.strip(),
            transform=right.transAxes,
            family="monospace",
            fontsize=7.2,
            color=ACCENT if is_member else MUTED,
        )
    right.text(
        0.0,
        0.93 - len(lines) * 0.085 - 0.06,
        "identical tag, identical fill, opaque fixed-length geometry.\n"
        "nothing here says which one is top-left.",
        transform=right.transAxes,
        fontsize=8,
        color=INK,
    )

    fig.suptitle(
        "Figure 1  -  the information gap this instrument measures",
        x=0.02,
        ha="left",
        fontsize=11,
        fontweight="bold",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(OUT / "fig01_ambiguity.png", bbox_inches="tight")
    plt.close(fig)


def figure_two_witnesses(corpus) -> None:  # type: ignore[no-untyped-def]
    """Two independent measurements of the same shapes must agree."""
    analytic: list[float] = []
    raster: list[float] = []
    for sample in corpus[:12]:
        measured = measure_document(sample.resolved_svg, sample.canvas_size, scale=1)
        for geometry in measured.values():
            analytic.append(geometry.analytic.area)
            raster.append(geometry.raster.area)

    errors = [(r - a) / a for a, r in zip(analytic, raster, strict=True)]

    fig, (scatter, hist) = plt.subplots(1, 2, figsize=(9.5, 4.0))

    limits = (min(analytic) * 0.75, max(analytic) * 1.3)
    scatter.plot(
        limits, limits, color=MUTED, linewidth=1.0, linestyle="--", label="exact agreement"
    )
    scatter.scatter(analytic, raster, s=16, color=COOL, alpha=0.75, edgecolor="none")
    scatter.set_xscale("log")
    scatter.set_yscale("log")
    scatter.set_xlim(*limits)
    scatter.set_ylim(*limits)
    scatter.set_xlabel("analytic area  (svgelements, Python)")
    scatter.set_ylabel("raster coverage  (resvg, Rust)")
    scatter.set_title(f"Independent witnesses, n={len(analytic)}", loc="left")
    scatter.legend(frameon=False, fontsize=8, loc="upper left")

    hist.hist([e * 100 for e in errors], bins=28, color=COOL, alpha=0.85)
    hist.axvline(0, color=MUTED, linewidth=1.0, linestyle="--")
    hist.set_xlabel("relative disagreement (%)")
    hist.set_ylabel("elements")
    hist.set_title(
        f"max |disagreement| = {max(abs(e) for e in errors) * 100:.2f}%   (tolerance 2%)",
        loc="left",
    )

    fig.suptitle(
        "Figure 2  -  ground truth is corroborated, not asserted",
        x=0.02,
        ha="left",
        fontsize=11,
        fontweight="bold",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(OUT / "fig02_witness_agreement.png", bbox_inches="tight")
    plt.close(fig)


def figure_three_construct_validity(tally: Counter[str]) -> None:
    """Why predicate slots are refused. The 9.4% row is what C8 exists for."""
    labels = {
        "valid": "admitted",
        "distractor_outranks_target": "a distractor wins the predicate",
        "margin_too_small": "winner not decisive enough",
        "definition_disagreement": "reasonable definitions disagree",
        "winner_outside_quadrant": "winner outside the named quadrant",
    }
    rows = [(labels[k], tally.get(k, 0)) for k in labels if tally.get(k, 0) > 0]
    rows.sort(key=lambda kv: kv[1])
    total = sum(v for _, v in rows)

    fig, axis = plt.subplots(figsize=(8.2, 3.4))
    colours = [
        COOL if name == "admitted" else (ACCENT if "definitions" in name else MUTED)
        for name, _ in rows
    ]
    bars = axis.barh([name for name, _ in rows], [v for _, v in rows], color=colours)
    for bar, (_, value) in zip(bars, rows, strict=True):
        axis.text(
            value + total * 0.008,
            bar.get_y() + bar.get_height() / 2,
            f"{value}  ({100 * value / total:.1f}%)",
            va="center",
            fontsize=8,
            color=INK,
        )
    axis.set_xlim(0, max(v for _, v in rows) * 1.22)
    axis.set_xlabel(f"predicate slots  (of {total})")
    axis.set_title("Construct-validity gate: which slots become benchmark cases", loc="left")
    axis.grid(axis="y", visible=False)

    fig.suptitle(
        "Figure 3  -  a mathematically unique answer is not a humanly unique answer",
        x=0.02,
        ha="left",
        fontsize=11,
        fontweight="bold",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    fig.savefig(OUT / "fig03_construct_validity.png", bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    config = load_config(BASE).config
    corpus = generate_corpus(config)
    truths, tally = build_corpus_ground_truth(corpus, config)

    figure_one_ambiguity(corpus, truths)
    figure_two_witnesses(corpus)
    figure_three_construct_validity(tally)

    for path in sorted(OUT.glob("*.png")):
        print(f"wrote {path.relative_to(REPO_ROOT)}  ({path.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
