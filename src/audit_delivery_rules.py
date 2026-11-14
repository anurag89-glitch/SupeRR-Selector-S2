
import pandas as pd
from pathlib import Path

balls = pd.read_csv(
    Path("data/processed") / "selected_ball_by_ball.csv"
)

print("===== EXTRAS TYPE DISTRIBUTION =====")
print(balls["extras_type"].fillna("none").value_counts())

print("\n===== RUNS DISTRIBUTION BY EXTRAS =====")
print(
    balls.groupby(
        balls["extras_type"].fillna("none")
    ).agg(
        deliveries=("match_id", "count"),
        batter_runs=("runs", "sum"),
        extras1=("extras1_runs", "sum"),
        extras2=("extras_2_runs", "sum")
    ).to_string()
)

print("\n===== NON-ZERO BATTER RUNS SAMPLE =====")
print(
    balls[balls["runs"] > 0][
        ["runs", "extras1_runs", "extras_2_runs", "extras_type"]
    ].head(15).to_string(index=False)
)

print("\n===== WIDE AND NO-BALL SAMPLES =====")
for kind in ["wide", "noballs", "no ball", "noball"]:
    sample = balls[
        balls["extras_type"].astype(str).str.lower() == kind
    ]

    if not sample.empty:
        print(f"\n{kind}:")
        print(sample[[
            "runs", "extras1_runs", "extras_2_runs",
            "innings_ball_num", "over_ball_num"
        ]].head(10).to_string(index=False))

print("\nDELIVERY RULE AUDIT COMPLETED!")
