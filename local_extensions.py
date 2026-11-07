"""
Jinja filters for the template, registered in cookiecutter.json.

Cookiecutter puts the template directory on ``sys.path`` while 
rendering, so ``_extensions: ["local_extensions.<name>"]`` finds the 
filters below.
"""

from cookiecutter.utils import simple_filter


@simple_filter
def escape_double_quoted(value: object) -> str:
    """
    Escape ``value`` for use between double quotes.

    The result is valid inside a TOML basic string ("...") and a Python
    string literal ("..." or \"\"\"...\"\"\"), as long as ``value`` has 
    no control characters (prompt answers are single lines).
    """
    return str(value).replace("\\", "\\\\").replace('"', '\\"')
