copier-pypackage
================

[![CI](https://github.com/GeorgySk/copier-pypackage/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/GeorgySk/copier-pypackage/actions/workflows/ci.yml "CI")
[![](https://img.shields.io/github/license/GeorgySk/copier-pypackage.svg)](https://github.com/GeorgySk/copier-pypackage/blob/main/LICENSE "License")
[![](https://img.shields.io/github/v/tag/GeorgySk/copier-pypackage?sort=semver&label=release)](https://github.com/GeorgySk/copier-pypackage/tags "Latest release")
[![](https://img.shields.io/badge/python-3.11%20%E2%80%93%203.14-blue.svg)](https://github.com/GeorgySk/copier-pypackage/blob/main/copier.yml "Supported Python versions of generated projects")
[![](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/copier-org/copier/master/img/badge/badge-grayscale-inverted-border-orange.json)](https://copier.readthedocs.io "Copier template")

Summary
-------

Copier-pypackage is a [Copier](https://copier.readthedocs.io) template for
a Python library. A generated project comes ready to develop, test,
document and release:

- packaging and dependencies with [Poetry](https://python-poetry.org/),
- linting and formatting with [Ruff](https://docs.astral.sh/ruff/), strict
  type checking with [mypy](https://mypy.readthedocs.io/), both also run by
  [pre-commit](https://pre-commit.com/) hooks,
- tests with [pytest](https://pytest.org/),
  [pytest-cov](https://pytest-cov.readthedocs.io/) and
  [Hypothesis](https://hypothesis.readthedocs.io/),
- documentation with [Sphinx](https://www.sphinx-doc.org/) on
  [Read the Docs](https://readthedocs.org/),
- versioning with
  [bump-my-version](https://github.com/callowayproject/bump-my-version) and
  a [Keep a Changelog](https://keepachangelog.com/) changelog,
- optionally, a Docker/Docker Compose setup and a
  [dev container](https://containers.dev/),
- CI/CD on GitHub Actions and/or GitLab CI that checks every push and
  publishes releases to PyPI (and a Docker image to a container registry),
- Dependabot updates of dependencies.

Projects generated from it can later pull in improvements to the template
with `copier update`, by hand or through a scheduled pull request.

The generated project
---------------------

### Questions

| Question | Default | Effect |
| --- | --- | --- |
| `full_name`, `email` | | Package author in `pyproject.toml`, `__init__.py` and the license. |
| `github_username` | | Namespace of the repository on GitHub or GitLab, used in the README links, badges and Docker image name. |
| `project_name` | `Python Boilerplate` | Human-readable name (README and docs titles). |
| `project_slug` | derived from `project_name` | Package directory and PyPI name. Must be a valid, non-keyword Python identifier in lower case (`[a-z_][a-z0-9_]*`); Copier asks again otherwise. |
| `project_short_description` | | Package description and module docstring. |
| `version` | `0.1.0` | Initial version. |
| `open_source_license` | MIT | MIT, BSD, ISC, Apache 2.0, GPL v3 or "Not open source". |
| `python_version` | `3.11` | Minimum supported Python (3.11–3.14). CI tests every version from it up to 3.14. |
| `use_devcontainer` | yes | Add `.devcontainer/`. |
| `use_docker_compose` | yes | Add `Dockerfile`, `compose.yaml` and `.env`. |
| `ci_provider` | `github` | `github`, `gitlab`, `both` or `none`. |

Answers that you don't need leave no trace: files for an unused option are
not generated at all (no empty or commented-out files), and they are added
or removed by `copier update` when you change the answer later.

### Layout

```
my_project/
├── my_project/            # the package: __init__.py (version, author), py.typed
├── tests/                 # pytest suite; conftest.py, strategies/ for Hypothesis
├── docs/source/           # Sphinx sources (conf.py, API page, changelog)
├── pyproject.toml         # metadata, dependency groups, Ruff/mypy/pytest config
├── .bumpversion.toml      # bump-my-version
├── CHANGES.rst            # changelog
├── .pre-commit-config.yaml
├── .readthedocs.yaml
├── Dockerfile, compose.yaml, .env    # use_docker_compose
├── .devcontainer/                    # use_devcontainer
├── .github/               # dependabot.yml, workflows/ci.yml, template-update.yml
├── .gitlab-ci.yml                    # ci_provider gitlab or both
├── .copier-answers.yml    # answers and template version, for copier update
├── LICENSE
└── README.md              # instructions for the project's developers
```

### Packaging and dependencies

The project uses Poetry 2 with standard PEP 621 metadata (`[project]`) and
PEP 735 dependency groups. The package has no runtime dependencies. Tools
live in two optional groups, so a plain `poetry install` stays minimal:

- `dev`: pytest, pytest-cov, Hypothesis, Ruff, mypy, pre-commit and
  bump-my-version (`poetry install --with dev`),
- `docs`: Sphinx and the Read the Docs theme (`poetry install --with docs`).

Hypothesis and Ruff are pinned exactly, so test runs and lint results are
the same on every machine; the rest use ranges. `requires-python` is a
PEP 440 range (`>=3.11,<4.0`) rather than Poetry's `^3.11`, because Ruff
reads it to pick its target version.

### Code quality

- **Ruff** lints (rules `E`, `W`, `F`, `B`, `I`: pycodestyle, Pyflakes,
  flake8-bugbear, isort) and formats, with 79-character lines. One tool
  replaces Black, isort and Flake8.
- **mypy** runs in strict mode on the whole project, tests and Sphinx
  configuration included. The package ships a `py.typed` marker
  (PEP 561), so the type hints also reach the package's users.
- **pre-commit** runs Ruff and mypy on each commit. mypy runs from the
  project's environment (a `local` hook) so it sees the project's
  dependencies and has a single version pin.

Every generated file passes these checks, so a new project starts with a
green CI.

### Testing

pytest runs the tests with coverage from pytest-cov. `tests/strategies/` is
the place for [Hypothesis](https://hypothesis.readthedocs.io/) strategies
for property-based tests. `tests/conftest.py` registers a `default`
Hypothesis profile (no deadline, so slow CI machines don't cause flaky
failures) and lets a project without tests yet pass instead of failing with
"no tests collected".

### Documentation

`docs/source/` holds a Sphinx project with autodoc, the Read the Docs theme
and intersphinx links to Python's documentation. `conf.py` reads the name,
authors and version from `pyproject.toml`, so they are never duplicated.
The changelog is included in the docs. `.readthedocs.yaml` builds the docs
on Read the Docs with the `docs` dependency group. CI builds them with
warnings treated as errors, so broken references are caught before a
release.

### Versioning and changelog

Versions follow [semantic versioning](https://semver.org/), with
`X.Y.Z-alpha` pre-releases. bump-my-version updates the
version in `pyproject.toml`, `__init__.py` and the Docker image tag in
`compose.yaml` together. A `release` bump also turns the `Unreleased`
section of `CHANGES.rst` into a dated one. With a dev container, the bump
also commits and tags `vX.Y.Z`, and pushing that tag publishes the release.

`CHANGES.rst` follows [Keep a Changelog](https://keepachangelog.com/) and
is written in reStructuredText so that Sphinx can include it.

### Docker and dev container

With `use_docker_compose`, the project gets a multi-stage `Dockerfile`:

- `base`: the Python image with Poetry and the project sources,
- `prod`: `base` plus runtime dependencies (the image that is published),
- `dev`: `base` plus the `dev` group.

`compose.yaml` builds it and mounts the project at `/opt/<project_slug>`.
`.env` is the single place that sets the Python and Poetry versions and the
stage (`IMAGE_TYPE=dev|prod`).

With `use_devcontainer`, `.devcontainer/` lets VS Code (or any dev
container client) open the project in a ready environment with the Ruff
extension. When Docker Compose is also enabled, the dev container runs the
Compose service (always its `dev` stage), so the container you develop in
is the same one `docker compose` builds and there is one environment
definition. Without Compose, it uses the official Python image and the
Poetry dev container feature. In both cases `setup_user.sh` gives the
container user the uid and gid of the host workspace's owner, so files
created in the container stay yours.

### CI/CD

`ci_provider` selects GitHub Actions (`.github/workflows/ci.yml`), GitLab
CI (`.gitlab-ci.yml`), both, or none. Both files run the same jobs with the
same commands:

| Job | What it does |
| --- | --- |
| `lint` | `ruff check`, `mypy .` |
| `test` | pytest with coverage on every Python from the minimum to 3.14; coverage goes to Codecov (GitHub) or GitLab's coverage report |
| `build` | `poetry build` (sdist and wheel) |
| `docs` | `sphinx-build -W` |
| `publish-pypi` | uploads the built package to PyPI |
| `publish-docker` | pushes the `prod` image to GHCR or the GitLab registry (with `use_docker_compose`) |

The publish jobs run only for final release tags (`vX.Y.Z`, not
`vX.Y.Z-alpha`), only after all checks pass, and first check that the tag
matches the version in `pyproject.toml`. GitHub publishes to PyPI with
[Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (no stored
token); GitLab uses a protected `PYPI_API_TOKEN` variable. With `both`,
only GitHub publishes to PyPI, since a second upload of the same version
would fail. The generated README lists the one-time setup.

### Dependency updates

Projects hosted on GitHub (`ci_provider` other than `gitlab`) get a weekly
Dependabot configuration for the Python dependencies (minor and patch
updates grouped into one pull request), the dev container features and
the GitHub Actions used by the workflows. Some versions are outside
Dependabot's reach and are updated by template releases instead: the Python
and Poetry versions in `.env` and CI, and the Ruff `rev` in
`.pre-commit-config.yaml`. After Dependabot bumps Ruff, update that `rev`
by hand.

### Design decisions

- **Updatable projects.** The template is meant to be followed, not just
  copied once: answers and the template version are recorded, releases
  are tagged, and changes are kept additive so that `copier update`
  merges cleanly. Files that are yours after generation (`CHANGES.rst`,
  `<project_slug>/__init__.py`, `tests/strategies/__init__.py`) are never
  touched by updates.
- **No unsafe Copier features.** The template uses no tasks, migrations or
  Jinja extensions, so neither `copier copy` nor `copier update` needs
  `--trust`, and nothing runs on your machine besides rendering files.
- **Safe free-text answers.** Names and descriptions may contain quotes,
  backslashes or any Unicode; they are escaped so `pyproject.toml` and
  `__init__.py` stay valid and pass Ruff.
- **One source for each version.** The Python and Poetry versions live in
  `.env` (Docker, Compose, dev container), and the package's metadata in
  `pyproject.toml` (Sphinx reads it).
- **Strict by default.** Strict mypy, Sphinx warnings as errors and checks
  on every push are cheapest to adopt in an empty project.

Usage
------------

### Generate a project

1. [Install Copier](https://copier.readthedocs.io/en/stable/#installation),
   for example with
    ```shell
    pipx install copier
    ```

2. Generate your project, answering the questions
    ```shell
    copier copy gh:GeorgySk/copier-pypackage my_project
    ```
   This uses the latest released version of the template; add
   `--vcs-ref=main` for the development version.

3. Put the project under version control
    ```shell
    cd my_project
    git init
    git add --all
    git commit -m "Initial commit"
    ```

Always generate from the repository URL (not from a local clone or a copy
of the files): the URL and the template version are recorded in the
project's `.copier-answers.yml`, which `copier update` needs.

### Update a project

When a new version of the template is released, run inside the project,
with all changes committed:
```shell
copier update --defaults
```
Copier re-applies the template with your recorded answers and merges the
changes between the template versions into your project, keeping your own
changes. Review the result with `git diff`, resolve any conflict markers,
and commit. Leave out `--defaults` to be asked the questions again (to
change an answer, such as the CI provider).

Never edit `.copier-answers.yml` by hand.

#### Automatic updates

Projects generated with GitHub Actions (CI provider `github` or `both`)
include a `Template update` workflow
(`.github/workflows/template-update.yml`). Every Monday, or when run by
hand from the Actions tab, it runs `copier update --defaults` and, if there
is a new template release, opens a pull request with the changes:

- There is one pull request per release (branch
  `template-update/<version>`). Closing it without merging skips that
  release; the next release gets a new pull request.
- If the update conflicts with your changes, the pull request is opened as
  a draft with the conflict markers committed. Resolve them on its branch.
- The project must have been generated from a URL GitHub can clone (the
  `_src_path` in `.copier-answers.yml`).

By default the workflow uses `GITHUB_TOKEN`, which needs "Allow GitHub
Actions to create and approve pull requests" enabled (Settings → Actions →
General). Pull requests opened with it don't run CI, and updates that
change files in `.github/workflows` can't be pushed. To avoid both, add a
`TEMPLATE_UPDATE_TOKEN` repository secret: a fine-grained personal access
token for the repository with read and write access to Contents, Pull
requests and Workflows. The generated project's `README.md` repeats these
steps.

GitLab-only projects don't get the workflow; update them with
`copier update` as above.

### With Docker
1. Clone the current repository
    ```shell
    git clone https://github.com/GeorgySk/copier-pypackage.git
    cd copier-pypackage
    ```
2. Build the image
    ```shell
    docker compose build
    ```
3. Generate the project into the mounted repository directory, then move
   it out. Running as your own user keeps the files yours.
    ```shell
    docker compose run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp copier-pypackage \
        copier copy gh:GeorgySk/copier-pypackage my_project
    mv my_project ..
    ```
   Copier asks every question. To accept the defaults instead, add
   `--defaults` (and `--data key=value` for any answer you want to set).

   On Windows, the command above works in a WSL terminal but not in
   PowerShell, which has no `id` command and continues lines with a
   backtick instead of `\`. In PowerShell, leave out `--user` and `HOME`.
   Docker Desktop shows files on Windows drives as owned by you anyway:
    ```powershell
    docker compose run --rm copier-pypackage copier copy gh:GeorgySk/copier-pypackage my_project
    mv my_project ..
    ```

Development
-----------

Open the repository in its dev container (`.devcontainer/devcontainer.json`)
or install the dependencies with
`poetry install --with dev --no-root`, then run the tests with `pytest`.

### Bumping version

#### Preparation

Install
[bump-my-version](https://github.com/callowayproject/bump-my-version/tree/master?tab=readme-ov-file#installation) if not running a dev container.

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

This will set version to `major.minor.patch`, commit the change and tag it
`vmajor.minor.patch`. Push the tag:
```bash
git push --follow-tags
```

`copier copy` and `copier update` use the latest such tag, so a template
change reaches users only once it is released.
