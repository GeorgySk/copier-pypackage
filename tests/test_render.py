"""Render every combination of the choice prompts and inspect it."""

import datetime as dt
import json
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from packaging.requirements import Requirement

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
cli_choices = pytest.mark.parametrize("use_cli", BOOLS)
ci_choices = pytest.mark.parametrize(
    ("ci_provider", "use_docker_compose"),
    [
        (ci_provider, use_docker_compose)
        for ci_provider in ["github", "gitlab", "both"]
        for use_docker_compose in BOOLS
    ],
)

# Rendered only with use_cli.
CLI_FILES = ["{slug}/cli.py", "{slug}/__main__.py", "tests/test_cli.py"]

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
@cli_choices
def test_files_match_choices(
    baked: Baked,
    ci_provider: str,
    use_docker_compose: bool,
    use_devcontainer: bool,
    use_cli: bool,
) -> None:
    project = baked(
        ci_provider=ci_provider,
        use_docker_compose=use_docker_compose,
        use_devcontainer=use_devcontainer,
        use_cli=use_cli,
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
    for name in CLI_FILES:
        assert (project / name.format(slug=project.name)).is_file() == use_cli


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


def test_dependabot_skips_template_dependencies(baked: Baked) -> None:
    """
    The project's Dependabot updates only its own dependencies.

    The dev and docs groups come from template-dependencies/pyproject.toml,
    which the template repository's Dependabot updates.
    """
    project = baked()
    config = load_yaml(project / ".github" / "dependabot.yml")
    (pip,) = [
        update
        for update in config["updates"]
        if update["package-ecosystem"] == "pip"
    ]

    assert pip["allow"] == [{"dependency-type": "production"}]


def test_root_dependabot_updates_template_dependencies() -> None:
    config = load_yaml(REPO_ROOT / ".github" / "dependabot.yml")
    (pip,) = [
        update
        for update in config["updates"]
        if update["package-ecosystem"] == "pip"
    ]

    assert set(pip["directories"]) == {"/", "/template-dependencies"}


def test_dependency_groups_come_from_template_dependencies(
    baked: Baked,
) -> None:
    project = baked()
    source = load_toml(REPO_ROOT / "template-dependencies" / "pyproject.toml")
    generated = load_toml(project / "pyproject.toml")

    assert generated["dependency-groups"] == source["dependency-groups"]
    # Only the groups are copied: the table must stay last in the source.
    assert list(source)[-1] == "dependency-groups"


def test_template_dependencies_python_floor() -> None:
    """Dependabot must only pick versions the oldest choice can install."""
    source = load_toml(REPO_ROOT / "template-dependencies" / "pyproject.toml")

    assert source["project"]["requires-python"] == (
        f">={PYTHON_VERSIONS[0]},<4.0"
    )


@cli_choices
def test_cli(baked: Baked, use_cli: bool) -> None:
    project = baked(project_name="Demo Lib", use_cli=use_cli)
    config = load_toml(project / "pyproject.toml")["project"]
    source = load_toml(REPO_ROOT / "template-dependencies" / "pyproject.toml")
    readme = (project / "README.md").read_text()
    api = (project / "docs" / "source" / "demo_lib.rst").read_text()

    if use_cli:
        # Click's requirement comes from where Dependabot updates it.
        assert config["dependencies"] == source["project"]["dependencies"]
        assert [Requirement(dep).name for dep in config["dependencies"]] == [
            "click"
        ]
        assert config["scripts"] == {"demo-lib": "demo_lib.cli:main"}
    else:
        assert config["dependencies"] == []
        assert "scripts" not in config
    assert ("demo-lib --help" in readme) == use_cli
    assert ("python -m demo_lib --help" in readme) == use_cli
    assert (".. automodule:: demo_lib.cli" in api) == use_cli


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
    common = {"lint", "test", "build", "docs", "release"}
    docker = {"publish-docker"} if use_docker_compose else set()

    if ci_provider in ("github", "both"):
        # ci-passed is the one check to require before merging (GitLab
        # requires the whole pipeline instead).
        assert github_jobs(project) == (
            common | {"publish-pypi", "ci-passed"} | docker
        )
    if ci_provider in ("gitlab", "both"):
        # With "both", only GitHub publishes to PyPI.
        pypi = {"publish-pypi"} if ci_provider == "gitlab" else set()
        assert gitlab_jobs(project) == common | pypi | docker


def github_release_notes_script(workflow: Path) -> str:
    """Return the run script of the release notes step in ``workflow``."""
    steps = load_yaml(workflow)["jobs"]["release"]["steps"]
    [step] = [
        step for step in steps if step.get("name", "").startswith("Write")
    ]
    script: str = step["run"]
    return script


def gitlab_release_notes_script(project: Path) -> str:
    [script] = load_yaml(project / ".gitlab-ci.yml")["release"]["script"]
    return str(script)


def test_release_notes(baked: Baked, tmp_path: Path) -> None:
    project = shutil.copytree(
        baked(
            ci_provider="both", use_devcontainer=False, version="1.2.0-alpha"
        ),
        tmp_path / "project",
    )
    changes = project / "CHANGES.rst"
    changes.write_text(
        changes.read_text().replace(
            "Unreleased\n----------\n",
            "Unreleased\n----------\n\n"
            "Added\n~~~~~\n\n- A ``feature``.\n\n"
            "Fixed\n~~~~~\n\n- A bug.\n\n"
            "1.1.0 (2026-01-01)\n------------------\n\n"
            "Added\n~~~~~\n\n- An older feature.\n",
        )
    )
    git_commit_all(project)
    result = run_isolated(
        [sys.executable, "-m", "bumpversion", "bump", "release"], cwd=project
    )
    assert result.returncode == 0, result.stderr
    scripts = {
        "GITHUB_REF_NAME": github_release_notes_script(
            project / ".github" / "workflows" / "ci.yml"
        ),
        "CI_COMMIT_TAG": gitlab_release_notes_script(project),
    }

    for variable, script in scripts.items():
        notes = project / "release-notes.md"
        notes.unlink(missing_ok=True)
        result = run_isolated(
            ["sh", "-c", script], cwd=project, extra_env={variable: "v1.2.0"}
        )
        assert result.returncode == 0, result.stderr
        assert notes.read_text().strip() == (
            "### Added\n\n- A ``feature``.\n\n### Fixed\n\n- A bug."
        )

        # The tag must match pyproject.toml, and the version needs a section.
        result = run_isolated(
            ["sh", "-c", script], cwd=project, extra_env={variable: "v1.1.0"}
        )
        assert result.returncode != 0
        assert "does not match" in result.stderr
        changes.write_text(changes.read_text().replace("1.2.0 (", "9.9.9 ("))
        result = run_isolated(
            ["sh", "-c", script], cwd=project, extra_env={variable: "v1.2.0"}
        )
        assert result.returncode != 0
        assert "No section for 1.2.0" in result.stderr
        changes.write_text(changes.read_text().replace("9.9.9 (", "1.2.0 ("))


@ci_choices
def test_release_runs_alongside_publish(
    baked: Baked, ci_provider: str, use_docker_compose: bool
) -> None:
    """``release`` waits for the checks like the publish jobs, not for them."""
    project = baked(
        ci_provider=ci_provider, use_docker_compose=use_docker_compose
    )

    if ci_provider in ("github", "both"):
        jobs = load_yaml(project / ".github" / "workflows" / "ci.yml")["jobs"]
        assert jobs["release"]["needs"] == jobs["publish-pypi"]["needs"]
        assert jobs["release"]["if"] == jobs["publish-pypi"]["if"]
    if ci_provider in ("gitlab", "both"):
        config = load_yaml(project / ".gitlab-ci.yml")
        assert config["release"]["stage"] == "publish"
        assert config["release"]["extends"] == ".release-rules"

def test_release_notes_in_sync(baked: Baked) -> None:
    """The template repository's release workflow uses the same script."""
    project = baked(ci_provider="both")
    generated = github_release_notes_script(
        project / ".github" / "workflows" / "ci.yml"
    )

    assert generated == github_release_notes_script(
        REPO_ROOT / ".github" / "workflows" / "release.yml"
    )
    assert generated == gitlab_release_notes_script(project).replace(
        "CI_COMMIT_TAG", "GITHUB_REF_NAME"
    )


def test_root_workflows_lint() -> None:
    if shutil.which("actionlint") is None:
        pytest.skip("actionlint is not installed")
    workflows = sorted((REPO_ROOT / ".github" / "workflows").glob("*.yml"))

    result = subprocess.run(
        ["actionlint", *map(str, workflows)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr

@choices
@cli_choices
def test_no_unrendered_jinja(
    baked: Baked,
    ci_provider: str,
    use_docker_compose: bool,
    use_devcontainer: bool,
    use_cli: bool,
) -> None:
    project = baked(
        ci_provider=ci_provider,
        use_docker_compose=use_docker_compose,
        use_devcontainer=use_devcontainer,
        use_cli=use_cli,
    )

    leftovers = {
        str(path.relative_to(project)): match.group()
        for path in project_files(project)
        if (match := UNRENDERED_JINJA.search(path.read_text()))
    }
    assert leftovers == {}


@choices
@cli_choices
def test_config_files_parse(
    baked: Baked,
    ci_provider: str,
    use_docker_compose: bool,
    use_devcontainer: bool,
    use_cli: bool,
) -> None:
    project = baked(
        ci_provider=ci_provider,
        use_docker_compose=use_docker_compose,
        use_devcontainer=use_devcontainer,
        use_cli=use_cli,
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
            check=False,
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
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_python_version_choices() -> None:
    # Python 3.11 is the minimum (3.10 is end-of-life), and the choices end
    # where the CI matrices end (range(..., 15) in the test_pythons macro).
    expected = [f"3.{minor}" for minor in range(11, 15)]
    assert expected == PYTHON_VERSIONS


def github_test_pythons(project: Path) -> dict[str, list[str]]:
    """
    Return the GitHub test matrix's Python versions for each kind of run.

    The matrix is an expression that picks a JSON list by event: release
    tags, then pull requests, then pushes to main.
    """
    workflow = load_yaml(project / ".github" / "workflows" / "ci.yml")
    expression = workflow["jobs"]["test"]["strategy"]["matrix"][
        "python-version"
    ]
    lists = re.findall(r"'(\[[^']*\])'", expression)
    kinds = ["tag", "pull_request", "main"]
    return dict(zip(kinds, map(json.loads, lists), strict=True))


def gitlab_test_pythons(project: Path) -> dict[str, list[str]]:
    """
    Return the GitLab test matrix's Python versions for each kind of run.

    Evaluates the test job's ``rules`` (a tag, a merge request, the default
    branch) for every ``PYTHON_VERSION`` in the matrix.
    """
    test = load_yaml(project / ".gitlab-ci.yml")["test"]
    [matrix] = test["parallel"]["matrix"]
    pipelines = {
        "tag": "$CI_COMMIT_TAG",
        "pull_request": '$CI_PIPELINE_SOURCE == "merge_request_event"',
        "main": "$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH",
    }
    return {
        kind: [
            version
            for version in matrix["PYTHON_VERSION"]
            if any(
                rule["if"].startswith(condition)
                and (
                    "$PYTHON_VERSION" not in rule["if"]
                    or f'$PYTHON_VERSION == "{version}"' in rule["if"]
                )
                for rule in test["rules"]
            )
        ]
        for kind, condition in pipelines.items()
    }


@pytest.mark.parametrize("python_version", PYTHON_VERSIONS)
def test_python_matrix(baked: Baked, python_version: str) -> None:
    """
    Check the Python versions the CI tests run on.

    Every Python on release tags, the oldest and newest on pull requests, the
    oldest (which uploads coverage) on the default branch.
    """
    project = baked(ci_provider="both", python_version=python_version)
    assert (
        load_toml(project / "pyproject.toml")["project"]["requires-python"]
        == f">={python_version},<4.0"
    )
    minor = int(python_version.split(".")[1])
    every = [f"3.{m}" for m in range(minor, 15)]
    expected = {
        "tag": every,
        "pull_request": list(dict.fromkeys([every[0], every[-1]])),
        "main": [python_version],
    }

    assert github_test_pythons(project) == expected
    assert gitlab_test_pythons(project) == expected
    workflow = load_yaml(project / ".github" / "workflows" / "ci.yml")
    upload = [
        step
        for step in workflow["jobs"]["test"]["steps"]
        if "codecov" in step.get("uses", "")
    ]
    assert [step["if"] for step in upload] == [
        f"matrix.python-version == '{python_version}'"
    ]


def workflow_triggers(workflow: dict[Any, Any]) -> dict[str, Any]:
    """Return the ``on`` table (PyYAML reads the key ``on`` as ``True``)."""
    triggers: dict[str, Any] = workflow[True]
    return triggers


@pytest.mark.parametrize(
    ("tag", "publishes"),
    [
        ("v1.2.3", True),
        ("v10.20.30", True),
        ("v1.2.3-alpha", False),
        ("v1.2.3-beta", False),
        ("vX.Y.Z", False),
    ],
)
def test_ci_runs_on_final_tags_only(
    baked: Baked, tag: str, publishes: bool
) -> None:
    """
    Pre-release tags start no pipeline: they would only repeat the checks.

    In GitHub's tag filter, ``[0-9]`` and ``+`` mean what they mean in a
    regular expression, and ``.`` is literal.
    """
    project = baked(ci_provider="both")
    workflow = load_yaml(project / ".github" / "workflows" / "ci.yml")
    [pattern] = workflow_triggers(workflow)["push"]["tags"]
    github_regex = pattern.replace(".", r"\.")
    assert bool(re.fullmatch(github_regex, tag)) is publishes

    gitlab = load_yaml(project / ".gitlab-ci.yml")
    [tag_rule] = [
        rule["if"]
        for rule in gitlab["workflow"]["rules"]
        if rule["if"].startswith("$CI_COMMIT_TAG")
    ]
    gitlab_regex = tag_rule.split("=~", 1)[1].strip().strip("/")
    assert bool(re.search(gitlab_regex, tag)) is publishes


def test_ci_skips_drafts(baked: Baked) -> None:
    project = baked(ci_provider="both")
    workflow = load_yaml(project / ".github" / "workflows" / "ci.yml")
    pull_request = workflow_triggers(workflow)["pull_request"]
    assert "ready_for_review" in pull_request["types"]
    jobs = workflow["jobs"]
    for name in ("lint", "test", "ci-passed"):
        assert "!github.event.pull_request.draft" in jobs[name]["if"], name
    # The other checks run only after lint.
    for name in ("test", "build", "docs"):
        assert jobs[name]["needs"] == "lint", name
    assert workflow["concurrency"]["cancel-in-progress"]

    gitlab = load_yaml(project / ".gitlab-ci.yml")
    assert gitlab["workflow"]["rules"][0] == {
        "if": '$CI_MERGE_REQUEST_DRAFT == "true"',
        "when": "never",
    }


@ci_choices
def test_ci_checks_skip_main(
    baked: Baked, ci_provider: str, use_docker_compose: bool
) -> None:
    """
    Only the tests run on the default branch.

    Its changes were checked in their pull request. Every check runs on
    release tags.
    """
    project = baked(
        ci_provider=ci_provider, use_docker_compose=use_docker_compose
    )

    if ci_provider in ("github", "both"):
        jobs = load_yaml(project / ".github" / "workflows" / "ci.yml")["jobs"]
        assert "github.ref_type == 'tag'" in jobs["lint"]["if"]
        assert "github.event_name == 'pull_request'" in jobs["lint"]["if"]
        assert set(jobs["ci-passed"]["needs"]) == {
            "lint",
            "test",
            "build",
            "docs",
        }
    if ci_provider in ("gitlab", "both"):
        config = load_yaml(project / ".gitlab-ci.yml")
        check_rules = config[".check-rules"]["rules"]
        assert check_rules[0] == {
            "if": "$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH",
            "when": "never",
        }
        for name in ("lint", "docs", "build"):
            extends = config[name]["extends"]
            assert ".check-rules" in (
                extends if isinstance(extends, list) else [extends]
            ), name


@ci_choices
def test_ci_jobs_time_out(
    baked: Baked, ci_provider: str, use_docker_compose: bool
) -> None:
    """A hanging job stops long before the default 6 hours (GitHub)."""
    project = baked(
        ci_provider=ci_provider, use_docker_compose=use_docker_compose
    )

    if ci_provider in ("github", "both"):
        jobs = load_yaml(project / ".github" / "workflows" / "ci.yml")["jobs"]
        for name, job in jobs.items():
            assert 0 < job.get("timeout-minutes", 0) <= 30, name  # noqa: PLR2004
    if ci_provider in ("gitlab", "both"):
        config = load_yaml(project / ".gitlab-ci.yml")
        assert config["default"]["timeout"] == "20 minutes"
        assert config["default"]["interruptible"] is True
        assert config[".release-rules"]["interruptible"] is False


@choices
def test_dependabot_schedule(
    baked: Baked,
    ci_provider: str,
    use_docker_compose: bool,
    use_devcontainer: bool,
) -> None:
    """Monthly and grouped: every Dependabot pull request runs CI."""
    if ci_provider == "gitlab":
        pytest.skip("no .github/ for GitLab projects")
    project = baked(
        ci_provider=ci_provider,
        use_docker_compose=use_docker_compose,
        use_devcontainer=use_devcontainer,
    )

    config = load_yaml(project / ".github" / "dependabot.yml")
    for update in config["updates"]:
        ecosystem = update["package-ecosystem"]
        assert update["schedule"]["interval"] == "monthly", ecosystem
        assert update["groups"], ecosystem


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
    # With the CLI, so that its files are checked too.
    project = baked(
        open_source_license=license_, full_name=full_name, use_cli=True
    )
    # local date, like the template's `'%Y' | strftime`
    year = str(dt.date.today().year)  # noqa: DTZ011

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
    if ci_provider in ("github", "both"):
        assert f"{github_badge}?branch=main" in readme
    assert f"img.shields.io/pypi/pyversions/{slug}" in readme
    assert "copier-org/copier/master/img/badge/" in readme


@pytest.mark.parametrize("license_", LICENSES)
def test_readme_license_badge(baked: Baked, license_: str) -> None:
    project = baked(open_source_license=license_)
    readme = (project / "README.md").read_text()
    has_badge = "img.shields.io/github/license/" in readme
    assert has_badge == (license_ != "Not open source")


# Licenses whose copyright notice only has to accompany copies of the work
# (the LICENSE file does that), so the generated project skips per-file
# notices. Same list as `licenses_without_file_notices` in macros.jinja.
LICENSES_WITHOUT_FILE_NOTICES = ["MIT license", "BSD license", "ISC license"]
SPDX_IDENTIFIERS = {
    "Apache Software License 2.0": "Apache-2.0",
    "GNU General Public License v3": "GPL-3.0-or-later",
}


@pytest.mark.parametrize("license_", LICENSES)
def test_copyright_headers(baked: Baked, license_: str) -> None:
    full_name = "Jane Doe"
    project = baked(open_source_license=license_, full_name=full_name)
    year = dt.date.today().year  # noqa: DTZ011
    notices = license_ not in LICENSES_WITHOUT_FILE_NOTICES

    ruff = load_toml(project / "pyproject.toml")["tool"]["ruff"]["lint"]
    assert ("CPY001" in ruff["ignore"]) != notices
    expected = [f"# Copyright (c) {year}, {full_name}"]
    if license_ in SPDX_IDENTIFIERS:
        expected.append(
            f"# SPDX-License-Identifier: {SPDX_IDENTIFIERS[license_]}"
        )
    for path in project.rglob("*.py"):
        lines = path.read_text().splitlines()
        header = lines[: len(expected)]
        assert (header == expected) == notices, path
    # The generated config (with CPY001 when it's enabled) accepts them.
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "."],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_devcontainer_setup_script_exists(baked: Baked) -> None:
    project = baked(use_devcontainer=True, project_name="Demo Lib")
    config = load_json(project / ".devcontainer" / "devcontainer.json")
    workspace = config["workspaceFolder"]

    command = config["onCreateCommand"]
    script = command.removeprefix("bash ")
    assert script.startswith(f"{workspace}/")
    assert (project / script.removeprefix(f"{workspace}/")).is_file()


# Copier copies each template file's mode into the project, so a stray
# executable bit (easily committed from a Windows checkout) spreads to users.
EXECUTABLE_FILES = {".devcontainer/setup_user.sh"}


def test_committed_executable_bits() -> None:
    """Only scripts are executable in the git index that releases come from."""
    result = subprocess.run(
        ["git", "ls-files", "--stage", "-z"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip("the template is not a git repository")
    executable = {
        entry.split("\t", 1)[1]
        for entry in result.stdout.split("\0")
        if entry.startswith("100755 ")
    }
    assert executable == {
        ".devcontainer/setup_user.sh",
        (
            "template/{% if use_devcontainer %}.devcontainer{% endif %}"
            "/setup_user.sh"
        ),
    }


@choices
def test_executable_bits(
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

    executable = {
        path.relative_to(project).as_posix()
        for path in project_files(project)
        if path.stat().st_mode & 0o111
    }
    assert executable == (EXECUTABLE_FILES if use_devcontainer else set())


def test_docs_automodule_targets_exist(baked: Baked) -> None:
    project = baked(project_name="Demo Lib", use_cli=True)
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


DEVCONTAINER_EXTENSIONS = {
    "anthropic.claude-code",
    "charliermarsh.ruff",
    "ms-python.python",
}


@pytest.mark.parametrize("use_docker_compose", BOOLS)
def test_devcontainer_extensions(
    baked: Baked, use_docker_compose: bool
) -> None:
    # Both dev containers install the same VS Code extensions.
    project = baked(
        use_devcontainer=True, use_docker_compose=use_docker_compose
    )
    for path in (
        project / ".devcontainer" / "devcontainer.json",
        REPO_ROOT / ".devcontainer" / "devcontainer.json",
    ):
        config = load_json(path)
        extensions = config["customizations"]["vscode"]["extensions"]
        assert set(extensions) == DEVCONTAINER_EXTENSIONS


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


def test_copier_in_dev_group(baked: Baked) -> None:
    # The generated project installs Copier for `copier update`: a version
    # that can render the template, admitting the one it's tested with.
    project = baked()
    dev = load_toml(project / "pyproject.toml")["dependency-groups"]["dev"]
    (requirement,) = [
        Requirement(dep) for dep in dev if Requirement(dep).name == "copier"
    ]
    lock = load_toml(REPO_ROOT / "poetry.lock")
    (locked,) = (
        package["version"]
        for package in lock["package"]
        if package["name"] == "copier"
    )
    minimum = load_yaml(REPO_ROOT / "copier.yml")["_min_copier_version"]

    assert locked in requirement.specifier
    assert {spec.operator: spec.version for spec in requirement.specifier}[
        ">="
    ] == minimum


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
@cli_choices
def test_answers_file(
    baked: Baked,
    ci_provider: str,
    use_docker_compose: bool,
    use_devcontainer: bool,
    use_cli: bool,
) -> None:
    # `copier update` re-renders the project from these answers.
    context = {
        "ci_provider": ci_provider,
        "use_docker_compose": use_docker_compose,
        "use_devcontainer": use_devcontainer,
        "use_cli": use_cli,
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
