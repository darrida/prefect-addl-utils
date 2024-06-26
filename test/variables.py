from __future__ import annotations

from prefect.blocks.system import Secret
from prefect.runner.storage import GitRepository
from prefect.variables import Variable

repo_name = Variable.set("github_flows_repo_name", value="prefect-addl-utils", overwrite=True)
repo_url = Variable.set("github_flows_storage", value="https://github.com/darrida/prefect-addl-utils.git", overwrite=True)
repo_branch = Variable.set("github_flows_branch", value="main", overwrite=True)
# token = Secret(value="lkasjdflkjasdf")
# token.save("github-flows-token")


git_storage = GitRepository(
    name=Variable.get("github_flows_repo_name").value,
    url=Variable.get("github_flows_storage").value,
    branch=Variable.get("github_flows_branch").value,
    # credentials={"access_token": Secret.load("github-flows-token")},
)