"""Shapley value decomposition for fleet optimization."""

import json
import random
from collections.abc import Callable
from pathlib import Path

import pandas as pd

from src.optimization.types import OptimizationParams, ShapleyResult


def _compute_coalition_cost(
    vessel_df: pd.DataFrame,
    coalition_ids: set[str],
    params: OptimizationParams,
    infeasible_penalty: float,
) -> float:
    """Compute the cost of a coalition of vessels.

    If the coalition satisfies all constraints, returns the total adjusted cost.
    Otherwise, returns the infeasible penalty.
    """
    if not coalition_ids:
        return infeasible_penalty

    coalition_df = vessel_df[vessel_df["vessel_id"].isin(coalition_ids)]

    total_dwt = coalition_df["dwt"].sum()
    if total_dwt < params.min_dwt:
        return infeasible_penalty

    avg_safety = coalition_df["safety_score"].mean()
    if avg_safety < params.min_avg_safety:
        return infeasible_penalty

    if params.require_all_fuel_types:
        required_types = set(vessel_df["main_engine_fuel_type"].unique())
        coalition_types = set(coalition_df["main_engine_fuel_type"].unique())
        if coalition_types != required_types:
            return infeasible_penalty

    return float(coalition_df["adjusted_cost_usd"].sum())


def _categorize_shapley_value(
    shapley_value: float,
    max_value: float,
) -> str:
    """Categorize a vessel based on its Shapley value contribution.

    Categories:
        - essential: Top 20% of contribution
        - useful: Middle 60% of contribution
        - marginal: Bottom 20% of contribution
    """
    if max_value <= 0:
        return "marginal"

    ratio = shapley_value / max_value
    if ratio >= 0.8:
        return "essential"
    elif ratio >= 0.2:
        return "useful"
    else:
        return "marginal"


def compute_shapley_values(
    vessel_df: pd.DataFrame,
    optimal_fleet_ids: list[str],
    num_permutations: int = 1000,
    params: OptimizationParams | None = None,
    on_progress: Callable[[int, int], None] | None = None,
    seed: int | None = 42,
) -> list[ShapleyResult]:
    """Compute Shapley values for vessels in the optimal fleet.

    Uses sampling-based approximation with random permutations to estimate
    each vessel's marginal contribution to cost reduction.

    The characteristic function v(S) returns the cost when using only vessels
    in coalition S, or an infeasible penalty if constraints are not met.

    Shapley value represents how much each vessel contributes to reducing
    the total cost compared to not having that vessel.

    Args:
        vessel_df: DataFrame with vessel data
        optimal_fleet_ids: List of vessel IDs in the optimal fleet
        num_permutations: Number of random permutations for approximation
        params: Optimization parameters (uses defaults if None)
        on_progress: Optional callback(current, total) for progress updates
        seed: Random seed for reproducibility

    Returns:
        List of ShapleyResult dictionaries sorted by Shapley value descending
    """
    if params is None:
        params = OptimizationParams()

    if seed is not None:
        random.seed(seed)

    infeasible_penalty = vessel_df["adjusted_cost_usd"].sum() * 2
    marginal_contributions: dict[str, float] = dict.fromkeys(optimal_fleet_ids, 0.0)

    for perm_idx in range(num_permutations):
        permutation = optimal_fleet_ids.copy()
        random.shuffle(permutation)

        coalition: set[str] = set()
        prev_cost = _compute_coalition_cost(
            vessel_df, coalition, params, infeasible_penalty
        )

        for vessel_id in permutation:
            coalition.add(vessel_id)
            current_cost = _compute_coalition_cost(
                vessel_df, coalition, params, infeasible_penalty
            )
            marginal_contribution = prev_cost - current_cost
            marginal_contributions[vessel_id] += marginal_contribution
            prev_cost = current_cost

        if on_progress is not None:
            on_progress(perm_idx + 1, num_permutations)

    shapley_values = {
        vid: contrib / num_permutations
        for vid, contrib in marginal_contributions.items()
    }

    sorted_vessels = sorted(
        shapley_values.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    max_value = sorted_vessels[0][1] if sorted_vessels else 0.0

    results: list[ShapleyResult] = []
    for rank, (vessel_id, value) in enumerate(sorted_vessels, start=1):
        category = _categorize_shapley_value(value, max_value)
        result: ShapleyResult = {
            "vessel_id": vessel_id,
            "shapley_value": round(value, 2),
            "rank": rank,
            "category": category,
        }
        results.append(result)

    return results


def save_shapley_values(results: list[ShapleyResult], output_path: Path) -> None:
    """Save Shapley value results to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    total_shapley = sum(r["shapley_value"] for r in results)
    essential_count = sum(1 for r in results if r["category"] == "essential")
    useful_count = sum(1 for r in results if r["category"] == "useful")
    marginal_count = sum(1 for r in results if r["category"] == "marginal")

    output = {
        "summary": {
            "total_shapley_value": round(total_shapley, 2),
            "vessel_count": len(results),
            "essential_count": essential_count,
            "useful_count": useful_count,
            "marginal_count": marginal_count,
        },
        "vessels": results,
    }

    with output_path.open("w") as f:
        json.dump(output, f, indent=2)
