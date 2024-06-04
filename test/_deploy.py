from __future__ import annotations

import asyncio
from pathlib import Path

from flow import main
from prefect.blocks.system import Secret
from prefect.runner.storage import GitRepository
from prefect.variables import Variable

from prefect_addl_utils import DeploymentConfig, build_entrypoint_str, deploy_process

work_pool = "test-pool"

deployment = DeploymentConfig(
    name="test-deployment",
    version="1.0.0",
    work_queue_name="default",
    job_variables={},
    parameters={},
    description=open(Path(__file__).parent / "_description.md").read(),
    schedule=None,
    tags=["tag1", "tag2"]
)

git_storage = GitRepository(
    name=Variable.get("github_flows_repo_name").value,
    url=Variable.get("github_flows_storage").value,
    branch=Variable.get("github_flows_branch").value,
    # credentials={"access_token": Secret.load("github-flows-token")},
)

if __name__ == "__main__":
    asyncio.run(
        deploy_process(
            flow=main,
            source=git_storage,
            entrypoint=build_entrypoint_str(__file__),
            deployments=deployment,
            work_pool_name=work_pool
        )
    )