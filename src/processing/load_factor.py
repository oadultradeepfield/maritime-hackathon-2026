"""Load factor and max speed calculations."""

import pandas as pd

from src.constants import LOAD_FACTOR_FLOOR, MAX_SPEED_MULTIPLIER


def calculate_max_speed(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["max_speed"] = MAX_SPEED_MULTIPLIER * result["vref"]
    return result


def calculate_load_factor(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()

    if "max_speed" not in result.columns:
        result = calculate_max_speed(result)

    result["load_factor"] = (result["speed_knots"] / result["max_speed"]) ** 3
    result["load_factor"] = result["load_factor"].round(2)

    transit_or_maneuver = result["operating_mode"].isin(["Transit", "Maneuver"])
    below_floor = result["load_factor"] < LOAD_FACTOR_FLOOR
    result.loc[transit_or_maneuver & below_floor, "load_factor"] = LOAD_FACTOR_FLOOR

    return result
