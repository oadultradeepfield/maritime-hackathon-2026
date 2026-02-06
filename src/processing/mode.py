"""Operating mode classification for vessel AIS data."""

import pandas as pd


def classify_operating_mode(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()

    in_anchorage = result["in_anchorage"].notna() & (result["in_anchorage"] != "null")
    in_port = result["in_port_boundary"].notna() & (
        result["in_port_boundary"] != "null"
    )
    speed = result["speed_knots"]

    conditions = [
        in_anchorage & (speed < 1),
        in_port & (speed > 1),
        ~in_port & (speed >= 1),
    ]
    choices = ["Anchorage", "Maneuver", "Transit"]

    result["operating_mode"] = pd.Series("Drifting", index=result.index)
    for condition, choice in zip(conditions, choices, strict=False):
        result.loc[condition, "operating_mode"] = choice

    return result
