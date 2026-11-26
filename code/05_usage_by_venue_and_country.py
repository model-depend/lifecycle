#!/usr/bin/env python3
"""Step 5: model-type usage by venue and by country, LLM era 2023-2026
(Section 4.2; Appendix Figure 9, Tables 6 and 13).

  -> data/aggregated/venue_rates.csv, country_rates.csv
  -> figures/ineq_venue_flagship.pdf   five selected venues (Figure 4)
     figures/ineq_venue.pdf            extended venues by category (Figure 9)
     figures/ineq_country_rates.pdf    top-20 countries/regions (Figure 5)
  -> tables/venue_rates_by_year.txt    journals vs. main conferences by year (Table 6)
     tables/country_rates.txt          countries with >= 10 fractional papers (Table 13)

Venue rates use whole-paper counting (each paper has one venue); country
rates are credit-weighted with the fractional author-share weights.
"""
import csv
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import (AGG, COLORS, COUNTRY_NAMES, LLM_ERA, RC, load_flags,
                    save_figure, write_table)

TYPES = ["close_llm", "open_llm", "classic_plm"]
SERIES = [("classic_plm", "classic PLM", "^"), ("open_llm", "open-weight LLM", "s"),
          ("close_llm", "closed LLM", "o")]
VENUE_NAMES = {
    "findings": "Findings", "acl": "ACL", "emnlp": "EMNLP", "coling-lrec": "LREC-COLING",
    "naacl": "NAACL", "eacl": "EACL", "semeval": "SemEval", "coling": "COLING",
    "jeptalnrecital": "JEP-TALN (Fr.)", "ccl": "CCL", "aacl": "AACL-IJCNLP",
    "arabicnlp": "ArabicNLP", "wmt": "WMT", "ranlp": "RANLP", "clicit": "CLiC-it",
    "paclic": "PACLIC", "tacl": "TACL", "propor": "PROPOR", "bea": "BEA",
    "dravidianlangtech": "DravidianLT", "bionlp": "BioNLP", "sigdial": "SIGDIAL",
    "icon": "ICON", "nodalida": "NoDaLiDa", "wassa": "WASSA", "finnlp": "FinNLP",
    "eamt": "EAMT", "rocling": "ROCLING", "clinicalnlp": "ClinicalNLP",
    "konvens": "KONVENS", "cl": "CL",
}
CATEGORIES = [("flagship", "Flagship"), ("findings", "Findings"),
              ("other_major", "Other major"), ("workshop_other", "Workshops & other"),
              ("industry", "Industry")]
# series shown in their own row; their demo/SRW side tracks are not re-listed as workshops
BIG_SERIES = {"acl", "emnlp", "naacl", "tacl", "cl", "findings", "eacl", "coling",
              "coling-lrec", "aacl"}
YEAR_GROUPS = [("TACL (journal)", {"tacl"}), ("CL (journal)", {"cl"}),
               ("ACL / EMNLP / NAACL (main conferences)", {"acl", "emnlp", "naacl"})]


def in_llm_era(year):
    return LLM_ERA[0] <= year <= LLM_ERA[1]


# ----------------------------------------------------------------- venues
def venue_rates(flags):
    agg = defaultdict(lambda: [0, 0, 0, 0])            # (category, venue) -> n, uses
    for fl in flags.values():
        if in_llm_era(fl["year"]) and fl["venue_type"]:
            a = agg[(fl["venue_type"], fl["venue"])]
            a[0] += 1
            for i, t in enumerate(TYPES):
                a[i + 1] += fl[t]
    rows = [{"category": c, "venue": v, "n_papers": a[0],
             **{f"rate_{t}": a[i + 1] / a[0] for i, t in enumerate(TYPES)}}
            for (c, v), a in sorted(agg.items(), key=lambda kv: (kv[0][0], -kv[1][0]))]
    with (AGG / "venue_rates.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows({k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in r.items()}
                    for r in rows)
    return rows


def dumbbell(ax, rows, ys, labels, size=24, **marker_kw):
    for y, r in zip(ys, rows):
        ax.plot(sorted([r["rate_close_llm"], r["rate_open_llm"]]), [y, y],
                color="#AAB4BE", lw=1.0, zorder=1)
    for t, label, marker in SERIES:
        ax.scatter([r[f"rate_{t}"] for r in rows], ys, s=size, color=COLORS[t],
                   marker=marker, zorder=3, label=label, **marker_kw)
    ax.set_yticks(ys)
    ax.set_yticklabels(labels)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def plot_flagship(rows):
    rows = sorted((r for r in rows if r["category"] == "flagship"),
                  key=lambda r: r["rate_close_llm"])
    fig, ax = plt.subplots(figsize=(3.3, 2.05))
    dumbbell(ax, rows, list(range(len(rows))),
             [VENUE_NAMES.get(r["venue"], r["venue"]) for r in rows])
    ax.tick_params(axis="y", labelsize=9)
    ax.set_xlabel("Venue's Model Usage", fontsize=9)
    ax.set_xlim(0, 0.9)
    ax.set_ylim(-0.6, len(rows) - 0.15)
    ax.tick_params(axis="x", labelsize=9)
    ax.legend(loc="upper left", ncols=1, frameon=False, fontsize=7.5, handlelength=1.0,
              handletextpad=0.3, labelspacing=0.25, borderaxespad=0.25)
    fig.tight_layout(pad=0.3)
    save_figure(fig, "ineq_venue_flagship")


def plot_all_venues(rows, workshops_shown=20):
    """One row per venue, grouped by venue category (industry at the bottom)."""
    placed, separators, spans, y = [], [], [], 0.0
    for i, (cat, title) in enumerate(reversed(CATEGORIES)):
        rs = [r for r in rows if r["category"] == cat]
        if cat == "workshop_other":
            rs = sorted((r for r in rs if r["venue"] not in BIG_SERIES),
                        key=lambda r: -r["n_papers"])[:workshops_shown]
        rs.sort(key=lambda r: r["rate_close_llm"])
        if i:
            separators.append(y - 1.0)
        spans.append((title, cat, y, y + len(rs) - 1))
        for r in rs:
            name = VENUE_NAMES.get(r["venue"], r["venue"])
            placed.append((y, r, f"{name} (ind.)" if cat == "industry" else name))
            y += 1
        y += 1.0
    top = y - 2.0
    fig, ax = plt.subplots(figsize=(3.6, 0.185 * (top + 2) + 0.5))
    dumbbell(ax, [p[1] for p in placed], [p[0] for p in placed], [p[2] for p in placed],
             size=22)
    ax.tick_params(axis="y", labelsize=7.5)
    for s in separators:
        ax.axhline(s, color="#888888", lw=0.7, zorder=2)
    for title, cat, lo, hi in spans:
        if cat != "findings":                 # single venue: the row name says it
            ax.text(-0.62, (lo + hi) / 2, title, rotation=90, va="center", ha="center",
                    fontsize=8.5, style="italic", color="#333333",
                    transform=ax.get_yaxis_transform(), clip_on=False)
    ax.set_ylim(-0.8, top + 0.8)
    ax.set_xlabel("Venue's Model Usage", fontsize=9)
    ax.set_xlim(0, 0.9)
    ax.tick_params(axis="x", labelsize=9)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.05), ncols=3, frameon=False,
              fontsize=8.5, handlelength=1.0, columnspacing=0.6, handletextpad=0.2)
    fig.tight_layout(pad=0.3)
    save_figure(fig, "ineq_venue")


def venue_year_table(flags):
    agg = defaultdict(lambda: [0, 0, 0, 0])
    for fl in flags.values():
        if not in_llm_era(fl["year"]):
            continue
        for g, (_, venues) in enumerate(YEAR_GROUPS):
            if fl["venue"] in venues:
                for key in ((g, fl["year"]), (g, "2023-26")):
                    a = agg[key]
                    a[0] += 1
                    for i, t in enumerate(TYPES):
                        a[i + 1] += fl[t]
    lines = ["share (%) of the venue's papers using each model type",
             f"{'year':<9}{'N':>7}{'closed':>8}{'open':>6}{'PLM':>6}"]
    for g, (title, _) in enumerate(YEAR_GROUPS):
        lines.append(title)
        for y in (2023, 2024, 2025, 2026, "2023-26"):
            n, c, o, p = agg[(g, y)]
            lines.append(f"{y!s:<9}{n:>7,}{c / n * 100:>8.0f}{o / n * 100:>6.0f}{p / n * 100:>6.0f}")
    write_table("venue_rates_by_year.txt", "\n".join(lines))


# -------------------------------------------------------------- countries
def country_rates(flags):
    credit, used = defaultdict(float), defaultdict(lambda: [0.0, 0.0, 0.0])
    with (AGG / "paper_country_weights.csv").open() as f:
        for r in csv.DictReader(f):
            if not r["country"] or not in_llm_era(int(r["year"])):
                continue
            w, fl = float(r["weight"]), flags[r["anthology_id"]]
            credit[r["country"]] += w
            for i, t in enumerate(TYPES):
                used[r["country"]][i] += w * fl[t]
    rows = [{"country": c, "frac_papers": v,
             **{f"rate_{t}": used[c][i] / v for i, t in enumerate(TYPES)}}
            for c, v in sorted(credit.items(), key=lambda kv: -kv[1])]
    with (AGG / "country_rates.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(list(rows[0]))
        for r in rows:
            w.writerow([r["country"], f"{r['frac_papers']:.1f}"] +
                       [f"{r[f'rate_{t}']:.4f}" for t in TYPES])
    return rows


def plot_countries(rows, top_n=20):
    rows = sorted(rows[:top_n], key=lambda r: r["rate_open_llm"] - r["rate_close_llm"])
    fig, ax = plt.subplots(figsize=(3.5, 4.4))
    ys = list(range(len(rows)))
    for y in ys:
        ax.axhline(y, color="#EEEEEE", lw=0.6, zorder=0)
    dumbbell(ax, rows, ys, [COUNTRY_NAMES.get(r["country"], r["country"]) for r in rows],
             size=22, linewidths=0)
    ax.tick_params(axis="y", labelsize=8, length=0)
    ax.set_xlabel("Country/Region's Model Usage", fontsize=9)
    ax.set_xlim(0.15, 0.8)
    ax.tick_params(axis="x", labelsize=10)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.11), ncols=3, frameon=False,
              fontsize=8.5, handlelength=1.0, columnspacing=0.6, handletextpad=0.2)
    fig.tight_layout(pad=0.3)
    save_figure(fig, "ineq_country_rates")


def country_table(rows, min_papers=10.0):
    lines = ["share (%) of the country/region's papers using each model type, 2023-2026",
             f"{'country/region':<24}{'N':>7}{'closed':>8}{'open':>7}{'PLM':>7}"]
    for r in rows:
        if r["frac_papers"] >= min_papers:
            lines.append(f"{COUNTRY_NAMES.get(r['country'], r['country']):<24}"
                         f"{r['frac_papers']:>7,.0f}{r['rate_close_llm'] * 100:>8.1f}"
                         f"{r['rate_open_llm'] * 100:>7.1f}{r['rate_classic_plm'] * 100:>7.1f}")
    write_table("country_rates.txt", "\n".join(lines))


def main():
    plt.rcParams.update(RC)
    flags = load_flags()
    venues = venue_rates(flags)
    plot_flagship(venues)
    plot_all_venues(venues)
    venue_year_table(flags)
    countries = country_rates(flags)
    plot_countries(countries)
    country_table(countries)


if __name__ == "__main__":
    main()
