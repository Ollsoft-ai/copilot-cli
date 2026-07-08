import json
import sys

import click
import httpx

from .. import api
from ..config import load_company
from ..utils import console, require_auth


@click.command("report-event")
@click.argument("payload", required=False)
@click.option("--file", "file_path", type=click.Path(exists=True), help="Read the JSON event from a file.")
def report_event(payload: str | None, file_path: str | None) -> None:
    """Report a compliance event (JSON). Accepts inline arg, --file path, or stdin.

    Examples:\n
      compliance report-event --file event.json\n
      echo '{\"rule\":\"...\"}' | compliance report-event
    """
    require_auth()

    if file_path:
        raw_bytes = open(file_path, "rb").read()
        if raw_bytes[:2] in (b"\xff\xfe", b"\xfe\xff"):
            raw = raw_bytes.decode("utf-16")
        else:
            raw = raw_bytes.decode("utf-8-sig")
    elif payload:
        raw = payload
    else:
        raw = sys.stdin.read()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid JSON:[/] {exc}")
        raise SystemExit(1)

    company = load_company()
    if company:
        data.setdefault("company_id", company[0])

    try:
        api.report_event(data)
        console.print("[bold green]OK[/] Event reported.")
    except httpx.HTTPStatusError as exc:
        console.print(f"[bold red]Error:[/] {exc.response.text}")
        raise SystemExit(1)

