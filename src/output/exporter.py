"""Export functions for fleet optimization results."""

import json
from pathlib import Path

import pandas as pd

from src.optimization.types import OptimizationResult


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

    total_dwt = selected["dwt"].sum()
    weighted_safety = (selected["safety_score"] * selected["dwt"]).sum() / total_dwt

    submission = {
        "team_name": "TeamName",
        "category": "Open",
        "report_file_name": "report.pdf",
        "sum_of_fleet_deadweight": int(result.total_dwt),
        "total_cost_of_fleet": round(result.total_cost, 2),
        "average_fleet_safety_score": round(weighted_safety, 2),
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
