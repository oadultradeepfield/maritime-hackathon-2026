"""Progress indicators for long-running operations."""

from collections.abc import Callable, Generator
from contextlib import contextmanager

from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from src.cli.console import console, is_quiet


@contextmanager
def spinner(message: str) -> Generator[None, None, None]:
    """Context manager that displays a spinner during execution."""
    if is_quiet():
        yield
        return

    with console.status(f"[cyan]{message}[/cyan]", spinner="dots"):
        yield


def run_with_spinner[T](message: str, func: Callable[[], T]) -> T:
    """Execute a function while displaying a spinner."""
    with spinner(message):
        return func()


def create_progress_bar() -> Progress:
    """Create a progress bar for tracking iteration progress."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
        disable=is_quiet(),
    )
