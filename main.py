import argparse
from pathlib import Path

import pandas as pd

from src.aggregation import aggregate_by_vessel
from src.cli import console as cli_console
from src.cli import (
    create_progress_bar,
    display_data_summary,
    display_optimization_result,
    print_phase_header,
    print_success,
    print_title,
)
from src.cli.console import print_verbose, set_quiet_mode, set_verbose_mode
from src.cost import calculate_costs
from src.data import (
    CalculationFactors,
    load_calculation_factors,
    load_llaf_table,
    load_vessel_movements,
)
from src.emissions import calculate_emissions
from src.fuel import calculate_fuel_consumption
from src.optimization import (
    OptimizationResult,
    compute_shapley_values,
    optimize_fleet,
    run_carbon_sensitivity,
    run_mcmc_robustness,
    run_pareto_analysis,
    run_sensitivity_heatmap,
    save_pareto_frontier,
)
from src.output import (
    export_carbon_sensitivity_json,
    export_fleet_result_json,
    export_fuel_type_summary_json,
    export_mcmc_results_json,
    export_sensitivity_comparison_csv,
    export_sensitivity_heatmap_json,
    export_shapley_values_json,
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
    print_phase_header(1, "Processing Data")

    movements = classify_operating_mode(movements)
    print_success("Operating modes classified")
    print_verbose(f"Modes: {movements['operating_mode'].value_counts().to_dict()}")

    movements = calculate_activity_hours(movements)
    print_success("Activity hours calculated")
    print_verbose(
        f"Range: {movements['activity_hours'].min():.2f} - "
        f"{movements['activity_hours'].max():.2f}"
    )

    movements = calculate_max_speed(movements)
    movements = calculate_load_factor(movements)
    print_success("Load factors computed")
    print_verbose(
        f"Range: {movements['load_factor'].min():.2f} - "
        f"{movements['load_factor'].max():.2f}"
    )

    return movements


def _calculate_fuel_and_emissions(
    movements: pd.DataFrame,
    factors: CalculationFactors,
    llaf: pd.DataFrame,
) -> pd.DataFrame:
    """Phase 2-3: Calculate fuel consumption and emissions."""
    print_phase_header(2, "Fuel Consumption")

    movements = calculate_fuel_consumption(movements, factors.cf)
    total_fuel = movements["fuel_total"].sum()
    print_success(f"Fuel consumption calculated ({total_fuel:,.0f} tonnes total)")
    print_verbose(
        f"ME: {movements['fuel_me'].min():.4f} - {movements['fuel_me'].max():.4f} tonnes"
    )
    print_verbose(
        f"AE: {movements['fuel_ae'].min():.4f} - {movements['fuel_ae'].max():.4f} tonnes"
    )
    print_verbose(
        f"ABL: {movements['fuel_abl'].min():.4f} - {movements['fuel_abl'].max():.4f} tonnes"
    )

    print_phase_header(3, "Emissions Calculation")

    movements = calculate_emissions(movements, llaf, factors.cf)
    co2_total = (movements["co2_me"] + movements["co2_ae"] + movements["co2_abl"]).sum()
    co2eq_total = movements["co2eq_total"].sum()
    print_success(f"Emissions calculated ({co2eq_total:,.0f} tonnes CO2eq)")
    print_verbose(f"CO2: {co2_total:,.0f} tonnes")
    print_verbose(
        f"N2O: {(movements['n2o_me'] + movements['n2o_ae'] + movements['n2o_abl']).sum():.4f} tonnes"
    )
    print_verbose(
        f"CH4: {(movements['ch4_me'] + movements['ch4_ae'] + movements['ch4_abl']).sum():.4f} tonnes"
    )

    return movements


def _aggregate_and_cost(
    movements: pd.DataFrame,
    factors: CalculationFactors,
) -> pd.DataFrame:
    """Phase 4-5: Aggregate by vessel and calculate costs."""
    print_phase_header(4, "Vessel Aggregation")

    vessel_data = aggregate_by_vessel(movements)
    print_success(f"Aggregated {len(vessel_data)} vessels")
    print_verbose(f"Fuel types: {vessel_data['main_engine_fuel_type'].nunique()}")
    print_verbose(f"Total fuel: {vessel_data['total_fuel'].sum():,.0f} tonnes")
    print_verbose(f"Total CO2eq: {vessel_data['total_co2eq'].sum():,.0f} tonnes")

    print_phase_header(5, "Cost Calculation")

    vessel_data = calculate_costs(vessel_data, factors)
    print_success("Costs calculated")
    print_verbose(
        f"Fuel cost: ${vessel_data['fuel_cost_usd'].min():,.0f} - "
        f"${vessel_data['fuel_cost_usd'].max():,.0f}"
    )
    print_verbose(
        f"Carbon cost: ${vessel_data['carbon_cost_usd'].min():,.0f} - "
        f"${vessel_data['carbon_cost_usd'].max():,.0f}"
    )
    print_verbose(
        f"Adjusted cost: ${vessel_data['adjusted_cost_usd'].min():,.0f} - "
        f"${vessel_data['adjusted_cost_usd'].max():,.0f}"
    )

    return vessel_data


def _run_sensitivity_analyses(
    vessel_data: pd.DataFrame,
    result: OptimizationResult,
    output_dir: Path,
) -> None:
    """Phase 7b-7d: Run all sensitivity analyses."""
    print_phase_header("7b", "Shapley Value Analysis")

    with create_progress_bar() as progress:
        task = progress.add_task("Computing Shapley values...", total=1000)

        def update_shapley_progress(current: int, _total: int) -> None:
            progress.update(task, completed=current)

        shapley_results = compute_shapley_values(
            vessel_data,
            result.selected_vessel_ids,
            num_permutations=1000,
            on_progress=update_shapley_progress,
        )

    export_shapley_values_json(shapley_results, output_dir)
    essential_count = sum(1 for r in shapley_results if r["category"] == "essential")
    print_success(
        f"Computed Shapley values for {len(shapley_results)} vessels ({essential_count} essential)"
    )

    print_phase_header("7c", "Sensitivity Analysis")

    with create_progress_bar() as progress:
        task = progress.add_task("Running sensitivity heatmap...", total=20)

        def update_heatmap_progress(current: int, _total: int) -> None:
            progress.update(task, completed=current)

        heatmap_cells = run_sensitivity_heatmap(
            vessel_data, on_progress=update_heatmap_progress
        )

    export_sensitivity_heatmap_json(heatmap_cells, output_dir)
    feasible_count = sum(1 for c in heatmap_cells if c["feasible"])
    print_success(
        f"Generated {len(heatmap_cells)} heatmap cells ({feasible_count} feasible)"
    )

    carbon_sensitivity = run_carbon_sensitivity(vessel_data)
    export_carbon_sensitivity_json(carbon_sensitivity, output_dir)
    print_success(f"Analyzed {len(carbon_sensitivity)} carbon price scenarios")

    print_phase_header("7d", "MCMC Robustness Analysis")

    with create_progress_bar() as progress:
        task = progress.add_task("Running MCMC sampling...", total=10000)

        def update_mcmc_progress(current: int, _total: int) -> None:
            progress.update(task, completed=current)

        mcmc_results = run_mcmc_robustness(
            vessel_data,
            result.selected_vessel_ids,
            num_iterations=10000,
            on_progress=update_mcmc_progress,
        )

    export_mcmc_results_json(mcmc_results, output_dir)
    mcmc_essential = sum(1 for r in mcmc_results if r["category"] == "essential")
    print_success(f"MCMC analysis complete ({mcmc_essential} essential vessels)")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Maritime Fleet Optimization Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed statistics during processing",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Minimal output (errors only)",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=Path("output"),
        help="Output directory for results (default: output)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    return parser.parse_args()


def main() -> None:
    """Run the fleet optimization pipeline."""
    args = parse_args()

    if args.no_color:
        cli_console.no_color = True

    set_quiet_mode(args.quiet)
    set_verbose_mode(args.verbose)

    print_title("Maritime Fleet Optimization Pipeline")

    movements = load_vessel_movements()
    factors = load_calculation_factors()
    llaf = load_llaf_table()

    fuel_types = sorted(movements["main_engine_fuel_type"].unique())
    display_data_summary(
        ais_records=len(movements),
        unique_vessels=movements["vessel_id"].nunique(),
        fuel_types=len(fuel_types),
        fuel_type_names=fuel_types,
        llaf_rows=len(llaf),
        cf_rows=len(factors.cf),
    )

    movements = _process_movements(movements)
    movements = _calculate_fuel_and_emissions(movements, factors, llaf)
    vessel_data = _aggregate_and_cost(movements, factors)

    print_phase_header(6, "Fleet Optimization")

    result = optimize_fleet(vessel_data)
    print_success("Optimization complete")

    display_optimization_result(
        solver_status=result.solver_status,
        fleet_size=result.fleet_size,
        total_cost=result.total_cost,
        total_dwt=result.total_dwt,
        avg_safety_score=result.avg_safety_score,
        total_co2eq=result.total_co2eq,
        total_fuel=result.total_fuel,
        fuel_types_count=result.fuel_types_count,
    )

    print_phase_header("7a", "Pareto Analysis")

    with create_progress_bar() as progress:
        task = progress.add_task("Running Pareto analysis...", total=21)

        def update_pareto_progress(current: int, _total: int) -> None:
            progress.update(task, completed=current)

        pareto_points = run_pareto_analysis(
            vessel_data, on_progress=update_pareto_progress
        )

    save_pareto_frontier(pareto_points, args.output_dir / "pareto_frontier.json")
    print_success(f"Generated {len(pareto_points)} Pareto points")

    export_sensitivity_comparison_csv(pareto_points, vessel_data, args.output_dir)
    print_success("Saved sensitivity_comparison.csv")

    _run_sensitivity_analyses(vessel_data, result, args.output_dir)

    print_phase_header(8, "Output Generation")

    export_submission_csv(result, vessel_data, args.output_dir)
    export_fleet_result_json(result, vessel_data, args.output_dir)
    export_fuel_type_summary_json(vessel_data, args.output_dir)
    print_success("Saved submission.csv, fleet_result.json, fuel_type_summary.json")

    print_success("Processing complete!")


if __name__ == "__main__":
    main()
