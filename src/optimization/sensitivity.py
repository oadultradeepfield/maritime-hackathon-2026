"""Sensitivity analysis for fleet optimization."""

import json
from collections.abc import Callable
from pathlib import Path

import pandas as pd

from src.constants import SAFETY_SCORE_ADJUSTMENTS
from src.optimization.solver import optimize_fleet
from src.optimization.types import (
    CarbonSensitivityPoint,
    HeatmapCell,
    OptimizationParams,
)


def _recalculate_costs_with_carbon_price(
    vessel_df: pd.DataFrame,
    carbon_price: float,
) -> pd.DataFrame:
    """Recalculate vessel costs with a different carbon price."""
    result = vessel_df.copy()

    result["carbon_cost_usd"] = result["total_co2eq"] * carbon_price

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


def run_carbon_sensitivity(
    vessel_df: pd.DataFrame,
    carbon_prices: list[float] | None = None,
    on_progress: Callable[[int, int], None] | None = None,
) -> list[CarbonSensitivityPoint]:
    """Run sensitivity analysis across different carbon prices.

    Recalculates vessel costs and re-runs optimization at each carbon price
    to show how the optimal fleet changes.
    """
    if carbon_prices is None:
        carbon_prices = [40, 80, 120, 160]

    points: list[CarbonSensitivityPoint] = []
    total_steps = len(carbon_prices)

    for idx, price in enumerate(carbon_prices):
        adjusted_df = _recalculate_costs_with_carbon_price(vessel_df, price)
        result = optimize_fleet(adjusted_df)

        point: CarbonSensitivityPoint = {
            "carbon_price": price,
            "total_cost": result.total_cost,
            "total_co2eq": result.total_co2eq,
            "fleet_size": result.fleet_size,
            "fleet_vessel_ids": result.selected_vessel_ids,
        }
        points.append(point)

        if on_progress is not None:
            on_progress(idx + 1, total_steps)

    return points


def run_sensitivity_heatmap(
    vessel_df: pd.DataFrame,
    carbon_prices: list[float] | None = None,
    safety_thresholds: list[float] | None = None,
    on_progress: Callable[[int, int], None] | None = None,
) -> list[HeatmapCell]:
    """Run 2D sensitivity analysis across carbon prices and safety thresholds.

    Creates a grid of optimization results showing how total cost varies
    with both carbon price and safety constraint.
    """
    if carbon_prices is None:
        carbon_prices = [40, 80, 120, 160]
    if safety_thresholds is None:
        safety_thresholds = [3.0, 3.5, 4.0, 4.5, 5.0]

    cells: list[HeatmapCell] = []
    total_steps = len(carbon_prices) * len(safety_thresholds)
    current_step = 0

    for price in carbon_prices:
        adjusted_df = _recalculate_costs_with_carbon_price(vessel_df, price)

        for threshold in safety_thresholds:
            params = OptimizationParams(
                min_dwt=4_576_667,
                min_avg_safety=threshold,
                require_all_fuel_types=True,
            )
            result = optimize_fleet(adjusted_df, params)

            feasible = result.solver_status == "Optimal"

            cell: HeatmapCell = {
                "carbon_price": price,
                "safety_threshold": threshold,
                "total_cost": result.total_cost if feasible else 0.0,
                "fleet_size": result.fleet_size if feasible else 0,
                "feasible": feasible,
            }
            cells.append(cell)

            current_step += 1
            if on_progress is not None:
                on_progress(current_step, total_steps)

    return cells


def save_carbon_sensitivity(
    points: list[CarbonSensitivityPoint],
    output_path: Path,
) -> None:
    """Save carbon sensitivity analysis results to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w") as f:
        json.dump(points, f, indent=2)


def save_sensitivity_heatmap(cells: list[HeatmapCell], output_path: Path) -> None:
    """Save sensitivity heatmap results to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w") as f:
        json.dump(cells, f, indent=2)
