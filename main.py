import typer
from core.engine import Engine
from interface.cli.commands import app
from interface.cli.app import run_interactive

# Shared engine instance
_engine = Engine()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Astra — Personal AI Chief of Staff."""
    ctx.ensure_object(dict)
    ctx.obj = _engine

    # No subcommand given → drop into interactive REPL
    if ctx.invoked_subcommand is None:
        run_interactive(_engine)


if __name__ == "__main__":
    app()
