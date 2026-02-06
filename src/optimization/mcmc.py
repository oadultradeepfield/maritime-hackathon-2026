"""MCMC robustness analysis for fleet optimization."""

import json
import math
import random
from collections.abc import Callable
from pathlib import Path

import pandas as pd

from src.optimization.types import MCMCResult, OptimizationParams


def _is_fleet_feasible(
    vessel_df: pd.DataFrame,
    fleet_ids: set[str],
    params: OptimizationParams,
) -> bool:
    """Check if a fleet satisfies all optimization constraints."""
    if not fleet_ids:
        return False

    fleet_df = vessel_df[vessel_df["vessel_id"].isin(fleet_ids)]

    total_dwt = fleet_df["dwt"].sum()
    if total_dwt < params.min_dwt:
        return False

    avg_safety = fleet_df["safety_score"].mean()
    if avg_safety < params.min_avg_safety:
        return False

    if params.require_all_fuel_types:
        required_types = set(vessel_df["main_engine_fuel_type"].unique())
        fleet_types = set(fleet_df["main_engine_fuel_type"].unique())
        if fleet_types != required_types:
            return False

    return True


def _compute_fleet_cost(vessel_df: pd.DataFrame, fleet_ids: set[str]) -> float:
    """Compute total adjusted cost for a fleet."""
    fleet_df = vessel_df[vessel_df["vessel_id"].isin(fleet_ids)]
    return float(fleet_df["adjusted_cost_usd"].sum())


def _categorize_appearance(frequency: float) -> str:
    """Categorize a vessel based on its appearance frequency.

    Categories:
        - essential: Appears in >90% of sampled fleets
        - stable: Appears in 50-90% of sampled fleets
        - variable: Appears in <50% of sampled fleets
    """
    if frequency >= 0.9:
        return "essential"
    elif frequency >= 0.5:
        return "stable"
    else:
        return "variable"


def _run_mcmc_sampling(
    vessel_df: pd.DataFrame,
    all_vessel_ids: list[str],
    optimal_fleet_ids: list[str],
    initial_fleet: set[str],
    initial_cost: float,
    num_iterations: int,
    beta: float,
    params: OptimizationParams,
    on_progress: Callable[[int, int], None] | None,
) -> dict[str, int]:
    """Run MCMC sampling and return appearance counts."""
    current_fleet = initial_fleet
    current_cost = initial_cost
    appearance_counts: dict[str, int] = dict.fromkeys(optimal_fleet_ids, 0)

    for iteration in range(num_iterations):
        vessel_to_flip = random.choice(all_vessel_ids)

        proposed_fleet = current_fleet.copy()
        if vessel_to_flip in proposed_fleet:
            proposed_fleet.remove(vessel_to_flip)
        else:
            proposed_fleet.add(vessel_to_flip)

        if _is_fleet_feasible(vessel_df, proposed_fleet, params):
            proposed_cost = _compute_fleet_cost(vessel_df, proposed_fleet)
            cost_diff = proposed_cost - current_cost
            acceptance_prob = 1.0 if cost_diff <= 0 else math.exp(-beta * cost_diff)

            if random.random() < acceptance_prob:
                current_fleet = proposed_fleet
                current_cost = proposed_cost

        for vid in optimal_fleet_ids:
            if vid in current_fleet:
                appearance_counts[vid] += 1

        if on_progress is not None and (iteration + 1) % 100 == 0:
            on_progress(iteration + 1, num_iterations)

    return appearance_counts


def run_mcmc_robustness(
    vessel_df: pd.DataFrame,
    optimal_fleet_ids: list[str],
    num_iterations: int = 10000,
    beta: float = 0.0001,
    params: OptimizationParams | None = None,
    on_progress: Callable[[int, int], None] | None = None,
    seed: int | None = 42,
) -> list[MCMCResult]:
    """Run MCMC robustness analysis using Metropolis-Hastings sampling.

    Explores near-optimal fleet configurations to identify which vessels
    consistently appear in good solutions (essential) vs those that are
    easily substitutable (variable).

    The algorithm:
        1. Start with the optimal fleet
        2. Propose a new fleet by flipping one vessel's inclusion
        3. Accept with probability min(1, exp(-beta * cost_increase))
        4. Track vessel appearance frequencies

    Args:
        vessel_df: DataFrame with vessel data
        optimal_fleet_ids: List of vessel IDs in the optimal fleet
        num_iterations: Number of MCMC iterations
        beta: Inverse temperature parameter (higher = stricter acceptance)
        params: Optimization parameters (uses defaults if None)
        on_progress: Optional callback(current, total) for progress updates
        seed: Random seed for reproducibility

    Returns:
        List of MCMCResult dictionaries for vessels in optimal fleet
    """
    if params is None:
        params = OptimizationParams()

    if seed is not None:
        random.seed(seed)

    all_vessel_ids = vessel_df["vessel_id"].tolist()
    initial_fleet = set(optimal_fleet_ids)
    initial_cost = _compute_fleet_cost(vessel_df, initial_fleet)

    appearance_counts = _run_mcmc_sampling(
        vessel_df,
        all_vessel_ids,
        optimal_fleet_ids,
        initial_fleet,
        initial_cost,
        num_iterations,
        beta,
        params,
        on_progress,
    )

    results: list[MCMCResult] = []
    for vessel_id in optimal_fleet_ids:
        frequency = appearance_counts[vessel_id] / num_iterations
        category = _categorize_appearance(frequency)
        result: MCMCResult = {
            "vessel_id": vessel_id,
            "appearance_frequency": round(frequency, 4),
            "category": category,
        }
        results.append(result)

    results.sort(key=lambda x: x["appearance_frequency"], reverse=True)

    return results


def save_mcmc_results(results: list[MCMCResult], output_path: Path) -> None:
    """Save MCMC robustness results to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    essential_count = sum(1 for r in results if r["category"] == "essential")
    stable_count = sum(1 for r in results if r["category"] == "stable")
    variable_count = sum(1 for r in results if r["category"] == "variable")

    output = {
        "summary": {
            "vessel_count": len(results),
            "essential_count": essential_count,
            "stable_count": stable_count,
            "variable_count": variable_count,
        },
        "vessels": results,
    }

    with output_path.open("w") as f:
        json.dump(output, f, indent=2)
