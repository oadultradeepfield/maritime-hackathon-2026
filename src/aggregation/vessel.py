"""Aggregate AIS data points to per-vessel summaries."""

import pandas as pd


_VESSEL_AGG_SPEC: dict[str, str] = {
    "vessel_type_new": "first",
    "dwt": "first",
    "safety_score": "first",
    "main_engine_fuel_type": "first",
    "aux_engine_fuel_type": "first",
    "boil_engine_fuel_type": "first",
    "fuel_me": "sum",
    "fuel_ae": "sum",
    "fuel_abl": "sum",
    "fuel_total": "sum",
    "co2_me": "sum",
    "co2_ae": "sum",
    "co2_abl": "sum",
    "n2o_me": "sum",
    "n2o_ae": "sum",
    "n2o_abl": "sum",
    "ch4_me": "sum",
    "ch4_ae": "sum",
    "ch4_abl": "sum",
    "co2eq_total": "sum",
    "activity_hours": "sum",
}

_VESSEL_RENAME_MAP: dict[str, str] = {
    "vessel_type_new": "vessel_type",
    "fuel_me": "total_fuel_me",
    "fuel_ae": "total_fuel_ae",
    "fuel_abl": "total_fuel_abl",
    "fuel_total": "total_fuel",
    "co2eq_total": "total_co2eq",
    "activity_hours": "total_activity_hours",
}

_GAS_COMPONENT_COLS: list[str] = [
    "co2_me",
    "co2_ae",
    "co2_abl",
    "n2o_me",
    "n2o_ae",
    "n2o_abl",
    "ch4_me",
    "ch4_ae",
    "ch4_abl",
]


def aggregate_by_vessel(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate AIS data points to one row per vessel.

    Filters to Transit/Maneuver modes only for sums, then groups by vessel_id.

    Returns DataFrame with columns:
        - vessel_id, vessel_type, dwt, safety_score
        - main_engine_fuel_type, aux_engine_fuel_type, boil_engine_fuel_type
        - total_fuel_me, total_fuel_ae, total_fuel_abl, total_fuel
        - total_co2, total_n2o, total_ch4, total_co2eq
        - total_activity_hours
    """
    active = df[df["operating_mode"].isin(["Transit", "Maneuver"])].copy()
    vessel_df = active.groupby("vessel_id", as_index=False).agg(_VESSEL_AGG_SPEC)
    vessel_df = vessel_df.rename(columns=_VESSEL_RENAME_MAP)

    vessel_df["total_co2"] = (
        vessel_df["co2_me"] + vessel_df["co2_ae"] + vessel_df["co2_abl"]
    )
    vessel_df["total_n2o"] = (
        vessel_df["n2o_me"] + vessel_df["n2o_ae"] + vessel_df["n2o_abl"]
    )
    vessel_df["total_ch4"] = (
        vessel_df["ch4_me"] + vessel_df["ch4_ae"] + vessel_df["ch4_abl"]
    )

    vessel_df = vessel_df.drop(columns=_GAS_COMPONENT_COLS)

    return vessel_df
