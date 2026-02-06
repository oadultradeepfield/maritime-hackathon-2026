"""Export functions for fleet optimization results."""

import json
from pathlib import Path

import pandas as pd

from src.optimization.types import (
    CarbonSensitivityPoint,
    HeatmapCell,
    MCMCResult,
    OptimizationResult,
    ParetoPoint,
    ShapleyResult,
)


def export_submission_csv(
    result: OptimizationResult,
    vessel_df: pd.DataFrame,
    output_dir: Path,
) -> None:
    """Export competition submission CSV.

    Creates submission.csv with the required fields per competition spec.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    selected = vessel_df[vessel_df["vessel_id"].isin(result.selected_vessel_ids)]

    avg_safety = selected["safety_score"].mean()

    submission = {
        "sum_of_fleet_deadweight": int(result.total_dwt),
        "total_cost_of_fleet": round(result.total_cost, 2),
        "average_fleet_safety_score": round(avg_safety, 2),
        "no_of_unique_main_engine_fuel_types_in_fleet": result.fuel_types_count,
        "sensitivity_analysis_performance": "Yes",
        "size_of_fleet_count": result.fleet_size,
        "total_emission_CO2_eq": round(result.total_co2eq, 2),
        "total_fuel_consumption": round(result.total_fuel, 2),
    }

    submission_df = pd.DataFrame([submission])
    submission_df.to_csv(output_dir / "submission.csv", index=False)


def export_fleet_result_json(
    result: OptimizationResult,
    vessel_df: pd.DataFrame,
    output_dir: Path,
) -> None:
    """Export fleet result as JSON.

    Creates fleet_result.json with optimal fleet summary and all vessels.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    selected_ids = set(result.selected_vessel_ids)
    vessels = []
    for _, row in vessel_df.iterrows():
        vessel = {
            "vessel_id": row["vessel_id"],
            "vessel_type": row["vessel_type"],
            "dwt": int(row["dwt"]),
            "safety_score": int(row["safety_score"]),
            "main_engine_fuel_type": row["main_engine_fuel_type"],
            "total_fuel": round(row["total_fuel"], 2),
            "total_co2eq": round(row["total_co2eq"], 2),
            "adjusted_cost_usd": round(row["adjusted_cost_usd"], 2),
            "selected": row["vessel_id"] in selected_ids,
        }
        vessels.append(vessel)

    output = {
        "optimal_fleet": {
            "fleet_size": result.fleet_size,
            "total_cost": round(result.total_cost, 2),
            "total_dwt": int(result.total_dwt),
            "avg_safety_score": round(result.avg_safety_score, 2),
            "total_co2eq": round(result.total_co2eq, 2),
            "total_fuel": round(result.total_fuel, 2),
            "fuel_types_count": result.fuel_types_count,
            "solver_status": result.solver_status,
        },
        "vessels": vessels,
    }

    with (output_dir / "fleet_result.json").open("w") as f:
        json.dump(output, f, indent=2)


def export_fuel_type_summary_json(
    vessel_df: pd.DataFrame,
    output_dir: Path,
) -> None:
    """Export fuel type summary as JSON.

    Creates fuel_type_summary.json with aggregated stats per fuel type.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    agg = vessel_df.groupby("main_engine_fuel_type").agg(
        {
            "vessel_id": "count",
            "dwt": "sum",
            "total_fuel": "sum",
            "total_co2eq": "sum",
            "adjusted_cost_usd": "sum",
            "safety_score": "mean",
        }
    )

    fuel_types = []
    for fuel_type, row in agg.iterrows():
        fuel_types.append(
            {
                "fuel_type": fuel_type,
                "vessel_count": int(row["vessel_id"]),
                "total_dwt": int(row["dwt"]),
                "total_fuel": round(row["total_fuel"], 2),
                "total_co2eq": round(row["total_co2eq"], 2),
                "total_cost": round(row["adjusted_cost_usd"], 2),
                "avg_safety_score": round(row["safety_score"], 2),
            }
        )

    output = {"fuel_types": fuel_types}

    with (output_dir / "fuel_type_summary.json").open("w") as f:
        json.dump(output, f, indent=2)


def export_shapley_values_json(
    results: list[ShapleyResult],
    output_dir: Path,
) -> None:
    """Export Shapley value analysis results as JSON.

    Creates shapley_values.json with per-vessel Shapley values and summary.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

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

    with (output_dir / "shapley_values.json").open("w") as f:
        json.dump(output, f, indent=2)


def export_sensitivity_heatmap_json(
    cells: list[HeatmapCell],
    output_dir: Path,
) -> None:
    """Export sensitivity heatmap results as JSON.

    Creates sensitivity_heatmap.json with grid of optimization results.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    feasible_count = sum(1 for c in cells if c["feasible"])
    carbon_prices = sorted({c["carbon_price"] for c in cells})
    safety_thresholds = sorted({c["safety_threshold"] for c in cells})

    output = {
        "summary": {
            "total_cells": len(cells),
            "feasible_cells": feasible_count,
            "carbon_prices": carbon_prices,
            "safety_thresholds": safety_thresholds,
        },
        "cells": cells,
    }

    with (output_dir / "sensitivity_heatmap.json").open("w") as f:
        json.dump(output, f, indent=2)


def export_carbon_sensitivity_json(
    points: list[CarbonSensitivityPoint],
    output_dir: Path,
) -> None:
    """Export carbon price sensitivity analysis results as JSON.

    Creates carbon_sensitivity.json with results at different carbon prices.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    output = {
        "summary": {
            "num_points": len(points),
            "carbon_prices": [p["carbon_price"] for p in points],
        },
        "points": points,
    }

    with (output_dir / "carbon_sensitivity.json").open("w") as f:
        json.dump(output, f, indent=2)


def export_mcmc_results_json(
    results: list[MCMCResult],
    output_dir: Path,
) -> None:
    """Export MCMC robustness analysis results as JSON.

    Creates mcmc_robustness.json with vessel appearance frequencies.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

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

    with (output_dir / "mcmc_robustness.json").open("w") as f:
        json.dump(output, f, indent=2)


def _compute_comparison_metrics(
    baseline_vessels: pd.DataFrame,
    sensitivity_vessels: pd.DataFrame,
    baseline: ParetoPoint,
    sensitivity: ParetoPoint,
) -> pd.DataFrame:
    """Compute comparison metrics between baseline and sensitivity scenarios."""
    comparison = {
        "metric": [
            "total_cost",
            "fleet_size",
            "total_co2eq",
            "avg_safety_score",
            "total_dwt",
            "total_fuel",
        ],
        "baseline_3.0": [
            baseline["total_cost"],
            baseline["fleet_size"],
            baseline["total_co2eq"],
            baseline_vessels["safety_score"].mean(),
            baseline_vessels["dwt"].sum(),
            baseline_vessels["total_fuel"].sum(),
        ],
        "sensitivity_4.0": [
            sensitivity["total_cost"],
            sensitivity["fleet_size"],
            sensitivity["total_co2eq"],
            sensitivity_vessels["safety_score"].mean(),
            sensitivity_vessels["dwt"].sum(),
            sensitivity_vessels["total_fuel"].sum(),
        ],
    }

    comparison_df = pd.DataFrame(comparison)
    comparison_df["delta_pct"] = (
        (comparison_df["sensitivity_4.0"] - comparison_df["baseline_3.0"])
        / comparison_df["baseline_3.0"]
        * 100
    ).round(2)
    return comparison_df


def export_sensitivity_comparison_csv(
    pareto_points: list[ParetoPoint],
    vessel_df: pd.DataFrame,
    output_dir: Path,
) -> None:
    """Export comparison between baseline (safety >= 3.0) and sensitivity (safety >= 4.0)."""
    output_dir.mkdir(parents=True, exist_ok=True)

    baseline = next((p for p in pareto_points if p["safety_threshold"] == 3.0), None)
    sensitivity = next((p for p in pareto_points if p["safety_threshold"] == 4.0), None)

    if baseline is None or sensitivity is None:
        return

    baseline_vessels = vessel_df[
        vessel_df["vessel_id"].isin(baseline["fleet_vessel_ids"])
    ]
    sensitivity_vessels = vessel_df[
        vessel_df["vessel_id"].isin(sensitivity["fleet_vessel_ids"])
    ]

    comparison_df = _compute_comparison_metrics(
        baseline_vessels, sensitivity_vessels, baseline, sensitivity
    )
    comparison_df.to_csv(output_dir / "sensitivity_comparison.csv", index=False)
