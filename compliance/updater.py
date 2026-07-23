"""Auto-update: checks GitHub Releases once per day and upgrades if a newer version exists."""

import json
import subprocess
import sys
from datetime import date
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import httpx

_PACKAGE = "compliance-copilot"
_GITHUB_REPO = "Ollsoft-ai/copilot-cli"
_INSTALL_URL = "git+https://github.com/Ollsoft-ai/copilot-cli.git"
_CHECK_FILE = Path.home() / ".compliance" / "update_check.json"


def _current_version() -> str | None:
    try:
        return version(_PACKAGE)
    except PackageNotFoundError:
        return None


def _load_check() -> dict:
    try:
        return json.loads(_CHECK_FILE.read_text()) if _CHECK_FILE.exists() else {}
    except Exception:
        return {}


def _save_check(data: dict) -> None:
    _CHECK_FILE.parent.mkdir(parents=True, exist_ok=True)
    _CHECK_FILE.write_text(json.dumps(data))


def check_and_update() -> None:
    """Check GitHub Releases for a newer version once per day and auto-upgrade."""
    data = _load_check()
    if data.get("date") == date.today().isoformat():
        return  # already checked today

    current = _current_version()
    _save_check({"date": date.today().isoformat()})

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
