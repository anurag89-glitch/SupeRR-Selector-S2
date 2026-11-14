
import pandas as pd
from pathlib import Path

DATA = Path("data/processed")

balls = pd.read_csv(DATA / "selected_ball_by_ball.csv")
matches = pd.read_csv(DATA / "analysis_matches.csv")

# Regular innings only
regular = balls[balls["innings"].isin([1, 2])].copy()

print("===== MATCHES WITHOUT SECOND INNINGS =====")

innings_count = regular.groupby(
    ["match_id", "innings"]
).size().unstack(fill_value=0)

missing_second = innings_count[innings_count.get(2, 0) == 0]

print("Matches without innings 2:", len(missing_second))

details = matches[
    matches["match_id"].isin(missing_second.index)
]

print(details[[
    "match_id", "comp_name", "match_date", "result"
]].to_string(index=False))

# Verify how runs and extras are stored
print("\n===== RUNS AND EXTRAS SAMPLE =====")

sample = balls[
    (balls["extras1_runs"].fillna(0) > 0) |
    (balls["extras_2_runs"].fillna(0) > 0)
]

print(sample[[
    "runs", "extras1_runs", "extras_2_runs", "extras_type"
]].head(20).to_string(index=False))

print("\n===== OVER NUMBER VERIFICATION =====")

for match_id in [17395, 50371]:
    sample_match = regular[
        (regular["match_id"] == match_id) &
        (regular["innings"] == 1)
    ]

    print(f"\nMatch ID: {match_id}")
    print("Over IDs:", sorted(sample_match["overid"].dropna().unique()))
    print("Maximum innings ball number:",
          sample_match["innings_ball_num"].max())

print("\n===== SUPER OVER CHECK =====")
print("Super Over matches:",
      balls.loc[balls["innings"].isin([3, 4]), "match_id"].nunique())

print("\nVERIFICATION COMPLETED!")
