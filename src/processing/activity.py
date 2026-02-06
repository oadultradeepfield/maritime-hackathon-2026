"""Activity hours calculation for vessel AIS data."""

import pandas as pd


def calculate_activity_hours(df: pd.DataFrame) -> pd.DataFrame:
    result = df.sort_values(["vessel_id", "timestamp"]).copy()

    time_diff = result.groupby("vessel_id")["timestamp"].diff()
    result["activity_hours"] = time_diff.dt.total_seconds() / 3600
    result["activity_hours"] = result["activity_hours"].fillna(0)

    return result
