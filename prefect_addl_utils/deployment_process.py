from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from git import Repo
from prefect import Flow, deploy, get_client
from prefect.client.schemas.objects import DeploymentSchedule, MinimalDeploymentSchedule
from prefect.client.schemas.responses import DeploymentResponse
from prefect.exceptions import ObjectNotFound
from prefect.runner.storage import GitRepository
from pydantic.v1 import BaseModel
from rich.console import Console
from rich.rule import Rule
from rich.status import Status

from . import deployment_output as rich_deploy

GIT_REPO_ROOT = os.environ.get("GIT_REPO_ROOT") or Path(__file__).parent.parent

console = Console()
repo = Repo(GIT_REPO_ROOT)

def help_text():
    print("""
`_deloy.py` executes deployment process

By default parameters, schedules, or tags are not updated.

To...
- update parameters, pass `--parameters`
- update schedules, pass `--schedules`
- update tags, pass `--tags`
- update all config, pass `--update-all`
"""
    )
    exit()


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
    schedules: list[MinimalDeploymentSchedule] | list[DeploymentSchedule] | None = None
    tags: list | None = None


async def execute_deploy_process(
    flow: Flow,
    source: GitRepository,
    entrypoint: str,
    deployments: list[DeploymentConfig] | DeploymentConfig,
    work_pool_name: str,
):
    cli_flags = sys.argv[1:]

    if "--help" in cli_flags:
        help_text()

    if repo.is_dirty():
        console.print("\n[bold yellow]WARNING:[/bold yellow] Unstaged/uncommitted changed detected. When deploying against the deployment source branch uncommitted changes may be missing from actual deployment. Commit or remove changes and try again.\n")
        exit()

    if not isinstance(deployments, list):
        deployments = [deployments]
    flow_ready = await flow.from_source(source=source, entrypoint=entrypoint)

    with console.status("[bold green]Prepping deployment(s)...\n") as spinner_status:
        prepped_deployments_l = []
        for deployment in deployments:
            deployment_name = f"{flow.name}/{deployment.name}"
            current_deployment = await __read_deployment(deployment_name)
            if current_deployment:
                deployment = __deployment_updates(deployment_name, deployment, current_deployment, cli_flags, spinner_status)
            deployment.schedules = [MinimalDeploymentSchedule(schedule=x.schedule, active=x.active) for x in deployment.schedules]
            deployment_ready = await flow_ready.to_deployment(**deployment.dict())
            prepped_deployments_l.append(deployment_ready)

    await deploy(*prepped_deployments_l, work_pool_name=work_pool_name, ignore_warnings=True)

    console.print(Rule(title="Deployment Results", style="white"))
    for deployment in deployments:
        name = f"{flow.name}/{deployment.name}"
        with console.status("[bold green]Generating results..."):
            updated_deployment = await __read_deployment(name)
        success = rich_deploy.show_deployment_results(name, updated_deployment, current_deployment)
        if success is None:
            console.print(f"[yellow]***WARNING***:[/yellow] Updated deployment information is missing for [blue]{name}[/blue]. Often, this happens when attempting to deploy changes not yet committed in git.\n")


async def __read_deployment(name: str) -> DeploymentResponse:
    try:
        async with get_client() as client:
            deployment_obj = await client.read_deployment_by_name(name)
            return deployment_obj
    except ObjectNotFound:
        return None


def __deployment_updates(name: str, deployment: DeploymentResponse, previous_deployment: DeploymentResponse, cli_flags: list, spinner_status: Status):
    update_all = True if "--update-all" in cli_flags else False
    if "--parameters" in cli_flags or update_all:
        spinner_status.update(f"{name} [blue]-> [yellow]`parameters`: prepping to update")
        time.sleep(2)
        deployment.parameters = previous_deployment.parameters
    if "--schedules" in cli_flags or "--schedule" in cli_flags or update_all:
        spinner_status.update(f"{name} [blue]-> [yellow]`schedules`: prepping to update")
        deployment.schedules = previous_deployment.schedules
        time.sleep(2)
    if "--tags" in cli_flags or update_all:
        spinner_status.update(f"{name} [blue]-> [yellow]`tags`: prepping to update")
        deployment.tags = previous_deployment.tags
        time.sleep(2)
    return deployment