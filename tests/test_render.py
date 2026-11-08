"""Render every combination of the choice prompts and inspect it."""

import datetime
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from helpers import (
    ANSWERS_FILE,
    BOOLS,
    CI_PROVIDERS,
    DEFAULTS,
    LICENSES,
    PYTHON_VERSIONS,
    REPO_ROOT,
    dependabot_ecosystems,
    git_commit_all,
    github_jobs,
    gitlab_jobs,
    load_json,
    load_toml,
    load_yaml,
    run_isolated,
)

Baked = Callable[..., Path]

choices = pytest.mark.parametrize(
    ("ci_provider", "use_docker_compose", "use_devcontainer"),
    [
        (ci_provider, use_docker_compose, use_devcontainer)
        for ci_provider in CI_PROVIDERS
        for use_docker_compose in BOOLS
        for use_devcontainer in BOOLS
    ],
)
ci_choices = pytest.mark.parametrize(
    ("ci_provider", "use_docker_compose"),
    [
        (ci_provider, use_docker_compose)
        for ci_provider in ["github", "gitlab", "both"]
        for use_docker_compose in BOOLS
    ],
)

# The generated project's GitHub Actions workflows.
WORKFLOWS = ["ci.yml", "template-update.yml"]

# `{{`, `{%` or `{#` left over by Jinja; GitHub's `${{ ... }}` is expected.
UNRENDERED_JINJA = re.compile(r"(?<!\$)\{\{|\{%|\{#")


def project_files(project: Path) -> list[Path]:
    return [
        path
        for path in project.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(project).parts
    ]


@choices
def test_files_match_choices(
    baked: Baked,
    ci_provider: str,
    use_docker_compose: bool,
    use_devcontainer: bool,
) -> None:
    project = baked(
        ci_provider=ci_provider,
        use_docker_compose=use_docker_compose,
        use_devcontainer=use_devcontainer,
    )

    assert (project / ".devcontainer").is_dir() == use_devcontainer
    devcontainer_compose = (
        project / ".devcontainer" / "compose.devcontainer.yaml"
    )
    assert devcontainer_compose.is_file() == (
        use_devcontainer and use_docker_compose
    )
    for name in ("Dockerfile", "compose.yaml", ".env"):
        assert (project / name).is_file() == use_docker_compose
    for workflow in WORKFLOWS:
        assert (project / ".github" / "workflows" / workflow).is_file() == (
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
    use_docker_compose: bool,
    use_devcontainer: bool,
) -> None:
    if ci_provider == "gitlab":
        pytest.skip("no .github/ for GitLab projects")
    project = baked(
        ci_provider=ci_provider,
        use_docker_compose=use_docker_compose,
        use_devcontainer=use_devcontainer,
    )

    expected = {"pip"}
    if use_devcontainer:
        expected.add("devcontainers")
    if ci_provider in ("github", "both"):
        expected.add("github-actions")
    assert dependabot_ecosystems(project) == expected


@choices
def test_ci_jobs(
    baked: Baked,
    ci_provider: str,
    use_docker_compose: bool,
    use_devcontainer: bool,
) -> None:
    project = baked(
        ci_provider=ci_provider,
        use_docker_compose=use_docker_compose,
        use_devcontainer=use_devcontainer,
    )
    common = {"lint", "test", "build", "docs"}
    docker = {"publish-docker"} if use_docker_compose else set()

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
    use_docker_compose: bool,
    use_devcontainer: bool,
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
    use_docker_compose: bool,
    use_devcontainer: bool,
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
    use_docker_compose: bool,
    use_devcontainer: bool,
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
    assert config["commit"] == config["tag"] == use_devcontainer

    # bump-my-version refuses to run in a dirty or missing repository.
    git_commit_all(project)
    result = run_isolated(
        [sys.executable, "-m", "bumpversion", "bump", "--dry-run", "patch"],
        cwd=project,
    )
    assert result.returncode == 0, result.stderr


@ci_choices
def test_ci_schemas(
    baked: Baked, ci_provider: str, use_docker_compose: bool
) -> None:
    if shutil.which("check-jsonschema") is None:
        pytest.skip("check-jsonschema is not installed")
    project = baked(
        ci_provider=ci_provider, use_docker_compose=use_docker_compose
    )
    files = [
        ("vendor.github-workflows", project / ".github" / "workflows" / name)
        for name in WORKFLOWS
    ] + [("vendor.gitlab-ci", project / ".gitlab-ci.yml")]

    for schema, path in files:
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
    baked: Baked, ci_provider: str, use_docker_compose: bool
) -> None:
    if ci_provider == "gitlab":
        pytest.skip("no GitHub workflow")
    if shutil.which("actionlint") is None:
        pytest.skip("actionlint is not installed")
    project = baked(
        ci_provider=ci_provider, use_docker_compose=use_docker_compose
    )

    result = subprocess.run(
        ["actionlint", *(f".github/workflows/{name}" for name in WORKFLOWS)],
        cwd=project,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_python_version_choices() -> None:
    # Python 3.11 is the minimum (3.10 is end-of-life), and the choices end
    # where the CI matrices end (range(..., 15) in both CI files).
    assert PYTHON_VERSIONS == [f"3.{minor}" for minor in range(11, 15)]


@pytest.mark.parametrize("python_version", PYTHON_VERSIONS)
def test_python_matrix(baked: Baked, python_version: str) -> None:
    project = baked(ci_provider="both", python_version=python_version)
    assert (
        load_toml(project / "pyproject.toml")["project"]["requires-python"]
        == f">={python_version},<4.0"
    )
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
    project = baked(use_devcontainer=True, project_name="Demo Lib")
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


def test_ruff_pins_in_sync(baked: Baked) -> None:
    project = baked()
    hooks = load_yaml(project / ".pre-commit-config.yaml")["repos"]
    (ruff_hooks,) = [
        repo for repo in hooks if repo["repo"].endswith("/ruff-pre-commit")
    ]
    dev = load_toml(project / "pyproject.toml")["dependency-groups"]["dev"]
    (generated_pin,) = [dep for dep in dev if dep.startswith("ruff==")]
    root = load_toml(REPO_ROOT / "pyproject.toml")
    root_pin = root["tool"]["poetry"]["group"]["dev"]["dependencies"]["ruff"]

    assert (
        ruff_hooks["rev"].removeprefix("v")
        == generated_pin.removeprefix("ruff==")
        == root_pin
    )


@ci_choices
def test_lint_job_type_checks(
    baked: Baked, ci_provider: str, use_docker_compose: bool
) -> None:
    project = baked(
        ci_provider=ci_provider, use_docker_compose=use_docker_compose
    )

    if ci_provider in ("github", "both"):
        workflow = load_yaml(project / ".github" / "workflows" / "ci.yml")
        steps = workflow["jobs"]["lint"]["steps"]
        assert "poetry run mypy ." in [step.get("run") for step in steps]
    if ci_provider in ("gitlab", "both"):
        lint = load_yaml(project / ".gitlab-ci.yml")["lint"]
        assert "poetry run mypy ." in lint["script"]


def test_package_is_typed(baked: Baked) -> None:
    project = baked()
    assert (project / project.name / "py.typed").is_file()
    config = load_toml(project / "pyproject.toml")
    assert config["tool"]["mypy"]["strict"] is True


def test_poetry_versions_in_sync() -> None:
    # The template's default for generated projects and the template repo's
    # own environment (.env, used by Docker, CI and the dev container) use
    # the same Poetry, so the template is developed with what it generates.
    default = DEFAULTS["poetry_version"]
    env = dict(
        line.split("=", 1)
        for line in (REPO_ROOT / ".env").read_text().splitlines()
        if line.startswith("POETRY_VERSION=")
    )

    assert default == env["POETRY_VERSION"]
    # The dev container gets Poetry from .env too, not a second pin.
    root = load_json(REPO_ROOT / ".devcontainer" / "devcontainer.json")
    assert not poetry_features(root)


def test_copier_versions_in_sync(baked: Baked) -> None:
    # The template-update workflow runs the Copier the template is tested
    # with (the root lock file), which must satisfy _min_copier_version.
    project = baked(ci_provider="github")
    workflow = load_yaml(
        project / ".github" / "workflows" / "template-update.yml"
    )
    pinned = workflow["env"]["COPIER_VERSION"]
    lock = load_toml(REPO_ROOT / "poetry.lock")
    (locked,) = (
        package["version"]
        for package in lock["package"]
        if package["name"] == "copier"
    )
    minimum = load_yaml(REPO_ROOT / "copier.yml")["_min_copier_version"]

    assert pinned == locked
    assert version_tuple(pinned) >= version_tuple(minimum)


def version_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def poetry_features(devcontainer: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        options
        for feature, options in devcontainer.get("features", {}).items()
        if "/poetry:" in feature
    ]


def assert_devcontainer_runs_compose(project: Path) -> None:
    """The dev container runs the compose service: one environment."""
    devcontainer_dir = project / ".devcontainer"
    config = load_json(devcontainer_dir / "devcontainer.json")
    assert "image" not in config
    assert not poetry_features(config)

    compose_files = [
        devcontainer_dir / name for name in config["dockerComposeFile"]
    ]
    assert all(path.is_file() for path in compose_files)
    base, override = (load_yaml(path) for path in compose_files)
    service = config["service"]
    assert service in base["services"]
    # The workspace is where compose.yaml bind-mounts the project.
    mounts = [
        volume.split(":")[1]
        for volume in base["services"][service]["volumes"]
        if volume.split(":")[0] == "."
    ]
    assert mounts == [config["workspaceFolder"]]
    assert override["services"][service]["build"]["target"] == "dev"


@choices
def test_devcontainer_environment(
    baked: Baked,
    ci_provider: str,
    use_docker_compose: bool,
    use_devcontainer: bool,
) -> None:
    if not use_devcontainer:
        pytest.skip("no dev container")
    project = baked(
        ci_provider=ci_provider,
        use_docker_compose=use_docker_compose,
        use_devcontainer=use_devcontainer,
    )

    if use_docker_compose:
        assert_devcontainer_runs_compose(project)
        return
    # Without Docker Compose the dev container is the only definition.
    config = load_json(project / ".devcontainer" / "devcontainer.json")
    assert config["image"] == f"python:{DEFAULTS['python_version']}-bookworm"
    (poetry_feature,) = poetry_features(config)
    assert poetry_feature["version"] == DEFAULTS["poetry_version"]


def test_root_devcontainer_runs_compose() -> None:
    assert_devcontainer_runs_compose(REPO_ROOT)


@pytest.mark.parametrize("use_docker_compose", BOOLS)
def test_devcontainer_remote_user(
    baked: Baked, use_docker_compose: bool
) -> None:
    # ${localEnv:USER} is empty on Windows hosts (it has USERNAME), which
    # left setup_user.sh running as root; use the common-utils user.
    project = baked(
        use_docker_compose=use_docker_compose, use_devcontainer=True
    )
    for root in (project, REPO_ROOT):
        config = load_json(root / ".devcontainer" / "devcontainer.json")
        assert config["remoteUser"] == "vscode"


@choices
def test_answers_file(
    baked: Baked,
    ci_provider: str,
    use_docker_compose: bool,
    use_devcontainer: bool,
) -> None:
    # `copier update` re-renders the project from these answers.
    context = {
        "ci_provider": ci_provider,
        "use_docker_compose": use_docker_compose,
        "use_devcontainer": use_devcontainer,
    }
    project = baked(**context)
    answers = load_yaml(project / ANSWERS_FILE)

    assert answers["_src_path"]
    expected = DEFAULTS | context | {"project_slug": project.name}
    # Not asked, so not recorded: an update brings in the current default.
    del expected["poetry_version"]
    recorded = {
        key: value for key, value in answers.items() if not key.startswith("_")
    }
    assert recorded == expected
