
import pandas as pd
from pathlib import Path

RAW = Path("data/raw")
PROCESSED = Path("data/processed")

matches = pd.read_csv(PROCESSED / "selected_matches.csv")
balls = pd.read_csv(PROCESSED / "selected_ball_by_ball.csv")
playing = pd.read_csv(RAW / "playing_eleven.csv")

# Identify matches without ball-by-ball data
ball_ids = set(balls["match_id"].dropna())
missing_ids = set(matches["match_id"].dropna()) - ball_ids

missing = matches[matches["match_id"].isin(missing_ids)].copy()

print("===== MISSING MATCH AUDIT =====")

# Show useful match information
possible_columns = [
    "match_id", "comp_name", "match_date",
    "team1_name", "team2_name", "result",
    "winner", "status", "match_format"
]

available = [c for c in possible_columns if c in missing.columns]

print("\nMATCH DETAILS:")
print(missing[available].to_string(index=False))

# Check whether playing XI data exists
if "match_id" in playing.columns:
    xi_counts = (
        playing[playing["match_id"].isin(missing_ids)]
        .groupby("match_id")
        .size()
    )

    print("\nPLAYING XI COVERAGE:")
    for match_id in sorted(missing_ids):
        print(
            f"Match {match_id}: "
            f"{xi_counts.get(match_id, 0)} playing XI records"
        )
else:
    print("\nNo match_id column found in playing_eleven.csv")

print("\nAUDIT COMPLETED!")
