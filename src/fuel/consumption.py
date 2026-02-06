"""Fuel consumption calculation for vessel machinery."""

import pandas as pd

from src.constants import REFERENCE_LCV_MJ_PER_KG


def _build_lcv_lookup(cf_table: pd.DataFrame) -> dict[str, float]:
    """Build a fuel type to LCV lookup dictionary from Cf table.

    Keys are normalized to lowercase for case-insensitive matching.
    """
    valid = cf_table.dropna(subset=["Fuel Type", "LCV (MJ/kg)"])
    return dict(zip(valid["Fuel Type"].str.lower(), valid["LCV (MJ/kg)"], strict=True))


def calculate_fuel_consumption(
    df: pd.DataFrame, cf_table: pd.DataFrame
) -> pd.DataFrame:
    """Calculate fuel consumption for main engine, aux engine, and aux boiler.

    Fuel consumption is only calculated for Transit and Maneuver modes.
    Other modes have zero fuel consumption.

    Formulas (in tonnes):
        Main Engine: (LF * mep * sfc_adjusted_me * A) / 1,000,000
        Aux Engine:  (ael * sfc_adjusted_ae * A) / 1,000,000
        Aux Boiler:  (abl * sfc_adjusted_blr * A) / 1,000,000

    Where sfc_adjusted = sfc * (42.7 / LCV)
    """
    result = df.copy()
    lcv_lookup = _build_lcv_lookup(cf_table)

    lcv_me = result["main_engine_fuel_type"].str.lower().map(lcv_lookup)
    lcv_ae = result["aux_engine_fuel_type"].str.lower().map(lcv_lookup)
    lcv_abl = result["boil_engine_fuel_type"].str.lower().map(lcv_lookup)

    sfc_adj_me = result["sfc_me"] * (REFERENCE_LCV_MJ_PER_KG / lcv_me)
    sfc_adj_ae = result["sfc_ae"] * (REFERENCE_LCV_MJ_PER_KG / lcv_ae)
    sfc_adj_abl = result["sfc_ab"] * (REFERENCE_LCV_MJ_PER_KG / lcv_abl)

    activity = result["activity_hours"]
    load_factor = result["load_factor"]

    fuel_me = (load_factor * result["mep"] * sfc_adj_me * activity) / 1_000_000
    fuel_ae = (result["ael"] * sfc_adj_ae * activity) / 1_000_000
    fuel_abl = (result["abl"] * sfc_adj_abl * activity) / 1_000_000

    active_modes = result["operating_mode"].isin(["Transit", "Maneuver"])

    result["fuel_me"] = fuel_me.where(active_modes, 0)
    result["fuel_ae"] = fuel_ae.where(active_modes, 0)
    result["fuel_abl"] = fuel_abl.where(active_modes, 0)
    result["fuel_total"] = result["fuel_me"] + result["fuel_ae"] + result["fuel_abl"]

    return result
