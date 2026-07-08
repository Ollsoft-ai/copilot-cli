from rich.console import Console

from .config import load_company, load_tokens

console = Console()

_SEVERITY_STYLE: dict[str, str] = {
    "HIGH":   "bold red",
    "MEDIUM": "bold yellow",
    "LOW":    "bold cyan",
    "NONE":   "dim",
}


def require_auth() -> None:
    if not load_tokens():
        console.print("[bold red]Not logged in.[/] Run [cyan]compliance login[/] first.")
        raise SystemExit(1)


def require_company() -> tuple[str, str]:
    """Return (company_id, company_name) or exit with a helpful message."""
    company = load_company()
    if not company:
        console.print(
            "[bold red]No active company.[/] "
            "Run [cyan]compliance login[/] or [cyan]compliance switch[/] to select one."
        )
        raise SystemExit(1)
    return company
