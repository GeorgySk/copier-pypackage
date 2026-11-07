import keyword
import re
import sys

# Escaped so that a slug containing quotes or backslashes can't break this
# file; the Jinja expression sits inside a string so the template is valid
# Python too (for Ruff).
project_slug = "{{ cookiecutter.project_slug | escape_double_quoted }}"

# Importable as a package and valid as a PyPI project name.
if not re.fullmatch(r"[a-z_][a-z0-9_]*", project_slug) or keyword.iskeyword(
    project_slug
):
    sys.exit(
        f"ERROR: project_slug {project_slug!r} is not a valid package name.\n"
        "Use lowercase ASCII letters, digits and underscores, don't start "
        "with a digit and don't use a Python keyword (for example "
        "'my_package'). Re-run cookiecutter and enter a project_slug, or "
        "change project_name."
    )
