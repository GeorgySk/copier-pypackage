"""
Jinja filters for the template, registered in cookiecutter.json.

Cookiecutter puts the template directory on ``sys.path`` while
rendering, so ``_extensions: ["local_extensions.<name>"]`` finds the
filters below.
"""

from cookiecutter.utils import simple_filter


@simple_filter  # type: ignore[untyped-decorator]  # cookiecutter is untyped
def escape_double_quoted(value: object) -> str:
    """
    Escape ``value`` for use between double quotes.

    The result is valid inside a TOML basic string ("...") and a Python
    string literal ("..." or \"\"\"...\"\"\"), as long as ``value`` has
    no control characters (prompt answers are single lines).
    """
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


@simple_filter  # type: ignore[untyped-decorator]  # cookiecutter is untyped
def python_string(value: object) -> str:
    """
    Render ``value`` as a Python string literal, quotes included.

    Uses the quotes ``ruff format`` would pick: double quotes, unless the
    value has more double than single quotes. A generated project then
    passes ``ruff format --check`` whatever the prompt answer was.
    """
    text = str(value).replace("\\", "\\\\")
    if text.count('"') > text.count("'"):
        return "'" + text.replace("'", "\\'") + "'"
    return '"' + text.replace('"', '\\"') + '"'
