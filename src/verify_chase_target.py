
import pandas as pd

DATA = "data/processed/"

balls = pd.read_csv(DATA + "selected_ball_by_ball.csv")
matches = pd.read_csv(DATA + "analysis_matches.csv")

# Calculate first-innings team totals
regular = balls[balls["innings"].isin([1, 2])].copy()

regular["team_runs"] = (
    regular["runs"].fillna(0)
    + regular["extras1_runs"].fillna(0)
    + regular["extras_2_runs"].fillna(0)
)

first_innings = (
    regular[regular["innings"] == 1]
    .groupby("match_id")["team_runs"]
    .sum()
    .rename("first_innings_total")
)

check = matches.merge(
    first_innings,
    on="match_id",
    how="left"
)

check = check[
    check["revised_target"].notna()
].copy()

check["target_minus_first_total"] = (
    check["revised_target"] - check["first_innings_total"]
)

print("===== REVISED TARGET VALIDATION =====")
print("Matches with revised target:", len(check))

print(check[[
    "match_id", "comp_name", "first_innings_total",
    "revised_target", "target_minus_first_total",
    "result"
]].head(30).to_string(index=False))

print("\n===== TARGET DIFFERENCE SUMMARY =====")
print(check["target_minus_first_total"].describe())

print("\n===== SECOND INNINGS TOTAL COMPARISON =====")

second = (
    regular[regular["innings"] == 2]
    .groupby("match_id")["team_runs"]
    .sum()
    .rename("second_innings_total")
)

check = check.merge(second, on="match_id", how="left")

print(check[[
    "match_id", "revised_target",
    "second_innings_total", "result"
]].head(15).to_string(index=False))

print("\nTARGET VALIDATION COMPLETED!")
