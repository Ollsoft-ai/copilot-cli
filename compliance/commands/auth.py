import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import click
import httpx

from .. import api
from ..config import (
    CALLBACK_PORT, FRONTEND_URL,
    clear_tokens, default_token_name,
    load_pat, save_pat, save_tokens,
    load_company,
)
from ..utils import console, require_auth
from .workspace import pick_and_save_company


def _browser_login() -> dict:
    result: dict = {}
    ready = threading.Event()

    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path == "/ping":
                self._respond(b"ok")
                return
            if path == "/callback":
                params = parse_qs(urlparse(self.path).query)
                result["access_token"] = params.get("access_token", [None])[0]
                result["refresh_token"] = params.get("refresh_token", [None])[0]
                self._respond(b"<script>window.close()</script>")
                threading.Thread(target=server.shutdown, daemon=True).start()
                ready.set()
                return
            self._respond(b"")

        def _respond(self, body: bytes) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_):
            pass

    server = HTTPServer(("localhost", CALLBACK_PORT), _Handler)
    callback_uri = f"http://localhost:{CALLBACK_PORT}/callback"
    login_url = f"{FRONTEND_URL}/cli-login?redirect_uri={callback_uri}"

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    webbrowser.open(login_url)
    console.print(f"Opening browser: [dim]{login_url}[/]")
    console.print("Waiting for authentication  [dim](Ctrl+C to cancel)[/]")

    try:
        deadline = 120
        elapsed = 0
        while not ready.is_set() and elapsed < deadline:
            ready.wait(timeout=0.5)
            elapsed += 0.5
    except KeyboardInterrupt:
        console.print("\n[yellow]Login cancelled.[/]")
        server.shutdown()
        raise SystemExit(0)

    if not result.get("access_token"):
        raise RuntimeError("Authentication timed out or was cancelled.")

    return result


def _exchange_for_pat(access_token: str) -> str:
    name = default_token_name()
    pat = api.create_pat(access_token, name)
    save_pat(pat)
    return pat


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
        tokens = _browser_login()
        _exchange_for_pat(tokens["access_token"])
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
