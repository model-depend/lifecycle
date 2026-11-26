# Data

All files are keyed by the ACL Anthology paper ID (`anthology_id`, e.g.
`2023.acl-long.2`). Corpus: 74,029 papers, 2018–2026, Anthology snapshot of
2026-06-24. No paper text, titles, abstracts, or author names are included.

## `extraction/`

Both files are gzipped JSON Lines with one record per paper, in the same order.

### `paper_models.jsonl.gz` — models each paper uses (694,754 mentions)

| Field | Meaning |
|---|---|
| `anthology_id`, `year` | paper ID and publication year |
| `venue` | venue series (`acl`, `emnlp`, `tacl`, `findings`, …) |
| `venue_type` | `flagship`, `findings`, `other_major`, `workshop_other`, or `industry` |
| `extraction_status` | `ok`; `ok_salvaged` (4 papers, output repaired); `parse_error` (1 paper, no models) |
| `models` | list of extracted model mentions (below) |

Each entry of `models`:

| Field | Meaning |
|---|---|
| `name_verbatim` | model name exactly as written in the paper (Gemma output) |
| `version`, `size` | version and parameter size as printed in the paper, else `null` (Gemma output) |
| `grounded` | whether the extractor's evidence quote occurs verbatim in the paper |
| `name_normalized` | spelling-normalized name (case, dashes, spaces) |
| `model_in_paper` | distinct model within the paper: a generic name is absorbed by a more specific one (`gpt-4o` → `gpt-4o-2024-08-06`) |
| `group` | model type: `openai_closed`, `google_closed`, `anthropic_closed`, `other_closed`, `open_llm`, `classic_plm`, `other_model`, `method_metric`, `ambiguous_model`, `unclassified` |
| `subgroup` | finer label within the group (for `other_closed`: the provider) |
| `filtered_model` | `model_in_paper` for real models, `null` for noise groups |
| `model_name` | base model with date pins removed (`gpt-4o-2024-08-06` → `gpt-4o`) |
| `model_company` | developer; for open-weight models only official releases are credited |
| `model_status` | closed models of OpenAI, Google, Anthropic: `ongoing`, `deprecated`, `retired` (shut down), or `unknown`, as of 2026-06-24 |
| `deprecation_date`, `shutdown_date` | official deprecation-announcement and shutdown dates of the matched model version, else `null` |
| `open_model_in_paper` | open-weight models: distinct model within the paper |
| `open_model_name` | open-weight models: family and version line (`llama-3.1-8b-instruct` → `llama-3.1`) |
| `open_model_size` | open-weight models: parameters in billions (`"7B"`, `"0.41B"`), else `null` |
| `open_model_size_source` | `name` (parsed from the name) or `printed` (from `size`) |

The paper's three usage flags are: closed LLM = any of `openai_closed`,
`google_closed`, `anthropic_closed`; open-weight LLM = `open_llm`; classic
PLM = `classic_plm`. The remaining groups are excluded from the analyses.

### `paper_affiliations.jsonl.gz` — author affiliations (332,008 author slots)

`authors` lists the paper's authors in order, without names. Each has
`author_pos` and `affiliations`, a list of:

| Field | Meaning |
|---|---|
| `institution_final` | canonical institution name (ROR name or alias; 18,108 institutions) |
| `org_type_final` | ROR organization type: `academic`, `industry`, `facility`, `funder`, `nonprofit`, `government`, `healthcare`, `archive`, `other`, `unknown` |
| `country_final` | ISO 3166 alpha-2 code, `null` if unresolved |
| `country_source` | `printed` (in the paper header), `ror` (ROR record), `det_alias` / `det_string` (curated alias or string rule), `llm` (Gemma lookup over the institution list) |
| `ror_id` | ROR identifier when matched |

Papers whose header could not be parsed (528) have an empty `authors` list.

## `external/`

- `worldbank_gdp_per_capita.csv` — GDP per capita, PPP, constant 2021
  international $ (WDI indicator `NY.GDP.PCAP.PP.KD`), 2018–2025, with the
  World Bank region and income group. `country` is the ISO alpha-2 code.

## `aggregated/`

Written by the scripts in `code/`.

| File | Content | Script |
|---|---|---|
| `paper_flags.csv` | per paper: year, venue, and 0/1 flags `close_llm`, `open_llm`, `classic_plm`, and open size tiers `open_small` (≤10B), `open_mid` (10–70B), `open_xl` (>70B) | 01 |
| `paper_institution_weights.csv` | fractional author-share credit of each paper per institution | 01 |
| `paper_country_weights.csv` | the same per country (empty `country` = unresolved) | 01 |
| `gini_by_year_institution.csv`, `gini_by_year_country.csv` | per-year Gini index of each model type | 04 |
| `venue_rates.csv` | usage share per venue, 2023–2026 | 05 |
| `country_rates.csv` | credit-weighted usage share per country, 2023–2026 | 05 |
| `country_year_usage_gdp.csv` | country × year: fractional papers, usage shares, GDP per capita | 06 |
