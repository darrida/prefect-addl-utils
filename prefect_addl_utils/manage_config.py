from __future__ import annotations

from pathlib import Path

import tomllib
from git import Repo
from git.exc import InvalidGitRepositoryError


class AddlGitRepo:
    def find_pyproject_toml(return_none: bool = False) -> Path:
        cwd = Path.cwd()
        candidates = [cwd]
        candidates.extend(cwd.parents)

        for path in candidates:
            config_file = path / 'pyproject.toml'
            if config_file.exists():
                return config_file
        else:
            if return_none is True:
                return None
            raise RuntimeError(
                'prefect-addl-utils could not find a pyproject.toml file in {} or its parents'.format(cwd)
            )

    def read_pyproject_toml(pyproject_toml_path: str | Path, return_none: bool = False) -> dict:

        with open(pyproject_toml_path, 'rb') as f:
            config = tomllib.load(f)
        addl_config = config.get("tool").get("prefect-addl-utils")
        if not addl_config:
            if return_none is True:
                return
            raise RuntimeError(
                "prefect-addl-utils found a pyproject.toml file in {}, "
                "but did not find a section labelled 'tool.prefect-addl-utils'"
            )
        return addl_config
        

    def config_repo_root(return_none: bool = False):
        pyproject_toml_path: Path = AddlGitRepo.find_pyproject_toml(return_none)
        print(f"Using `pyproject.toml` from {pyproject_toml_path}")
        addl_config = AddlGitRepo.read_pyproject_toml(pyproject_toml_path, return_none)
        if not addl_config and return_none is True:
            return
        else:
            repo_root = addl_config.get("git-repo-root")
        if repo_root in (None, "."):
            repo_root = pyproject_toml_path.parent
        try:
            repo_root.exists()
            return repo_root
        except AttributeError as e:
            if "object has no attribute 'exists'" not in str(e):
                raise AttributeError(e) from e
        if return_none is True:
            return
        raise RuntimeError(
            f"'git-repo-root' found in {pyproject_toml_path} points to '{repo_root}', but that directory was not found."
        )

    @staticmethod
    def get():
        if path := AddlGitRepo.config_repo_root(return_none=True):
            try:
                candidates = [path]
            except InvalidGitRepositoryError:
                raise RuntimeError(
                    f"'git-repo-root' in [tools.prefect-addl-utils] from `pyproject.toml` configured {path} as a "
                    "directory to find a git repo, but no `.git` file was found."
                )
        else:
            cwd = Path.cwd()
            candidates = [cwd]
            candidates.extend(cwd.parents)

        for path in candidates:
            try:
                repo = Repo(path)
                print(f"Using git project from: {repo.common_dir}")
                return repo
            except InvalidGitRepositoryError:
                pass
        else:
            raise RuntimeError(
                'prefect-addl-utils could not find a pyproject.toml file in {} or its parents'.format(cwd)
            )


if __name__ == "__main__":
    AddlGitRepo.get()
