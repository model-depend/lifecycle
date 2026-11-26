#!/usr/bin/env python3
"""Step 1: derive the paper-level analysis tables from the extraction files.

Writes to data/aggregated/:
  paper_flags.csv                 per paper: year, venue, binary usage flags
                                  (closed LLM of the three major providers,
                                  open-weight LLM, classic PLM, open size tiers)
  paper_institution_weights.csv   fractional author-share credit per institution
  paper_country_weights.csv       fractional author-share credit per country
and the corpus counts per year (Appendix Figure 7):
  -> figures/papers_by_year.pdf, tables/corpus_papers_by_year.txt

Credit split (Appendix B): each paper gives 1/|authors| to every author; an
author with k resolvable affiliations passes 1/(|authors|*k) to each
institution and to that institution's country. Credits sum to <= 1 per paper.
"""
import csv
from collections import Counter, defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from common import (AGG, MAJOR_CLOSED, RC, paper_affiliations, paper_models,
                    save_figure, size_in_billions, write_table)

SMALL_MAX_B, MID_MAX_B = 10.0, 70.0   # open-weight tiers: <=10B, 10-70B, >70B


def build_flags():
    year_of, per_year = {}, Counter()
    with (AGG / "paper_flags.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["anthology_id", "year", "venue", "venue_type", "close_llm",
                    "open_llm", "classic_plm", "open_small", "open_mid", "open_xl"])
        for rec in paper_models():
            groups = {m["group"] for m in rec["models"]}
            small = mid = xl = 0
            for m in rec["models"]:
                b = size_in_billions(m["open_model_size"]) if m["group"] == "open_llm" else None
                if b is None:
                    continue
                if b <= SMALL_MAX_B:
                    small = 1
                elif b <= MID_MAX_B:
                    mid = 1
                else:
                    xl = 1
            w.writerow([rec["anthology_id"], rec["year"], rec["venue"], rec["venue_type"],
                        int(bool(groups & MAJOR_CLOSED)), int("open_llm" in groups),
                        int("classic_plm" in groups), small, mid, xl])
            year_of[rec["anthology_id"]] = rec["year"]
            per_year[rec["year"]] += 1
    return year_of, per_year


def build_weights(year_of):
    with (AGG / "paper_institution_weights.csv").open("w", newline="") as fi, \
         (AGG / "paper_country_weights.csv").open("w", newline="") as fc:
        wi, wc = csv.writer(fi), csv.writer(fc)
        wi.writerow(["anthology_id", "year", "institution", "weight"])
        wc.writerow(["anthology_id", "year", "country", "weight"])
        for rec in paper_affiliations():
            pid, authors = rec["anthology_id"], rec["authors"]
            inst_w, ctry_w = defaultdict(float), defaultdict(float)
            for a in authors:
                affs = [x for x in a["affiliations"] if x["institution_final"]]
                for x in affs:
                    share = 1.0 / (len(authors) * len(affs))
                    inst_w[x["institution_final"]] += share
                    ctry_w[x["country_final"] or ""] += share   # "" = unresolved country
            for inst, w in sorted(inst_w.items(), key=lambda kv: -kv[1]):
                wi.writerow([pid, year_of[pid], inst, f"{w:.6f}"])
            for c, w in sorted(ctry_w.items(), key=lambda kv: -kv[1]):
                wc.writerow([pid, year_of[pid], c, f"{w:.6f}"])


def plot_papers_by_year(per_year):
    years = sorted(per_year)
    vals = [per_year[y] for y in years]
    plt.rcParams.update(RC)
    fig, ax = plt.subplots(figsize=(3.5, 2.9))
    ax.bar(range(len(years)), vals, width=0.72, color="#3C6E9C", zorder=3)
    for i, v in enumerate(vals):
        ax.text(i, v + max(vals) * 0.015, f"{v:,}", ha="center", va="bottom",
                rotation=90, fontsize=12)
    ax.set_xticks(range(len(years)))
    ax.set_xticklabels([str(y) for y in years], fontsize=10, rotation=45, ha="right")
    ax.set_ylabel("Paper Count", fontsize=11)
    ax.set_ylim(0, max(vals) * 1.28)
    ax.set_yticks([0, 5000, 10000, 15000])
    ax.yaxis.set_major_formatter(
        FuncFormatter(lambda v, _: "0" if v == 0 else f"{int(v / 1000)}K"))
    ax.tick_params(axis="y", labelsize=11)
    ax.tick_params(axis="x", length=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout(pad=0.3)
    save_figure(fig, "papers_by_year")


def main():
    year_of, per_year = build_flags()
    build_weights(year_of)
    total = sum(per_year.values())
    pre = sum(v for y, v in per_year.items() if y <= 2022)
    lines = [f"{y}  {per_year[y]:>6,}" for y in sorted(per_year)]
    lines += [f"total            {total:,}", f"pre-LLM 2018-22  {pre:,}",
              f"LLM era 2023-26  {total - pre:,}"]
    write_table("corpus_papers_by_year.txt", "\n".join(lines))
    plot_papers_by_year(per_year)


if __name__ == "__main__":
    main()
