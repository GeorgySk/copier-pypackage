"""Render every combination of the choice prompts and inspect it."""

import datetime
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from helpers import (
    CI_PROVIDERS,
    LICENSES,
    YES_NO,
    dependabot_ecosystems,
    github_jobs,
    gitlab_jobs,
    load_json,
    load_toml,
    load_yaml,
)

Baked = Callable[..., Path]

choices = pytest.mark.parametrize(
    ("ci_provider", "use_docker_compose", "use_devcontainer"),
    [
        (ci_provider, use_docker_compose, use_devcontainer)
        for ci_provider in CI_PROVIDERS
        for use_docker_compose in YES_NO
        for use_devcontainer in YES_NO
    ],
)
ci_choices = pytest.mark.parametrize(
    ("ci_provider", "use_docker_compose"),
    [
        (ci_provider, use_docker_compose)
        for ci_provider in ["github", "gitlab", "both"]
        for use_docker_compose in YES_NO
    ],
)

# `{{`, `{%` or `{#` left over by Jinja; GitHub's `${{ ... }}` is expected.
UNRENDERED_JINJA = re.compile(r"(?<!\$)\{\{|\{%|\{#")


def project_files(project: Path) -> list[Path]:
    return [
        path
        for path in project.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(project).parts
    ]


def run_isolated(
    command: list[str], cwd: Path
) -> subprocess.CompletedProcess[str]:
    """
    Run ``command`` in ``cwd``, isolated from the caller's git setup.

    Inherited ``GIT_DIR``/``GIT_INDEX_FILE``/``GIT_WORK_TREE`` (set when
    pytest runs from a git hook) would point git at this repository
    instead of ``cwd``, and the user's git config could sign commits or
    run hooks, so both are dropped.
    """
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_")
    }
    env |= {
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_AUTHOR_NAME": "test",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "test",
        "GIT_COMMITTER_EMAIL": "test@example.com",
    }
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        timeout=60,
    )


@choices
def test_files_match_choices(
    baked: Baked,
    ci_provider: str,
    use_docker_compose: str,
    use_devcontainer: str,
) -> None:
    project = baked(
        ci_provider=ci_provider,
        use_docker_compose=use_docker_compose,
        use_devcontainer=use_devcontainer,
    )

    assert (project / ".devcontainer").is_dir() == (use_devcontainer == "yes")
    for name in ("Dockerfile", "compose.yaml", ".env"):
        assert (project / name).is_file() == (use_docker_compose == "yes")
    assert (project / ".github" / "workflows" / "ci.yml").is_file() == (
        ci_provider in ("github", "both")
    )
    assert (project / ".gitlab-ci.yml").is_file() == (
        ci_provider in ("gitlab", "both")
    )
    assert (project / ".github").exists() == (ci_provider != "gitlab")


@choices
def test_dependabot_ecosystems(
    baked: Baked,
    ci_provider: str,
    use_docker_compose: str,
    use_devcontainer: str,
) -> None:
    if ci_provider == "gitlab":
        pytest.skip("no .github/ for GitLab projects")
    project = baked(
        ci_provider=ci_provider,
        use_docker_compose=use_docker_compose,
        use_devcontainer=use_devcontainer,
    )

    expected = {"pip"}
    if use_devcontainer == "yes":
        expected.add("devcontainers")
    if ci_provider in ("github", "both"):
        expected.add("github-actions")
    assert dependabot_ecosystems(project) == expected


@choices
def test_ci_jobs(
    baked: Baked,
    ci_provider: str,
    use_docker_compose: str,
    use_devcontainer: str,
) -> None:
    project = baked(
        ci_provider=ci_provider,
        use_docker_compose=use_docker_compose,
        use_devcontainer=use_devcontainer,
    )
    common = {"lint", "test", "build", "docs"}
    docker = {"publish-docker"} if use_docker_compose == "yes" else set()

    if ci_provider in ("github", "both"):
        assert github_jobs(project) == common | {"publish-pypi"} | docker
    if ci_provider in ("gitlab", "both"):
        # With "both", only GitHub publishes to PyPI.
        pypi = {"publish-pypi"} if ci_provider == "gitlab" else set()
        assert gitlab_jobs(project) == common | pypi | docker


@choices
def test_no_unrendered_jinja(
    baked: Baked,
    ci_provider: str,
    use_docker_compose: str,
    use_devcontainer: str,
) -> None:
    project = baked(
        ci_provider=ci_provider,
        use_docker_compose=use_docker_compose,
        use_devcontainer=use_devcontainer,
    )

    leftovers = {
        str(path.relative_to(project)): match.group()
        for path in project_files(project)
        if (match := UNRENDERED_JINJA.search(path.read_text()))
    }
    assert leftovers == {}


@choices
def test_config_files_parse(
    baked: Baked,
    ci_provider: str,
    use_docker_compose: str,
    use_devcontainer: str,
) -> None:
    project = baked(
        ci_provider=ci_provider,
        use_docker_compose=use_docker_compose,
        use_devcontainer=use_devcontainer,
    )
    loaders = {
        ".toml": load_toml,
        ".yml": load_yaml,
        ".yaml": load_yaml,
        ".json": load_json,
    }

    for path in project_files(project):
        if loader := loaders.get(path.suffix):
            loader(path)


@choices
def test_bumpversion(
    baked: Baked,
    tmp_path: Path,
    ci_provider: str,
    use_docker_compose: str,
    use_devcontainer: str,
) -> None:
    project = shutil.copytree(
        baked(
            ci_provider=ci_provider,
            use_docker_compose=use_docker_compose,
            use_devcontainer=use_devcontainer,
        ),
        tmp_path / "project",
    )
    config = load_toml(project / ".bumpversion.toml")["tool"]["bumpversion"]
    assert config["commit"] == config["tag"] == (use_devcontainer == "yes")

    # bump-my-version refuses to run in a dirty or missing repository.
    for command in (
        ["git", "init", "--quiet", "--initial-branch=main"],
        ["git", "add", "--all"],
        ["git", "commit", "--quiet", "--no-verify", "--message", "Initial"],
    ):
        setup = run_isolated(command, cwd=project)
        assert setup.returncode == 0, setup.stderr
    result = run_isolated(
        [sys.executable, "-m", "bumpversion", "bump", "--dry-run", "patch"],
        cwd=project,
    )
    assert result.returncode == 0, result.stderr


@ci_choices
def test_ci_schemas(
    baked: Baked, ci_provider: str, use_docker_compose: str
) -> None:
    if shutil.which("check-jsonschema") is None:
        pytest.skip("check-jsonschema is not installed")
    project = baked(
        ci_provider=ci_provider, use_docker_compose=use_docker_compose
    )
    workflow = project / ".github" / "workflows" / "ci.yml"
    files = {
        "vendor.github-workflows": workflow,
        "vendor.gitlab-ci": project / ".gitlab-ci.yml",
    }

    for schema, path in files.items():
        if not path.exists():
            continue
        result = subprocess.run(
            ["check-jsonschema", "--builtin-schema", schema, str(path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr


@ci_choices
def test_actionlint(
    baked: Baked, ci_provider: str, use_docker_compose: str
) -> None:
    if ci_provider == "gitlab":
        pytest.skip("no GitHub workflow")
    if shutil.which("actionlint") is None:
        pytest.skip("actionlint is not installed")
    project = baked(
        ci_provider=ci_provider, use_docker_compose=use_docker_compose
    )

    result = subprocess.run(
        ["actionlint", ".github/workflows/ci.yml"],
        cwd=project,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("python_version", ["3.10", "3.14"])
def test_python_matrix(baked: Baked, python_version: str) -> None:
    project = baked(ci_provider="both", python_version=python_version)
    minor = int(python_version.split(".")[1])
    expected = [f"3.{m}" for m in range(minor, 15)]

    github = load_yaml(project / ".github" / "workflows" / "ci.yml")
    gitlab = load_yaml(project / ".gitlab-ci.yml")
    github_matrix = github["jobs"]["test"]["strategy"]["matrix"]
    gitlab_matrix = gitlab["test"]["parallel"]["matrix"][0]
    assert github_matrix["python-version"] == expected
    assert gitlab_matrix["PYTHON_VERSION"] == expected


LICENSE_FIRST_LINES = {
    "MIT license": "MIT License",
    "BSD license": "BSD License",
    "ISC license": "ISC License",
    "Apache Software License 2.0": "Apache Software License 2.0",
    "GNU General Public License v3": "GNU GENERAL PUBLIC LICENSE",
    "Not open source": "Copyright (c) {year}, {full_name}",
}


def test_license_choices_are_covered() -> None:
    assert set(LICENSE_FIRST_LINES) == set(LICENSES)


@pytest.mark.parametrize("license_", LICENSES)
def test_license(baked: Baked, license_: str) -> None:
    full_name = "Jane Doe"
    project = baked(open_source_license=license_, full_name=full_name)
    year = str(datetime.date.today().year)

    text = (project / "LICENSE").read_text()
    expected_first_line = LICENSE_FIRST_LINES[license_].format(
        year=year, full_name=full_name
    )
    assert text.splitlines()[0] == expected_first_line
    assert year in text
    assert full_name in text


@pytest.mark.parametrize("ci_provider", CI_PROVIDERS)
def test_readme_links(baked: Baked, ci_provider: str) -> None:
    namespace, slug = "Jane-Doe", "demo_lib"
    project = baked(
        ci_provider=ci_provider,
        github_username=namespace,
        project_name="Demo Lib",
    )
    readme = (project / "README.md").read_text()
    urls = re.findall(r"https?://[^\s)\"]+", readme)

    own_urls = [url for url in urls if namespace in url]
    assert own_urls
    for url in own_urls:
        assert f"{namespace}/{slug}" in url or f"{namespace}%2F{slug}" in url

    github_badge = "actions/workflows/ci.yml/badge.svg"
    gitlab_badge = "badges/main/pipeline.svg"
    if ci_provider in ("github", "both"):
        assert github_badge in readme
        assert "codecov.io" in readme
    else:
        assert github_badge not in readme
        assert "codecov.io" not in readme
    assert (gitlab_badge in readme) == (ci_provider == "gitlab")
    if ci_provider == "gitlab":
        assert f"github.com/{namespace}" not in readme


def test_devcontainer_setup_script_exists(baked: Baked) -> None:
    project = baked(use_devcontainer="yes", project_name="Demo Lib")
    config = load_json(project / ".devcontainer" / "devcontainer.json")
    workspace = config["workspaceFolder"]

    command = config["onCreateCommand"]
    script = command.removeprefix("bash ")
    assert script.startswith(f"{workspace}/")
    assert (project / script.removeprefix(f"{workspace}/")).is_file()


def test_docs_automodule_targets_exist(baked: Baked) -> None:
    project = baked(project_name="Demo Lib")
    targets = [
        target
        for page in (project / "docs" / "source").glob("*.rst")
        for target in re.findall(
            r"^\.\. automodule:: (\S+)$", page.read_text(), re.MULTILINE
        )
    ]

    assert targets
    for target in targets:
        path = project.joinpath(*target.split("."))
        assert (path / "__init__.py").is_file() or path.with_suffix(
            ".py"
        ).is_file(), target
