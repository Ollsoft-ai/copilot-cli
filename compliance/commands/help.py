import click

from ..utils import console

_COMMANDS = [
    ("login",        "Log in via browser and save credentials locally."),
    ("logout",       "Log out and remove saved credentials."),
    ("switch",       "Switch the active company (without re-logging in)."),
    ("init",         "Download compliance rules into the current project."),
    ("update",       "Update compliance rules (overwrites existing files)."),
    ("search-rules", "Search rules by keyword or meaning."),
    ("keywords",     "List all unique keywords across active compliance rules.")
]


@click.command(name="help")
def help_cmd() -> None:
    """Show available commands."""
    console.print("\n[bold]Compliance Copilot CLI[/]\n")
    for name, desc in _COMMANDS:
        console.print(f"  [cyan]{name:<14}[/]  {desc}")
    console.print()
