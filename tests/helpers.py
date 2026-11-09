import json
import os
import re
import shutil
import subprocess
import tomllib
from pathlib import Path
from typing import Any

import yaml
from copier import run_copy

# TEMPLATE_DIR lets the tests run against a modified copy of the template.
REPO_ROOT = Path(
    os.environ.get("TEMPLATE_DIR", Path(__file__).resolve().parents[1])
)
# What Copier reads from the template repository: copier.yml at the root,
# the imported macros and the rendered subdirectory.
TEMPLATE_PATHS = ("copier.yml", "macros.jinja", "template")

CI_PROVIDERS = ["github", "gitlab", "both", "none"]
BOOLS = [True, False]
QUESTIONS = {
    key: value
    for key, value in yaml.safe_load(
        (REPO_ROOT / "copier.yml").read_text()
    ).items()
    if not key.startswith("_")
}
DEFAULTS = {key: question["default"] for key, question in QUESTIONS.items()}
LICENSES = QUESTIONS["open_source_license"]["choices"]
PYTHON_VERSIONS = QUESTIONS["python_version"]["choices"]
ANSWERS_FILE = ".copier-answers.yml"

# Same rule as the project_slug validator: importable and a valid PyPI name.
VALID_SLUG = re.compile(r"[a-z_][a-z0-9_]*")


def snapshot_template(destination: Path) -> Path:
    """
    Copy the template to ``destination``, outside any git repository.

    Copier renders a git template from a clone of a commit (HEAD plus
    uncommitted changes when ``vcs_ref="HEAD"``), which is slow and noisy;
    a plain directory is rendered as it is.
    """
    destination.mkdir(parents=True)
    for name in TEMPLATE_PATHS:
        source = REPO_ROOT / name
        if source.is_dir():
            shutil.copytree(source, destination / name)
        else:
            shutil.copy2(source, destination / name)
    return destination


def bake(output_dir: Path, template_dir: Path, **context: object) -> Path:
    """
    Render ``template_dir`` with ``context`` and return the project path.

    The project directory is named after the project slug, as a user would
    name it.
    """
    staging = output_dir / ".render"
    run_copy(
        str(template_dir),
        str(staging),
        data=context,
        defaults=True,
        quiet=True,
        # Copier's default: the latest tag, which may lag behind HEAD.
        vcs_ref="HEAD",
    )
    slug = load_yaml(staging / ANSWERS_FILE)["project_slug"]
    return staging.rename(output_dir / slug)


def load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as file:
        return tomllib.load(file)


def load_yaml(path: Path) -> Any:  # noqa: ANN401 (any YAML document)
    return yaml.safe_load(path.read_text())


def load_json(path: Path) -> Any:  # noqa: ANN401 (any JSON document)
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
        check=False,
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
