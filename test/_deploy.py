from __future__ import annotations

import asyncio
from pathlib import Path

from flow import Parameters, main
from prefect.client.schemas.objects import MinimalDeploymentSchedule as sch
from prefect.client.schemas.schedules import CronSchedule
from prefect.runner.storage import GitRepository
from prefect.variables import Variable

import prefect_addl_utils as addl

WORK_POOL_NAME = "test-pool"

deployment1 = addl.DeploymentConfig(
    name="test-deployment1",
    version="1.0.0",
    work_queue_name="default",
    job_variables={},
    schedules=[sch(schedule=CronSchedule(cron="0 2 1 * *", timezone="America/Chicago"), active=True)],
    tags=["tag1", "tag2", "tag3"],
    ####################################
    parameters=Parameters().dict(),
    description=open(Path(__file__).parent / "_description.md").read(),
)

deployment2 = addl.DeploymentConfig(
    name="test-deployment2",
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
        addl.execute_deploy_process(
            flow=main,
            source=git_storage,
            # entrypoint=addl.build_entrypoint_str(__file__),
            deployments=[deployment1, deployment2],
            work_pool_name=WORK_POOL_NAME,
        )
    )