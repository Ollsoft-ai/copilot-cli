import time
import webbrowser

import click
import httpx

from .. import api
from ..browser import has_gui_browser
from ..config import FRONTEND_URL, clear_tokens, load_company, load_pat, save_pat
from ..utils import console, require_auth
from .workspace import pick_and_save_company


def _device_login() -> str:
    """RFC 8628-style device flow: the CLI polls the backend while the user
    approves the login in a browser tab. Works headless (SSH, containers) as
    well as locally -- there's no loopback server to reach, just a URL the
    user can open on any device. Returns a PAT ready to save; the backend
    mints it directly on approval, so no separate exchange step is needed.
    """
    start = api.device_start()
    device_code, user_code = start["device_code"], start["user_code"]
    interval, expires_in = start["interval"], start["expires_in"]
    login_url = f"{FRONTEND_URL}/cli-authorize?device_code={device_code}"

    if has_gui_browser():
        webbrowser.open(login_url)
        console.print(f"Opening browser: [dim]{login_url}[/]")
    else:
        console.print("Open this URL in a browser to continue:")
        console.print(f"[cyan]{login_url}[/]")
    # Shown so the user can check it against the page the browser opened --
    # a mismatch means the link isn't the one this terminal generated.
    console.print(f"Confirm the code shown in the browser matches: [bold]{user_code}[/]")
    console.print("Waiting for authorization  [dim](Ctrl+C to cancel)[/]")

    deadline = time.monotonic() + expires_in
    try:
        while time.monotonic() < deadline:
            time.sleep(interval)
            result = api.device_token(device_code)
            if result.get("error") == "authorization_pending":
                continue
            if result.get("error"):
                break
            return result["token"]
    except KeyboardInterrupt:
        console.print("\n[yellow]Login cancelled.[/]")
        raise SystemExit(0)

    raise RuntimeError("The login link expired. Run `compliance login` again.")


@click.command()
def login() -> None:
    """Log in via browser and save a long-lived token locally."""
    if load_pat():
        console.print("[bold green]Already logged in.[/]")
        existing = load_company()
        if existing:
            console.print(f"  Active company: [cyan]{existing[1]}[/]")
        return
    try:
        save_pat(_device_login())
        console.print("[bold green]Logged in successfully.[/]")
        pick_and_save_company()
        console.print("\nRun [cyan]compliance help[/] to see available commands.")
    except (RuntimeError, Exception) as exc:
        console.print(f"[bold red]Login failed:[/] {exc}")
        raise SystemExit(1)


@click.command()
def logout() -> None:
    """Log out and remove saved credentials."""
    require_auth()
    try:
        api.logout()
    except httpx.HTTPStatusError:
        pass
    clear_tokens()
    console.print("[bold green]Logged out.[/]")
