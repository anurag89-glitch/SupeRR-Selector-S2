
import pandas as pd
from pathlib import Path

DATA = Path("data/processed")

matches = pd.read_csv(DATA / "selected_matches.csv")
balls = pd.read_csv(DATA / "selected_ball_by_ball.csv")

# Identify matches that actually have delivery records
played_ids = balls["match_id"].dropna().unique()

analysis_matches = matches[
    matches["match_id"].isin(played_ids)
].copy()

excluded_matches = matches[
    ~matches["match_id"].isin(played_ids)
].copy()

# Save final analytical datasets
analysis_matches.to_csv(
    DATA / "analysis_matches.csv", index=False
)

excluded_matches.to_csv(
    DATA / "excluded_abandoned_matches.csv", index=False
)

print("===== FINAL DATASET SUMMARY =====")
print("Reference matches:", matches["match_id"].nunique())
print("Matches used for analysis:", analysis_matches["match_id"].nunique())
print("Excluded abandoned matches:", excluded_matches["match_id"].nunique())
print("Ball-by-ball records:", len(balls))

print("\nAll excluded matches abandoned:",
      excluded_matches["result"].eq("Match Abandoned").all())

print("\nFINALIZATION COMPLETED!")
