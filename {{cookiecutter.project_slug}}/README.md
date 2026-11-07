{{ cookiecutter.project_name }}
===

[![](https://github.com/{{ cookiecutter.github_username }}/{{ cookiecutter.project_slug }}/workflows/CI/badge.svg)](https://github.com/{{ cookiecutter.github_username }}/{{ cookiecutter.project_slug }}/actions/workflows/ci.yml "Github Actions")
[![](https://codecov.io/gh/{{ cookiecutter.github_username }}/{{ cookiecutter.project_slug }}/branch/master/graph/badge.svg)](https://codecov.io/gh/{{ cookiecutter.github_username }}/{{ cookiecutter.project_slug }} "Codecov")
[![](https://readthedocs.org/projects/{{ cookiecutter.project_slug }}/badge/?version=latest)](https://{{ cookiecutter.project_slug }}.readthedocs.io/en/latest "Documentation")
[![](https://img.shields.io/github/license/{{ cookiecutter.github_username }}/{{ cookiecutter.project_slug }}.svg)](https://github.com/{{ cookiecutter.github_username }}/{{ cookiecutter.project_slug }}/blob/master/LICENSE "License")
[![](https://badge.fury.io/py/{{ cookiecutter.project_slug }}.svg)](https://badge.fury.io/py/{{ cookiecutter.project_slug }} "PyPI")

Summary
-------

{{ cookiecutter.project_short_description }}.

---

In what follows, `python` is an alias for `python{{ cookiecutter.python_version }}`
or any later version.

Installation
------------

Install the latest `pip` & `setuptools` packages versions
```bash
python -m pip install --upgrade pip setuptools
```

### User

Download and install the latest stable version from `PyPI` repository
```bash
python -m pip install --upgrade {{ cookiecutter.project_slug }}
```

### Developer

Download the latest version from `GitHub` repository
```bash
git clone https://github.com/{{ cookiecutter.github_username }}/{{ cookiecutter.project_slug }}.git
cd {{ cookiecutter.project_slug }}
```

Install
```bash
poetry install
```

Usage
-----

...

Development
-----------

### Bumping version

#### Preparation

Install
[bump-my-version](https://github.com/callowayproject/bump-my-version/tree/master?tab=readme-ov-file#installation).

#### Pre-release

Choose which version number category to bump following [semver
specification](http://semver.org/).

Test bumping version
```bash
bump-my-version bump --dry-run --verbose $CATEGORY
```

where `$CATEGORY` is the target version number category name, possible
values are `patch`/`minor`/`major`.

Bump version
```bash
bump-my-version bump --verbose $CATEGORY
```

This will set version to `major.minor.patch-alpha`. 

#### Release

Test bumping version
```bash
bump-my-version bump --dry-run --verbose release
```

Bump version
```bash
bump-my-version bump --verbose release
```

This will set version to `major.minor.patch`.

### Linting and formatting

[Ruff](https://docs.astral.sh/ruff/) is used for both linting and formatting
(installed with the `dev` dependency group).

Check code
```bash
ruff check .
```

Fix automatically fixable issues
```bash
ruff check --fix .
```

Format code
```bash
ruff format .
```

To run these checks automatically on each commit,
install the [pre-commit](https://pre-commit.com/) hooks
(once, after the repository has been initialized with `git init`)
```bash
pre-commit install
```

### Running tests

Install dependencies
```bash
python -m pip install -r requirements-tests.txt
```

Plain
```bash
pytest
```
{%- if cookiecutter.use_docker_compose == "yes" %}

Inside `Docker` container:
  ```bash
  docker-compose run --entrypoint pytest {{ cookiecutter.project_slug }}
  ```
{%- endif %}
