"""
Delivery-Level Feature Engineering Pipeline
Project: SupeRR Selector Season 2 - Rajasthan Royals IPL 2027
Author: Senior Cricket Analytics Researcher & Data Scientist

Builds match-state features using strictly pre-delivery information (zero future leakage).
- Handles first and second innings separately.
- Uses match-specific revised over limits (6-ball units).
- Categorizes target provenance rigorously:
    * STANDARD_TARGET: Ordinary first-innings total + 1 (including matches with equal curtailed overs).
    * VERIFIED_REVISED_TARGET: Verified DLS revised target supported by match conclusion.
    * UNRESOLVED_TARGET: Target semantics cannot be reliably established (e.g. Match 48610 retrospective par, interrupted matches).
    * NOT_APPLICABLE: First innings / non-chase deliveries.
- Unresolved targets are never used to compute chase pressure features (runs_required, RRR remain NaN).
- Preserves raw revised_target values without modification.
- Clamps runs required at 0 after verified target is reached.
- Excludes abandoned and interrupted/no-result matches from the primary completed-match dataset.
- Preserves interrupted and super over deliveries separately.
"""

from pathlib import Path
import pandas as pd
import numpy as np

PROCESSED_DIR = Path("data/processed")


def load_cleaned_datasets():
    """Load cleaned matches and deliveries produced by Stage 2."""
    print("Loading cleaned datasets from data/processed/...")
    matches = pd.read_csv(PROCESSED_DIR / "cleaned_matches.csv")
    deliveries = pd.read_csv(PROCESSED_DIR / "cleaned_deliveries.csv")
    return matches, deliveries


def compute_delivery_features(deliveries_df, matches_df):
    """
    Compute rigorous pre-delivery match state features.
    Guarantees zero data leakage: features reflect the exact state BEFORE each ball.
    """
    df = deliveries_df.copy()

    # Precompute match-level mappings
    match_meta = matches_df.set_index("match_id")[
        [
            "comp_id", "comp_name", "season", "match_format", "stage",
            "venue_id", "venue_country", "match_status_category",
            "first_inn_revised_overs", "second_inn_revised_overs", "revised_target"
        ]
    ].to_dict("index")

    # Determine max legal balls for each match and innings
    def get_max_balls(row):
        mid = row["match_id"]
        inn = row["innings"]
        info = match_meta.get(mid, {})
        if inn == 1:
            val = info.get("first_inn_revised_overs")
            return float(val) if pd.notna(val) and val > 0 else 120.0
        elif inn == 2:
            val2 = info.get("second_inn_revised_overs")
            if pd.notna(val2) and val2 > 0:
                return float(val2)
            val1 = info.get("first_inn_revised_overs")
            if pd.notna(val1) and val1 > 0:
                return float(val1)
            return 120.0
        else:
            # Super Overs
            return 6.0

    df["max_balls"] = df.apply(get_max_balls, axis=1)

    # Sort strictly chronologically within each match and innings
    sort_cols = ["match_id", "innings", "innings_ball_num", "overid", "over_ball_num"]
    df = df.sort_values(sort_cols).reset_index(drop=True)

    # Ensure numeric columns
    df["team_runs"] = pd.to_numeric(df["team_runs"], errors="coerce").fillna(0).astype(int)
    df["batter_runs"] = pd.to_numeric(df["batter_runs"], errors="coerce").fillna(0).astype(int)
    df["extras_runs"] = pd.to_numeric(df["extras_runs"], errors="coerce").fillna(0).astype(int)
    df["is_legal_delivery"] = df["is_legal_delivery"].astype(bool)
    df["is_wicket"] = df["is_wicket"].astype(bool)
    df["is_bowler_wicket"] = df["is_bowler_wicket"].astype(bool)

    group_keys = ["match_id", "innings"]

    # 1. State BEFORE delivery (Strict Pre-Delivery State)
    df["runs_before"] = (
        df.groupby(group_keys)["team_runs"].cumsum() - df["team_runs"]
    )

    df["wickets_before"] = (
        df.groupby(group_keys)["is_wicket"].cumsum() - df["is_wicket"].astype(int)
    )

    df["wickets_remaining"] = 10 - df["wickets_before"]

    df["legal_balls_before"] = (
        df.groupby(group_keys)["is_legal_delivery"].cumsum() - df["is_legal_delivery"].astype(int)
    )

    # 2. Balls remaining & Progression
    df["balls_remaining"] = (df["max_balls"] - df["legal_balls_before"]).clip(lower=0.0)
    df["innings_progress"] = np.where(
        df["max_balls"] > 0,
        (df["legal_balls_before"] / df["max_balls"]).clip(lower=0.0, upper=1.0),
        0.0
    )

    # 3. Current Run Rate before delivery
    df["current_run_rate"] = np.where(
        df["legal_balls_before"] > 0,
        (df["runs_before"] * 6.0) / df["legal_balls_before"],
        0.0
    )

    # 4. First-innings total mapping
    first_inn_totals = (
        df[df["innings"] == 1]
        .groupby("match_id")["team_runs"]
        .sum()
        .to_dict()
    )
    df["first_innings_total"] = df["match_id"].map(first_inn_totals)

    # 5. Target provenance classification
    # Categories: STANDARD_TARGET, VERIFIED_REVISED_TARGET, UNRESOLVED_TARGET, NOT_APPLICABLE
    def get_target_provenance(row):
        mid = row["match_id"]
        inn = row["innings"]
        if inn != 2:
            return "NOT_APPLICABLE"

        info = match_meta.get(mid, {})
        status = info.get("match_status_category", "UNKNOWN")
        revised = info.get("revised_target")
        first_tot = row["first_innings_total"]
        ord_target = float(first_tot) + 1.0 if pd.notna(first_tot) else np.nan

        # Unresolved cases:
        # Match 48610 has retrospective par cutoff target (115.0), where team continued batting to 125/4.
        # Interrupted matches without decisive finish have unresolved targets.
        if mid == 48610 or status == "INTERRUPTED_NO_RESULT":
            return "UNRESOLVED_TARGET"

        # Check revised target vs ordinary target
        if pd.notna(revised) and revised > 0:
            if pd.notna(ord_target) and float(revised) == ord_target:
                # Revised target equals ordinary first_innings_total + 1 (e.g. equal curtailed overs)
                return "STANDARD_TARGET"
            else:
                return "VERIFIED_REVISED_TARGET"

        return "STANDARD_TARGET"

    df["target_provenance"] = df.apply(get_target_provenance, axis=1)

    # 6. Second-innings target and chase calculations
    def compute_target(row):
        prov = row["target_provenance"]
        if prov in ["NOT_APPLICABLE", "UNRESOLVED_TARGET"]:
            return np.nan

        if prov == "VERIFIED_REVISED_TARGET":
            mid = row["match_id"]
            info = match_meta.get(mid, {})
            return float(info.get("revised_target"))

        if prov == "STANDARD_TARGET":
            first_tot = row["first_innings_total"]
            return float(first_tot) + 1.0 if pd.notna(first_tot) else np.nan

        return np.nan

    df["target_score"] = df.apply(compute_target, axis=1)

    # Raw vs clamped runs required
    df["runs_required_raw"] = np.where(
        df["target_score"].notna(),
        df["target_score"] - df["runs_before"],
        np.nan
    )

    # Flag deliveries recorded after verified target reached
    df["is_target_reached_before"] = np.where(
        df["target_score"].notna(),
        df["runs_required_raw"] <= 0,
        False
    )

    # Clamped runs required
    df["runs_required"] = np.where(
        df["target_score"].notna(),
        df["runs_required_raw"].clip(lower=0.0),
        np.nan
    )

    # Required Run Rate
    df["required_run_rate"] = np.where(
        df["runs_required"].notna() & (df["balls_remaining"] > 0),
        (df["runs_required"] * 6.0) / df["balls_remaining"],
        np.where(
            df["runs_required"].notna() & (df["balls_remaining"] == 0),
            0.0,
            np.nan
        )
    )

    # RRR minus CRR (chase strain / deficit)
    df["rrr_minus_crr"] = np.where(
        df["required_run_rate"].notna(),
        df["required_run_rate"] - df["current_run_rate"],
        np.nan
    )

    # 7. Innings Stage / Phase classification
    pp_cutoff = df["max_balls"] * 0.30
    death_cutoff = df["max_balls"] * 0.80

    conditions = [
        df["legal_balls_before"] < pp_cutoff,
        (df["legal_balls_before"] >= pp_cutoff) & (df["legal_balls_before"] < death_cutoff),
        df["legal_balls_before"] >= death_cutoff
    ]
    phases = ["POWERPLAY", "MIDDLE", "DEATH"]
    df["phase"] = np.select(conditions, phases, default="MIDDLE")

    # 8. Attach tournament & contextual metadata
    for col in ["comp_name", "season", "match_format", "stage", "venue_country"]:
        col_map = {mid: meta[col] for mid, meta in match_meta.items()}
        df[col] = df["match_id"].map(col_map)
    df["season"] = df["season"].astype(str)

    # 9. Delivery-level performance indicator columns
    df["is_dot_ball"] = (df["team_runs"] == 0) & df["is_legal_delivery"]
    df["is_boundary"] = df["is_four"] | df["is_six"]

    return df


def run_feature_engineering():
    """Execute feature engineering pipeline and output segmented datasets."""
    matches, deliveries = load_cleaned_datasets()

    print("Computing pre-delivery match state features (Zero-Leakage)...")
    enriched_deliveries = compute_delivery_features(deliveries, matches)

    # 1. Primary completed match dataset (regular innings only)
    completed_features = enriched_deliveries[
        (enriched_deliveries["match_status_category"] == "COMPLETED") &
        (~enriched_deliveries["is_super_over"])
    ].copy()

    # 2. Interrupted match features (preserved separately)
    interrupted_features = enriched_deliveries[
        enriched_deliveries["match_status_category"] == "INTERRUPTED_NO_RESULT"
    ].copy()

    # 3. Super Over features (preserved separately)
    super_over_features = enriched_deliveries[
        enriched_deliveries["is_super_over"]
    ].copy()

    # Save outputs
    print("Saving engineered feature datasets to data/processed/...")
    primary_out = PROCESSED_DIR / "delivery_pressure_features.csv"
    interrupted_out = PROCESSED_DIR / "interrupted_delivery_features.csv"
    super_over_out = PROCESSED_DIR / "super_over_delivery_features.csv"

    completed_features.to_csv(primary_out, index=False)
    interrupted_features.to_csv(interrupted_out, index=False)
    super_over_features.to_csv(super_over_out, index=False)

    print("\n" + "=" * 65)
    print("FEATURE ENGINEERING PIPELINE SUMMARY")
    print("=" * 65)
    print(f"Primary Completed Deliveries: {len(completed_features):,}")
    print(f"  - Innings 1 (NOT_APPLICABLE): {(completed_features['target_provenance'] == 'NOT_APPLICABLE').sum():,}")
    print(f"  - STANDARD_TARGET: {(completed_features['target_provenance'] == 'STANDARD_TARGET').sum():,}")
    print(f"  - VERIFIED_REVISED_TARGET: {(completed_features['target_provenance'] == 'VERIFIED_REVISED_TARGET').sum():,}")
    print(f"  - UNRESOLVED_TARGET (Match 48610): {(completed_features['target_provenance'] == 'UNRESOLVED_TARGET').sum():,}")
    print(f"  - Deliveries with target reached before ball: {completed_features['is_target_reached_before'].sum():,}")
    print(f"\nPreserved Auxiliary Deliveries:")
    print(f"  - Interrupted / No-Result Deliveries: {len(interrupted_features):,}")
    print(f"  - Super Over Deliveries: {len(super_over_features):,}")
    print(f"Total Deliveries Accounted For: {len(completed_features) + len(interrupted_features) + len(super_over_features):,}")
    print("=" * 65)

    return completed_features, interrupted_features, super_over_features


if __name__ == "__main__":
    run_feature_engineering()
