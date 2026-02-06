"""CLI module for interactive terminal output."""

from src.cli.console import (
    console,
    print_error,
    print_info,
    print_phase_header,
    print_success,
    print_title,
    print_warning,
)
from src.cli.progress import create_progress_bar, run_with_spinner, spinner
from src.cli.tables import display_data_summary, display_optimization_result


__all__ = [
    "console",
    "create_progress_bar",
    "display_data_summary",
    "display_optimization_result",
    "print_error",
    "print_info",
    "print_phase_header",
    "print_success",
    "print_title",
    "print_warning",
    "run_with_spinner",
    "spinner",
]
