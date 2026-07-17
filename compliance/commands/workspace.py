import click
import httpx
import questionary

from .. import api
from ..config import save_company
from ..utils import console, require_auth


def pick_and_save_company() -> None:
    """Fetch companies and interactively save the active one."""
    try:
        companies = api.companies_list()
    except httpx.HTTPStatusError as exc:
        console.print(f"[bold yellow]Warning:[/] Could not fetch companies: {exc.response.text}")
        return

    if not companies:
        console.print("[bold yellow]Warning:[/] No companies found for your account.")
        return

    if len(companies) == 1:
        save_company(companies[0]["id"], companies[0].get("name", ""))
        console.print(f"  Company: [cyan]{companies[0].get('name')}[/]")
        return

    choices = [
        questionary.Choice(title=c.get("name", c["id"]), value=c)
        for c in companies
    ]
    chosen = questionary.select(
        "Select company:",
        choices=choices,
        use_shortcuts=False,
        style=questionary.Style([
            ("selected",    "fg:#E20074 bold"),
            ("pointer",     "fg:#E20074 bold"),
            ("highlighted", "fg:#E20074"),
            ("question",    "bold"),
            ("answer",      "fg:#E20074 bold"),
        ]),
    ).ask()

    if chosen is None:
        console.print("[yellow]Selection cancelled.[/]")
        return

    save_company(chosen["id"], chosen.get("name", ""))
    console.print(f"  Active company set to: [cyan]{chosen.get('name')}[/]")


@click.command()
def switch() -> None:
    """Switch the active company (without re-logging in)."""
    require_auth()
    pick_and_save_company()
