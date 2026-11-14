
import pandas as pd
from pathlib import Path

DATA = Path("data/processed")

balls = pd.read_csv(DATA / "selected_ball_by_ball.csv")
matches = pd.read_csv(DATA / "analysis_matches.csv")

print("===== INNINGS DISTRIBUTION =====")
print(balls["innings"].value_counts().sort_index())

print("\n===== INNINGS SUMMARY =====")

summary = balls.groupby(
    ["match_id", "innings"]
).agg(
    deliveries=("innings_ball_num", "count"),
    max_over_id=("overid", "max"),
    max_ball_number=("innings_ball_num", "max"),
    total_runs=("runs", "sum"),
    wickets=("is_wicket", "sum")
).reset_index()

print(summary.groupby("innings").agg(
    matches=("match_id", "nunique"),
    total_deliveries=("deliveries", "sum"),
    average_runs=("total_runs", "mean"),
    total_wickets=("wickets", "sum")
).to_string())

print("\n===== INNINGS 3 AND 4 MATCHES =====")
extra_innings = summary[summary["innings"] >= 3]

if len(extra_innings):
    print(extra_innings.to_string(index=False))
else:
    print("No innings 3 or 4 found.")

print("\n===== REVISED OVERS VALUES =====")
cols = [
    "match_id", "comp_name",
    "first_inn_revised_overs",
    "second_inn_revised_overs",
    "revised_target"
]

print(matches[cols].dropna(
    subset=["first_inn_revised_overs",
            "second_inn_revised_overs"]
).head(15).to_string(index=False))

print("\n===== EXTRAS SAMPLE =====")
extras = balls[
    (balls["extras1_runs"].fillna(0) > 0) |
    (balls["extras_2_runs"].fillna(0) > 0)
]

print(extras[[
    "match_id", "innings", "runs",
    "extras1_runs", "extras_2_runs",
    "extras_type"
]].head(15).to_string(index=False))

print("\nINSPECTION COMPLETED!")
