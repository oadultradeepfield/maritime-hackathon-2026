"""Console utilities for formatted terminal output."""

from dataclasses import dataclass

from rich.console import Console
from rich.rule import Rule
from rich.text import Text


@dataclass
class ConsoleConfig:
    """Configuration for console output modes."""

    quiet: bool = False
    verbose: bool = False


console = Console()
_config: ConsoleConfig = ConsoleConfig()


def set_quiet_mode(quiet: bool) -> None:
    """Enable or disable quiet mode (minimal output)."""
    _config.quiet = quiet


def set_verbose_mode(verbose: bool) -> None:
    """Enable or disable verbose mode (detailed output)."""
    _config.verbose = verbose


def is_quiet() -> bool:
    """Check if quiet mode is enabled."""
    return _config.quiet


def is_verbose() -> bool:
    """Check if verbose mode is enabled."""
    return _config.verbose


def print_success(message: str) -> None:
    """Print a success message with green checkmark."""
    if not _config.quiet:
        console.print(f"[green]\u2713[/green] {message}")


def print_info(message: str) -> None:
    """Print an info message with blue bullet."""
    if not _config.quiet:
        console.print(f"[blue]\u2022[/blue] {message}")


def print_warning(message: str) -> None:
    """Print a warning message with yellow triangle."""
    if not _config.quiet:
        console.print(f"[yellow]\u26a0[/yellow] {message}")


def print_error(message: str) -> None:
    """Print an error message with red X."""
    console.print(f"[red]\u2717[/red] {message}")


def print_verbose(message: str) -> None:
    """Print a message only in verbose mode."""
    if _config.verbose and not _config.quiet:
        console.print(f"  [dim]{message}[/dim]")


def print_phase_header(phase_num: int | str, title: str) -> None:
    """Print a phase header with horizontal rule."""
    if not _config.quiet:
        console.print()
        rule = Rule(f"Phase {phase_num}: {title}", style="cyan")
        console.print(rule)


def print_title(title: str) -> None:
    """Print a title banner."""
    if not _config.quiet:
        console.print()
        text = Text(title, style="bold cyan")
        console.print(text, justify="center")
        console.print()
