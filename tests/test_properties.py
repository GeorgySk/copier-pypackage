"""Property-based tests for the free-text prompts."""

import ast
import keyword
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from hypothesis import example, given
from hypothesis import strategies as st

from helpers import VALID_SLUG, bake, load_toml

# Prompt answers are single lines, so control characters (which include
# newlines) and lone surrogates are out of scope. Anything else goes: Copier
# doesn't render answers as Jinja, and the project_slug validator rejects
# path-like slugs ("/", "..") before anything is written.
single_line = st.text(
    st.characters(exclude_categories=("Cs", "Cc")), max_size=60
)
name_like = st.text(
    st.characters(exclude_categories=("Cs", "Cc")), min_size=1, max_size=30
)
# Random text almost never gives a valid slug, so mix in plausible names
# ("My Lib", "data-tools 2") to exercise the accepting branch as well.
plausible_name = st.from_regex(
    r"[A-Za-z_][A-Za-z0-9_ \-]{0,29}", fullmatch=True
)
project_names = st.one_of(name_like, plausible_name)
# Long enough that the docstring in __init__.py has to wrap.
long_line = st.text(
    st.characters(exclude_categories=("Cs", "Cc")), max_size=200
)


def default_slug(project_name: str) -> str:
    """Same expression as the project_slug default in copier.yml."""
    return project_name.lower().replace(" ", "_").replace("-", "_")


def is_valid_slug(slug: str) -> bool:
    return bool(VALID_SLUG.fullmatch(slug)) and not keyword.iskeyword(slug)


def normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def assert_ruff_clean(project: Path, path: Path) -> None:
    """``path`` passes the generated project's Ruff config, bar E501."""
    # E501 is left to tests/test_tooling.py: heavily escaped names can
    # exceed 79 columns, which a realistic prompt answer won't.
    for command in (
        ["check", "--ignore", "E501", str(path)],
        ["format", "--check", "--diff", str(path)],
    ):
        result = subprocess.run(
            [sys.executable, "-m", "ruff", *command],
            cwd=project,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr


def module_strings(path: Path) -> tuple[str, dict[str, str]]:
    """Return the module docstring and its top-level string assignments."""
    module = ast.parse(path.read_text())
    docstring_node = module.body[0]
    assert isinstance(docstring_node, ast.Expr)
    assert isinstance(docstring_node.value, ast.Constant)
    assignments = {
        node.targets[0].id: ast.literal_eval(node.value)
        for node in module.body
        if isinstance(node, ast.Assign)
        and isinstance(node.targets[0], ast.Name)
    }
    docstring = docstring_node.value.value
    assert isinstance(docstring, str)
    return docstring, assignments


@given(full_name=single_line, email=single_line, description=long_line)
# Trailing whitespace is trimmed before the final "." (found on CI).
@example(full_name="", email="", description="0 ")
def test_free_text_round_trips(
    template_dir: Path, full_name: str, email: str, description: str
) -> None:
    with tempfile.TemporaryDirectory() as output_dir:
        project = bake(
            Path(output_dir),
            template_dir,
            full_name=full_name,
            email=email,
            project_short_description=description,
        )

        metadata = load_toml(project / "pyproject.toml")["project"]
        assert metadata["authors"] == [{"name": full_name, "email": email}]
        assert metadata["description"] == description

        init = project / project.name / "__init__.py"
        docstring, assignments = module_strings(init)
        # The docstring is stripped and wrapped at 72 columns.
        assert normalize_whitespace(docstring) == normalize_whitespace(
            description.strip() + "."
        )
        assert assignments["__author__"] == full_name
        assert assignments["__email__"] == email

        assert description in (project / "README.md").read_text()
        assert full_name in (project / "LICENSE").read_text()
        assert_ruff_clean(project, init)


def assert_slug_handled(template_dir: Path, slug: str, **context: str) -> None:
    with tempfile.TemporaryDirectory() as output_dir:
        if not is_valid_slug(slug):
            with pytest.raises(ValueError, match="project_slug"):
                bake(Path(output_dir), template_dir, **context)
            assert list(Path(output_dir).iterdir()) == []
            return

        project = bake(Path(output_dir), template_dir, **context)
        assert project.name == slug
        ast.parse((project / slug / "__init__.py").read_text())
        assert load_toml(project / "pyproject.toml")["project"]["name"] == slug


@given(project_name=project_names)
def test_default_slug_is_validated(
    template_dir: Path, project_name: str
) -> None:
    slug = default_slug(project_name)
    assert_slug_handled(template_dir, slug, project_name=project_name)


@given(slug=st.one_of(name_like, plausible_name.map(default_slug)))
def test_explicit_slug_is_validated(template_dir: Path, slug: str) -> None:
    assert_slug_handled(template_dir, slug, project_slug=slug)


@given(
    project_name=plausible_name.filter(
        lambda name: is_valid_slug(default_slug(name))
    )
)
def test_readme_title_is_project_name(
    template_dir: Path, project_name: str
) -> None:
    with tempfile.TemporaryDirectory() as output_dir:
        project = bake(
            Path(output_dir), template_dir, project_name=project_name
        )
        readme = (project / "README.md").read_text()
        assert readme.split("\n")[0] == project_name


@given(
    project_name=plausible_name.filter(
        lambda name: is_valid_slug(default_slug(name))
    )
)
def test_docs_title_underline_fits(
    template_dir: Path, project_name: str
) -> None:
    with tempfile.TemporaryDirectory() as output_dir:
        project = bake(
            Path(output_dir), template_dir, project_name=project_name
        )
        index = project / "docs" / "source" / "index.rst"
        title, underline = index.read_text().split("\n")[:2]
        assert title == project_name
        assert set(underline) == {"="}
        assert len(underline) >= len(title)
