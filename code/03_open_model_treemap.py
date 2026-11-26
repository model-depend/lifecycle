#!/usr/bin/env python3
"""Step 3: open-weight LLM usage by developer (Figure 2).

Treemap with block area proportional to the number of papers using each
open-weight model, grouped by developer; group headers give unique papers.
  -> figures/open_model_treemap.pdf, tables/open_model_developers.txt

A model counts toward a developer only for the developer's own official
releases; community fine-tunes and models without a company fall under
"Others". Small blocks inside a group are merged into an "other" block that
counts unique papers.
"""
import re
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Rectangle
from matplotlib.textpath import TextPath

from common import paper_models, save_figure, write_table

FP_REG = FontProperties(family="serif")


def text_w(txt: str, fs: float) -> float:
    """Exact rendered width (inches) of serif text at fontsize fs."""
    return TextPath((0, 0), txt, size=fs, prop=FP_REG).get_extents().width / 72.0


def worst(row, w):
    s = sum(row)
    return max(max((w * w * r) / (s * s), (s * s) / (w * w * r)) for r in row)


def squarify(sizes, x, y, dx, dy):
    """Bruls et al. squarified treemap; sizes (desc) must sum to dx*dy."""
    rects = []
    sizes = list(sizes)
    while sizes:
        w = min(dx, dy)
        row = [sizes.pop(0)]
        while sizes and worst(row + [sizes[0]], w) <= worst(row, w):
            row.append(sizes.pop(0))
        s = sum(row)
        if dx >= dy:
            rw = s / dy
            ry = y
            for r in row:
                rects.append((x, ry, rw, r / rw))
                ry += r / rw
            x += rw
            dx -= rw
        else:
            rh = s / dx
            rx = x
            for r in row:
                rects.append((rx, y, r / rh, rh))
                rx += r / rh
            y += rh
            dy -= rh
    return rects


TEAL = LinearSegmentedColormap.from_list(
    "teal", [(0, "#f3fbfc"), (0.5, "#57bfca"), (0.75, "#0fa3b1"),
             (1.0, "#06454d")])
GOLD = LinearSegmentedColormap.from_list(
    "gold", [(0, "#fdfae8"), (0.5, "#e3cc4e"), (0.75, "#b7950b"),
             (1.0, "#615008")])

# family folding inside the Others region (LLaVA-1.5 and LLaVA share a block)
OTHERS_FOLD = [
    (r"^llava(-|$|\d)", "llava"),
    (r"^phi-?\d", "phi"),
    (r"^chatglm", "chatglm"),
    (r"^olmo", "olmo"),
    (r"^baichuan", "baichuan"),
    (r"^yi(-|$|\d)", "yi"),
    (r"^aya(-|$)", "aya"),
    (r"^internlm", "internlm"),
    (r"^internvl", "internvl"),
    (r"^minicpm", "minicpm"),
    (r"^bloomz?", "bloom"),
    (r"^vicuna", "vicuna"),
    (r"^falcon", "falcon"),
    (r"^pythia", "pythia"),
    (r"^zephyr", "zephyr"),
    (r"^mpt(-|$)", "mpt"),
    (r"^command", "command-r"),
    (r"^tulu", "tulu"),
    (r"^glm-?\d", "glm"),
    (r"^gpt-neox?", "gpt-neo(x)"),
]
OTHERS_FOLD = [(re.compile(p), f) for p, f in OTHERS_FOLD]


def fold_others(base: str) -> str:
    for rx, f in OTHERS_FOLD:
        if rx.match(base):
            return f
    return base

# display-only folding of spelling twins (most are already merged in the data)
DISPLAY_FOLD = {
    "llava-ov": "llava-onevision",
}
PRETTY = {
    "llama": "Llama", "vicuna": "Vicuna", "alpaca": "Alpaca",
    "mistral": "Mistral", "mixtral": "Mixtral", "pixtral": "Pixtral",
    "flan-t5": "Flan-T5", "flan-ul2": "Flan-UL2", "bloom": "BLOOM",
    "bloomz": "BLOOMZ", "pythia": "Pythia", "opt": "OPT", "xglm": "XGLM",
    "llava": "LLaVA", "llava-1.5": "LLaVA-1.5", "llava-1.6": "LLaVA-1.6",
    "llava-next": "LLaVA-NeXT", "llava-onevision": "LLaVA-OneVision",
    "olmo": "OLMo", "olmo-2": "OLMo-2", "mpt": "MPT", "falcon": "Falcon",
    "gpt-oss": "GPT-OSS", "gpt-neo": "GPT-Neo", "gpt-neox": "GPT-NeoX",
    "gpt-j": "GPT-J", "internlm": "InternLM", "internlm2": "InternLM2",
    "chatglm": "ChatGLM", "chatglm2": "ChatGLM2", "chatglm3": "ChatGLM3",
    "glm-4": "GLM-4", "baichuan": "Baichuan", "baichuan2": "Baichuan2",
    "qwq": "QwQ", "minigpt-4": "MiniGPT-4", "mamba": "Mamba",
    "phi": "Phi", "yi": "Yi", "aya": "Aya", "command-r": "Command-R",
    "gpt-neo(x)": "GPT-Neo(X)", "internvl": "InternVL", "tulu": "Tülu",
    "minicpm": "MiniCPM", "glm": "GLM",
    "codellama": "CodeLlama", "code-llama": "CodeLlama",
    "tinyllama": "TinyLlama", "zephyr": "Zephyr", "gemma": "Gemma",
    "t5": "T5", "mt5": "mT5", "mt0": "mT0", "unifiedqa": "UnifiedQA",
    "eurollm": "EuroLLM", "aya": "Aya", "nllb": "NLLB",
}
TOKEN_PRETTY = {"t5": "T5", "vl": "VL", "r1": "R1", "v3": "V3", "it": "it",
                "moe": "MoE", "neo": "Neo", "neox": "NeoX", "j": "J",
                "oss": "OSS", "next": "NeXT", "coder": "Coder",
                "math": "Math", "guard": "Guard", "chat": "Chat"}


def pretty(name: str) -> str:
    if name in PRETTY:
        return PRETTY[name]
    toks = []
    for t in name.split("-"):
        if t in TOKEN_PRETTY:
            toks.append(TOKEN_PRETTY[t])
        elif t.startswith("deepseek"):
            toks.append("DeepSeek" + t[len("deepseek"):])
        elif t.startswith("qwen"):
            toks.append("Qwen" + t[len("qwen"):])
        elif t.startswith("llama"):
            toks.append("Llama" + t[len("llama"):])
        elif t.startswith("gpt"):
            toks.append("GPT" + t[len("gpt"):])
        elif t and t[0].isalpha():
            toks.append(t[0].upper() + t[1:])
        else:
            toks.append(t)
    return "-".join(toks)



MAGENTA = LinearSegmentedColormap.from_list(
    "magenta", [(0, "#fdf0f7"), (0.5, "#e178b8"), (0.75, "#c51b8a"),
                (1.0, "#67094a")])
CMAPS = {"Meta": cm.Purples, "Alibaba": cm.Reds, "Mistral AI": GOLD,
         "Google": cm.Blues, "DeepSeek": TEAL, "Microsoft": MAGENTA,
         "Others": cm.Greys}
TOP = ["Meta", "Alibaba", "Mistral AI", "Google", "DeepSeek", "Microsoft"]
ORDER = TOP + ["Others"]
FOLDED_REGIONS = {"Microsoft", "Others"}   # family-level blocks
MAX_BLOCKS = {"Meta": 4, "Alibaba": 3, "Mistral AI": 2, "Google": 2,
              "DeepSeek": 2, "Microsoft": 0, "Others": 2}
MIN_SHARE = 0.03
MIN_SHARE_R = {"Others": 0.02}


def main() -> None:
    def blocks_of(rec):
        per = set()
        for m in rec.get("models") or []:
            if m.get("group") != "open_llm" or not m.get("open_model_name"):
                continue
            base = DISPLAY_FOLD.get(m["open_model_name"],
                                        m["open_model_name"])
            co = m.get("model_company")
            reg = co if co in TOP else "Others"
            per.add((reg, fold_others(base) if reg in FOLDED_REGIONS
                     else base))
        return per

    by_comp: dict[str, Counter] = {c: Counter() for c in ORDER}
    papers_by_region: dict[str, set] = {c: set() for c in ORDER}
    for rec in paper_models():
        per = blocks_of(rec)
        for reg, n in per:
            by_comp[reg][n] += 1
        for reg in {r for r, _ in per}:
            papers_by_region[reg].add(rec["anthology_id"])

    # head/tail per region; the residual block must count UNIQUE papers
    # using >=1 of the tail models (a sum would double-count multi-model
    # papers), so a second pass takes the union.
    head_of: dict[str, list] = {}
    tailset_of: dict[str, set] = {}
    for c in ORDER:
        if c == "Microsoft":
            continue
        models = by_comp[c].most_common()
        csum = sum(by_comp[c].values())
        min_share = MIN_SHARE_R.get(c, MIN_SHARE)
        head_of[c] = [(n, v) for i, (n, v) in enumerate(models)
                      if i < MAX_BLOCKS[c] and v / csum >= min_share]
        tailset_of[c] = {n for n, _ in models[len(head_of[c]):]}
    resid: dict[str, set] = {c: set() for c in ORDER}
    for rec in paper_models():
        for reg, n in blocks_of(rec):
            if reg != "Microsoft" and n in tailset_of[reg]:
                resid[reg].add(rec["anthology_id"])

    plt.rcParams.update({"font.family": "serif", "font.size": 10,
                         "pdf.fonttype": 42})
    W, H = 3.3, 2.3
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.invert_yaxis()
    ax.axis("off")

    # every displayed number is a PAPER count; regions are sized by the
    # sum of their displayed blocks (Microsoft: its unique papers)
    items_of = {c: head_of[c] + ([("", len(resid[c]))]
                                 if tailset_of[c] else [])
                for c in ORDER if c != "Microsoft"}
    comp_tot = {c: (len(papers_by_region[c]) if c == "Microsoft"
                    else sum(v for _, v in items_of[c])) for c in ORDER}
    total = sum(comp_tot.values())

    # region sizes: inner (post-header) block area globally proportional.
    # Microsoft is a single consolidated block with NO header band.
    GAP = 0.03
    HB = 0.17
    hb_of = {c: (0.0 if c == "Microsoft" else HB) for c in ORDER}
    ratios = []
    sizes = [comp_tot[c] for c in ORDER]
    for _ in range(20):
        scale = W * H / sum(sizes)
        comp_rects = squarify([s * scale for s in sizes], 0, 0, W, H)
        overheads = [cw * ch - (cw - 2 * GAP) * (ch - 2 * GAP - hb_of[c])
                     for c, (cx, cy, cw, ch) in zip(ORDER, comp_rects)]
        k = (W * H - sum(overheads)) / total
        sizes = [k * comp_tot[c] + oh for c, oh in zip(ORDER, overheads)]

    for c, (cx, cy, cw, ch) in zip(ORDER, comp_rects):
        cmap = CMAPS[c]
        ix, iy = cx + GAP, cy + GAP
        iw, ih = cw - 2 * GAP, ch - 2 * GAP

        if c == "Microsoft":
            # one consolidated block: name / (papers) / e.g., Phi
            ax.add_patch(Rectangle((ix, iy), iw, ih, facecolor=cmap(0.50),
                                   edgecolor="white", linewidth=0.8))
            ratios.append(iw * ih / comp_tot[c])
            lines = ["Microsoft", f"({len(papers_by_region[c]):,})",
                     "e.g., Phi"]
            fs = min(8.0, 10.0 * (iw * 0.90)
                     / max(text_w(l, 10.0) for l in lines))
            fsizes = [fs, fs * 0.88, fs * 0.88]
            lh = 1.25 / 72
            ty = iy + ih / 2 - sum(fsizes) * lh / 2
            for txt, f in zip(lines, fsizes):
                ax.text(ix + iw / 2, ty + f * lh / 2, txt, ha="center",
                        va="center", fontsize=f, color="black")
                ty += f * lh
            continue

        items = items_of[c]
        vmax = items[0][1]

        ax.add_patch(Rectangle((ix, iy), iw, HB, facecolor=cmap(0.92),
                               edgecolor="white", linewidth=0.8))
        htext = f"{c} ({len(papers_by_region[c]):,})"
        hfs = min(8.0, 10.0 * (iw - 0.08) / text_w(htext, 10.0))
        if hfs < 5.8:                       # tiny region: name only
            htext = c
            hfs = min(8.0, 10.0 * (iw - 0.08) / text_w(htext, 10.0))
        ax.text(ix + 0.04, iy + HB / 2, htext, ha="left", va="center",
                fontsize=hfs, color="white")
        iy += HB
        ih -= HB
        area = iw * ih
        ssum = sum(v for _, v in items)
        rects = squarify([v * area / ssum for _, v in items], ix, iy, iw, ih)

        def split2(label):
            cuts = [i for i, ch_ in enumerate(label) if ch_ == "-"]
            if not cuts:
                return None
            i = min(cuts, key=lambda j: abs(j - len(label) / 2))
            return [label[: i + 1], label[i + 1:]]

        def fit(label, count, w, h):
            """Fit label line(s) + the count row; count width included so
            a wide count under a short name (V3 / 1,126) cannot overflow."""
            def fs_for(lines, ww, hh):
                wmax = max(max(text_w(l, 10.0) for l in lines),
                           text_w(count, 10.0) * 0.85)
                fs = min(8.5, 10.0 * (ww * 0.92) / wmax)
                max_h = (hh * 0.94 * 72) / ((len(lines) + 0.9) * 1.18)
                return min(fs, max_h)
            cands = [[label]]
            # family-prefix strip inside the family's own region
            # (DeepSeek-R1 -> R1);
            # tried before the 2-line split so R1/V3 render symmetrically
            if label.startswith("DeepSeek-") and len(label) > 9:
                cands.append([label[9:]])
            if split2(label):
                cands.append(split2(label))
            for lines in cands:
                fs = fs_for(lines, w, h)
                if fs >= 5.0:            # print floor at \columnwidth
                    return lines, fs, 0
            fs = fs_for([label], h, w)
            if fs >= 5.0:
                return [label], fs, 90
            return None

        for (n, v), (x, y, w, h) in zip(items, rects):
            ratios.append(w * h / v)
            is_tail = n == ""
            shade = 0.10 if is_tail else 0.18 + 0.38 * (v / vmax)
            color = cmap(shade)
            ax.add_patch(Rectangle((x, y), w, h, facecolor=color,
                                   edgecolor="white", linewidth=0.8))
            count = f"{v:,}"
            cx_, cy_ = x + w / 2, y + h / 2
            if is_tail:
                # residual block: italic "other" tag + count
                word = "other open models" if c == "Others" else "other"
                fitted = fit(word, count, w, h)
                if (fitted is None or fitted[2] != 0) and word != "other":
                    word = "other"
                    fitted = fit(word, count, w, h)
                if fitted is not None and fitted[2] == 0:
                    lines, fs, _ = fitted
                    rows = lines + [count]
                    fsizes = [fs] * len(lines) + [fs * 0.85]
                    lh = 1.22 / 72
                    ty = cy_ - sum(fsizes) * lh / 2
                    for txt, f in zip(rows, fsizes):
                        ax.text(cx_, ty + f * lh / 2, txt, ha="center",
                                va="center", fontsize=f, color="black",
                                style="italic" if txt != count else "normal")
                        ty += f * lh
                elif (fs := min(8.5, 10.0 * (w * 0.92) / text_w(count, 10.0),
                                (h * 0.94 * 72) / (1.9 * 1.18))) >= 5.0:
                    ax.text(cx_, cy_, count, ha="center", va="center",
                            fontsize=fs, color="black")
                continue
            label = pretty(n)
            tcol = "white" if shade > 0.60 else "black"
            fitted = fit(label, count, w, h)
            if fitted is None:
                print(f"UNLABELED: {c} | {label!r} v={v} w={w:.2f} h={h:.2f}")
                continue
            lines, fs, rot = fitted
            rows = lines + [count]
            fsizes = [fs] * len(lines) + [fs * 0.85]
            lh = 1.22 / 72
            total_h = sum(fsizes) * lh
            if rot == 0:
                ty = cy_ - total_h / 2
                for txt, f in zip(rows, fsizes):
                    ax.text(cx_, ty + f * lh / 2, txt, ha="center",
                            va="center", fontsize=f, color=tcol)
                    ty += f * lh
            else:
                tx = cx_ - total_h / 2
                for txt, f in zip(rows, fsizes):
                    ax.text(tx + f * lh / 2, cy_, txt, ha="center",
                            va="center", fontsize=f, color=tcol, rotation=90)
                    tx += f * lh

    save_figure(fig, "open_model_treemap")
    write_table("open_model_developers.txt", "\n".join(
        ["developer    #papers"] + [f"{c:<11}{len(papers_by_region[c]):>8,}" for c in ORDER]))


if __name__ == "__main__":
    main()
