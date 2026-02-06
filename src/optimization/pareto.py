"""Pareto frontier analysis for fleet optimization."""

import json
from pathlib import Path

import pandas as pd

from src.optimization.solver import optimize_fleet
from src.optimization.types import OptimizationParams, ParetoPoint


def run_pareto_analysis(
    vessel_df: pd.DataFrame,
    safety_min: float = 3.0,
    safety_max: float = 5.0,
    step: float = 0.1,
) -> list[ParetoPoint]:
    """Run Pareto analysis by varying safety constraint.

    Uses epsilon-constraint method: vary safety threshold from safety_min
    to safety_max, solving the cost minimization problem at each point.

    Args:
        vessel_df: DataFrame with vessel data
        safety_min: Minimum safety threshold to test
        safety_max: Maximum safety threshold to test
        step: Step size for safety threshold

    Returns:
        List of ParetoPoint dictionaries representing the frontier
    """
    points: list[ParetoPoint] = []
    prev_cost: float | None = None

    threshold = safety_min
    while threshold <= safety_max + 1e-9:  # Small epsilon for float comparison
        params = OptimizationParams(
            min_dwt=4_576_667,
            min_avg_safety=threshold,
            require_all_fuel_types=True,
        )

        result = optimize_fleet(vessel_df, params)

        shadow_price: float | None = None
        if prev_cost is not None and result.solver_status == "Optimal":
            shadow_price = (result.total_cost - prev_cost) / step

        point: ParetoPoint = {
            "safety_threshold": round(threshold, 1),
            "total_cost": result.total_cost,
            "total_co2eq": result.total_co2eq,
            "fleet_size": result.fleet_size,
            "fleet_vessel_ids": result.selected_vessel_ids,
            "shadow_price": shadow_price,
        }
        points.append(point)

        prev_cost = result.total_cost if result.solver_status == "Optimal" else None

        threshold += step

    return points


def save_pareto_frontier(points: list[ParetoPoint], output_path: Path) -> None:
    """Save Pareto frontier points to JSON file.

    Args:
        points: List of ParetoPoint dictionaries
        output_path: Path to output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w") as f:
        json.dump(points, f, indent=2)
