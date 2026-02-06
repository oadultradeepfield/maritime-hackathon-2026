"""Data loading functions for vessel movements and calculation factors."""

from pathlib import Path
from typing import NamedTuple

import pandas as pd


DATASET_DIR = Path(__file__).parent.parent.parent / "dataset"


class CalculationFactors(NamedTuple):
    cf: pd.DataFrame
    fuel_cost: pd.DataFrame
    carbon_cost: pd.DataFrame
    ship_cost: pd.DataFrame
    safety_adjustment: pd.DataFrame


def load_vessel_movements(path: Path | None = None) -> pd.DataFrame:
    if path is None:
        path = DATASET_DIR / "vessel_movements_dataset.csv"
    movements = pd.read_csv(path)
    movements["timestamp"] = pd.to_datetime(
        movements["timestamp"], format="mixed", utc=True
    )
    return movements


def load_calculation_factors(path: Path | None = None) -> CalculationFactors:
    if path is None:
        path = DATASET_DIR / "calculation_factors.xlsx"
    return CalculationFactors(
        cf=pd.read_excel(path, sheet_name="Cf"),
        fuel_cost=pd.read_excel(path, sheet_name="Fuel cost"),
        carbon_cost=pd.read_excel(path, sheet_name="Cost of Carbon"),
        ship_cost=pd.read_excel(path, sheet_name="Cost of ship"),
        safety_adjustment=pd.read_excel(path, sheet_name="Safety score adjustment"),
    )


def load_llaf_table(path: Path | None = None) -> pd.DataFrame:
    if path is None:
        path = DATASET_DIR / "llaf_table.csv"
    llaf = pd.read_csv(path)
    llaf["Load"] = llaf["Load"].str.rstrip("%").astype(float) / 100
    return llaf
