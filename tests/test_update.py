"""
Update rendered projects with ``copier update``.

A copy of the template is committed twice to a throwaway git repository:
``v1.0.0`` is the template as it is, ``v2.0.0`` adds lines to two files and
removes another. Projects rendered from ``v1.0.0`` are then updated to
``v2.0.0``, the way a user pulls in template changes.
"""

import os
import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest
from copier import run_copy, run_update

from helpers import (
    ANSWERS_FILE,
    BOOLS,
    CI_PROVIDERS,
    DROPPED_ENV_PREFIXES,
    git_commit_all,
    load_yaml,
    run_isolated,
    snapshot_template,
)

V1, V2 = "v1.0.0", "v2.0.0"
V2_LINE = "# Added in template v2"
# Files the user owns: `copier update` must leave them alone (copier.yml's
# _skip_if_exists, with project_slug rendered).
SKIPPED = ["CHANGES.rst", "{slug}/__init__.py", "tests/strategies/__init__.py"]
CONFLICT_MARKERS = ("<<<<<<<", ">>>>>>>")

choices = pytest.mark.parametrize(
    ("ci_provider", "use_docker_compose", "use_devcontainer"),
    [
        (ci_provider, use_docker_compose, use_devcontainer)
        for ci_provider in CI_PROVIDERS
        for use_docker_compose in BOOLS
        for use_devcontainer in BOOLS
    ],
)


def git(cwd: Path, *args: str) -> None:
    result = run_isolated(["git", *args], cwd=cwd)
    assert result.returncode == 0, result.stderr


@pytest.fixture(autouse=True)
def isolated_git(monkeypatch: pytest.MonkeyPatch) -> None:
    """Copier runs git: keep it away from the user's config and this repo."""
    for key in os.environ:
        if key.startswith(DROPPED_ENV_PREFIXES):
            monkeypatch.delenv(key)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    for role in ("AUTHOR", "COMMITTER"):
        monkeypatch.setenv(f"GIT_{role}_NAME", "test")
        monkeypatch.setenv(f"GIT_{role}_EMAIL", "test@example.com")


@pytest.fixture(scope="session")
def template_repo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """The template with a ``v1.0.0`` and a ``v2.0.0`` tag."""
    repo = snapshot_template(tmp_path_factory.mktemp("template-repo") / "t")
    git_commit_all(repo)
    git(repo, "tag", V1)

    template = repo / "template"
    for path in (
        template / ".gitignore",
        template / "{{project_slug}}" / "__init__.py.jinja",
    ):
        path.write_text(path.read_text() + V2_LINE + "\n")
    git(repo, "rm", "--quiet", "template/docs/make.bat")
    git(repo, "commit", "--quiet", "--all", "--message", "v2")
    git(repo, "tag", V2)
    return repo


def copy(template_repo: Path, dst: Path, ref: str, **data: object) -> Path:
    run_copy(
        str(template_repo),
        str(dst),
        data=data,
        defaults=True,
        quiet=True,
        vcs_ref=ref,
    )
    return dst


def update(project: Path, **data: object) -> None:
    run_update(
        str(project),
        data=data,
        defaults=True,
        overwrite=True,
        quiet=True,
        # Conflicts become inline markers, which assert_no_conflicts finds.
        conflict="inline",
    )


def tree(project: Path, exclude: set[str]) -> dict[str, bytes]:
    return {
        str(path.relative_to(project)): path.read_bytes()
        for path in sorted(project.rglob("*"))
        if path.is_file()
        and ".git" not in path.relative_to(project).parts
        and str(path.relative_to(project)) not in exclude
    }


def assert_no_conflicts(project: Path) -> None:
    for name, content in tree(project, exclude=set()).items():
        assert not name.endswith(".rej"), name
        text = content.decode(errors="replace")
        assert not any(marker in text for marker in CONFLICT_MARKERS), name


@pytest.fixture
def project(template_repo: Path, tmp_path: Path) -> Iterator[Path]:
    """A default project rendered from ``v1.0.0`` and committed."""
    path = copy(template_repo, tmp_path / "project", V1)
    git_commit_all(path)
    yield path
    shutil.rmtree(path, ignore_errors=True)


def test_update_merges_template_and_user_changes(project: Path) -> None:
    slug = load_yaml(project / ANSWERS_FILE)["project_slug"]
    gitignore = project / ".gitignore"
    init = project / slug / "__init__.py"
    gitignore.write_text("# Added by the user\n" + gitignore.read_text())
    init.write_text(init.read_text() + "USER_CODE = 1\n")
    git(project, "commit", "--quiet", "--all", "--message", "User changes")

    update(project)

    # The template's change is merged with the user's edit to the same file.
    lines = gitignore.read_text().splitlines()
    assert lines[0] == "# Added by the user"
    assert lines[-1] == V2_LINE
    # A file the template no longer has is deleted.
    assert not (project / "docs" / "make.bat").exists()
    # A file in _skip_if_exists keeps the user's version.
    assert "USER_CODE = 1" in init.read_text()
    assert V2_LINE not in init.read_text()
    assert load_yaml(project / ANSWERS_FILE)["_commit"] == V2
    assert_no_conflicts(project)


@choices
def test_untouched_project_updates_to_fresh_render(
    template_repo: Path,
    tmp_path: Path,
    ci_provider: str,
    use_docker_compose: bool,
    use_devcontainer: bool,
) -> None:
    answers = {
        "ci_provider": ci_provider,
        "use_docker_compose": use_docker_compose,
        "use_devcontainer": use_devcontainer,
    }
    project = copy(template_repo, tmp_path / "updated", V1, **answers)
    git_commit_all(project)
    update(project)
    fresh = copy(template_repo, tmp_path / "fresh", V2, **answers)

    slug = load_yaml(fresh / ANSWERS_FILE)["project_slug"]
    skipped = {name.format(slug=slug) for name in SKIPPED}
    assert tree(project, exclude=skipped) == tree(fresh, exclude=skipped)
    assert_no_conflicts(project)


@pytest.mark.parametrize(
    "changed",
    [
        {"use_devcontainer": False},
        {"use_docker_compose": False},
        {"ci_provider": "gitlab"},
        {"ci_provider": "none"},
        {"ci_provider": "both"},
    ],
)
def test_changed_answers_add_and_remove_files(
    project: Path, tmp_path: Path, changed: dict[str, object]
) -> None:
    template_repo = Path(load_yaml(project / ANSWERS_FILE)["_src_path"])

    update(project, **changed)
    fresh = copy(template_repo, tmp_path / "fresh", V2, **changed)

    slug = load_yaml(fresh / ANSWERS_FILE)["project_slug"]
    skipped = {name.format(slug=slug) for name in SKIPPED}
    assert tree(project, exclude=skipped) == tree(fresh, exclude=skipped)
    assert_no_conflicts(project)
