"""Fleet optimization module."""

from src.optimization.mcmc import run_mcmc_robustness, save_mcmc_results
from src.optimization.pareto import run_pareto_analysis, save_pareto_frontier
from src.optimization.sensitivity import (
    run_carbon_sensitivity,
    run_sensitivity_heatmap,
    save_carbon_sensitivity,
    save_sensitivity_heatmap,
)
from src.optimization.shapley import compute_shapley_values, save_shapley_values
from src.optimization.solver import optimize_fleet
from src.optimization.types import (
    CarbonSensitivityPoint,
    HeatmapCell,
    MCMCResult,
    OptimizationParams,
    OptimizationResult,
    ParetoPoint,
    ShapleyResult,
)


__all__ = [
    "CarbonSensitivityPoint",
    "HeatmapCell",
    "MCMCResult",
    "OptimizationParams",
    "OptimizationResult",
    "ParetoPoint",
    "ShapleyResult",
    "compute_shapley_values",
    "optimize_fleet",
    "run_carbon_sensitivity",
    "run_mcmc_robustness",
    "run_pareto_analysis",
    "run_sensitivity_heatmap",
    "save_carbon_sensitivity",
    "save_mcmc_results",
    "save_pareto_frontier",
    "save_sensitivity_heatmap",
    "save_shapley_values",
]
