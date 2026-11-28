"""
Install a rendered project and run its own tooling.

These tests need network access (PyPI, GitHub for pre-commit) and take a
few minutes, so they are marked ``tooling`` and left out of a plain
``pytest`` run. Run them with ``pytest -m tooling``.
"""

import configparser
import sys
import zipfile
from email.parser import Parser
from pathlib import Path

import pytest

from helpers import (
    DEFAULTS,
    bake,
    git_commit_all,
    run_isolated,
)

pytestmark = pytest.mark.tooling

STRESS_DESCRIPTION = (
    'Tools for loading, validating and "cleaning" tabular data from CSV, '
    "Parquet and JSON sources before it reaches 'downstream' analysis code"
)
CASES = {
    "default": {},
    "stress": {
        "full_name": 'Jane "JD" O\'Brien-Smith',
        "project_name": "Data Tools",
        "project_short_description": STRESS_DESCRIPTION,
        "open_source_license": "GNU General Public License v3",
        "ci_provider": "both",
        "use_cli": True,
    },
}


class Project:
    """A rendered and installed project, plus a way to run commands in it."""

    def __init__(
        self, path: Path, context: dict[str, object], env: dict[str, str]
    ) -> None:
        """Wrap the project at ``path``, rendered from ``context``."""
        self.path = path
        self.context = context
        self.env = env

    def run(self, *command: str, timeout: float = 300) -> str:
        """Run ``command`` and return its stdout, failing on non-zero exit."""
        result = run_isolated(
            list(command), cwd=self.path, extra_env=self.env, timeout=timeout
        )
        output = result.stdout + result.stderr
        assert result.returncode == 0, f"{' '.join(command)}:\n{output}"
        return result.stdout

    def poetry_run(self, *command: str, timeout: float = 300) -> str:
        """Run ``command`` in the project's environment, like ``run``."""
        return self.run("poetry", "run", *command, timeout=timeout)


@pytest.fixture(scope="module", params=list(CASES))
def project(
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory,
    template_dir: Path,
) -> Project:
    context = CASES[request.param]
    path = bake(
        tmp_path_factory.mktemp(f"tooling-{request.param}"),
        template_dir,
        **context,
    )
    # pre-commit only runs inside a git repository.
    git_commit_all(path)
    env = {
        # The dev container sets POETRY_VIRTUALENVS_CREATE=false; give
        # the rendered project its own environment instead.
        "POETRY_VIRTUALENVS_CREATE": "true",
        "POETRY_VIRTUALENVS_IN_PROJECT": "true",
        "PRE_COMMIT_HOME": str(tmp_path_factory.mktemp("pre-commit")),
    }
    installed = Project(path, context, env)
    installed.run("poetry", "env", "use", sys.executable)
    installed.run("poetry", "install", "--with", "dev,docs", timeout=900)
    return installed


def test_poetry_check(project: Project) -> None:
    project.run("poetry", "check", "--lock")


def test_ruff(project: Project) -> None:
    project.poetry_run("ruff", "check", ".")


def test_mypy(project: Project) -> None:
    # The same command as the generated CI's lint job (strict mode).
    project.poetry_run("mypy", ".")


def test_pytest(project: Project) -> None:
    # The same command as the generated CI's test job.
    project.poetry_run(
        "pytest",
        "--cov",
        "--cov-report=term",
        "--cov-report=xml",
        "--junitxml=report.xml",
    )


def test_package_imports(project: Project) -> None:
    slug = project.path.name
    output = project.poetry_run(
        "python", "-c", f"import {slug}; print({slug}.__version__)"
    )
    assert output.strip() == "0.1.0"


def test_cli_command(project: Project) -> None:
    if not (DEFAULTS | project.context)["use_cli"]:
        pytest.skip("no CLI")
    slug = project.path.name
    command = slug.replace("_", "-")

    assert project.poetry_run(command, "Alice") == "Hello, Alice!\n"
    version = f"{command}, version 0.1.0\n"
    assert project.poetry_run(command, "--version") == version
    assert project.poetry_run("python", "-m", slug, "--version") == version


def test_docs(project: Project, tmp_path: Path) -> None:
    # The same command as the generated CI's docs job.
    project.poetry_run(
        "sphinx-build",
        "-W",
        "--keep-going",
        "-b",
        "html",
        "docs/source",
        str(tmp_path / "html"),
    )


def test_build(project: Project, tmp_path: Path) -> None:
    slug = project.path.name
    project.run("poetry", "build", "--output", str(tmp_path))
    (wheel,) = tmp_path.glob("*.whl")

    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        dist_info = f"{slug}-0.1.0.dist-info"
        metadata = Parser().parsestr(
            archive.read(f"{dist_info}/METADATA").decode()
        )
        entry_points = (
            archive.read(f"{dist_info}/entry_points.txt").decode()
            if f"{dist_info}/entry_points.txt" in names
            else ""
        )
    assert f"{slug}/__init__.py" in names
    assert f"{slug}/py.typed" in names
    assert any(
        name.startswith(f"{dist_info}/") and name.endswith("/LICENSE")
        for name in names
    )
    assert metadata["Name"] == slug
    assert metadata["Requires-Python"] == ">=3.11,<4.0"
    expected = DEFAULTS | project.context
    assert metadata["Author"] == expected["full_name"]
    assert metadata["Author-email"] == expected["email"]
    parser = configparser.ConfigParser()
    parser.read_string(entry_points)
    scripts = (
        dict(parser["console_scripts"])
        if parser.has_section("console_scripts")
        else {}
    )
    command = slug.replace("_", "-")
    assert scripts == (
        {command: f"{slug}.cli:main"} if expected["use_cli"] else {}
    )
    assert any(
        requirement.startswith("click")
        for requirement in metadata.get_all("Requires-Dist", [])
    ) == expected["use_cli"]


def test_pre_commit(project: Project) -> None:
    project.poetry_run("pre-commit", "run", "--all-files", timeout=600)
