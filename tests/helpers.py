import json
import os
import re
import subprocess
import tomllib
from pathlib import Path
from typing import Any

import yaml
from cookiecutter.main import cookiecutter

# TEMPLATE_DIR lets the tests run against a modified copy of the template.
REPO_ROOT = Path(
    os.environ.get("TEMPLATE_DIR", Path(__file__).resolve().parents[1])
)

CI_PROVIDERS = ["github", "gitlab", "both", "none"]
YES_NO = ["yes", "no"]
COOKIECUTTER_JSON = json.loads((REPO_ROOT / "cookiecutter.json").read_text())
LICENSES = COOKIECUTTER_JSON["open_source_license"]
PYTHON_VERSIONS = COOKIECUTTER_JSON["python_version"]

# Same rule as hooks/pre_gen_project.py: importable and a valid PyPI name.
VALID_SLUG = re.compile(r"[a-z_][a-z0-9_]*")


def bake(output_dir: Path, config_file: Path, **context: str) -> Path:
    """Render the template with ``context`` and return the project path."""
    return Path(
        cookiecutter(
            str(REPO_ROOT),
            no_input=True,
            extra_context=context,
            output_dir=str(output_dir),
            config_file=str(config_file),
        )
    )


def load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as file:
        return tomllib.load(file)


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text())


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


GITLAB_RESERVED_KEYS = {
    "default",
    "include",
    "stages",
    "variables",
    "workflow",
}


def github_jobs(project: Path) -> set[str]:
    return set(load_yaml(project / ".github" / "workflows" / "ci.yml")["jobs"])


def gitlab_jobs(project: Path) -> set[str]:
    config = load_yaml(project / ".gitlab-ci.yml")
    return {
        key
        for key in config
        if key not in GITLAB_RESERVED_KEYS and not key.startswith(".")
    }


def dependabot_ecosystems(project: Path) -> set[str]:
    config = load_yaml(project / ".github" / "dependabot.yml")
    return {update["package-ecosystem"] for update in config["updates"]}


# Dropped from the environment of commands run in a rendered project:
# - GIT_DIR/GIT_INDEX_FILE/GIT_WORK_TREE (set when pytest runs from a git
#   hook) would point git at this repository instead of ``cwd``;
# - VIRTUAL_ENV/POETRY_ACTIVE would make Poetry install the rendered
#   project into the environment running the tests;
# - PYTHONPATH could shadow the rendered project's own modules.
DROPPED_ENV_PREFIXES = ("GIT_", "VIRTUAL_ENV", "POETRY_ACTIVE", "PYTHONPATH")


def run_isolated(
    command: list[str],
    cwd: Path,
    extra_env: dict[str, str] | None = None,
    timeout: float = 60,
) -> subprocess.CompletedProcess[str]:
    """
    Run ``command`` in ``cwd``, isolated from the caller's environment.

    The user's git config (which could sign commits or run hooks) is
    ignored too, and git gets a fixed identity.
    """
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(DROPPED_ENV_PREFIXES)
    }
    env |= {
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_AUTHOR_NAME": "test",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "test",
        "GIT_COMMITTER_EMAIL": "test@example.com",
    } | (extra_env or {})
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        timeout=timeout,
    )


def git_commit_all(project: Path) -> None:
    """Make ``project`` a git repository with everything committed."""
    for command in (
        ["git", "init", "--quiet", "--initial-branch=main"],
        ["git", "add", "--all"],
        ["git", "commit", "--quiet", "--no-verify", "--message", "Initial"],
    ):
        result = run_isolated(command, cwd=project)
        assert result.returncode == 0, result.stderr
