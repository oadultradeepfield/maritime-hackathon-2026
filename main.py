from pathlib import Path

import pandas as pd

from src.aggregation import aggregate_by_vessel
from src.cost import calculate_costs
from src.data import (
    CalculationFactors,
    load_calculation_factors,
    load_llaf_table,
    load_vessel_movements,
)
from src.emissions import calculate_emissions
from src.fuel import calculate_fuel_consumption
from src.optimization import optimize_fleet, run_pareto_analysis, save_pareto_frontier
from src.output import (
    export_fleet_result_json,
    export_fuel_type_summary_json,
    export_submission_csv,
)
from src.processing import (
    calculate_activity_hours,
    calculate_load_factor,
    calculate_max_speed,
    classify_operating_mode,
)


def _process_movements(movements: pd.DataFrame) -> pd.DataFrame:
    """Phase 1: Process raw AIS movements data."""
    print("\nPhase 1: Processing data...")
    movements = classify_operating_mode(movements)
    movements = calculate_activity_hours(movements)
    movements = calculate_max_speed(movements)
    movements = calculate_load_factor(movements)

    print(f"Operating modes: {movements['operating_mode'].value_counts().to_dict()}")
    print(
        f"Activity hours range: {movements['activity_hours'].min():.2f} - "
        f"{movements['activity_hours'].max():.2f}"
    )
    print(
        f"Load factor range: {movements['load_factor'].min():.2f} - "
        f"{movements['load_factor'].max():.2f}"
    )
    return movements


def _calculate_fuel_and_emissions(
    movements: pd.DataFrame,
    factors: CalculationFactors,
    llaf: pd.DataFrame,
) -> pd.DataFrame:
    """Phase 2-3: Calculate fuel consumption and emissions."""
    print("\nPhase 2: Calculating fuel consumption...")
    movements = calculate_fuel_consumption(movements, factors.cf)

    print(
        f"Fuel ME range: {movements['fuel_me'].min():.4f} - "
        f"{movements['fuel_me'].max():.4f} tonnes"
    )
    print(
        f"Fuel AE range: {movements['fuel_ae'].min():.4f} - "
        f"{movements['fuel_ae'].max():.4f} tonnes"
    )
    print(
        f"Fuel ABL range: {movements['fuel_abl'].min():.4f} - "
        f"{movements['fuel_abl'].max():.4f} tonnes"
    )
    print(f"Total fuel: {movements['fuel_total'].sum():.2f} tonnes")

    print("\nPhase 3: Calculating emissions...")
    movements = calculate_emissions(movements, llaf, factors.cf)

    co2_total = (movements["co2_me"] + movements["co2_ae"] + movements["co2_abl"]).sum()
    n2o_total = (movements["n2o_me"] + movements["n2o_ae"] + movements["n2o_abl"]).sum()
    ch4_total = (movements["ch4_me"] + movements["ch4_ae"] + movements["ch4_abl"]).sum()
    print(f"CO2 total: {co2_total:.2f} tonnes")
    print(f"N2O total: {n2o_total:.6f} tonnes")
    print(f"CH4 total: {ch4_total:.6f} tonnes")
    print(f"CO2eq total: {movements['co2eq_total'].sum():.2f} tonnes")

    return movements


def _aggregate_and_cost(
    movements: pd.DataFrame,
    factors: CalculationFactors,
) -> pd.DataFrame:
    """Phase 4-5: Aggregate by vessel and calculate costs."""
    print("\nPhase 4: Aggregating by vessel...")
    vessel_data = aggregate_by_vessel(movements)

    print(f"Unique vessels: {len(vessel_data)}")
    print(f"Fuel types: {vessel_data['main_engine_fuel_type'].nunique()}")
    print(f"Total fuel (fleet): {vessel_data['total_fuel'].sum():.2f} tonnes")
    print(f"Total CO2eq (fleet): {vessel_data['total_co2eq'].sum():.2f} tonnes")

    print("\nPhase 5: Calculating costs...")
    vessel_data = calculate_costs(vessel_data, factors)

    print(
        f"Fuel cost range: ${vessel_data['fuel_cost_usd'].min():,.0f} - "
        f"${vessel_data['fuel_cost_usd'].max():,.0f}"
    )
    print(
        f"Carbon cost range: ${vessel_data['carbon_cost_usd'].min():,.0f} - "
        f"${vessel_data['carbon_cost_usd'].max():,.0f}"
    )
    print(
        f"Ownership cost range: ${vessel_data['ownership_cost_monthly_usd'].min():,.0f} - "
        f"${vessel_data['ownership_cost_monthly_usd'].max():,.0f}"
    )
    print(
        f"Adjusted cost range: ${vessel_data['adjusted_cost_usd'].min():,.0f} - "
        f"${vessel_data['adjusted_cost_usd'].max():,.0f}"
    )

    return vessel_data


def main() -> None:
    """Run the fleet optimization pipeline."""
    print("Loading data...")
    movements = load_vessel_movements()
    factors = load_calculation_factors()
    llaf = load_llaf_table()

    print(f"Loaded {len(movements):,} AIS records")
    print(f"Unique vessels: {movements['vessel_id'].nunique()}")
    print(f"Fuel types: {movements['main_engine_fuel_type'].nunique()}")
    print(f"Fuel types present: {sorted(movements['main_engine_fuel_type'].unique())}")
    print(f"LLAF table rows: {len(llaf)}")
    print(f"Cf table rows: {len(factors.cf)}")

    movements = _process_movements(movements)
    movements = _calculate_fuel_and_emissions(movements, factors, llaf)
    vessel_data = _aggregate_and_cost(movements, factors)

    print("\nPhase 6: Optimizing fleet selection...")
    result = optimize_fleet(vessel_data)

    print(f"Solver status: {result.solver_status}")
    print(f"Fleet size: {result.fleet_size} vessels")
    print(f"Total cost: ${result.total_cost:,.0f}")
    print(f"Total DWT: {result.total_dwt:,.0f}")
    print(f"Avg safety score: {result.avg_safety_score:.2f}")
    print(f"Total CO2eq: {result.total_co2eq:,.0f} tonnes")
    print(f"Total fuel: {result.total_fuel:,.0f} tonnes")
    print(f"Fuel types: {result.fuel_types_count}")

    print("\nPhase 7a: Running Pareto analysis...")
    pareto_points = run_pareto_analysis(vessel_data)
    save_pareto_frontier(pareto_points, Path("output/pareto_frontier.json"))

    print(f"Generated {len(pareto_points)} Pareto points")
    print("Saved to output/pareto_frontier.json")

    print("\nPhase 8: Generating outputs...")
    output_dir = Path("output")
    export_submission_csv(result, vessel_data, output_dir)
    export_fleet_result_json(result, vessel_data, output_dir)
    export_fuel_type_summary_json(vessel_data, output_dir)
    print("Saved submission.csv, fleet_result.json, fuel_type_summary.json")

    print("\nProcessing complete!")


if __name__ == "__main__":
    main()
