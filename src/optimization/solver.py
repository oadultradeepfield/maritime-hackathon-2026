"""MILP solver for fleet selection optimization.

Use optimize_fleet() as the entry point. Implementation details
(formulas, lookup rules) live in the code itself.
"""

import pandas as pd
import pulp

from src.optimization.types import OptimizationParams, OptimizationResult


def _create_problem(
    vessel_df: pd.DataFrame,
    params: OptimizationParams,
) -> tuple[pulp.LpProblem, dict[str, pulp.LpVariable]]:
    """Create the MILP problem with decision variables and constraints."""
    prob = pulp.LpProblem("Fleet_Selection", pulp.LpMinimize)

    vessel_ids = vessel_df["vessel_id"].tolist()
    x = {vid: pulp.LpVariable(f"x_{vid}", cat=pulp.LpBinary) for vid in vessel_ids}

    cost_lookup = dict(
        zip(vessel_df["vessel_id"], vessel_df["adjusted_cost_usd"], strict=True)
    )
    dwt_lookup = dict(zip(vessel_df["vessel_id"], vessel_df["dwt"], strict=True))
    safety_lookup = dict(
        zip(vessel_df["vessel_id"], vessel_df["safety_score"], strict=True)
    )
    fuel_type_lookup = dict(
        zip(vessel_df["vessel_id"], vessel_df["main_engine_fuel_type"], strict=True)
    )

    prob += pulp.lpSum(cost_lookup[vid] * x[vid] for vid in vessel_ids)

    prob += (
        pulp.lpSum(dwt_lookup[vid] * x[vid] for vid in vessel_ids) >= params.min_dwt,
        "min_dwt",
    )

    prob += (
        pulp.lpSum(
            (safety_lookup[vid] - params.min_avg_safety) * x[vid] for vid in vessel_ids
        )
        >= 0,
        "min_avg_safety",
    )

    if params.require_all_fuel_types:
        fuel_types = vessel_df["main_engine_fuel_type"].unique()
        for fuel_type in fuel_types:
            vessels_with_fuel = [
                vid for vid in vessel_ids if fuel_type_lookup[vid] == fuel_type
            ]
            prob += (
                pulp.lpSum(x[vid] for vid in vessels_with_fuel) >= 1,
                f"fuel_type_{fuel_type}",
            )

    return prob, x


def _extract_result(
    prob: pulp.LpProblem,
    x: dict[str, pulp.LpVariable],
    vessel_df: pd.DataFrame,
) -> OptimizationResult:
    """Extract optimization result from solved problem."""
    selected_ids = [vid for vid, var in x.items() if var.varValue == 1]

    selected_df = vessel_df[vessel_df["vessel_id"].isin(selected_ids)]

    total_cost = selected_df["adjusted_cost_usd"].sum()
    total_dwt = selected_df["dwt"].sum()
    avg_safety = selected_df["safety_score"].mean()
    fleet_size = len(selected_ids)
    total_co2eq = selected_df["total_co2eq"].sum()
    total_fuel = selected_df["total_fuel"].sum()
    fuel_types_count = selected_df["main_engine_fuel_type"].nunique()

    return OptimizationResult(
        selected_vessel_ids=selected_ids,
        total_cost=total_cost,
        total_dwt=total_dwt,
        avg_safety_score=avg_safety,
        fleet_size=fleet_size,
        total_co2eq=total_co2eq,
        total_fuel=total_fuel,
        fuel_types_count=fuel_types_count,
        solver_status=pulp.LpStatus[prob.status],
    )


def optimize_fleet(
    vessel_df: pd.DataFrame,
    params: OptimizationParams | None = None,
) -> OptimizationResult:
    """Optimize fleet selection using MILP."""
    if params is None:
        params = OptimizationParams()

    prob, x = _create_problem(vessel_df, params)

    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    return _extract_result(prob, x, vessel_df)
