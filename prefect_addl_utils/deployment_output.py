from __future__ import annotations

from collections import OrderedDict, namedtuple
from typing import Literal

from cron_descriptor import get_description
from prefect.client.schemas.responses import DeploymentResponse
from prefect.client.schemas.schedules import CronSchedule, IntervalSchedule, RRuleSchedule
from pydantic.v1 import BaseModel
from rich.console import Console
from rich.panel import Panel
from rich.pretty import Pretty
from rich.rule import Rule
from rich.table import Table, box
from rich.tree import Tree

console = Console()

SCHEDULE_ACTIVE = "[dark_green]Active[/dark_green]"
SCHEDULE_INACIVE = "[dark_red]Inactive[/dark_red]"
SCHEDULE_ARROW = "[bold bright_cyan]->[/bold bright_cyan]"
OPEN_PARENTHESIS = "[bold bright_cyan]([/bold bright_cyan]"
CLOSE_PARENTHESIS = "[bold bright_cyan])[/bold bright_cyan]"


class Entrypoint(BaseModel):
    @staticmethod
    def build(new: DeploymentResponse, old: DeploymentResponse = None) -> str:
        new = new.entrypoint
        old = None if old is None else old.entrypoint

        if old == new or old in (None, ""):
            return f"[bold orange4]`{new}`[/bold orange4]"
        else:
            return f"[green]`{new}`[/green] [red][strike]`{old}`[/strike][/red]"


class TagsRow(BaseModel):
    @staticmethod
    def build(new: DeploymentResponse, old: DeploymentResponse = None) -> list:
        new_tags = new.tags
        old_tags = None if old is None else old.tags

        if not old_tags:
            old_tags = []

        added = set(new_tags).difference(set(old_tags))
        removed = set(old_tags).difference(set(new_tags))
        if old_tags:
            unchanged = set(new_tags).intersection(set(old_tags))

        tags_l = []
        if old_tags:
            tags_l += [f"{OPEN_PARENTHESIS}{x}{CLOSE_PARENTHESIS}" for x in unchanged]
        tags_l += [f"[green]{OPEN_PARENTHESIS}{x}{CLOSE_PARENTHESIS}[/green]" for x in added]
        tags_l += [f"[red][strike]{OPEN_PARENTHESIS}{x}{CLOSE_PARENTHESIS}[/strike][/red]" for x in removed]
        return sorted(tags_l)


class ScheduleRows(BaseModel):
    active: bool
    schedule: CronSchedule | IntervalSchedule | RRuleSchedule
    mode: Literal["added", "removed", None] = None

    @staticmethod
    def build(new: DeploymentResponse, old: DeploymentResponse = None):
        new_schedules = new.schedules
        old_schedules = None if old is None else old.schedules

        ScheduleTuple = namedtuple('ScheduleTuple', 'active schedule')

        old_schedules = [] if old_schedules is None else [ScheduleTuple(x.active, x.schedule) for x in old_schedules]
        new_schedules = [ScheduleTuple(x.active, x.schedule) for x in new_schedules]

        added_l, removed_l, unchanged_l = [], [], []
        for s in new_schedules:
            if s not in old_schedules:
                added_l.append(s)
            elif s not in unchanged_l:
                unchanged_l.append(s)
        for s in old_schedules:
            if s not in new_schedules:
                removed_l.append(s)
            elif s not in unchanged_l:
                unchanged_l.append(s)
        
        schedules_l = []
        schedules_l += [ScheduleRows(active=x.active, schedule=x.schedule, mode="added").__resolve() for x in added_l]
        schedules_l += [ScheduleRows(active=x.active, schedule=x.schedule, mode="removed").__resolve() for x in removed_l]
        schedules_l += [ScheduleRows(active=x.active, schedule=x.schedule, mode=None).__resolve() for x in unchanged_l]
        return schedules_l

    def __resolve(self):
        schedule_string = f"{SCHEDULE_ACTIVE if self.active else SCHEDULE_INACIVE} {SCHEDULE_ARROW} [:schedule_color]{self.schedule}[/:schedule_color]"
        if isinstance(self.schedule, CronSchedule):
            schedule_string = f"{schedule_string} ([gray50]{get_description(self.schedule.cron)}[/gray50])"
        if self.mode == "added":
            return schedule_string.replace(":schedule_color", "green")
        elif self.mode == "removed":
            return f"[strike]{schedule_string.replace(':schedule_color', 'red')}[/strike]"
        else:
            return schedule_string.replace("[:schedule_color]", "").replace("[/:schedule_color]", "")


class ParameterRows(BaseModel):
    @staticmethod
    def build(new: DeploymentResponse, old: DeploymentResponse = None):
        new = new.parameters
        old = None if old is None else old.parameters

        old = OrderedDict() if old is None else OrderedDict(sorted(old.items()))
        new = OrderedDict(sorted(new.items()))

        added_l = ParameterRows.__get_added(new, old)
        removed_l = ParameterRows.__get_removed(new, old)        
        changed, common_l = ParameterRows.__get_common(new, old)
        
        param_changed = ParameterRows.__determine_changed(added_l, removed_l, changed)
        parameters_l = added_l + removed_l + common_l

        return ParameterRows.__build_table(parameters_l, param_changed)

    def __get_added(new: dict, old: dict = None) -> list:
        added_params = sorted(set(new.keys()).difference(old.keys()))
        return [[f"{x} :star:", f"[green]{new[x]}[/green]", None] for x in added_params]
    
    def __get_removed(new: dict, old: dict = None) -> list:
        removed_params = sorted(set(old.keys()).difference(new.keys()))
        return [[f"{x} :star:", f"[red]{old[x]}[/red]"] for x in removed_params]
    
    def __get_common(new: dict, old: dict = None) -> tuple[bool, list]:
        parameters_l = []
        param_changed = False
        common_params = sorted(set(new.keys()).intersection(old.keys()))
        for param_name in common_params:
            changed = new[param_name] != old[param_name]
            if isinstance(new[param_name], dict) or isinstance(new[param_name], list):
                if changed:
                    param_changed = True
                    name = f"{param_name} :star:"
                    value = Panel(Pretty(new[param_name]), style="medium_spring_green")
                    old_value = Panel(Pretty(old[param_name]), style="red")
                else:
                    name = param_name
                    value = Pretty(new[param_name])
                    old_value = None
            else:
                if changed:
                    param_changed = True
                    name = f"{param_name} :star:"
                    value = f"[green]{new[param_name]}[/green]"
                    old_value = f"[red]{old[param_name]}[/red]"
                else:
                    name = param_name
                    value = f"[grey50]{new[param_name]}[/grey50]"
                    old_value = None
            parameters_l.append([name, value, old_value])
        return param_changed, parameters_l
    
    def __determine_changed(added: list, removed: list, common_changed: bool) -> bool:
        if added or removed or common_changed:
            return True
        
    def __build_table(parameters: list, old_value_col: bool) -> Table:
        parameters_table = Table(
            show_header=True,
            title_justify="left",
            title_style="bold blue",
            box=box.ROUNDED,
            show_lines=True,
        )

        parameters_table.add_column("[bold blue]Parameters", style="bold magenta")
        parameters_table.add_column("Value")
        if old_value_col is True:
            parameters_table.add_column("Old Value")

        for p in parameters:
            p = [x for x in p if x is not None]
            parameters_table.add_row(*p)
        return parameters_table


class Container(BaseModel):
    name: str
    target: int

    def __repr__(self):
        return f"Container(name={self.name}, target={self.target})"

    def __str__(self):
        return f"Container(name={self.name}, target={self.target})"


def show_deployment_results(name: str, new: DeploymentResponse, old: DeploymentResponse = None):
    console.print(Rule())
    tree = Tree(f":rocket: [bold bright_cyan]{name}")

    if new is None:
        return None

    entrypoint = Entrypoint.build(new, old or None)
    tree.add(f"[bold blue]entrypoint:[/bold blue] {entrypoint}")

    tags = TagsRow.build(new, old or None)
    tree.add(f"[bold blue]tags:[/bold blue] {" ".join(tags)}")

    schedules_l = ScheduleRows.build(new, old or None)
    schedule_tree = tree.add("[bold blue]schedules:")
    for s in schedules_l:
        schedule_tree.add(s)

    parameters_table = ParameterRows.build(new, old or None)
    tree.add(parameters_table)

    console.print(tree)

    return True





# ##############################################################################
# # DEPLOYMENTS
# ##############################################################################
# tree = Tree("[bold grey46]Deployments")

# ##############################################################################
# # DEPLOYMENT
# ##############################################################################
# subtree = tree.add(":rocket: [bold bright_cyan]flow/deployment1")

# ##############################################################################
# # ENTRYPOINT
# ##############################################################################
# old_entrypoint = "flows/deployment-name1/src/flow.py:main"
# new_entrypoint = "flows/deployment-name1/src/flow.py:main"

# entrypoint = Entrypoint.build(new_entrypoint, old_entrypoint)
# subtree.add(f"[bold blue]entrypoint:[/bold blue] {entrypoint}")

# ##############################################################################
# # TAGS
# ##############################################################################
# old_tags = ["priority-low", "infra-maintenance", "test-deployment"]
# new_tags = ["priority-low", "infra-maintenance", "prod-deployment"]

# tags = TagsRow.build(new_tags, old_tags)
# subtree.add(f"[bold blue]tags:[/bold blue] {" ".join(tags)}")

# ##############################################################################
# # SCHEDULES
# ##############################################################################
# schedules_new = [
#     CronSchedule(cron='0 9,17,20 * * *', timezone='America/Chicago', day_or=True),
#     CronSchedule(cron='0 9,18,20 * * *', timezone='America/Chicago', day_or=True),
# ]
# schedules_old = [
#     CronSchedule(cron='0 9,17,20 * * *', timezone='America/Chicago', day_or=True),
#     CronSchedule(cron='0 9,16,20 * * *', timezone='America/Chicago', day_or=True),
#     IntervalSchedule(interval=600)
# ]

# schedules_l = ScheduleRows.build(schedules_new, schedules_old)
# schedule_tree = subtree.add("[bold blue]schedules:")
# for s in schedules_l:
#     schedule_tree.add(s)

# ##############################################################################
# # PARAMETERS
# ##############################################################################
# old = {
#     "dsn": "PPRD",
#     "test_mod": True,
#     "dict1": [
#         {"key1": "stringsstringsstrings", "key2": "filename1.csv"},
#         {"key1": "stringsstringsstrings", "key2": "filename1.csv"}
#     ],
#     "files": Container(name="one", target=10)
# }
# new = {
#     "dsn": "PROD",
#     "test_mod": True,
#     "dict1": [
#         {"key1": "stringsstringsstrings", "key2": "filename1.csv"},
#         {"key1": "stringsstringsstrings", "key2": "filename1.csv"}
#     ],
#     "files": Container(name="one", target=10)
# }
# parameters_table = ParameterRows.build(new, old)
# subtree.add(parameters_table)

# ##############################################################################
# # PRINT RESULTS
# ##############################################################################
# console.print(tree)
