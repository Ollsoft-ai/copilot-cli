from pathlib import Path

import click
import httpx

from .. import api
from ..utils import console, require_auth, require_company


# ---------------------------------------------------------------------------
# Init / Update
# ---------------------------------------------------------------------------

def _download_compliance_files() -> int:
    try:
        data = api.skills_init()
    except httpx.HTTPStatusError as exc:
        console.print(f"[bold red]Error:[/] {exc.response.text}")
        raise SystemExit(1)

    for file_info in data.get("files", []):
        path = Path(file_info["path"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(file_info["content"], encoding="utf-8")
        console.print(f"  [green]OK[/] {path}")

    return len(data.get("files", []))


@click.command()
def init() -> None:
    """Download .compliance rules from the server into the current directory."""
    require_auth()
    count = _download_compliance_files()
    console.print(f"\n[bold green]Initialized {count} file(s) into .opencode/[/]")


@click.command()
def update() -> None:
    """Update .compliance rules from the server (overwrites existing files)."""
    require_auth()
    count = _download_compliance_files()
    console.print(f"\n[bold green]Updated {count} file(s) in .opencode/[/]")


# ---------------------------------------------------------------------------
# Rules list
# ---------------------------------------------------------------------------

@click.command()
def rules() -> None:
    """List active compliance rules from the server."""
    require_auth()
    company_id, company_name = require_company()

    try:
        data: list[dict] = api.rules_list(company_id)
    except httpx.HTTPStatusError as exc:
        console.print(f"[bold red]Error:[/] {exc.response.text}")
        raise SystemExit(1)

    if not data:
        console.print("No active rules found for this company.")
        return

    console.print(f"\nActive Rules - {company_name} ({len(data)})\n")

    for i, rule in enumerate(data, 1):
        name = rule.get("name", "")
        text = rule.get("text", "")
        severity = (rule.get("severity") or "MEDIUM").upper()
        flags = rule.get("flags") or []
        source_url = rule.get("source_url", "")

        console.print(f"[{i}] [bold]{name}[/]  [{severity}]")
        console.print(f"    {text}")
        if flags:
            console.print(f"    Flags: {', '.join(flags)}")
        if source_url:
            console.print(f"    Source: {source_url}")
        console.print()


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------

@click.command()
def tags() -> None:
    """List all unique tags across active compliance rules."""
    require_auth()
    company_id, _ = require_company()

    try:
        data: list[str] = api.tags_list(company_id)
    except httpx.HTTPStatusError as exc:
        console.print(f"[bold red]Error:[/] {exc.response.text}")
        raise SystemExit(1)

    if not data:
        console.print("No tags found for this company.")
        return

    console.print(f"\nTags library:\n{','.join(data)}\n")


# ---------------------------------------------------------------------------
# Keywords
# ---------------------------------------------------------------------------

@click.command()
def keywords() -> None:
    """List all unique keywords across active compliance rules."""
    require_auth()
    company_id, _ = require_company()

    try:
        data: list[str] = api.keywords_list(company_id)
    except httpx.HTTPStatusError as exc:
        console.print(f"[bold red]Error:[/] {exc.response.text}")
        raise SystemExit(1)

    if not data:
        console.print("No keywords found for this company.")
        return

    console.print(f"\nKeywords ({len(data)}):\n{', '.join(data)}\n")


# ---------------------------------------------------------------------------
# Search rules
# ---------------------------------------------------------------------------

@click.command("search-rules")
@click.argument("query", required=False, default=None)
@click.option(
    "--flags",
    "flags",
    default=None,
    metavar="a,b,c",
    help="Filter by flags/tags (comma-separated, OR logic).",
)
@click.option(
    "--severity",
    "severity",
    multiple=True,
    metavar="LEVEL",
    help="Filter by severity (repeatable: --severity HIGH --severity MEDIUM).",
)
@click.option(
    "--limit",
    default=10,
    show_default=True,
    metavar="N",
    help="Max number of results (backend cap: 100).",
)
@click.option(
    "--offset",
    default=0,
    show_default=True,
    metavar="N",
    help="Number of results to skip (for pagination).",
)
def search_rules(
    query: str | None,
    flags: str | None,
    severity: tuple[str, ...],
    limit: int,
    offset: int,
) -> None:
    """Search compliance rules by keyword or meaning.

    QUERY is an optional free-text search (semantic + BM25).
    You can omit it and use --flags / --severity for filter-only mode.

    \b
    Examples:
      compliance search-rules "verify firmware signature"
      compliance search-rules "logging user data" --flags gdpr,logging --severity HIGH
      compliance search-rules --flags auth,backend
      compliance search-rules "logging sensitive data" --flags gdpr --limit 10 --offset 10
    """
    if not query and not flags and not severity:
        raise click.UsageError("Provide a QUERY, --flags, or --severity (or a combination).")

    require_auth()
    company_id, company_name = require_company()

    tags = [t.strip() for t in flags.split(",") if t.strip()] if flags else None
    severity_list = [s.upper() for s in severity] if severity else None

    try:
        items: list[dict] = api.rules_search(
            company_id=company_id,
            query=query,
            tags=tags,
            severity=severity_list,
            limit=min(limit, 100),
            offset=offset,
        )
    except httpx.HTTPStatusError as exc:
        click.echo(f"Error: {exc.response.text}", err=True)
        raise SystemExit(1)

    if not items:
        parts = []
        if query:
            parts.append(f'"{query}"')
        if tags:
            parts.append(f"flags={','.join(tags)}")
        if severity_list:
            parts.append(f"severity={','.join(severity_list)}")
        msg = f"No rules found for {' '.join(parts)}."
        if offset:
            msg += f" (offset {offset} - try a lower value)"
        click.echo(msg)
        return

    summary_parts = []
    if query:
        summary_parts.append(f'"{query}"')
    if tags:
        summary_parts.append(f"flags: {', '.join(tags)}")
    if severity_list:
        summary_parts.append(f"severity: {', '.join(severity_list)}")

    page_from = offset + 1
    page_to = offset + len(items)
    page_info = f"#{page_from}-{page_to}" if offset else f"{len(items)} result{'s' if len(items) != 1 else ''}"
    click.echo(f"\nSearch: {' | '.join(summary_parts)}  ({page_info})\n")

    for i, rule in enumerate(items, page_from):
        name = rule.get("name", "")
        text = rule.get("text", "")
        severity_val = (rule.get("severity") or "NONE").upper()
        rule_flags = rule.get("flags") or []
        source_url = rule.get("source_url", "")

        click.echo(f"[{i}] {name}  [{severity_val}]")
        click.echo(f"    {text}")
        if rule_flags:
            click.echo(f"    Flags: {', '.join(rule_flags)}")
        if source_url:
            click.echo(f"    Source: {source_url}")
        click.echo()

    if len(items) == limit:
        next_offset = offset + limit
        hint_parts = [f'"{query}"'] if query else []
        if flags:
            hint_parts.append(f"--flags {flags}")
        if severity_list:
            hint_parts += [f"--severity {s}" for s in severity_list]
        hint_parts += [f"--limit {limit}", f"--offset {next_offset}"]
        click.echo(f"  -> next page: compliance search-rules {' '.join(hint_parts)}")
