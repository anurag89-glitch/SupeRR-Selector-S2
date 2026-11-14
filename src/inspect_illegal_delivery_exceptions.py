
import pandas as pd

balls = pd.read_csv(
    "data/processed/selected_ball_by_ball.csv"
)

balls["extras_type"] = (
    balls["extras_type"].fillna("none").str.lower()
)

# Count deliveries in each over
over_counts = balls.groupby(
    ["match_id", "innings", "overid"]
).size().rename("over_deliveries")

balls = balls.join(
    over_counts,
    on=["match_id", "innings", "overid"]
)

# Find unusual deliveries in overs with 6 or fewer records
exceptions = balls[
    balls["extras_type"].isin(["other", "overstep"]) &
    (balls["over_deliveries"] <= 6)
]

print("===== EXCEPTIONAL DELIVERY REPORT =====")
print("Total exceptions:", len(exceptions))

columns = [
    "match_id", "innings", "overid",
    "over_ball_num", "over_deliveries",
    "runs", "extras1_runs", "extras_2_runs",
    "is_wicket", "dismissal_type", "extras_type"
]

print(exceptions[columns].to_string(index=False))

print("\n===== EXCEPTIONS BY TYPE =====")
print(exceptions["extras_type"].value_counts())

print("\nAUDIT COMPLETED!")
