#!/usr/bin/env python3
"""Step 6: national wealth and model usage (Section 4.2, Appendix C).

Joins country-year usage shares to World Bank GDP per capita (PPP, constant
2021 international $; WDI release 2026-07-13) and fits, per publication year,
    log10(GDP per capita) = a + b * usage share (in 10-pp units)
    log10(GDP per capita) = a + b * log10(fractional paper count)
  -> data/aggregated/country_year_usage_gdp.csv
  -> figures/gdp_coefficient.pdf              (Figure 6)
  -> tables/gdp_regressions.txt               (Appendix Table 11)
     tables/gdp_papercount.txt                (Appendix Table 12)

Usage-share regressions include a country-year only with >= 10 fractional
papers (shares from very few papers are noisy). The paper-count regression
has no threshold: the count is the predictor itself. Taiwan and the Cook
Islands have no WDI GDP series and drop out. Estimates are correlational.
"""
import csv
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import to_rgb
from scipy import stats

from common import AGG, COLORS, DATA, RC, load_flags, save_figure, write_table

TYPES = ["close_llm", "open_llm", "classic_plm"]
MIN_FRACTIONAL_PAPERS = 10.0
SPEC = [("classic_plm", "PLM", range(2018, 2026)),     # LLM usage is negligible before 2023
        ("open_llm", "Open", range(2023, 2026)),
        ("close_llm", "Closed", range(2023, 2026))]


def build_country_year_table():
    flags = load_flags()
    credit, used = defaultdict(float), defaultdict(lambda: defaultdict(float))
    with (AGG / "paper_country_weights.csv").open() as f:
        for r in csv.DictReader(f):
            if not r["country"]:
                continue
            key, w = (r["country"], int(r["year"])), float(r["weight"])
            credit[key] += w
            for t in TYPES:
                used[key][t] += w * flags[r["anthology_id"]][t]
    usage = pd.DataFrame([{"country": c, "year": y, "frac_papers": round(v, 4),
                           **{f"rate_{t}": round(used[(c, y)][t] / v, 4) for t in TYPES}}
                          for (c, y), v in sorted(credit.items())])
    gdp = pd.read_csv(DATA / "external" / "worldbank_gdp_per_capita.csv",
                      keep_default_na=False)        # keep "NA" (Namibia) as a string
    df = usage.merge(gdp, on=["country", "year"], how="left")
    df.to_csv(AGG / "country_year_usage_gdp.csv", index=False)
    return df.dropna(subset=["gdp_pc_ppp"])


def fit(x, log_gdp):
    """OLS slope as % GDP difference per unit of x, with 95% CI and p-value."""
    r = stats.linregress(x, log_gdp)
    t = stats.t.ppf(0.975, len(x) - 2)
    pct = lambda b: (10.0 ** b - 1.0) * 100.0
    return len(x), pct(r.slope), pct(r.slope - t * r.stderr), pct(r.slope + t * r.stderr), r.pvalue


def stars(p):
    return "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""


def row(label, year, res):
    n, b, lo, hi, p = res
    pv = "<0.001" if p < 0.001 else f"{p:.3f}"
    ci = f"[{lo:+.1f}, {hi:+.1f}]"
    return f"{label:<8}{year:<6}{n:>4}{b:>+9.1f}   {ci:<17}{pv:>7} {stars(p)}".rstrip()


def main():
    df = build_country_year_table()
    fits = {}
    lines = ["% difference in GDP per capita per 10-pp-higher usage share",
             "type    year     n    % GDP   95% CI                 p"]
    for t, label, years in SPEC:
        for y in years:
            d = df[(df.year == y) & (df.frac_papers >= MIN_FRACTIONAL_PAPERS)]
            fits[(t, y)] = fit(d[f"rate_{t}"].values * 10.0, np.log10(d.gdp_pc_ppp.values))
            lines.append(row(label, y, fits[(t, y)]))
    write_table("gdp_regressions.txt", "\n".join(lines))

    lines = ["% difference in GDP per capita per tenfold fractional paper count",
             "        year     n    % GDP   95% CI                 p"]
    for y in range(2018, 2026):
        d = df[df.year == y]
        lines.append(row("", y, fit(np.log10(d.frac_papers.values), np.log10(d.gdp_pc_ppp.values))))
    write_table("gdp_papercount.txt", "\n".join(lines))
    plot_coefficients(fits)


def plot_coefficients(fits):
    years = [2023, 2024, 2025]
    lighten = {2023: 0.38, 2024: 0.19, 2025: 0.0}     # earlier years lighter
    blocks = [("close_llm", "Closed", "o"), ("open_llm", "Open", "s"), ("classic_plm", "PLM", "^")]
    lo_all = min(fits[(t, y)][2] for t, *_ in blocks for y in years)
    hi_all = max(fits[(t, y)][3] for t, *_ in blocks for y in years)
    span = hi_all - lo_all
    plt.rcParams.update(RC)
    fig, axes = plt.subplots(3, 1, figsize=(3.5, 3.0), sharex=True, gridspec_kw={"hspace": 0.22})
    for ax, (t, title, marker) in zip(axes, blocks):
        ax.axvline(0, color="#999999", lw=1.0, ls="--", zorder=1)
        for k, y in enumerate(years):
            _, b, lo, hi, p = fits[(t, y)]
            color = tuple(c + (1 - c) * lighten[y] for c in to_rgb(COLORS[t]))
            ax.plot([lo, hi], [-k, -k], color=color, lw=1.6, solid_capstyle="butt", zorder=3)
            for end in (lo, hi):
                ax.plot([end, end], [-k - 0.14, -k + 0.14], color=color, lw=1.4, zorder=3)
            ax.scatter([b], [-k], s=46, marker=marker, zorder=4, edgecolors=color,
                       facecolors=color if p < 0.05 else "white", linewidths=1.5)
            ax.text(hi + 0.025 * span, -k, stars(p), va="center", ha="left",
                    fontsize=12, color=color)
        ax.set_ylabel(title, fontsize=11.5)
        ax.set_yticks([0, -1, -2])
        ax.set_yticklabels([str(y) for y in years], fontsize=10.5)
        ax.set_ylim(-2.4, 0.4)
        ax.set_xlim(lo_all - 0.04 * span, hi_all + 0.16 * span)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.tick_params(axis="y", length=0)
        ax.tick_params(axis="x", labelsize=10.5)
        ax.grid(axis="x", lw=0.4, alpha=0.3)
    for ax in axes[:-1]:
        ax.spines["bottom"].set_visible(False)
        ax.tick_params(axis="x", length=0)
    axes[-1].set_xlabel("$\\Delta$ GDP per capita (%)", fontsize=12)
    save_figure(fig, "gdp_coefficient")


if __name__ == "__main__":
    main()
