from __future__ import annotations

from pathlib import Path

import click
from prefect import Flow, deploy, get_client
from prefect.client.schemas.objects import DeploymentSchedule, MinimalDeploymentSchedule
from prefect.client.schemas.responses import DeploymentResponse
from prefect.client.schemas.schedules import CronSchedule, IntervalSchedule, RRuleSchedule
from prefect.exceptions import ObjectNotFound
from prefect.runner.storage import GitRepository
from pydantic.v1 import BaseModel, validator
from rich.console import Console

from . import deployment_rich as rich_deploy

console = Console()


def schedule(schedule: CronSchedule | IntervalSchedule | RRuleSchedule, active: bool, **kwargs):
    return DeploymentSchedule(schedule=schedule, active=active, **kwargs)


def build_entrypoint_str(deploy__file__: str, *, flow_module: str = "flow.py", flow_func: str = "main") -> str:
    this__file__ = __file__
    repo_root_dir = Path(this__file__).parent.parent
    relative_from_repo_root = Path(deploy__file__).parent.relative_to(repo_root_dir) / flow_module
    return f"{relative_from_repo_root.as_posix()}:{flow_func}"


class DeploymentConfig(BaseModel):
    name: str = None
    version: str
    work_queue_name: str = "default"
    job_variables: dict | None = None
    parameters: dict | None = None
    description: str | None = None
    schedules: list[DeploymentSchedule] | DeploymentResponse | CronSchedule | IntervalSchedule | RRuleSchedule | None = None
    tags: list | None = None

    @validator("schedules")
    def schedule_list_check(cls, v):
        if isinstance(v, CronSchedule) or isinstance(v, IntervalSchedule) or isinstance(v, RRuleSchedule):
            return [DeploymentResponse(schedule=v)]
        if isinstance(v, DeploymentResponse):
            return [v]
        return v


# git_storage = GitRepository(
#     name=Variable.get("gitlab_flows_repo_name").value,
#     url=Variable.get("gitlab_flows_storage").value,
#     branch=Variable.get("gitlab_flows_branch").value,
#     credentials={"access_token": Secret.load("gitlab-flows-token")},
# )


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
        click.echo(click.style("Parameters: Prepping to CHANGE", fg="yellow"))
    if update_schedules == "yes":
        click.echo(click.style("Schedules: Prepping to CHANGE", fg="yellow"))
    if update_tags == "yes":
        click.echo(click.style("Tags: Prepping to CHANGE", fg="yellow"))

    with console.status("[bold green]Prepping deployment(s)...") as status:
        prepped_deployments_l = []
        for count, deployment in enumerate(deployments, start=1):
            deployment_name = f"{flow.name}/{deployment.name}"
            current_deployment = await __read_deployment(deployment_name)
            if current_deployment:
                if update_parameters != "yes":
                    deployment.parameters = current_deployment.parameters
                if update_schedules != "yes":
                    deployment.schedules = current_deployment.schedules
                    print(deployment.schedules)
                if update_tags != "yes":
                    deployment.tags = current_deployment.tags

            deployment.schedules = [MinimalDeploymentSchedule(schedule=x.schedule, active=x.active) for x in deployment.schedules]
            deployment_ready = await flow_ready.to_deployment(**deployment.dict())
            prepped_deployments_l.append(deployment_ready)

    await deploy(*prepped_deployments_l, work_pool_name=work_pool_name, ignore_warnings=True)

    for count, deployment in enumerate(deployments, start=1):
        name = f"{flow.name}/{deployment.name}"
        print(name)
        with console.status("[bold green]Generating results..."):
            updated_deployment = await __read_deployment(name)
        rich_deploy.show_deployment_results(name, updated_deployment, current_deployment)


async def __read_deployment(name: str) -> DeploymentResponse:
    try:
        async with get_client() as client:
            deployment_obj = await client.read_deployment_by_name(name)
            return deployment_obj
    except ObjectNotFound:
        return None
