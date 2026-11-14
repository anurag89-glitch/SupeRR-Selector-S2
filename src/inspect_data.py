
from pathlib import Path
import pandas as pd

DATA_DIR = Path("data/raw")

files = [
    "ball_by_ball.csv",
    "matches.csv",
    "playing_eleven.csv",
    "competition_team_player_mapping.csv",
    "teams.csv",
    "competitions.csv"
]

for filename in files:
    print("\n" + "=" * 70)
    print(f"DATASET: {filename}")
    print("=" * 70)

    df = pd.read_csv(DATA_DIR / filename)

    print("Shape:", df.shape)
    print("\nColumns:")
    print(df.columns.tolist())

    print("\nData types:")
    print(df.dtypes.to_string())

    print("\nMissing values:")
    print(df.isnull().sum().to_string())

    print("\nDuplicate rows:", df.duplicated().sum())

    print("\nFirst 3 records:")
    print(df.head(3).to_string(index=False))

print("\nDATASET INSPECTION COMPLETED!")
