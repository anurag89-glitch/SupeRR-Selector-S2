
import pandas as pd
from pathlib import Path

RAW = Path("data/raw")
PROCESSED = Path("data/processed")

PROCESSED.mkdir(parents=True, exist_ok=True)

# Load data
matches = pd.read_csv(RAW / "matches.csv")
competitions = pd.read_csv(RAW / "competitions.csv")
balls = pd.read_csv(RAW / "ball_by_ball.csv")

# Identify IPL and T20I matches
match_data = matches.merge(competitions, on="comp_id", how="left")

is_ipl = match_data["comp_name"].str.contains(
    r"\bIPL\b|Indian Premier League",
    case=False,
    na=False
)

is_t20i = match_data["match_format"].eq("T20I")

selected_matches = match_data[is_ipl | is_t20i].copy()

# Filter ball-by-ball data
selected_ids = selected_matches["match_id"].unique()

selected_balls = balls[
    balls["match_id"].isin(selected_ids)
].copy()

# Save processed datasets
selected_matches.to_csv(
    PROCESSED / "selected_matches.csv", index=False
)

selected_balls.to_csv(
    PROCESSED / "selected_ball_by_ball.csv", index=False
)

print("===== DATASET PREPARATION COMPLETE =====")
print("Selected matches:", len(selected_ids))
print("Selected ball-by-ball records:", len(selected_balls))
print("Unique matches in ball data:", selected_balls["match_id"].nunique())
print("Saved files in:", PROCESSED)
