
import pandas as pd
import numpy as np
from pathlib import Path

DATA = Path("data/processed")

balls = pd.read_csv(DATA / "selected_ball_by_ball.csv")
matches = pd.read_csv(DATA / "analysis_matches.csv")

# Keep regular innings; Super Overs are handled separately
balls = balls[balls["innings"].isin([1, 2])].copy()

# Convert numeric columns safely
numeric_cols = [
    "runs", "extras1_runs", "extras_2_runs",
    "innings_ball_num", "is_wicket"
]

for col in numeric_cols:
    balls[col] = pd.to_numeric(balls[col], errors="coerce").fillna(0)

# Calculate total team runs on each delivery
balls["team_runs"] = (
    balls["runs"]
    + balls["extras1_runs"]
    + balls["extras_2_runs"]
)

# Provisional legal-ball classification
balls["extras_type_clean"] = (
    balls["extras_type"].fillna("none").str.lower()
)

non_legal_types = ["wide", "overstep", "other"]

balls["is_legal_ball"] = (
    ~balls["extras_type_clean"].isin(non_legal_types)
)

balls["is_wicket"] = balls["is_wicket"].fillna(False).astype(bool)

# Sort deliveries in chronological order
balls = balls.sort_values(
    ["match_id", "innings", "innings_ball_num", "overid", "over_ball_num"]
).reset_index(drop=True)

group_cols = ["match_id", "innings"]

# Calculate match situation BEFORE each delivery
balls["runs_before"] = (
    balls.groupby(group_cols)["team_runs"].cumsum()
    - balls["team_runs"]
)

balls["wickets_before"] = (
    balls.groupby(group_cols)["is_wicket"].cumsum()
    - balls["is_wicket"].astype(int)
)

balls["legal_balls_before"] = (
    balls.groupby(group_cols)["is_legal_ball"].cumsum()
    - balls["is_legal_ball"].astype(int)
)

balls["wickets_remaining"] = 10 - balls["wickets_before"]

# Calculate first-innings totals
first_totals = (
    balls[balls["innings"] == 1]
    .groupby("match_id")["team_runs"]
    .sum()
    .rename("first_innings_total")
)

balls = balls.merge(
    first_totals,
    on="match_id",
    how="left"
)

# Attach match-specific over limits and revised targets
match_fields = matches[[
    "match_id",
    "first_inn_revised_overs",
    "second_inn_revised_overs",
    "revised_target"
]].copy()

balls = balls.merge(
    match_fields,
    on="match_id",
    how="left"
)

# These fields are stored in balls, not overs.
balls["max_balls"] = np.where(
    balls["innings"] == 1,
    balls["first_inn_revised_overs"],
    balls["second_inn_revised_overs"]
)

# Standard T20 limit when no revised limit is supplied
balls["max_balls"] = (
    pd.to_numeric(balls["max_balls"], errors="coerce")
    .fillna(120)
)

balls["balls_remaining"] = (
    balls["max_balls"] - balls["legal_balls_before"]
).clip(lower=0)

# Target score: revised target when available,
# otherwise first-innings total + 1
balls["target_score"] = balls["revised_target"].fillna(
    balls["first_innings_total"] + 1
)

# Chase-specific pressure inputs
balls["runs_required"] = np.where(
    balls["innings"] == 2,
    balls["target_score"] - balls["runs_before"],
    np.nan
)

balls["required_run_rate"] = np.where(
    (balls["innings"] == 2) & (balls["balls_remaining"] > 0),
    balls["runs_required"] * 6 / balls["balls_remaining"],
    np.nan
)

# Save
output = DATA / "delivery_state.csv"
balls.to_csv(output, index=False)

print("===== DELIVERY STATE DATASET CREATED =====")
print("Total deliveries:", len(balls))
print("Unique matches:", balls["match_id"].nunique())

print("\nDeliveries by innings:")
print(balls["innings"].value_counts().sort_index())

print("\nAverage wickets remaining:")
print(balls.groupby("innings")["wickets_remaining"].mean())

print("\nChase records with target:")
print(
    balls[balls["innings"] == 2]["target_score"]
    .notna().sum()
)

print("\nSaved:", output)
print("\nDELIVERY STATE BUILD COMPLETED!")
