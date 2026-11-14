
import pandas as pd

balls = pd.read_csv(
    "data/processed/selected_ball_by_ball.csv"
)

balls["extras_type"] = (
    balls["extras_type"].fillna("none").str.lower()
)

# Count deliveries in each over
overs = balls.groupby(
    ["match_id", "innings", "overid"]
).agg(
    total_deliveries=("match_id", "size"),
    other_count=("extras_type", lambda x: (x == "other").sum()),
    wide_count=("extras_type", lambda x: (x == "wide").sum()),
    overstep_count=("extras_type", lambda x: (x == "overstep").sum())
).reset_index()

print("===== OVER-LEVEL VALIDATION =====")

print("\nOvers with more than 6 recorded deliveries:")
print((overs["total_deliveries"] > 6).sum())

print("\nOvers containing OTHER:")
print((overs["other_count"] > 0).sum())

print("\nOTHER deliveries in overs with more than 6 deliveries:")
print(
    overs[
        (overs["other_count"] > 0) &
        (overs["total_deliveries"] > 6)
    ][[
        "match_id", "innings", "overid",
        "total_deliveries", "other_count",
        "wide_count", "overstep_count"
    ]].head(25).to_string(index=False)
)

print("\n===== SUMMARY =====")
print(
    overs.groupby(
        overs["total_deliveries"] > 6
    ).agg(
        overs=("match_id", "size"),
        overs_with_other=("other_count", lambda x: (x > 0).sum()),
        overs_with_wide=("wide_count", lambda x: (x > 0).sum()),
        overs_with_overstep=("overstep_count", lambda x: (x > 0).sum())
    ).to_string()
)

print("\nVALIDATION COMPLETED!")
