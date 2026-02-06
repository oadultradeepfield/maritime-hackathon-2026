"""Table formatters for displaying data summaries and results."""

from rich.table import Table

from src.cli.console import console, is_quiet


def display_data_summary(
    ais_records: int,
    unique_vessels: int,
    fuel_types: int,
    fuel_type_names: list[str],
    llaf_rows: int,
    cf_rows: int,
) -> None:
    """Display a summary table of loaded data.

    Args:
        ais_records: Number of AIS records loaded
        unique_vessels: Number of unique vessels
        fuel_types: Number of unique fuel types
        fuel_type_names: List of fuel type names
        llaf_rows: Number of LLAF table rows
        cf_rows: Number of Cf table rows
    """
    if is_quiet():
        return

    table = Table(title="Data Summary", show_header=True, header_style="bold")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    table.add_row("AIS Records", f"{ais_records:,}")
    table.add_row("Unique Vessels", str(unique_vessels))

    fuel_preview = ", ".join(fuel_type_names[:3])
    if len(fuel_type_names) > 3:
        fuel_preview += ", ..."
    table.add_row("Fuel Types", f"{fuel_types} ({fuel_preview})")

    table.add_row("LLAF Rows", str(llaf_rows))
    table.add_row("Cf Rows", str(cf_rows))

    console.print(table)


def display_optimization_result(
    solver_status: str,
    fleet_size: int,
    total_cost: float,
    total_dwt: float,
    avg_safety_score: float,
    total_co2eq: float,
    total_fuel: float,
    fuel_types_count: int,
) -> None:
    """Display a table with fleet optimization results.

    Args:
        solver_status: Status from the solver
        fleet_size: Number of vessels in optimal fleet
        total_cost: Total adjusted cost in USD
        total_dwt: Total deadweight tonnage
        avg_safety_score: Average safety score of fleet
        total_co2eq: Total CO2 equivalent emissions
        total_fuel: Total fuel consumption
        fuel_types_count: Number of unique fuel types
    """
    if is_quiet():
        return

    table = Table(
        title="Fleet Optimization Result", show_header=True, header_style="bold"
    )
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    status_style = "green" if solver_status == "Optimal" else "red"
    table.add_row("Solver Status", f"[{status_style}]{solver_status}[/{status_style}]")
    table.add_row("Fleet Size", f"{fleet_size} vessels")
    table.add_row("Total Cost", f"${total_cost:,.0f}")
    table.add_row("Total DWT", f"{total_dwt:,.0f}")
    table.add_row("Avg Safety Score", f"{avg_safety_score:.2f}")
    table.add_row("Total CO2eq", f"{total_co2eq:,.0f} tonnes")
    table.add_row("Total Fuel", f"{total_fuel:,.0f} tonnes")
    table.add_row("Fuel Types", str(fuel_types_count))

    console.print(table)
