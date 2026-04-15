import typer
from rich import print as rprint
from rich.console import Console

from interface.cli.commands import app

console = Console()


def run_interactive(engine) -> None:
    """REPL mode: read input, handle it, print response."""
    rprint("[bold cyan]Astra[/bold cyan] — type a command or question. [dim]Ctrl+C to exit.[/dim]\n")
    while True:
        try:
            user_input = console.input("[bold]>[/bold] ").strip()
        except (KeyboardInterrupt, EOFError):
            rprint("\n[dim]Goodbye.[/dim]")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "bye"):
            rprint("[dim]Goodbye.[/dim]")
            break

        with console.status("[dim]Thinking...[/dim]"):
            response = engine.handle(user_input)
        rprint(response)
        rprint()
