
import pandas as pd

balls = pd.read_csv(
    "data/processed/selected_ball_by_ball.csv"
)

# Examine all deliveries classified as other
other = balls[
    balls["extras_type"].fillna("").str.lower() == "other"
].copy()

print("===== OTHER EXTRAS SUMMARY =====")
print("Total records:", len(other))
print("Unique matches:", other["match_id"].nunique())

print("\nOver-ball number distribution:")
print(other["over_ball_num"].value_counts().sort_index())

print("\nRuns and extras combinations:")
print(
    other.groupby(
        ["runs", "extras1_runs", "extras_2_runs"]
    ).size().sort_values(ascending=False).head(20)
)

print("\n===== DELIVERY SEQUENCES =====")

groups = other[
    ["match_id", "innings", "overid"]
].drop_duplicates().head(8)

for _, group in groups.iterrows():
    sequence = balls[
        (balls["match_id"] == group["match_id"]) &
        (balls["innings"] == group["innings"]) &
        (balls["overid"] == group["overid"])
    ]

    print(
        f"\nMatch {group['match_id']}, "
        f"Innings {group['innings']}, "
        f"Over {group['overid']}"
    )

    print(sequence[[
        "over_ball_num", "runs",
        "extras1_runs", "extras_2_runs",
        "extras_type"
    ]].to_string(index=False))

print("\nVERIFICATION COMPLETED!")
