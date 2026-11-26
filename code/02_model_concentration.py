#!/usr/bin/env python3
"""Step 2: model concentration (Section 4.1).

Reproduces
  Table 1   most-used closed models per provider     -> tables/closed_model_usage.txt
  Figure 1  cumulative papers relying on deprecated /
            shut-down closed models                  -> figures/status_cumulative.pdf
  Table 2   ten most-used open-weight model sizes    -> tables/open_size_ranked.txt
  the lifecycle and open-weight numbers in the text  -> tables/lifecycle_exposure.txt,
                                                        tables/open_weight_usage.txt

Lifecycle status is evaluated at the corpus snapshot (2026-06-24). Mentions that
cannot be resolved to a dated release (e.g. bare "ChatGPT") never count as
deprecated or shut down, so all exposure numbers are lower bounds.
"""
import re
import statistics
from collections import Counter, defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from common import (MAJOR_CLOSED, SNAPSHOT, paper_models, save_figure,
                    size_in_billions, write_table)

PROVIDER = {"openai_closed": "OpenAI", "google_closed": "Google",
            "anthropic_closed": "Anthropic", "other_closed": "Others"}
SPELLING_TWINS = {   # display-only merge of version-spelling twins
    "claude-3-5-sonnet": "claude-3.5-sonnet", "claude-3-5-haiku": "claude-3.5-haiku",
    "claude-3-7-sonnet": "claude-3.7-sonnet", "claude-4-sonnet": "claude-sonnet-4",
    "claude-4-opus": "claude-opus-4", "gemini-1-5-pro": "gemini-1.5-pro",
}
# an exact API snapshot or build id in the model name or its printed version
SNAPSHOT_PIN = re.compile(
    r"(\d{4}-\d{2}-\d{2}|20\d{6}"
    r"|-(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])(?:-preview)?\b|-00[1-9]\b)")


def pct(a, b):
    return f"{a:,} ({a / b:.1%})"


def main():
    n_papers = n_llm_era = 0
    # --- closed models ---
    provider_papers = defaultdict(set)
    model_papers = Counter()                 # (provider, base model) -> papers
    other_vendor_papers = defaultdict(set)
    closed_papers = closed_llm_era = 0
    mentions = dated = pinned = 0
    papers_dated = papers_dep = papers_shut = papers_all_shut = 0
    first_dep, first_shut = Counter(), Counter()   # event year -> papers
    # --- open-weight models ---
    open_papers = open_llm_era = 0
    models_per_paper, sized_papers, paper_sizes = [], 0, []
    open_mentions = sized_mentions = 0
    mention_sizes = []
    size_papers = defaultdict(set)
    size_family_papers = defaultdict(lambda: defaultdict(set))

    for rec in paper_models():
        pid, year = rec["anthology_id"], rec["year"]
        llm_era = year >= 2023
        n_papers += 1
        n_llm_era += llm_era

        closed = [m for m in rec["models"] if m["group"] in PROVIDER and m["model_name"]]
        for prov, name in {(PROVIDER[m["group"]],
                            SPELLING_TWINS.get(m["model_name"], m["model_name"]))
                           for m in closed}:
            model_papers[(prov, name)] += 1
            provider_papers[prov].add(pid)
        for m in closed:
            if m["group"] == "other_closed":
                other_vendor_papers[m["subgroup"]].add(pid)

        major = [m for m in rec["models"] if m["group"] in MAJOR_CLOSED]
        if major:
            closed_papers += 1
            closed_llm_era += llm_era
            status = [m["model_status"] for m in major]
            mentions += len(major)
            dated += sum(s != "unknown" for s in status)
            pinned += sum(bool(SNAPSHOT_PIN.search(f"{m['name_normalized']} {m['version'] or ''}"))
                          for m in major)
            papers_dated += any(s != "unknown" for s in status)
            papers_dep += any(s in ("deprecated", "retired") for s in status)
            papers_shut += "retired" in status
            papers_all_shut += all(s == "retired" for s in status)
            # event time: a paper is affected from max(publication year, event year)
            deps = [m["deprecation_date"] for m in major
                    if m["deprecation_date"] and m["deprecation_date"] <= SNAPSHOT]
            shuts = [m["shutdown_date"] for m in major
                     if m["shutdown_date"] and m["shutdown_date"] <= SNAPSHOT]
            if deps:
                first_dep[max(year, int(min(deps)[:4]))] += 1
            if shuts:
                first_shut[max(year, int(min(shuts)[:4]))] += 1

        opens = [m for m in rec["models"] if m["group"] == "open_llm"]
        if opens:
            open_papers += 1
            open_llm_era += llm_era
            models_per_paper.append(len({m["open_model_in_paper"] for m in opens}))
            open_mentions += len(opens)
            distinct_sized = {}
            for m in opens:
                b = size_in_billions(m["open_model_size"])
                if b is None:
                    continue
                sized_mentions += 1
                mention_sizes.append(b)
                distinct_sized[m["open_model_in_paper"]] = b
                size_papers[m["open_model_size"]].add(pid)
                if m["open_model_name"]:
                    size_family_papers[m["open_model_size"]][m["open_model_name"]].add(pid)
            if distinct_sized:
                sized_papers += 1
                paper_sizes.extend(distinct_sized.values())

    # ---- Table 1 ----
    lines = [f"Papers using >=1 closed model of the three major providers: "
             f"{closed_papers:,} ({closed_papers / n_papers:.1%} of {n_papers:,}; "
             f"{closed_llm_era / n_llm_era:.1%} of the LLM era)", ""]
    for prov in ("OpenAI", "Google", "Anthropic"):
        lines.append(f"{prov} ({len(provider_papers[prov]):,} papers)")
        top = Counter({n: v for (p, n), v in model_papers.items() if p == prov})
        lines += [f"  {n:<22}{v:>7,}" for n, v in top.most_common(5)]
    lines.append(f"Others ({len(provider_papers['Others']):,} papers)")
    for vendor, ps in sorted(other_vendor_papers.items(), key=lambda kv: -len(kv[1]))[:5]:
        lines.append(f"  {vendor:<22}{len(ps):>7,}")
    write_table("closed_model_usage.txt", "\n".join(lines))

    # ---- lifecycle exposure ----
    write_table("lifecycle_exposure.txt", "\n".join([
        f"papers using a major-provider closed model   {closed_papers:,}",
        f"  >=1 model matched to official lifecycle dates  {pct(papers_dated, closed_papers)}",
        f"  >=1 deprecated (or shut-down) model            {pct(papers_dep, closed_papers)}",
        f"  >=1 shut-down model                            {pct(papers_shut, closed_papers)}",
        f"  every closed model shut down                   {papers_all_shut:,}",
        f"closed-model mentions                        {mentions:,}",
        f"  resolved to a dated release                    {pct(dated, mentions)}",
        f"  exact snapshot specified                       {pct(pinned, mentions)}",
        "",
        "cumulative papers by event year (Figure 1)",
        "year  >=1 deprecated  >=1 shut down",
        *[f"{y}  {sum(first_dep[k] for k in range(2023, y + 1)):>14,}"
          f"  {sum(first_shut[k] for k in range(2023, y + 1)):>13,}"
          for y in range(2023, 2027)],
    ]))
    plot_status_cumulative(first_dep, first_shut)

    # ---- open-weight usage ----
    n78 = sum(7 <= b <= 8 for b in mention_sizes)
    write_table("open_weight_usage.txt", "\n".join([
        f"papers using >=1 open-weight LLM   {open_papers:,} ({open_papers / n_papers:.1%} of all; "
        f"{open_llm_era / n_llm_era:.1%} of the LLM era)",
        f"distinct open-weight models per paper   mean {statistics.mean(models_per_paper):.1f}, "
        f"median {statistics.median(models_per_paper):g}",
        f"papers with >=1 sized open-weight model  {pct(sized_papers, open_papers)}",
        f"size of distinct sized models per paper  mean {statistics.mean(paper_sizes):.1f}B, "
        f"SD {statistics.stdev(paper_sizes):.1f}",
        f"open-weight mentions                     {open_mentions:,}, sized {pct(sized_mentions, open_mentions)}",
        f"  7-8B share of sized mentions           {n78 / sized_mentions:.1%}",
        f"  median size of sized mentions          {statistics.median(mention_sizes):g}B",
    ]))

    # ---- Table 2 ----
    rows = ["size   #papers  most-used model families"]
    for size, ps in sorted(size_papers.items(), key=lambda kv: -len(kv[1]))[:10]:
        fam = sorted(size_family_papers[size].items(), key=lambda kv: -len(kv[1]))[:2]
        rows.append(f"{size:<6}{len(ps):>8,}  {', '.join(n for n, _ in fam)}")
    write_table("open_size_ranked.txt", "\n".join(rows))


def plot_status_cumulative(first_dep, first_shut):
    years = list(range(2023, 2027))
    cum = lambda c: [sum(c[k] for k in years[:i + 1]) for i in range(len(years))]
    dep, shut = cum(first_dep), cum(first_shut)
    plt.rcParams.update({"font.family": "serif", "font.size": 15, "pdf.fonttype": 42})
    fig, ax = plt.subplots(figsize=(3.5, 2.9))
    x = range(len(years))
    ax.plot(x, dep, color="#6B4C9A", lw=2.4, marker="s", ms=8, label="$\\geq$1 deprecated")
    ax.plot(x, shut, color="#C0392B", lw=2.4, marker="x", ms=10, markeredgewidth=2.4,
            label="$\\geq$1 shut down")
    ax.set_xticks(list(x))
    ax.set_xticklabels([str(y) for y in years], fontsize=16)
    top = max(dep)
    ax.set_ylabel("# Papers", fontsize=17)
    ax.set_ylim(-top * 0.05, top * 1.3)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: "0" if v == 0 else f"{v / 1000:g}K"))
    fig.canvas.draw()
    ax.set_yticks([t for t in ax.get_yticks() if 0 <= t <= top * 1.3])
    ax.tick_params(axis="y", labelsize=16)
    ax.tick_params(axis="x", length=3)
    ax.set_xlim(-0.35, len(years) - 1 + 0.12)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(loc="upper left", frameon=False, fontsize=15, handlelength=1.4,
              borderaxespad=0.1, labelspacing=0.35)
    fig.tight_layout(pad=0.3)
    save_figure(fig, "status_cumulative")


if __name__ == "__main__":
    main()
