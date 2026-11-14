
import pandas as pd
from pathlib import Path

DATA = Path("data/processed")

matches = pd.read_csv(DATA / "analysis_matches.csv")
balls = pd.read_csv(DATA / "selected_ball_by_ball.csv")

print("===== MATCH DATA COLUMNS =====")
print(matches.columns.tolist())

print("\n===== BALL-BY-BALL COLUMNS =====")
print(balls.columns.tolist())

print("\n===== MATCH PRESSURE FIELDS =====")
match_keywords = [
    "target", "run", "result", "winner",
    "overs", "team", "date", "toss"
]

for col in matches.columns:
    if any(word in col.lower() for word in match_keywords):
        print(f"\n{col}")
        print(matches[col].dropna().head(5).to_list())

print("\n===== DELIVERY PRESSURE FIELDS =====")
ball_keywords = [
    "innings", "over", "ball", "runs",
    "wicket", "batting_team", "bowling_team"
]

for col in balls.columns:
    if any(word in col.lower() for word in ball_keywords):
        print(f"\n{col}")
        print(balls[col].dropna().head(5).to_list())

print("\n===== INNINGS DISTRIBUTION =====")
print(balls["innings"].value_counts().sort_index())

print("\nPRESSURE FIELD INSPECTION COMPLETED!")
