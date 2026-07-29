"""Generate the GitHub social preview image.

1280x640, the size GitHub renders in link embeds. Generated from a script rather than
drawn by hand so the numbers on it cannot drift away from the result.

GitHub exposes no API for social previews, so the output must be uploaded manually under
Settings, Social preview.

Usage:
    python scripts/make_social_preview.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt

matplotlib.use("Agg")

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT = REPO_ROOT / "assets" / "social-preview.png"

INK = "#1a1a1a"
MUTED = "#8a8a8a"
ACCENT = "#c0392b"
COOL = "#2c6fa8"

# The chain, with the verdict measured at each link.
STAGES = (
    ("context", "", MUTED),
    ("prompt", "changed", COOL),
    ("response", "changed", COOL),
    ("identification", "unchanged", ACCENT),
)


def main() -> int:
    figure = plt.figure(figsize=(12.8, 6.4), dpi=100)
    figure.patch.set_facecolor("white")
    axis = figure.add_axes((0, 0, 1, 1))
    axis.axis("off")
    axis.set_xlim(0, 128)
    axis.set_ylim(0, 64)

    axis.text(7, 55, "Does added context help because of its", fontsize=25, color=INK, va="center")
    axis.text(
        7,
        49.5,
        "information, or its format?",
        fontsize=25,
        color=INK,
        va="center",
        fontweight="bold",
    )
    axis.plot([7, 45], [45.5, 45.5], color=ACCENT, linewidth=3)
    axis.text(7, 40, "Most evaluations cannot tell them apart.", fontsize=13.5, color=MUTED)
    axis.text(
        7, 35.5, "A format-matched control can.", fontsize=13.5, color=COOL, fontweight="bold"
    )

    y = 25
    for index, (label, verdict, colour) in enumerate(STAGES):
        x = 8 + index * 29
        axis.add_patch(
            plt.Rectangle((x, y - 3.6), 21, 7.2, facecolor="white", edgecolor=colour, linewidth=2)
        )
        axis.text(x + 10.5, y, label, ha="center", va="center", fontsize=12.5, color=INK)
        if index:
            axis.annotate(
                "",
                xy=(x - 0.6, y),
                xytext=(x - 7.4, y),
                arrowprops={"arrowstyle": "-|>", "color": colour, "linewidth": 2.2},
            )
            # Well clear of the box edge; at thumbnail size a collision here reads as a
            # rendering fault rather than as a label.
            axis.text(
                x - 4,
                y + 5.6,
                verdict,
                ha="center",
                fontsize=10,
                color=colour,
                fontweight="bold",
            )

    axis.text(7, 12.5, "Result: the context changed what the model said,", fontsize=13, color=INK)
    axis.text(
        7, 8, "not which element it identified.", fontsize=13, color=ACCENT, fontweight="bold"
    )
    axis.text(
        121,
        9.5,
        "pre-registered  |  280 tests  |  540 responses committed",
        fontsize=9,
        color=MUTED,
        ha="right",
    )
    axis.text(121, 4, "svg-ambiguity-bench", fontsize=11.5, color=MUTED, ha="right")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(OUT, facecolor="white")
    plt.close(figure)
    print(f"wrote {OUT.relative_to(REPO_ROOT)} (1280x640)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
