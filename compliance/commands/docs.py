from pathlib import Path

import click
import httpx

from .. import api
from ..utils import require_auth, require_company


@click.command("get-docs")
@click.option(
    "--id", "doc_ids",
    multiple=True,
    type=int,
    metavar="ID",
    help="Document ID(s) to fetch (repeatable: --id 1 --id 2).",
)
@click.option(
    "--all", "fetch_all",
    is_flag=True,
    default=False,
    help="Download all documents.",
)
@click.option(
    "-o", "--output",
    default=".",
    show_default=True,
    metavar="DIR",
    help="Directory where the .md files will be saved.",
)
def get_docs(doc_ids: tuple[int, ...], fetch_all: bool, output: str) -> None:
    """Download document(s) as Markdown files.

    \b
    Examples:
      compliance get-docs --id 1
      compliance get-docs --id 1 --id 2 -o ./docs
      compliance get-docs --all -o ./rule_docs
    """
    if not doc_ids and not fetch_all:
        raise click.UsageError("Provide --id ID or --all.")

    require_auth()
    company_id, _ = require_company()

    if fetch_all:
        try:
            docs = api.list_documents(company_id)
        except httpx.HTTPStatusError as exc:
            raise click.ClickException(exc.response.text)
        ids = [d["id"] for d in docs]
    else:
        ids = list(doc_ids)

    out_dir = Path(output)
    out_dir.mkdir(parents=True, exist_ok=True)

    for doc_id in ids:
        try:
            data = api.document_markdown(company_id, doc_id)
        except httpx.HTTPStatusError as exc:
            raise click.ClickException(f"[{doc_id}] {exc.response.text}")

        dest = out_dir / f"{doc_id}.md"
        dest.write_text(data.get("markdown") or "", encoding="utf-8")
