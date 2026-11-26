#!/usr/bin/env python3
"""Step 4: concentration of model-type usage (Section 4.2, Appendix B).

Per-year Gini index of each model type's usage mass across publishing
institutions (Figure 3) and across countries (Appendix Figure 8).
  -> data/aggregated/gini_by_year_{institution,country}.csv
  -> figures/ineq_gini_by_year.pdf, figures/ineq_gini_by_year_country.pdf

Usage mass of unit i for type t in year y:  x_i = sum_p w_p(i) * u_p(t),
with w_p(i) the fractional author-share credit and u_p(t) the binary usage
flag. The Gini runs over all units receiving any credit that year (zeros
included). Type-years with fewer than 30 fractional papers are not reported.
"""
import csv
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from common import AGG, COLORS, RC, YEARS, load_flags, save_figure

TYPES = ["classic_plm", "open_small", "open_mid", "open_xl", "close_llm"]
MARKERS = {"classic_plm": "^", "open_small": "s", "open_mid": "D", "open_xl": "v",
           "close_llm": "o"}
MIN_FRACTIONAL_PAPERS = 30


def gini(x):
    x = np.sort(np.asarray(x, dtype=float))
    n, s = x.size, x.sum()
    return float((2 * np.arange(1, n + 1) @ x) / (n * s) - (n + 1) / n)


def gini_by_year(unit, flags):
    """unit = 'institution' or 'country' -> {type: {year: gini or None}}, n units/year."""
    credit = defaultdict(lambda: defaultdict(float))                      # year -> unit -> credit
    mass = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))   # year -> type -> unit
    with (AGG / f"paper_{unit}_weights.csv").open() as f:
        for r in csv.DictReader(f):
            if not r[unit]:
                continue                      # unresolved country
            y, w, fl = int(r["year"]), float(r["weight"]), flags[r["anthology_id"]]
            credit[y][r[unit]] += w
            for t in TYPES:
                if fl[t]:
                    mass[y][t][r[unit]] += w
    out = {t: {} for t in TYPES}
    for y in YEARS:
        units = sorted(credit[y])
        for t in TYPES:
            x = [mass[y][t].get(u, 0.0) for u in units]
            out[t][y] = gini(x) if sum(x) >= MIN_FRACTIONAL_PAPERS else None
    with (AGG / f"gini_by_year_{unit}.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["year", "n_units"] + TYPES)
        for y in YEARS:
            w.writerow([y, len(credit[y])] +
                       ["" if out[t][y] is None else f"{out[t][y]:.4f}" for t in TYPES])
    return out


def base_axes(series, ylabel, divider="#999999"):
    plt.rcParams.update(RC)
    fig, ax = plt.subplots(figsize=(3.5, 2.9))
    for t in TYPES:
        pts = [(i, series[t][y]) for i, y in enumerate(YEARS) if series[t][y] is not None]
        ax.plot(*zip(*pts), color=COLORS[t], lw=1.4, marker=MARKERS[t], ms=3.5, zorder=4)
    ax.axvline(YEARS.index(2023) - 0.5, color=divider, lw=1.3, ls="--", zorder=2)
    ticks = [i for i, y in enumerate(YEARS) if y % 2 == 0]
    ax.set_xticks(ticks)
    ax.set_xticklabels([str(YEARS[i]) for i in ticks], fontsize=10)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.tick_params(axis="y", labelsize=11)
    ax.tick_params(axis="x", length=3)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    return fig, ax


def plot_institutions(series):
    fig, ax = base_axes(series, "Gini (institutions)")

    def label(text, t, xy, ha, seg):          # direct label + dashed connector
        ax.text(*xy, text, fontsize=9, color=COLORS[t], ha=ha, va="center", zorder=5)
        if seg:
            ax.plot(seg[0::2], seg[1::2], color=COLORS[t], lw=0.7, ls="--", zorder=3)

    label("classic PLM", "classic_plm", (0.3, 0.783), "left", None)
    label("closed LLM", "close_llm", (3.3, 0.925), "right", (3.35, 0.9305, 3.60, 0.9705))
    label("$\\leq$10B", "open_small", (3.2, 1.002), "center", (3.72, 0.998, 3.94, 0.990))
    label("10–70B", "open_mid", (8.70, 0.881), "right", (8.05, 0.875, 8.01, 0.854))
    label("$>$70B", "open_xl", (8.40, 0.990), "right", (7.72, 0.984, 7.42, 0.919))
    ax.set_ylim(0.75, 1.012)
    ax.set_yticks([0.75, 0.80, 0.85, 0.90, 0.95, 1.00])
    ax.set_xlim(-0.45, 8.75)
    fig.tight_layout(pad=0.3)
    save_figure(fig, "ineq_gini_by_year")


def plot_countries(series):
    fig, ax = base_axes(series, "Gini (countries)", divider="#555555")
    names = {"classic_plm": "classic PLM", "open_small": "$\\leq$10B", "open_mid": "10–70B",
             "open_xl": "$>$70B", "close_llm": "closed LLM"}
    for line, t in zip(ax.get_lines(), TYPES):
        line.set_label(names[t])
    ax.margins(x=0.02)
    ax.legend(frameon=False, handlelength=1.3, borderaxespad=0.1, labelspacing=0.3,
              handletextpad=0.4, loc="lower right", fontsize=7.5)
    fig.tight_layout(pad=0.3)
    save_figure(fig, "ineq_gini_by_year_country")


def main():
    flags = load_flags()
    plot_institutions(gini_by_year("institution", flags))
    plot_countries(gini_by_year("country", flags))
    for unit in ("institution", "country"):
        print(f"\ndata/aggregated/gini_by_year_{unit}.csv")
        print((AGG / f"gini_by_year_{unit}.csv").read_text())


if __name__ == "__main__":
    main()
