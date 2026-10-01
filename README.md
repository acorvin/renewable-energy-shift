# Renewable Energy Shift, 2014–2024

**Which countries actually shifted to renewable energy over the decade, and which already had it.** Published as the case study *The Real Movers*.

Most renewable-energy rankings are led by Iceland, Norway and Canada. They earned that position decades ago with rivers and dams. This project asks a different question: over the last decade, who actually moved?

Live dashboard: https://acorvin.github.io/renewable-energy-shift/

## Findings

- **2024 was the first year wind and solar supplied more of the world's energy than hydropower:** 6.4% of primary energy against 6.2%. In electricity it was 15.0% against 14.3%.
- **The world's renewable share of primary energy rose from 9.7% to 14.8%.** Wind and solar added 4.9 of the 5.1 points. Hydro's share fell slightly.
- **The hydro-rich leaders split.** Iceland, Norway and Canada barely moved. Sweden and Brazil, also hydro-rich, each gained about 12 points, mostly from wind and solar.
- **The biggest movers** were Denmark (+16.4 points), Lithuania, Finland, the Netherlands, the UK and Chile.
- **Vietnam's share fell overall** even though solar added 4.3 points and wind 2.1. Hydro lost 7.3.

## Data

All data comes from [Our World in Data's energy dataset](https://github.com/owid/energy-data) (CC BY 4.0):

| Measure | Original source | Coverage |
|---|---|---|
| Share of primary energy | Energy Institute, *Statistical Review of World Energy* | 79 countries + World, 2000–2024 |
| Share of electricity | Ember and Energy Institute | 195 countries in 2024; the dashboard keeps the 128 generating at least 5 TWh |

## Method

- **Primary energy shares use the substitution method.** Wind, solar and hydro are counted as the fossil fuel input they would replace, so they aren't undercounted against fuels that lose energy as heat.
- **"Other renewables"** combines biofuels, bioenergy, geothermal and smaller sources.
- **Change** is 2024 minus 2014, in percentage points, split by source.
- **Driver** is the source that added the most share. Countries that gained under 1 point are grouped separately.
- **2025 is left out**, because electricity data for that year is still incomplete.

## Limitations

- **Africa is barely covered in the primary-energy series.** It includes only four African countries (Algeria, Egypt, Morocco, South Africa). The electricity view covers far more.
- **Traditional biomass is excluded.** Wood and charcoal for cooking are a large share of energy in many low-income countries, so their energy mix is understated.
- **Nuclear is low-carbon but not renewable**, so it's left out. Countries such as France and Sweden would rank differently on a low-carbon measure.
- **This is descriptive.** Nothing here explains *why* a country moved.

## Repository

```
notebooks/analysis.ipynb      the analysis, step by step, with checks and charts
scripts/build.py              download, clean, and build the dashboard
src/dashboard.template.html   dashboard source (D3), with a data placeholder
data/processed/               cleaned CSVs
docs/index.html               built dashboard, self-contained (GitHub Pages)
embed/squarespace-snippet.html  iframe embed with auto-height
```

## Analysis notebook

`notebooks/analysis.ipynb` walks through the study: data checks, the world crossover, change by country, what drove it, the Vietnam case, and a robustness check against electricity data. It reads the cleaned CSVs in `data/processed/`, so it runs without a download.

```bash
jupyter lab notebooks/analysis.ipynb
```

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/build.py
```

The script downloads the latest Our World in Data file into `data/raw/` (not tracked by git), rewrites the CSVs in `data/processed/`, and rebuilds `docs/index.html`. To work from a saved copy, use `python scripts/build.py --input path/to/owid-energy-data.csv`.

## Embedding

`docs/index.html` is a single self-contained page. With GitHub Pages set to deploy from `main` → `/docs`, it is served at the repository's Pages URL. Any other static host works too. To place it inside another page, use `embed/squarespace-snippet.html`. The dashboard reports its height to the parent page, so the iframe resizes to fit.

## Credits

Data: Energy Institute, Ember, compiled by Our World in Data (CC BY 4.0).
Analysis and design: Alex Corvin.
