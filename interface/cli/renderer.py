"""
CLI Renderer — converts structured response dicts into terminal output.

The engine always returns a dict with {type, message, data}.
This module maps each type to appropriate Rich formatting.
"""
from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

console = Console()


def render(response) -> None:
    """
    Render an engine response to the terminal.

    Accepts ChatResponse (Pydantic), dict, or plain str (legacy fallback).
    """
    if isinstance(response, str):
        rprint(response)
        return

    # Normalise Pydantic model → dict so the rest of the function is uniform
    if hasattr(response, "model_dump"):
        response = response.model_dump()

    rtype   = response.get("type", "chat")
    message = response.get("message", "")
    data    = response.get("data", {})

    actions = response.get("actions", [])

    if rtype == "task_list":
        _render_task_list(message, data.get("tasks", []))

    elif rtype == "action_result":
        # Covers task_created, task_updated, complete, remove
        tasks = data.get("tasks", [])
        if tasks:
            rprint(f"[green]✓[/green] {message}")
            task = tasks[0]
            rprint(f"  [dim]id: {task.get('id')}  priority: {task.get('priority')}[/dim]")
        else:
            rprint(f"[cyan]↻[/cyan] {message}")

    elif rtype == "confirmation":
        rprint(f"[yellow]?[/yellow] {message}")
        rprint("[dim]  Reply yes / yeah / sure to confirm, or anything else to cancel.[/dim]")

    elif rtype == "awaiting_input":
        rprint(f"[yellow]→[/yellow] {message}")

    elif rtype == "error":
        rprint(f"[red]✗[/red] {message}")

    else:
        # chat, plan, reflect, generic
        rprint(message)

    # Surface non-confirmation actions as dim hints in the terminal
    follow_ups = [a for a in actions if a.get("type") not in ("cancel",) and rtype != "confirmation"]
    if follow_ups:
        labels = " | ".join(a.get("label", "") for a in follow_ups)
        rprint(f"[dim]  → {labels}[/dim]")


def _render_task_list(header: str, tasks: list[dict]) -> None:
    if not tasks:
        rprint("[dim]No tasks found.[/dim]")
        return

    table = Table(show_header=True, header_style="bold blue", box=None)
    table.add_column("ID",       style="dim",    width=10)
    table.add_column("Title",                    min_width=20)
    table.add_column("Priority", width=10)
    table.add_column("Status",   width=14)
    table.add_column("Due",      width=12)

    priority_color = {"high": "red", "medium": "yellow", "low": "green"}
    status_color   = {"todo": "white", "in_progress": "cyan", "done": "green"}

    for t in tasks:
        pc = priority_color.get(t.get("priority", ""), "white")
        sc = status_color.get(t.get("status", ""), "white")
        table.add_row(
            t.get("id", ""),
            t.get("title", ""),
            f"[{pc}]{t.get('priority', '')}[/{pc}]",
            f"[{sc}]{t.get('status', '')}[/{sc}]",
            t.get("due_date") or "—",
        )

    console.print(f"\n{header}")
    console.print(table)
