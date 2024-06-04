from __future__ import annotations

import asyncio
from pathlib import Path

from flow import Parameters, main
from prefect.client.schemas.objects import MinimalDeploymentSchedule as sch
from prefect.client.schemas.schedules import CronSchedule
from prefect.runner.storage import GitRepository
from prefect.variables import Variable

import prefect_addl_utils as utils

# from prefect_addl_utils import DeploymentConfig, build_entrypoint_str, deploy_process

WORK_POOL_NAME = "test-pool"

deployment = utils.DeploymentConfig(
    name="test-deployment",
    version="1.0.0",
    work_queue_name="default",
    job_variables={},
    schedules=[sch(schedule=CronSchedule(cron="0 2 1 * *", timezone="America/Chicago"), active=True)],
    tags=["tag1", "tag2", "tag3"],
    ####################################
    parameters=Parameters().dict(),
    description=open(Path(__file__).parent / "_description.md").read(),
)

git_storage = GitRepository(
    name=Variable.get("github_flows_repo_name").value,
    url=Variable.get("github_flows_storage").value,
    branch=Variable.get("github_flows_branch").value,
    # credentials={"access_token": Secret.load("github-flows-token")},
)

if __name__ == "__main__":
    asyncio.run(
        utils.execute_deploy_process(
            flow=main,
            source=git_storage,
            entrypoint=utils.build_entrypoint_str(__file__),
            deployments=deployment,
            work_pool_name=WORK_POOL_NAME
        )
    )