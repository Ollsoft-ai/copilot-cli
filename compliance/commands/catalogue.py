import json
from pathlib import Path

import click
import httpx

from .. import api
from ..utils import console, require_auth, require_company

_DEFAULT_OUTPUT = Path("catalogue.json")


@click.command("get-catalogue")
@click.option(
    "--output", "-o",
    default=str(_DEFAULT_OUTPUT),
    show_default=True,
    help="Path to the output JSON file.",
)
def get_catalogue(output: str) -> None:
    """Fetch all documents (id, filename, preface) and save them to a JSON file."""
    require_auth()
    company_id, _ = require_company()

    try:
        docs: list[dict] = api.catalogue_list(company_id)
    except httpx.HTTPStatusError as exc:
        console.print(f"[bold red]Error:[/] {exc.response.text}")
        raise SystemExit(1)

    out_path = Path(output)
    out_path.write_text(json.dumps(docs, ensure_ascii=False, indent=2), encoding="utf-8")
    console.print(f"[bold green]OK[/] Saved {len(docs)} document(s) to [cyan]{out_path}[/]")
