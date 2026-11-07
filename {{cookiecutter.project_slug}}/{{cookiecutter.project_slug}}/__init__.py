"""{{ ((cookiecutter.project_short_description | trim) ~ ".") | wordwrap(72, break_long_words=false, break_on_hyphens=false) | escape_double_quoted }}"""

__author__ = {{ cookiecutter.full_name | python_string }}
__email__ = {{ cookiecutter.email | python_string }}
__version__ = "{{ cookiecutter.version }}"
