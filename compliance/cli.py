import sys

import click
import httpx

from . import api
from .utils import console
from .commands.auth import login, logout
from .commands.workspace import switch
from .commands.rules import init, update, rules, search_rules, tags, keywords
from .commands.telemetry import report_event
from .commands.catalogue import get_catalogue
from .commands.help import help_cmd
from .commands.docs import get_docs


def _make_output_streams_unicode_safe() -> None:
    """Prevent crashes when printing unicode (e.g. en-dashes, arrows) on
    terminals using a limited codepage (common on Windows, e.g. cp1250).

    Text that can't be represented in the console's encoding is replaced
    with '?' instead of raising UnicodeEncodeError and killing the CLI.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(errors="replace")
        except (ValueError, OSError):
            pass


_make_output_streams_unicode_safe()


@click.group()
def main() -> None:
    """Compliance Copilot CLI"""


main.add_command(login)
main.add_command(logout)
main.add_command(switch)
main.add_command(init)
main.add_command(update)
main.add_command(rules)
main.add_command(search_rules)
main.add_command(tags)
main.add_command(keywords)
main.add_command(report_event)
main.add_command(get_catalogue)
main.add_command(help_cmd)
main.add_command(get_docs)


@main.command()
def health() -> None:
    """Check if the backend server is reachable."""
    try:
        data = api.health()
        console.print(f"[bold green]Server status:[/] {data.get('status', 'ok')}")
    except httpx.ConnectError:
        console.print("[bold red]Cannot reach server.[/] Check COMPLIANCE_SERVER_URL.")
        raise SystemExit(1)
