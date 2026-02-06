"""Maritime Hackathon 2026 - Fleet optimization for bunker fuel transport."""

from src.data import load_calculation_factors, load_llaf_table, load_vessel_movements
from src.emissions import calculate_emissions
from src.fuel import calculate_fuel_consumption
from src.optimization import (
    OptimizationParams,
    OptimizationResult,
    ParetoPoint,
    optimize_fleet,
    run_pareto_analysis,
    save_pareto_frontier,
)
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


__version__ = "0.1.0"

__all__ = [
    "OptimizationParams",
    "OptimizationResult",
    "ParetoPoint",
    "calculate_activity_hours",
    "calculate_emissions",
    "calculate_fuel_consumption",
    "calculate_load_factor",
    "calculate_max_speed",
    "classify_operating_mode",
    "export_fleet_result_json",
    "export_fuel_type_summary_json",
    "export_submission_csv",
    "load_calculation_factors",
    "load_llaf_table",
    "load_vessel_movements",
    "optimize_fleet",
    "run_pareto_analysis",
    "save_pareto_frontier",
]
