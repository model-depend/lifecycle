"""Shared paths, loaders, and plot style for all replication scripts."""
import gzip
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
AGG = DATA / "aggregated"          # derived tables written by the scripts
FIGS = REPO / "results" / "figures"
TABLES = REPO / "results" / "tables"
for _d in (AGG, FIGS, TABLES):
    _d.mkdir(parents=True, exist_ok=True)

SNAPSHOT = "2026-06-24"            # ACL Anthology snapshot = lifecycle reference date
YEARS = list(range(2018, 2027))
LLM_ERA = (2023, 2026)             # pre-LLM era: 2018-2022
MAJOR_CLOSED = {"openai_closed", "google_closed", "anthropic_closed"}

# house colors: classic PLM black, closed LLM orange, open-weight purple ramp
COLORS = {"classic_plm": "#111111", "close_llm": "#D08A2E", "open_llm": "#8A6FA8",
          "open_small": "#BCA6D6", "open_mid": "#8A6FA8", "open_xl": "#503A6E"}
RC = {"font.family": "serif", "font.size": 13, "pdf.fonttype": 42,
      "axes.linewidth": 0.8}


def read_jsonl_gz(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)


def paper_models():
    """One record per paper: id, year, venue keys, and extracted models[]."""
    return read_jsonl_gz(DATA / "extraction" / "paper_models.jsonl.gz")


def paper_affiliations():
    """One record per paper: per-author canonical affiliations (no names)."""
    return read_jsonl_gz(DATA / "extraction" / "paper_affiliations.jsonl.gz")


def size_in_billions(s):
    """'7B' / '0.41B' -> 7.0 / 0.41; None if the size is unknown."""
    try:
        return float(s.rstrip("Bb")) if s else None
    except ValueError:
        return None


def write_table(name, text):
    (TABLES / name).write_text(text.rstrip() + "\n")
    print(f"--- results/tables/{name}\n{text.rstrip()}\n")


def save_figure(fig, name):
    # no creation timestamp, so re-running leaves the files byte-identical
    fig.savefig(FIGS / f"{name}.pdf", bbox_inches="tight", metadata={"CreationDate": None})
    print(f"wrote results/figures/{name}.pdf")


def load_flags():
    """anthology_id -> dict of paper_flags.csv (ints for year and flags)."""
    import csv
    out = {}
    with (AGG / "paper_flags.csv").open() as f:
        for r in csv.DictReader(f):
            out[r["anthology_id"]] = {k: (v if k in ("anthology_id", "venue", "venue_type")
                                          else int(v)) for k, v in r.items()}
    return out


COUNTRY_NAMES = {
    "CN": "China", "US": "United States", "DE": "Germany", "GB": "United Kingdom",
    "IN": "India", "FR": "France", "KR": "South Korea", "JP": "Japan", "CA": "Canada",
    "IT": "Italy", "SG": "Singapore", "HK": "Hong Kong", "NL": "Netherlands",
    "CH": "Switzerland", "AU": "Australia", "ES": "Spain", "BR": "Brazil",
    "AE": "United Arab Emirates", "IL": "Israel", "TW": "Taiwan", "BD": "Bangladesh",
    "DK": "Denmark", "SE": "Sweden", "IE": "Ireland", "CZ": "Czechia", "VN": "Vietnam",
    "BE": "Belgium", "FI": "Finland", "RU": "Russia", "PT": "Portugal", "PL": "Poland",
    "IR": "Iran", "NO": "Norway", "AT": "Austria", "RO": "Romania", "SA": "Saudi Arabia",
    "QA": "Qatar", "TR": "Turkey", "GR": "Greece", "EG": "Egypt", "MX": "Mexico",
    "PK": "Pakistan", "BG": "Bulgaria", "TH": "Thailand", "MO": "Macao",
    "LU": "Luxembourg", "EE": "Estonia", "PH": "Philippines", "ZA": "South Africa",
    "IS": "Iceland", "SI": "Slovenia", "SK": "Slovakia", "NZ": "New Zealand",
    "LK": "Sri Lanka", "UA": "Ukraine", "HR": "Croatia", "ID": "Indonesia",
    "HU": "Hungary", "MA": "Morocco", "NP": "Nepal", "NG": "Nigeria", "PS": "Palestine",
    "CO": "Colombia", "LV": "Latvia", "AR": "Argentina", "CL": "Chile", "MT": "Malta",
    "MY": "Malaysia", "DZ": "Algeria", "RS": "Serbia", "TN": "Tunisia", "ET": "Ethiopia",
    "KZ": "Kazakhstan", "UY": "Uruguay",
}
