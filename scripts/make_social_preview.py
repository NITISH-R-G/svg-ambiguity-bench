"""GitHub social preview: 1280x640, readable at thumbnail size."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

INK, MUTED, ACCENT, COOL = "#1a1a1a", "#8a8a8a", "#c0392b", "#2c6fa8"
fig = plt.figure(figsize=(12.8, 6.4), dpi=100)
fig.patch.set_facecolor("white")
ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_xlim(0, 128); ax.set_ylim(0, 64)

ax.text(7, 55, "Does added context help because of its", fontsize=25, color=INK, va="center")
ax.text(7, 49.5, "information, or its format?", fontsize=25, color=INK, va="center", fontweight="bold")
ax.plot([7, 45], [45.5, 45.5], color=ACCENT, linewidth=3)
ax.text(7, 40, "Most evaluations cannot tell them apart.", fontsize=13.5, color=MUTED, va="center")
ax.text(7, 35.5, "A format-matched control can.", fontsize=13.5, color=COOL, va="center", fontweight="bold")

# the chain, compact
y = 25
for i, (label, verdict, col) in enumerate([
    ("context", "", MUTED), ("prompt", "changed", COOL),
    ("response", "changed", COOL), ("identification", "unchanged", ACCENT)]):
    x = 8 + i * 29
    ax.add_patch(plt.Rectangle((x, y - 3.6), 21, 7.2, facecolor="white",
                               edgecolor=col, linewidth=2))
    ax.text(x + 10.5, y, label, ha="center", va="center", fontsize=12.5, color=INK)
    if i:
        ax.annotate("", xy=(x - 0.6, y), xytext=(x - 7.4, y),
                    arrowprops={"arrowstyle": "-|>", "color": col, "linewidth": 2.2})
        ax.text(x - 4, y + 5.6, verdict, ha="center", fontsize=10,
                color=col, fontweight="bold")

ax.text(7, 12.5, "Result: the context changed what the model said,", fontsize=13, color=INK)
ax.text(7, 8, "not which element it identified.", fontsize=13, color=ACCENT, fontweight="bold")
ax.text(121, 4, "svg-ambiguity-bench", fontsize=11.5, color=MUTED, ha="right")
ax.text(121, 9.5, "pre-registered  ·  280 tests  ·  540 responses committed",
        fontsize=9, color=MUTED, ha="right")

fig.savefig("assets/social-preview.png", facecolor="white")
print("assets/social-preview.png written (1280x640)")
