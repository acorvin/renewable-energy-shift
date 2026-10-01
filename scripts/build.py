"""Build the Renewable Energy Shift dataset and dashboard.

Steps:
  1. Download the Our World in Data energy dataset (or read a local copy).
  2. Keep individual countries plus the World total, and the share-by-source columns.
  3. Write cleaned CSVs to data/processed/.
  4. Inject the chart data into src/dashboard.template.html and write docs/index.html (served by GitHub Pages).

Usage:
  python scripts/build.py                       # downloads the latest data
  python scripts/build.py --input path/to.csv   # uses a local copy instead
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE_URL = "https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv"
RAW_PATH = ROOT / "data" / "raw" / "owid-energy-data.csv"
OUT_DIR = ROOT / "data" / "processed"
TEMPLATE = ROOT / "src" / "dashboard.template.html"
SITE_OUT = ROOT / "docs" / "index.html"

BASE_YEAR, END_YEAR = 2014, 2024
ENERGY_FROM, ELEC_FROM = 2000, 2010
MIN_GENERATION_TWH = 5  # drop very small power systems from the electricity view

# ISO codes for African countries, used only for the coverage note.
AFRICA = set(
    "DZA AGO BEN BWA BFA BDI CPV CMR CAF TCD COM COD COG CIV DJI EGY GNQ ERI SWZ ETH "
    "GAB GMB GHA GIN GNB KEN LSO LBR LBY MDG MWI MLI MRT MUS MAR MOZ NAM NER NGA RWA "
    "STP SEN SYC SLE SOM ZAF SSD SDN TZA TGO TUN UGA ZMB ZWE ESH".split()
)

SOURCES = ["hydro", "wind", "solar", "other"]


def load(path: Path | None) -> pd.DataFrame:
    if path is None:
        RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not RAW_PATH.exists():
            print(f"Downloading {SOURCE_URL}")
            pd.read_csv(SOURCE_URL).to_csv(RAW_PATH, index=False)
        path = RAW_PATH
    df = pd.read_csv(path)
    # Real countries have a three-letter ISO code; regional aggregates do not.
    is_country = df["iso_code"].fillna("").str.len().eq(3)
    df = df[is_country | df["country"].eq("World")].copy()
    df.loc[df["country"].eq("World"), "iso_code"] = "WLD"
    return df


def energy_table(df: pd.DataFrame) -> pd.DataFrame:
    """Renewable share of primary energy (substitution method), by source."""
    d = df[(df["year"] >= ENERGY_FROM) & df["renewables_share_energy"].notna()].copy()
    out = pd.DataFrame({
        "country": d["country"],
        "iso_code": d["iso_code"],
        "year": d["year"],
        "population": d["population"],
        "primary_energy_twh": d["primary_energy_consumption"].round(2),
        "renewables_pct": d["renewables_share_energy"].round(2),
        "hydro_pct": d["hydro_share_energy"].fillna(0).round(2),
        "wind_pct": d["wind_share_energy"].fillna(0).round(2),
        "solar_pct": d["solar_share_energy"].fillna(0).round(2),
        # OWID keeps biofuels apart from other renewables; they are combined here.
        "other_pct": (d["other_renewables_share_energy"].fillna(0) + d["biofuel_share_energy"].fillna(0)).round(2),
        "nuclear_pct": d["nuclear_share_energy"].round(2),
        "fossil_pct": d["fossil_share_energy"].round(2),
    })
    return out.reset_index(drop=True)


def electricity_table(df: pd.DataFrame) -> pd.DataFrame:
    """Renewable share of electricity generation, by source."""
    d = df[(df["year"] >= ELEC_FROM) & (df["year"] <= END_YEAR) & df["renewables_share_elec"].notna()].copy()
    out = pd.DataFrame({
        "country": d["country"],
        "iso_code": d["iso_code"],
        "year": d["year"],
        "generation_twh": d["electricity_generation"].round(2),
        "renewables_pct": d["renewables_share_elec"].round(2),
        "hydro_pct": d["hydro_share_elec"].fillna(0).round(2),
        "wind_pct": d["wind_share_elec"].fillna(0).round(2),
        "solar_pct": d["solar_share_elec"].fillna(0).round(2),
        "other_pct": d["other_renewables_share_elec"].fillna(0).round(2),
        "nuclear_pct": d["nuclear_share_elec"].round(2),
        "fossil_pct": d["fossil_share_elec"].round(2),
    })
    return out.reset_index(drop=True)


def chart_series(t: pd.DataFrame, min_gen: float | None = None) -> dict:
    """Per-country yearly shares by source, keeping countries with both end years."""
    series = {}
    for (country, iso), g in t.groupby(["country", "iso_code"]):
        g = g.set_index("year").sort_index()
        if BASE_YEAR not in g.index or END_YEAR not in g.index:
            continue
        if min_gen and iso != "WLD" and not g.loc[END_YEAR, "generation_twh"] >= min_gen:
            continue
        series[country] = {
            "iso": iso,
            "af": iso in AFRICA,
            "y": g.index.tolist(),
            "h": g["hydro_pct"].tolist(),
            "w": g["wind_pct"].tolist(),
            "s": g["solar_pct"].tolist(),
            "o": g["other_pct"].tolist(),
        }
    return series


def change_table(series: dict, measure: str) -> pd.DataFrame:
    rows = []
    keys = dict(zip(SOURCES, "hwso"))
    for country, v in series.items():
        i0, i1 = v["y"].index(BASE_YEAR), v["y"].index(END_YEAR)
        r = {"measure": measure, "country": country, "iso_code": v["iso"]}
        for name, k in keys.items():
            r[f"{name}_{BASE_YEAR}"] = v[k][i0]
            r[f"{name}_{END_YEAR}"] = v[k][i1]
            r[f"{name}_change_pp"] = round(v[k][i1] - v[k][i0], 2)
        r[f"total_{BASE_YEAR}"] = round(sum(v[k][i0] for k in "hwso"), 2)
        r[f"total_{END_YEAR}"] = round(sum(v[k][i1] for k in "hwso"), 2)
        r["total_change_pp"] = round(r[f"total_{END_YEAR}"] - r[f"total_{BASE_YEAR}"], 2)
        rows.append(r)
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", type=Path, help="local copy of owid-energy-data.csv")
    args = ap.parse_args()

    df = load(args.input)
    energy, elec = energy_table(df), electricity_table(df)
    energy_series = chart_series(energy)
    elec_series = chart_series(elec, MIN_GENERATION_TWH)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    energy.to_csv(OUT_DIR / f"renewables_share_primary_energy_{ENERGY_FROM}_{END_YEAR}.csv", index=False)
    elec.to_csv(OUT_DIR / f"renewables_share_electricity_{ELEC_FROM}_{END_YEAR}.csv", index=False)
    pd.concat([change_table(energy_series, "primary_energy"), change_table(elec_series, "electricity")]).to_csv(
        OUT_DIR / f"renewables_change_{BASE_YEAR}_{END_YEAR}_by_source.csv", index=False
    )

    elec_end = elec[elec["year"] == END_YEAR]
    meta = {
        "energyCountries": len(energy_series) - 1,
        "elecCountries": len(elec_series) - 1,
        "africaEnergy": sum(v["af"] for v in energy_series.values()),
        "africaElec": sum(v["af"] for v in elec_series.values()),
        "africaElecAll": int(elec_end["iso_code"].isin(AFRICA).sum()),
        "elecAll2024": int((elec_end["iso_code"] != "WLD").sum()),
    }
    payload = json.dumps({"energy": energy_series, "elec": elec_series, "meta": meta}, separators=(",", ":"))

    html = TEMPLATE.read_text(encoding="utf-8").replace("__DATA__", payload)
    SITE_OUT.parent.mkdir(parents=True, exist_ok=True)
    SITE_OUT.write_text(html, encoding="utf-8")

    world = energy_series["World"]
    i0, i1 = world["y"].index(BASE_YEAR), world["y"].index(END_YEAR)
    total = lambda i: sum(world[k][i] for k in "hwso")
    print(f"Countries: {meta['energyCountries']} (energy), {meta['elecCountries']} (electricity)")
    print(f"World renewables, primary energy: {total(i0):.1f}% -> {total(i1):.1f}%")
    print(f"Wrote {SITE_OUT.relative_to(ROOT)} and {OUT_DIR.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
