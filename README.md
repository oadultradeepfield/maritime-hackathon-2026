# Maritime Fleet Optimization

Selects an optimal fleet of chemical/products tankers to transport ~4.6M tonnes/month of bunker fuel from Port Hedland
(Australia) to Singapore, minimizing total cost while meeting safety and fuel diversity constraints.

This repository contains a solution submitted by the team Kopibara.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

## Installation

Clone the repository:

```bash
git clone https://github.com/oadultradeepfield/maritime-hackathon-2026.git
cd maritime-hackathon-2026
```

Install dependencies:

```bash
make install
```

For development with linting and type checking:

```bash
make install-dev
```

## Dataset Setup

The dataset is not included in this repository. Place the following files in the `dataset/` folder:

| File                           | Description                                    |
|--------------------------------|------------------------------------------------|
| `vessel_movements_dataset.csv` | AIS data with 13K+ vessel movement records     |
| `calculation_factors.xlsx`     | Cf factors, LCV values, fuel costs, ship costs |
| `llaf_table.csv`               | Low Load Adjustment Factors for emissions      |
| `submission_template.csv`      | Output format reference                        |

## Quick Start

Run the optimization pipeline:

```bash
make run
```

View the submission results:

```bash
cat output/submission.csv
```

## Commands

| Command            | Description                 |
|--------------------|-----------------------------|
| `make run`         | Run optimization pipeline   |
| `make run-verbose` | Run with detailed output    |
| `make run-quiet`   | Run with minimal output     |
| `make check`       | Run linter and type checker |
| `make format`      | Auto-format code            |
| `make clean`       | Remove cache files          |
| `make help`        | Show all commands           |

## Output Files

Results are written to `output/`:

| File                         | Description                                      |
|------------------------------|--------------------------------------------------|
| `submission.csv`             | Hackathon submission with fleet metrics          |
| `fleet_result.json`          | Selected vessels and optimization summary        |
| `pareto_frontier.json`       | Pareto points from epsilon-constraint method     |
| `carbon_sensitivity.json`    | Fleet changes across carbon price scenarios      |
| `sensitivity_heatmap.json`   | Carbon price x safety threshold cost grid        |
| `sensitivity_comparison.csv` | Comparison of baseline vs high-safety scenarios  |
| `shapley_values.json`        | Per-vessel cost contribution rankings            |
| `fuel_type_summary.json`     | Aggregated statistics by fuel type               |
| `mcmc_robustness.json`       | Vessel appearance frequencies from MCMC sampling |

## Optimization Constraints

The MILP solver satisfies:

1. Combined fleet DWT >= 4,576,667 tonnes
2. Average fleet safety score >= 3.0
3. At least one vessel per fuel type (8 types required)
4. Each vessel selected at most once

## Beyond the Constraints

This solution includes additional analyses:

- **Pareto Analysis** - Explores cost vs safety trade-offs using epsilon-constraint method across 21 safety thresholds (
  3.0 to 5.0).
- **Shapley Value Decomposition** - Identifies which vessels contribute most to cost reduction using sampling-based
  approximation (1000 permutations).
- **MCMC Robustness** - Samples 10,000 feasible fleets to identify "essential" vessels that appear in >90% of low-cost
  solutions.
- **Sensitivity Analysis** - Tests fleet composition across carbon prices ($40-$160/tCO2) and safety thresholds.

## Project Structure

```
src/
├── data/          # Dataset loading
├── processing/    # Mode classification, activity hours, load factor
├── fuel/          # Fuel consumption calculations
├── emissions/     # CO2eq emissions with LLAF lookup
├── cost/          # Fuel, carbon, ownership, and risk premium costs
├── optimization/  # MILP solver, Pareto, Shapley, MCMC
└── output/        # CSV and JSON exporters
```
