from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from prefect.client.schemas.objects import MinimalDeploymentSchedule as sch
from prefect.client.schemas.schedules import CronSchedule

import prefect_utils_addl as addl

######################################################################
# USER CONFIGURATION BEGINS HERE
# >>> WARNING >>> "Source-of-truth" for `schedules`, `tags`, and `parameters` is the is the Prefect Cloud Scheduler.
#                 The associated values below MAY NOT reflect what is actually currently used in production.
#                 Check https://app.prefect.cloud for up to date `schedules`, `tags`, and `parameters`
######################################################################
if True:
    from flow import main

WORK_POOL_NAME = "2.19.3"

deployment1 = wcc.DeploymentConfig(
    name="deployment-name1",
    version="0.0.1",
    work_queue_name="default",
    schedules=[sch(schedule=CronSchedule(cron="0 */1 * * *", timezone="America/Chicago"))],
    tags=["production", "maintenance"],
    parameters={"dir": "/data1", "number": 7},
    ####################################
    description=open(Path(__file__).parent / "_description.md").read(),
)

deployment2 = wcc.DeploymentConfig(
    name="deployment-name2",
    version="0.0.1",
    work_queue_name="default",
    schedules=[sch(schedule=CronSchedule(cron="0 */1 * * *", timezone="America/Chicago"))],
    tags=["test", "maintenance"],
    parameters={"dir": "/data", "number": 7},
    ####################################
    description=open(Path(__file__).parent / "_description.md").read(),
)

deployments_l = [deployment1, deployment2]

######################################################################
# CODE BELOW IS USUALLY UNCHANGED
######################################################################
gitlab_storage = GitRepository(
    name=Variable.get("gitlab_flows_repo_name").value,
    url=Variable.get("gitlab_flows_storage").value,
    branch=Variable.get("gitlab_flows_branch").value,
    credentials={
        "access_token": Secret.load("gitlab-flows-token"),
    },
)

if __name__ == "__main__":
    asyncio.run(
        wcc.execute_deploy_process(
            flow=main,
            source=gitlab_storage,
            entrypoint=wcc.build_entrypoint_str(__file__),
            deployments=deployments_l,
            work_pool_name=WORK_POOL_NAME,
        )
    )
