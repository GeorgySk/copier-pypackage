{%- set namespace = cookiecutter.github_username -%}
{%- set slug = cookiecutter.project_slug -%}
{%- set on_gitlab = cookiecutter.ci_provider == "gitlab" -%}
{%- set repo_url = ("https://gitlab.com/" if on_gitlab else "https://github.com/") ~ namespace ~ "/" ~ slug -%}
{{ cookiecutter.project_name }}
===
{% if cookiecutter.ci_provider in ["github", "both"] %}
[![](https://github.com/{{ namespace }}/{{ slug }}/actions/workflows/ci.yml/badge.svg)](https://github.com/{{ namespace }}/{{ slug }}/actions/workflows/ci.yml "GitHub Actions")
[![](https://codecov.io/gh/{{ namespace }}/{{ slug }}/branch/main/graph/badge.svg)](https://codecov.io/gh/{{ namespace }}/{{ slug }} "Codecov")
{%- elif on_gitlab %}
[![](https://gitlab.com/{{ namespace }}/{{ slug }}/badges/main/pipeline.svg)](https://gitlab.com/{{ namespace }}/{{ slug }}/-/pipelines "GitLab CI")
[![](https://gitlab.com/{{ namespace }}/{{ slug }}/badges/main/coverage.svg)](https://gitlab.com/{{ namespace }}/{{ slug }}/-/pipelines "Coverage")
{%- endif %}
[![](https://readthedocs.org/projects/{{ slug }}/badge/?version=latest)](https://{{ slug }}.readthedocs.io/en/latest "Documentation")
{%- if on_gitlab %}
[![](https://img.shields.io/gitlab/license/{{ namespace }}%2F{{ slug }}.svg)]({{ repo_url }}/-/blob/main/LICENSE "License")
{%- else %}
[![](https://img.shields.io/github/license/{{ namespace }}/{{ slug }}.svg)]({{ repo_url }}/blob/main/LICENSE "License")
{%- endif %}
[![](https://badge.fury.io/py/{{ slug }}.svg)](https://badge.fury.io/py/{{ slug }} "PyPI")

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
git clone {{ repo_url }}.git
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
{%- if cookiecutter.ci_provider != "none" %}

### Publishing

Pushing a final release tag `vX.Y.Z` runs the CI publish jobs, which upload
the package to PyPI{% if cookiecutter.use_docker_compose == "yes" %} and push
the `prod` Docker image to the
{%- if on_gitlab %} GitLab container registry
{%- elif cookiecutter.ci_provider == "both" %} GitHub (GHCR) and GitLab container registries
{%- else %} GitHub container registry (GHCR){% endif %}{% endif %}.
{%- if cookiecutter.ci_provider == "both" %}
Only the GitHub workflow publishes to PyPI, so the same version isn't uploaded
twice.
{%- endif %}
Pre-release tags such as `vX.Y.Z-alpha` are not published.
{% if cookiecutter.use_devcontainer == "yes" %}
`bump-my-version bump release` commits and tags the release, so push both:
```bash
git push --follow-tags
```
{%- else %}
`bump-my-version` is configured not to commit or tag, so do it by hand:
```bash
git commit -am "Bump version to X.Y.Z"
git tag vX.Y.Z
git push --follow-tags
```
{%- endif %}

One-time setup:
{%- if cookiecutter.ci_provider in ["github", "both"] %}

- GitHub: on PyPI, add a
  [Trusted Publisher](https://docs.pypi.org/trusted-publishers/adding-a-publisher/)
  for this repository with workflow `ci.yml` and environment `pypi`.
- GitHub: add a `CODECOV_TOKEN` repository secret from
  [Codecov](https://codecov.io/).
{%- endif %}
{%- if on_gitlab %}

- GitLab: protect the `v*` tags (Settings > Repository > Protected tags), then
  add a PyPI API token as a masked, protected CI/CD variable `PYPI_API_TOKEN`.
  Protected variables are only available to pipelines for protected tags.
{%- endif %}
{%- endif %}

### Linting, formatting and type checking

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

[mypy](https://mypy.readthedocs.io/) checks types in strict mode
(configured in `pyproject.toml`)
```bash
mypy .
```

The package ships a `py.typed` marker, so projects that use it get its type
hints too.

To run these checks (Ruff and mypy) automatically on each commit,
install the [pre-commit](https://pre-commit.com/) hooks
(once, after the repository has been initialized with `git init`)
```bash
pre-commit install
```

### Running tests

Install the project with the `dev` dependency group (pytest, pytest-cov,
Hypothesis)
```bash
poetry install --with dev
```

Run the tests
```bash
poetry run pytest
```

Run the tests with a coverage report, as CI does
```bash
poetry run pytest --cov --cov-report=term
```
{%- if cookiecutter.use_devcontainer == "yes" %}

Inside the dev container, dependencies are already installed into the
container's Python, so `poetry run` can be dropped: `pytest`.
{%- endif %}
{%- if cookiecutter.use_docker_compose == "yes" %}

Inside a `Docker` container (the default `IMAGE_TYPE=dev` image includes the
`dev` group)
```bash
docker compose run --rm --entrypoint pytest {{ cookiecutter.project_slug }}
```
{%- endif %}
