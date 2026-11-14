
import pandas as pd

balls = pd.read_csv(
    "data/processed/selected_ball_by_ball.csv"
)

for kind in ["Overstep", "other", "Penalty"]:
    sample = balls[
        balls["extras_type"].fillna("").str.lower() == kind.lower()
    ]

    print(f"\n===== {kind.upper()} =====")
    print("Records:", len(sample))

    if not sample.empty:
        print(sample[[
            "match_id", "innings", "overid",
            "over_ball_num", "innings_ball_num",
            "striker_name", "bowler_name",
            "runs", "extras1_runs", "extras_2_runs",
            "is_wicket", "dismissal_type", "extras_type"
        ]].head(12).to_string(index=False))

print("\nINSPECTION COMPLETED!")
