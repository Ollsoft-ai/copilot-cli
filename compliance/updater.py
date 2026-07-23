"""Auto-update: checks GitHub Releases on every command run and upgrades if a newer version exists."""

import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version

import httpx

_PACKAGE = "compliance-copilot"
_GITHUB_REPO = "Ollsoft-ai/copilot-cli"
_INSTALL_URL = "git+https://github.com/Ollsoft-ai/copilot-cli.git"


def _current_version() -> str | None:
    try:
        return version(_PACKAGE)
    except PackageNotFoundError:
        return None


def check_and_update() -> None:
    """Check GitHub Releases on every run and auto-upgrade if a newer version exists."""
    current = _current_version()
    if current is None:
        return

    try:
        resp = httpx.get(
            f"https://api.github.com/repos/{_GITHUB_REPO}/releases/latest",
            headers={"Accept": "application/vnd.github+json"},
            timeout=3,
        )
        latest: str = resp.json()["tag_name"].lstrip("v")
    except Exception:
        return  # silently ignore network / parse errors

    if latest == current:
        return

    from .utils import console  # local import to avoid circular deps

    console.print(f"[dim]🔄 Updating {_PACKAGE} {current} → {latest}...[/]")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", _INSTALL_URL, "-q"],
        capture_output=True,
    )
    if result.returncode == 0:
        console.print(f"[green]✓ Updated to {latest}. Please re-run your command.[/]")
        raise SystemExit(0)
    else:
        console.print(
            f"[yellow]⚠ New version {latest} available.[/] "
            f"Run: [cyan]pip install --upgrade {_INSTALL_URL}[/]"
        )
