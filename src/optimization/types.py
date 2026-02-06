"""Type definitions for fleet optimization."""

from typing import NamedTuple, TypedDict


class OptimizationParams(NamedTuple):
    """Parameters for fleet optimization."""

    min_dwt: float = 4_576_667
    min_avg_safety: float = 3.0
    require_all_fuel_types: bool = True


class OptimizationResult(NamedTuple):
    """Result from fleet optimization."""

    selected_vessel_ids: list[str]
    total_cost: float
    total_dwt: float
    avg_safety_score: float
    fleet_size: int
    total_co2eq: float
    total_fuel: float
    fuel_types_count: int
    solver_status: str


class ParetoPoint(TypedDict):
    """A point on the Pareto frontier."""

    safety_threshold: float
    total_cost: float
    total_co2eq: float
    fleet_size: int
    fleet_vessel_ids: list[str]
    shadow_price: float | None


class CarbonSensitivityPoint(TypedDict):
    """Result from carbon price sensitivity analysis."""

    carbon_price: float
    total_cost: float
    total_co2eq: float
    fleet_size: int
    fleet_vessel_ids: list[str]


class HeatmapCell(TypedDict):
    """A cell in the sensitivity heatmap grid."""

    carbon_price: float
    safety_threshold: float
    total_cost: float
    fleet_size: int
    feasible: bool


class ShapleyResult(TypedDict):
    """Shapley value for a vessel in the optimal fleet."""

    vessel_id: str
    shapley_value: float
    rank: int
    category: str


class MCMCResult(TypedDict):
    """MCMC robustness analysis result for a vessel."""

    vessel_id: str
    appearance_frequency: float
    category: str
