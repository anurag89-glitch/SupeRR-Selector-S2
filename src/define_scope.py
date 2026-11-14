
import pandas as pd
from pathlib import Path

DATA = Path("data/raw")

matches = pd.read_csv(DATA / "matches.csv")
competitions = pd.read_csv(DATA / "competitions.csv")

df = matches.merge(competitions, on="comp_id", how="left")

# Include IPL and T20I only
ipl = df["comp_name"].str.contains(
    r"\bIPL\b|Indian Premier League",
    case=False,
    na=False
)

t20i = df["match_format"].eq("T20I")

selected = df[ipl | t20i].copy()

print("\n===== FINAL DATASET SCOPE =====")
print("Total selected matches:", selected["match_id"].nunique())

print("\nMatches by format:")
print(selected.groupby("match_format")["match_id"].nunique())

print("\nIPL matches:")
print(selected[ipl]["match_id"].nunique())

print("\nT20I matches:")
print(selected[t20i]["match_id"].nunique())

print("\nSelected seasons:")
print(sorted(selected["season"].dropna().unique()))

print("\nExcluded matches:", len(df) - len(selected))

print("\nSCOPE VALIDATION COMPLETED!")
