#!/usr/bin/env python3
"""Render the four FINDINGS.md charts as PNGs (light background, matches the report).

Usage:  python docs/make_charts.py docs/img      # requires matplotlib + numpy

All data is inlined below (from results/report.csv), so the figures regenerate
identically without needing the raw run outputs.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

GEMINI, GEMMA, POS, NEG = "#3B4EA8", "#B0741A", "#3F8A5B", "#C0553F"
INK, MUTED, LINE = "#1A1C22", "#5C6270", "#DfE2EA"

plt.rcParams.update({
    "font.size": 11, "font.family": "DejaVu Sans",
    "text.color": INK, "axes.labelcolor": MUTED, "axes.edgecolor": MUTED,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.linewidth": 0.8,
    "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
})

def _clean(ax):
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)

def save(fig, name, outdir):
    fig.savefig(os.path.join(outdir, name), dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)

def quality(outdir):
    cats = ["ecomm", "mmqa", "movie", "overall"]
    gem = [.952, .908, .766, .875]
    off = [.866, .867, .717, .817]
    on = [.876, .862, .725, .821]
    x = np.arange(len(cats)); w = 0.26
    fig, ax = plt.subplots(figsize=(7.2, 3.3))
    b1 = ax.bar(x - w, gem, w, label="Gemini FL", color=GEMINI)
    b2 = ax.bar(x, off, w, label="Gemma · CD-off", color=GEMMA)
    b3 = ax.bar(x + w, on, w, label="Gemma · CD-on", color=GEMMA, alpha=0.5)
    for bars in (b1, b2, b3):
        for r in bars:
            ax.text(r.get_x() + r.get_width() / 2, r.get_height() + 0.012,
                    f"{r.get_height():.2f}", ha="center", va="bottom", fontsize=7.5, color=MUTED)
    ax.set_xticks(x); ax.set_xticklabels(cats)
    ax.set_ylim(0, 1.06); ax.set_yticks([0, .25, .5, .75, 1.0])
    ax.set_ylabel("quality (0–1)")
    ax.yaxis.grid(True, color=LINE, lw=0.8); ax.set_axisbelow(True)
    _clean(ax)
    ax.legend(frameon=False, fontsize=9, ncol=3, loc="lower center", bbox_to_anchor=(0.5, -0.22))
    save(fig, "quality.png", outdir)

def cost(outdir):
    labels = ["Gemini 3.1\nFlash-Lite", "Gemma E4B\n(local)"]
    vals = [5.324, 0.051]; colors = [GEMINI, GEMMA]
    fig, ax = plt.subplots(figsize=(7.2, 2.2))
    y = np.arange(len(labels))[::-1]
    ax.barh(y, vals, color=colors, height=0.55)
    ax.set_xscale("log"); ax.set_xlim(0.01, 12)
    for yi, v in zip(y, vals):
        ax.text(v * 1.15, yi, f"${v:.2f}", va="center", ha="left", fontsize=10, color=INK)
    ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=9.5)
    ax.set_xlabel("cost per run (USD, log scale)")
    ax.xaxis.grid(True, color=LINE, lw=0.8); ax.set_axisbelow(True)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(left=False)
    save(fig, "cost.png", outdir)

def latency(outdir):
    cats = ["ecomm", "mmqa", "movie"]
    gem = [71.4, 4.2, 59.0]; gma = [36.8, 0.6, 11.5]
    x = np.arange(len(cats)); w = 0.36
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    b1 = ax.bar(x - w / 2, gem, w, label="Gemini", color=GEMINI)
    b2 = ax.bar(x + w / 2, gma, w, label="Gemma (local)", color=GEMMA)
    ax.set_yscale("log"); ax.set_ylim(0.3, 140)
    for bars in (b1, b2):
        for r in bars:
            ax.text(r.get_x() + r.get_width() / 2, r.get_height() * 1.06,
                    f"{r.get_height():.1f}s", ha="center", va="bottom", fontsize=8, color=MUTED)
    ax.set_xticks(x); ax.set_xticklabels(cats)
    ax.set_ylabel("latency per query (s, log scale)")
    ax.yaxis.grid(True, color=LINE, lw=0.8); ax.set_axisbelow(True)
    _clean(ax)
    ax.legend(frameon=False, fontsize=9)
    save(fig, "latency.png", outdir)

def cd(outdir):
    names = ["movie Q10", "movie Q4", "mmqa Q6c", "ecomm Q5", "ecomm Q3", "ecomm Q7",
             "movie Q7", "mmqa Q3a", "mmqa Q4", "movie Q8", "mmqa Q3f", "movie Q3"]
    vals = [.093, .072, .037, .032, .009, -.001, -.001, -.009, -.026, -.041, -.048, -.048]
    y = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    colors = [POS if v >= 0 else NEG for v in vals]
    ax.barh(y, vals, color=colors, height=0.62)
    ax.invert_yaxis()  # largest positive at top
    ax.axvline(0, color=MUTED, lw=1.0)
    for yi, v in zip(y, vals):
        lab = "~0" if abs(v) < 0.005 else f"{v:+.2f}"
        ax.text(v + (0.002 if v >= 0 else -0.002), yi, lab,
                va="center", ha="left" if v >= 0 else "right", fontsize=8, color=MUTED)
    ax.set_yticks(y); ax.set_yticklabels(names, fontsize=9)
    ax.set_xlim(-0.062, 0.11)
    ax.set_xlabel("Δ quality from constrained decoding  (Gemma CD-on − CD-off)")
    ax.xaxis.grid(True, color=LINE, lw=0.8); ax.set_axisbelow(True)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(left=False)
    # tiny legend
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=POS, label="CD helped"), Patch(color=NEG, label="CD hurt")],
              frameon=False, fontsize=9, loc="lower right")
    save(fig, "cd.png", outdir)

if __name__ == "__main__":
    import sys
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    quality(outdir); cost(outdir); latency(outdir); cd(outdir)
    print("wrote 4 charts to", outdir)
