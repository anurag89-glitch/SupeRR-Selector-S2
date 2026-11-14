
import pandas as pd
from pathlib import Path

DATA = Path("data/raw")

matches = pd.read_csv(DATA / "matches.csv")
competitions = pd.read_csv(DATA / "competitions.csv")

# Connect matches with competition information
df = matches.merge(competitions, on="comp_id", how="left")

print("\n===== MATCH FORMAT DISTRIBUTION =====")
print(df["match_format"].value_counts(dropna=False))

print("\n===== SEASON DISTRIBUTION =====")
print(df["season"].value_counts(dropna=False).sort_index())

print("\n===== MATCHES BY FORMAT =====")
print(df.groupby("match_format")["match_id"].nunique())

print("\n===== COMPETITION DETAILS =====")
summary = (
    df.groupby(["comp_id", "comp_name", "match_format", "season"])
    ["match_id"]
    .nunique()
    .reset_index(name="matches")
)

print(summary.to_string(index=False))

print("\n===== IPL COMPETITIONS =====")
print(
    summary[
        summary["comp_name"].str.contains(
            "Indian Premier League|IPL",
            case=False,
            na=False
        )
    ].to_string(index=False)
)

print("\nCOMPETITION EXPLORATION COMPLETED!")
