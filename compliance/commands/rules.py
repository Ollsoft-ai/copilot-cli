from pathlib import Path

import click
import httpx
import questionary

from .. import api
from ..utils import console, require_auth, require_company

_PICKER_STYLE = questionary.Style([
    ("selected",    "fg:#E20074 bold"),
    ("pointer",     "fg:#E20074 bold"),
    ("highlighted", "fg:#E20074"),
    ("question",    "bold"),
    ("answer",      "fg:#E20074 bold"),
])


# ---------------------------------------------------------------------------
# Init / Update
# ---------------------------------------------------------------------------

def _pick_skill_type() -> str:
    try:
        skills = api.skills_list()
    except httpx.HTTPStatusError as exc:
        console.print(f"[bold yellow]Warning:[/] Could not fetch skill types: {exc.response.text}")
        return "opencode"

    if len(skills) == 1:
        return skills[0]

    chosen = questionary.select(
        "Select agent type:",
        choices=skills,
        style=_PICKER_STYLE,
    ).ask()

    if chosen is None:
        console.print("[yellow]Selection cancelled.[/]")
        raise SystemExit(0)

    return chosen


def _download_compliance_files(skill_type: str) -> int:
    try:
        data = api.skills_init(skill_type)
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
    """Download compliance rules from the server into the current directory."""
    require_auth()
    skill_type = _pick_skill_type()
    count = _download_compliance_files(skill_type)
    console.print(f"\n[bold green]Initialized {count} file(s) into .{skill_type}/[/]")


@click.command()
def update() -> None:
    """Update compliance rules from the server (overwrites existing files)."""
    require_auth()
    skill_type = _pick_skill_type()
    count = _download_compliance_files(skill_type)
    console.print(f"\n[bold green]Updated {count} file(s) in .{skill_type}/[/]")


# ---------------------------------------------------------------------------
# Rules list
# ---------------------------------------------------------------------------

@click.command()
@click.option(
    "--limit",
    default=100,
    show_default=True,
    type=click.IntRange(1, 500),
    metavar="N",
    help="Maximum number of rules to return (backend cap: 500).",
)
@click.option(
    "--offset",
    default=0,
    show_default=True,
    type=click.IntRange(0),
    metavar="N",
    help="Number of rules to skip for pagination.",
)
def rules(limit: int, offset: int) -> None:
    """List all workspace rules from the server.

    \b
    Examples:
      compliance rules
      compliance rules --limit 100 --offset 0
      compliance rules --limit 100 --offset 100
    """
    require_auth()
    company_id, company_name = require_company()

    try:
        data: list[dict] = api.rules_list(company_id, limit=limit, offset=offset)
    except httpx.HTTPStatusError as exc:
        console.print(f"[bold red]Error:[/] {exc.response.text}")
        raise SystemExit(1)

    if not data:
        console.print("No rules found for this company.")
        return

    page_from = offset + 1
    page_to = offset + len(data)
    console.print(f"\nRules - {company_name} (#{page_from}-{page_to})\n")

    for i, rule in enumerate(data, page_from):
        name = rule.get("name", "")
        text = rule.get("text", "")
        severity = (rule.get("severity") or "MEDIUM").upper()
        flags = rule.get("flags") or rule.get("tags") or []
        source_url = rule.get("source_url", "")

        console.print(f"[{i}] [bold]{name}[/]  [{severity}]")
        console.print(f"    {text}")
        if flags:
            console.print(f"    Flags: {', '.join(flags)}")
        if source_url:
            console.print(f"    Source: {source_url}")
        console.print()

    if len(data) == limit:
        console.print(f"  -> next page: compliance rules --limit {limit} --offset {offset + limit}")


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------

@click.command()
def tags() -> None:
    """List all unique tags across active compliance rules, with rule counts."""
    require_auth()
    company_id, _ = require_company()

    try:
        data: dict[str, int] = api.tags_list(company_id)
    except httpx.HTTPStatusError as exc:
        console.print(f"[bold red]Error:[/] {exc.response.text}")
        raise SystemExit(1)

    if not data:
        console.print("No tags found for this company.")
        return

    formatted = ", ".join(f"{tag}({count})" for tag, count in data.items())
    console.print(f"\nTags library ({len(data)}):\n{formatted}\n")


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
    help="Max number of results (backend cap: 500).",
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
    You can omit it and use --flags / --severity for filter-only mode,
    or omit everything and just page through all rules with --limit/--offset.

    \b
    Examples:
      compliance search-rules "verify firmware signature"
      compliance search-rules "logging user data" --flags gdpr,logging --severity HIGH
      compliance search-rules --flags auth,backend
      compliance search-rules "logging sensitive data" --flags gdpr --limit 10 --offset 10
      compliance search-rules --limit 50 --offset 100
    """
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
            limit=min(limit, 500),
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
        rule_flags = rule.get("tags") or []
       # filename = rule.get("document_filename")
        source_url = rule.get("source_url", "")

        click.echo(f"[{i}] {name}  [{severity_val}]")
        click.echo(f"    {text}")
       # if filename:
       #     click.echo(f"    File: {filename}")
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
