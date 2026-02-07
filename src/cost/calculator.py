"""Cost calculation for per-vessel data.

Use calculate_costs() as the entry point. Implementation details
(formulas, lookup rules) live in the code itself.
"""

import pandas as pd

from src.constants import (
    CARBON_PRICE_USD_PER_TCO2,
    DISCOUNT_RATE,
    SAFETY_SCORE_ADJUSTMENTS,
    SALVAGE_RATE,
    SHIP_LIFETIME_YEARS,
)
from src.data.loader import CalculationFactors


def _build_fuel_cost_lookup(fuel_cost_table: pd.DataFrame) -> dict[str, float]:
    """Build fuel type to cost per tonne lookup."""
    valid = fuel_cost_table.dropna(
        subset=["Fuel Type", "Cost per GJ (USD)", "LCV (MJ/kg)"]
    )
    cost_per_tonne = valid["Cost per GJ (USD)"] * valid["LCV (MJ/kg)"]
    return dict(zip(valid["Fuel Type"].str.lower(), cost_per_tonne, strict=True))


def _get_dwt_bracket(dwt: float) -> str:
    """Determine DWT bracket for ship cost lookup."""
    if dwt <= 40_000:
        return "10-40k DWT"
    elif dwt <= 55_000:
        return "40-55k DWT"
    elif dwt <= 80_000:
        return "55-80k DWT"
    elif dwt <= 120_000:
        return "80-120k DWT"
    else:
        return ">120 DWT"


_DISTILLATE_FUEL_ROW_INDEX = 2
_FUEL_MULTIPLIER_ROW_START = 4
_FUEL_MULTIPLIER_ROW_END = 11


def _parse_ship_cost_table(
    ship_cost_table: pd.DataFrame,
) -> tuple[dict[str, float], dict[str, float]]:
    """Parse ship cost table into base costs and fuel type multipliers."""
    base_row = ship_cost_table.iloc[_DISTILLATE_FUEL_ROW_INDEX]
    base_costs = {
        "10-40k DWT": float(base_row["Cost of ship (in million USD)"]),
        "40-55k DWT": float(base_row["Unnamed: 2"]),
        "55-80k DWT": float(base_row["Unnamed: 3"]),
        "80-120k DWT": float(base_row["Unnamed: 4"]),
        ">120 DWT": float(base_row["Unnamed: 5"]),
    }

    multipliers = {"distillate fuel": 1.0}
    for idx in range(_FUEL_MULTIPLIER_ROW_START, _FUEL_MULTIPLIER_ROW_END):
        row = ship_cost_table.iloc[idx]
        fuel_type = row["Unnamed: 0"]
        multiplier = row["Cost of ship (in million USD)"]
        if pd.notna(fuel_type) and pd.notna(multiplier):
            multipliers[fuel_type.lower()] = float(multiplier)

    return base_costs, multipliers


def _calculate_crf() -> float:
    """Calculate Capital Recovery Factor."""
    r = DISCOUNT_RATE
    n = SHIP_LIFETIME_YEARS
    factor = (1 + r) ** n
    return r * factor / (factor - 1)


def _calculate_ownership_cost(
    dwt: float,
    fuel_type: str,
    base_costs: dict[str, float],
    multipliers: dict[str, float],
) -> float:
    """Calculate monthly ownership cost for a vessel.

    Returns cost in USD.
    """
    bracket = _get_dwt_bracket(dwt)
    p_base = base_costs[bracket]
    m = multipliers.get(fuel_type.lower(), 1.0)
    p = p_base * m  # million USD

    s = SALVAGE_RATE * p
    crf = _calculate_crf()
    annual = (p - s) * crf + DISCOUNT_RATE * s
    monthly = annual / 12

    return monthly * 1_000_000  # Convert to USD


def calculate_costs(df: pd.DataFrame, factors: CalculationFactors) -> pd.DataFrame:
    """Calculate all cost components for per-vessel data."""
    result = df.copy()

    fuel_cost_lookup = _build_fuel_cost_lookup(factors.fuel_cost)
    base_costs, multipliers = _parse_ship_cost_table(factors.ship_cost)

    cost_per_tonne_me = (
        result["main_engine_fuel_type"].str.lower().map(fuel_cost_lookup)
    )
    cost_per_tonne_ae = result["aux_engine_fuel_type"].str.lower().map(fuel_cost_lookup)
    cost_per_tonne_abl = (
        result["boil_engine_fuel_type"].str.lower().map(fuel_cost_lookup)
    )

    result["fuel_cost_usd"] = (
        result["total_fuel_me"] * cost_per_tonne_me
        + result["total_fuel_ae"] * cost_per_tonne_ae
        + result["total_fuel_abl"] * cost_per_tonne_abl
    )

    result["carbon_cost_usd"] = result["total_co2eq"] * CARBON_PRICE_USD_PER_TCO2

    dwt_bracket = result["dwt"].apply(_get_dwt_bracket)
    p_base = dwt_bracket.map(base_costs)
    m = result["main_engine_fuel_type"].str.lower().map(multipliers).fillna(1.0)
    p = p_base * m
    s = SALVAGE_RATE * p
    crf = _calculate_crf()
    annual = (p - s) * crf + DISCOUNT_RATE * s
    result["ownership_cost_monthly_usd"] = (annual / 12) * 1_000_000

    result["total_monthly_cost_usd"] = (
        result["fuel_cost_usd"]
        + result["carbon_cost_usd"]
        + result["ownership_cost_monthly_usd"]
    )

    safety_adjustment = result["safety_score"].map(SAFETY_SCORE_ADJUSTMENTS)
    result["risk_premium_usd"] = result["total_monthly_cost_usd"] * safety_adjustment

    result["adjusted_cost_usd"] = (
        result["total_monthly_cost_usd"] + result["risk_premium_usd"]
    )

    return result
