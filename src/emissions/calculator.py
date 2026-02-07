"""Emissions calculation for vessel machinery.

Use calculate_emissions() as the entry point. Implementation details
(formulas, lookup rules) live in the code itself.
"""

import pandas as pd

from src.constants import GWP_CH4, GWP_CO2, GWP_N2O


def _get_llaf_values(
    load_factor: pd.Series, operating_mode: pd.Series, llaf_table: pd.DataFrame
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Look up LLAF values for CO2, N2O, and CH4 based on load factor."""
    lf_percent = (load_factor * 100).round().astype(int)

    active_modes = operating_mode.isin(["Transit", "Maneuver"])
    lf_percent = lf_percent.where(~(active_modes & (lf_percent < 2)), 2)

    llaf_lookup = llaf_table.set_index((llaf_table["Load"] * 100).round().astype(int))

    in_range = (lf_percent >= 2) & (lf_percent <= 20)
    lf_clamped = lf_percent.where(in_range)

    llaf_co2 = lf_clamped.map(llaf_lookup["CO2"]).fillna(1.0)
    llaf_n2o = lf_clamped.map(llaf_lookup["N2O"]).fillna(1.0)
    llaf_ch4 = lf_clamped.map(llaf_lookup["CH4"]).fillna(1.0)

    return llaf_co2, llaf_n2o, llaf_ch4


def _build_cf_lookup(cf_table: pd.DataFrame) -> dict[str, dict[str, float]]:
    """Build a fuel type to Cf factors lookup dictionary.

    Keys are normalized to lowercase for case-insensitive matching.
    """
    valid = cf_table.dropna(subset=["Fuel Type"])
    fuel_types = valid["Fuel Type"].str.lower()
    return {
        ft: {"CO2": co2, "N2O": n2o, "CH4": ch4}
        for ft, co2, n2o, ch4 in zip(
            fuel_types, valid["Cf_CO2"], valid["Cf_N2O"], valid["Cf_CH4"], strict=True
        )
    }


def calculate_emissions(
    df: pd.DataFrame, llaf_table: pd.DataFrame, cf_table: pd.DataFrame
) -> pd.DataFrame:
    """Calculate emissions for main engine, aux engine, and aux boiler."""
    result = df.copy()

    llaf_co2, llaf_n2o, llaf_ch4 = _get_llaf_values(
        result["load_factor"], result["operating_mode"], llaf_table
    )

    cf_lookup = _build_cf_lookup(cf_table)

    def get_cf_series(fuel_type_column: pd.Series, gas: str) -> pd.Series:
        """Map fuel types to Cf values for a specific gas."""
        return fuel_type_column.map(
            lambda x: cf_lookup.get(x.lower() if isinstance(x, str) else "", {}).get(
                gas, 0
            )
        )

    machinery_config = [
        ("main_engine_fuel_type", "me"),
        ("aux_engine_fuel_type", "ae"),
        ("boil_engine_fuel_type", "abl"),
    ]
    llaf_map = {"CO2": llaf_co2, "N2O": llaf_n2o, "CH4": llaf_ch4}

    for fuel_col, suffix in machinery_config:
        for gas in ["CO2", "N2O", "CH4"]:
            cf_series = get_cf_series(result[fuel_col], gas)
            result[f"{gas.lower()}_{suffix}"] = (
                llaf_map[gas] * cf_series * result[f"fuel_{suffix}"]
            )

    total_co2 = result["co2_me"] + result["co2_ae"] + result["co2_abl"]
    total_n2o = result["n2o_me"] + result["n2o_ae"] + result["n2o_abl"]
    total_ch4 = result["ch4_me"] + result["ch4_ae"] + result["ch4_abl"]

    result["co2eq_total"] = (
        (GWP_CO2 * total_co2) + (GWP_N2O * total_n2o) + (GWP_CH4 * total_ch4)
    )

    return result
