from pathlib import Path

import click
import httpx

from .. import api
from ..utils import console, require_auth, require_company

_OUTPUT_DIR = Path("rule_docs")


@click.command("get-rules")
@click.option(
    "--doc", "doc_ids",
    multiple=True,
    type=int,
    required=True,
    metavar="ID",
    help="Document ID(s) to fetch rules for (repeatable: --doc 14 --doc 57).",
)
def get_rules(doc_ids: tuple[int, ...]) -> None:
    """Download active rules for the given document IDs as a single Markdown file.

    \b
    The file is saved to rule_docs/rules_<sorted_ids>.md automatically.

    \b
    Examples:
      compliance get-rules --doc 14 --doc 57
      compliance get-rules --doc 6
    """
    require_auth()
    company_id, _ = require_company()

    sorted_ids = sorted(doc_ids)
    filename = "rules_" + "_".join(str(i) for i in sorted_ids) + ".md"
    out_path = _OUTPUT_DIR / filename

    try:
        markdown = api.rules_markdown(company_id, sorted_ids)
    except httpx.HTTPStatusError as exc:
        raise click.ClickException(exc.response.text)

    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown, encoding="utf-8")
    console.print(f"[bold green]OK[/] Saved rules to [cyan]{out_path}[/]")
