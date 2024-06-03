from __future__ import annotations

from rich.console import Console
from rich.table import Table, box
from rich.tree import Tree

console = Console()
tree = Tree("[bold grey46]Deployments")

subtree = tree.add(":rocket: [bold bright_cyan]flow/deployment1")
subtree.add("[bold blue]Entrypoint:[/bold blue] [orange4]flows/deployment-name1/src/flow.py:main[/orange4]")

open_bracket = "[bold bright_cyan]([/bold bright_cyan]"
close_bracket = "[bold bright_cyan])[/bold bright_cyan]"
subtree.add(
    f"[bold blue]Tags:[/bold blue] {open_bracket}priority-low{close_bracket} {open_bracket}infra-maintenance{close_bracket} [green]{open_bracket}prod-deployment{close_bracket}[/green] [red][strike]{open_bracket}test-deployment{close_bracket}[/strike][/red]"
)

schedule_tree = subtree.add("[bold blue]Schedules:")
schedule_tree.add("[dark_green]Active[/dark_green] | cron='0 9,17,20 * * *' timezone='America/Chicago' day_or=True")

parameters_table = Table(
    show_header=True,
    title="Parameters:",
    # show_edge=False,
    title_justify="left",
    title_style="bold blue",
    box=box.DOUBLE_EDGE,
    show_lines=True,
    padding=(0, 1),
)

from rich.pretty import Pretty

parameters_table.add_column("[bold blue]Parameters", style="bold magenta")
parameters_table.add_column("Value")
parameters_table.add_row("dsn", "[grey50]FIRST")
parameters_table.add_row("test_mode", "[green]True[/green] [red][strike]False[/strike][/red]")
parameters_table.add_row(
    "dict",
    Pretty(
        [
            {"key1": 1, "key2": 2},
            {"key1": 1, "key2": 2},
            {"key1": 1, "key2": 2},
            {"key1": 1, "key2": 2},
        ],
        max_length=50,
        max_depth=50,
        max_string=50,
    ),
)
subtree.add(parameters_table)

console.print(tree)
