import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from memory import Priority, TaskStatus

console = Console()
app = typer.Typer(
    help="Astra — your personal AI Chief of Staff.",
    no_args_is_help=False,
)
task_app = typer.Typer(help="Manage tasks.")
app.add_typer(task_app, name="task")


def _engine(ctx: typer.Context):
    """Retrieve the Engine instance stored on the Typer context."""
    return ctx.obj


# ── plan ──────────────────────────────────────────────────────────────────────

@app.command()
def plan(ctx: typer.Context):
    """Generate a daily plan based on your current tasks."""
    with console.status("[bold green]Planning your day..."):
        response = _engine(ctx).handle("plan my day")
    console.print(Panel(response, title="[bold cyan]Daily Plan", border_style="cyan"))


# ── reflect ───────────────────────────────────────────────────────────────────

@app.command()
def reflect(ctx: typer.Context):
    """Run an end-of-day reflection on what you completed."""
    with console.status("[bold green]Reflecting..."):
        response = _engine(ctx).handle("reflect on today")
    console.print(Panel(response, title="[bold magenta]Reflection", border_style="magenta"))


# ── note ──────────────────────────────────────────────────────────────────────

@app.command()
def note(ctx: typer.Context, content: str = typer.Argument(..., help="Note content")):
    """Save a quick note."""
    response = _engine(ctx).handle(f"note {content}")
    rprint(f"[green]✓[/green] {response}")


# ── task add ──────────────────────────────────────────────────────────────────

@task_app.command("add")
def task_add(
    ctx: typer.Context,
    title: str = typer.Argument(..., help="Task title"),
    description: str = typer.Option("", "--desc", "-d", help="Optional description"),
    priority: Priority = typer.Option(Priority.MEDIUM, "--priority", "-p", help="low | medium | high"),
    due: str = typer.Option(None, "--due", help="Due date YYYY-MM-DD"),
):
    """Add a new task."""
    task = _engine(ctx).memory.add_task(title, description, priority, due)
    rprint(f"[green]✓[/green] Task added: [bold]{task.title}[/bold] [dim](id: {task.id})[/dim]")


# ── task list ─────────────────────────────────────────────────────────────────

@task_app.command("list")
def task_list(
    ctx: typer.Context,
    status: str = typer.Option("pending", "--status", "-s", help="all | pending | done"),
):
    """List tasks."""
    memory = _engine(ctx).memory
    status_filter = None if status == "all" else (TaskStatus.DONE if status == "done" else TaskStatus.TODO)
    tasks = memory.get_tasks(status_filter)

    if not tasks:
        rprint("[dim]No tasks found.[/dim]")
        return

    table = Table(show_header=True, header_style="bold blue")
    table.add_column("ID", style="dim", width=10)
    table.add_column("Title")
    table.add_column("Priority", width=10)
    table.add_column("Status", width=14)
    table.add_column("Due", width=12)

    priority_color = {"high": "red", "medium": "yellow", "low": "green"}
    status_color = {"todo": "white", "in_progress": "cyan", "done": "green"}

    for t in tasks:
        pc = priority_color.get(t.priority, "white")
        sc = status_color.get(t.status, "white")
        table.add_row(
            t.id,
            t.title,
            f"[{pc}]{t.priority}[/{pc}]",
            f"[{sc}]{t.status}[/{sc}]",
            t.due_date or "—",
        )

    console.print(table)


# ── task done ─────────────────────────────────────────────────────────────────

@task_app.command("done")
def task_done(ctx: typer.Context, task_id: str = typer.Argument(..., help="Task ID")):
    """Mark a task as complete."""
    task = _engine(ctx).memory.complete_task(task_id)
    if task:
        rprint(f"[green]✓[/green] Completed: [bold]{task.title}[/bold]")
    else:
        rprint(f"[red]Task not found:[/red] {task_id}")
        raise typer.Exit(code=1)


# ── task remove ───────────────────────────────────────────────────────────────

@task_app.command("remove")
def task_remove(ctx: typer.Context, task_id: str = typer.Argument(..., help="Task ID")):
    """Remove a task."""
    removed = _engine(ctx).memory.remove_task(task_id)
    if removed:
        rprint(f"[green]✓[/green] Task [dim]{task_id}[/dim] removed.")
    else:
        rprint(f"[red]Task not found:[/red] {task_id}")
        raise typer.Exit(code=1)
