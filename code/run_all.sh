#!/usr/bin/env bash
# Reproduce every reported number, table, and figure (CPU only, ~2 minutes).
set -euo pipefail
cd "$(dirname "$0")"
for step in 01_build_paper_tables 02_model_concentration 03_open_model_treemap \
            04_usage_concentration_gini 05_usage_by_venue_and_country \
            06_gdp_regressions; do
    echo "=== $step"
    python "$step.py"
done
