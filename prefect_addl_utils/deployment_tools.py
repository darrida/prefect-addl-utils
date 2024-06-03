from __future__ import annotations

from pathlib import Path

import click
from prefect import Flow, deploy, get_client
from prefect.blocks.system import Secret
from prefect.client.schemas.responses import DeploymentResponse
from prefect.client.schemas.schedules import CronSchedule, IntervalSchedule, RRuleSchedule
from prefect.exceptions import ObjectNotFound
from prefect.runner.storage import GitRepository
from prefect.variables import Variable
from pydantic.v1 import BaseModel
from rich.console import Console

from . import deployment_rich as rich_deploy

console = Console()


def build_entrypoint_str(deploy__file__: str, *, flow_module: str = "flow.py", flow_func: str = "main") -> str:
    this__file__ = __file__
    repo_root_dir = Path(this__file__).parent.parent
    relative_from_repo_root = Path(deploy__file__).parent.relative_to(repo_root_dir) / flow_module
    return f"{relative_from_repo_root.as_posix()}:{flow_func}"


class DeploymentConfig(BaseModel):
    name: str = None
    version: str
    work_queue_name: str
    job_variables: dict | None = None
    parameters: dict | None = None
    description: str | None = None
    schedule: CronSchedule | IntervalSchedule | RRuleSchedule | None = None
    tags: list | None = None


git_storage = GitRepository(
    name=Variable.get("gitlab_flows_repo_name").value,
    url=Variable.get("gitlab_flows_storage").value,
    branch=Variable.get("gitlab_flows_branch").value,
    credentials={
        "access_token": Secret.load("gitlab-flows-token"),
    },
)


async def deploy_process(
    flow: Flow,
    source: GitRepository,
    entrypoint: str,
    deployments: list[DeploymentConfig] | DeploymentConfig,
    work_pool_name: str,
):
    if not isinstance(deployments, list):
        deployments = [deployments]
    flow_ready = await flow.from_source(source=source, entrypoint=entrypoint)

    update_parameters = input("Overwrite cloud options: parameters with local parameters? (yes/no | default: no): ")
    update_schedules = input("Overwrite cloud schedule with local schedule? (yes/no | default: no): ")
    update_tags = input("Overwrite cloud tags with local tags? (yes/no | default: no): ")

    if update_parameters == "yes":
        click.echo(click.style("Parameters: Prepping to CHANGE"), fb="yellow")
    if update_schedules == "yes":
        click.echo(click.style("Schedules: Prepping to CHANGE"), fb="yellow")
    if update_tags == "yes":
        click.echo(click.style("Tags: Prepping to CHANGE"), fb="yellow")

    with console.status("[bold green]Prepping deployment(s)...") as status:
        prepped_deployments_l = []
        for count, deployment in enumerate(deployments, start=1):
            deployment_name = f"{flow.name}/{deployment.name}"
            current_deployment = await __read_deployment(deployment_name)
            if update_parameters != "yes":
                deployment.parameters = current_deployment.parameters
            if update_schedules != "yes":
                deployment.schedule = current_deployment.schedule
            if update_tags != "yes":
                deployment.tags = current_deployment.tags
            deployment_ready = await flow_ready.to_deployment(**deployment.dict())
            prepped_deployments_l.append(deployment_ready)

    await deploy(*prepped_deployments_l, work_pool_name=work_pool_name, ignore_warnings=True)

    with console.status("[bold green]Generating results...") as status:
        for count, deployment in enumerate(deployments, start=1):
            name = f"{flow.name}/{deployment.name}"
            updated_deployment = await __read_deployment(name)
            rich_deploy.show_deployment_results(name, updated_deployment, current_deployment)



            # deploy_results = __DeploymentResults(previous=current_deployment, updated=updated_deployment)
            # deploy_results.show(count, name)

    # table = Table(show_header=True, header_style="bold magenta", box=box.HEAVY_HEAD)
    # table.add_column("Config", style="green", width=12)
    # table.add_column("Values")
    # table.add_column("Previous Values", style="yellow")
    # table.add_row("Parameters", "{'dsn': 'PROD'}", "{'dsn': 'PPRD'}")
    # table.add_row("Schedules", "cron='0 9,17,20 * * *' timezone='America/Chicago' day_or=True")
    # table.add_row("Tags", '["priority-low", "prod-deployment", "entsys-maintenance"]')
    # table.add_row("Entrypoint", "flows/idm-employee-start/src/flow.py:main")
    # console.print(table)


async def __read_deployment(name: str) -> DeploymentResponse:
    try:
        async with get_client() as client:
            deployment_obj = await client.read_deployment_by_name(name)
            return deployment_obj
    except ObjectNotFound:
        return None


# class __DeploymentResults(BaseModel):
#     previous: DeploymentResponse
#     updated: DeploymentResponse

#     def show(self, count: int, name: str):
#         click.echo(click.style("----------------------------------------------------", fg="blue"))
#         click.echo(f'{click.style(f"DEPLOYMENT {count} RESULTS", fg="blue")}: {name}')
#         click.echo(click.style("----------------------------------------------------", fg="blue"))
#         self.__print_parameters()
#         self.__print_schedules()
#         self.__print_tags()
#         self.__print_entrypoint()

#     def __print_parameters(self):
#         parameter_changes = set(self.previous.parameters.items()) - set(self.updated.parameters.items())
#         if parameter_changes:
#             click.echo(f'{click.style("- Parameters CHANGED:", fg="yellow")} {dict(parameter_changes)}')
#             print(f"  - All Before: {self.previous.parameters}")
#             print(f"  - All After: {self.updated.parameters}")
#         else:
#             click.echo(f"{click.style('- Parameters:', fg='green')} {self.updated.parameters}")

#     def __print_schedules(self):
#         if str(self.previous.schedule) != str(self.updated.schedule):
#             click.echo(click.style("- Schedule CHANGED:", fg="yellow"))
#             print(f"  - Before: {self.previous.schedule}")
#             print(f"  - After: {self.updated.schedule}")
#         else:
#             click.echo(f"{click.style('- Schedule:', fg='green')} {self.updated.schedule}")

#     def __print_tags(self):
#         if set(self.previous.tags).difference(set(self.updated.tags)):
#             click.echo(click.style("- Tags CHANGED:", fg="yellow"))
#             print(f"  - Before: {self.previous.tags}")
#             print(f"  - After: {self.updated.tags}")
#         else:
#             click.echo(f"{click.style('- Tags:', fg='green')} {self.updated.tags}")

#     def __print_entrypoint(self):
#         if self.previous.entrypoint != self.updated.entrypoint:
#             click.echo(click.style("- Entrypoint CHANGED:", fg="yellow"))
#             print(f"  - Before: {self.previous.entrypoint}")
#             print(f"  - After: {self.updated.entrypoint}")
#         else:
#             click.echo(f"{click.style('- Entrypoint:', fg='green')} {click.style(self.updated.entrypoint, fg="blue")}")
