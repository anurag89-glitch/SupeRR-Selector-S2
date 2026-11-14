
import pandas as pd
from pathlib import Path

DATA = Path("data/processed")

matches = pd.read_csv(DATA / "selected_matches.csv")
balls = pd.read_csv(DATA / "selected_ball_by_ball.csv")

# Compare match IDs
match_ids = set(matches["match_id"].dropna())
ball_ids = set(balls["match_id"].dropna())

missing_ids = match_ids - ball_ids

missing = matches[
    matches["match_id"].isin(missing_ids)
].copy()

print("===== MISSING MATCHES REPORT =====")
print("Selected matches:", len(match_ids))
print("Matches with ball data:", len(ball_ids))
print("Missing matches:", len(missing_ids))

print("\nMissing match details:")

columns = [
    col for col in [
        "match_id", "comp_name", "match_date",
        "team1_name", "team2_name", "match_format"
    ]
    if col in missing.columns
]

print(missing[columns].to_string(index=False))

print("\n===== CHECK COMPLETED =====")
