Changelog
=========

All notable changes to this template are documented in this file.
The format is based on `Keep a Changelog <https://keepachangelog.com/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/>`_.

Unreleased
----------

0.28.3 (2026-11-10)
------------------------------

Changed
~~~~~~~

- The generated project's Ruff config selects every rule
  (``select = ["ALL"]``). A few are ignored, each with a comment giving the
  reason: ``COM812``, ``B905``, ``CPY001``, ``TC002``, ``D401``, ``D212``,
  ``D203``, ``EM101``, ``EM102``, ``TRY003`` and ``RUF001``–``RUF003``.
  ``tests/`` and ``docs/`` have their own per-file ignores, and so does
  the package's ``__init__.py``, whose docstring and strings come from the
  prompt answers: ``D205``, ``D301``, ``D404``, ``PLE2502`` and
  ``PLE2515``. The template repository's own Ruff config follows suit.
- When the short description is too long for one line, the docstring of
  the generated package's ``__init__.py`` starts on the line after the
  opening quotes and ends with the closing quotes on their own line.

Fixed
~~~~~

- The generated ``docs/source/conf.py`` is no longer executable, and it
  finds the project root with ``pathlib`` instead of ``os.path``.

0.28.2 (2026-11-08)
------------------------------

Added
~~~~~

- The README explains how to run the Docker generation command from
  Windows PowerShell, and that Copier asks every question unless
  ``--defaults`` is passed.

0.28.1 (2026-11-08)
------------------------------

Added
~~~~~

- The generated ``README.md`` has a supported Python versions badge (from
  PyPI) and a "Made with Copier" badge linking to this template.

Changed
~~~~~~~

- The GitHub Actions badge in the generated ``README.md`` shows the status
  of the ``main`` branch instead of the latest run on any branch.
- The generated ``README.md`` has no license badge when the license is
  "Not open source".

Fixed
~~~~~

- The template's ``LICENSE`` named Audrey Roy Greenfeld in the
  non-endorsement clause; it now refers to the copyright holder.

0.28.0 (2026-11-08)
------------------------------

Added
~~~~~

- Generated projects that use GitHub Actions get a ``Template update``
  workflow (``.github/workflows/template-update.yml``). Every Monday, or
  when run by hand, it runs ``copier update`` and opens a pull request for a
  new template release: one pull request per release, as a draft when
  there are conflicts to resolve. An optional ``TEMPLATE_UPDATE_TOKEN``
  secret lets the pull request run CI and update workflow files (see the
  generated ``README.md``).

0.27.1 (2026-11-08)
------------------------------

0.27.0 (2026-11-08)
------------------------------

Added
~~~~~

- Generated projects can pull in later template releases with
  ``copier update``: answers and the template version are recorded in
  ``.copier-answers.yml``. ``CHANGES.rst``, ``<project_slug>/__init__.py``
  and ``tests/strategies/__init__.py`` belong to the project and are never
  touched by updates. The generated ``README.md`` explains how to update.
- Releases of the template are tagged ``vX.Y.Z`` (``bump-my-version`` now
  commits and tags), which is how Copier finds template versions.

Changed
~~~~~~~

- **Breaking:** the template is now a `Copier <https://copier.readthedocs.io>`_
  template instead of a Cookiecutter one. Generate projects with
  ``copier copy gh:GeorgySk/copier-pypackage <directory>``. The generated
  files are the same as before.
- **Breaking:** ``use_devcontainer`` and ``use_docker_compose`` are yes/no
  booleans instead of the strings ``"yes"`` and ``"no"`` (pass ``true`` or
  ``false`` with ``--data``).
- An invalid ``project_slug`` is asked again instead of aborting generation.
- ``poetry_version`` is no longer a question: generated projects always use
  the template's Poetry version, and ``copier update`` brings in new ones.
- The repository is renamed from ``cookiecutter-pypackage`` to
  ``copier-pypackage``, and its container workspace from
  ``/opt/cookiecutter-pypackage`` to ``/opt/copier-pypackage``.

Removed
~~~~~~~

- Cookiecutter support (``cookiecutter.json``, ``hooks/`` and
  ``local_extensions.py``). To generate with Cookiecutter, use version
  0.26.0 or earlier.

Fixed
~~~~~

- The dev container's ``setup_user.sh`` failed when the container user
  already had the workspace owner's uid and gid (the dev container CLI sets
  them on Linux), or when a group with that gid already existed. It now
  changes only what differs and reuses existing groups.
- The dev container's ``onCreateCommand`` failed on Windows hosts with
  ``usermod: UID '1000' already exists``. ``remoteUser`` was
  ``${localEnv:USER}``, which is empty on Windows, so ``setup_user.sh`` ran
  as root and tried to give root the workspace owner's uid. Both dev
  containers now use the ``vscode`` user that the ``common-utils`` feature
  creates, and ``setup_user.sh`` never changes root's ids.

0.26.0 (2026-11-08)
------------------------------

Changed
~~~~~~~

- With ``use_devcontainer=yes`` and ``use_docker_compose=yes``, the
  generated dev container now runs the ``compose.yaml`` service (the
  ``Dockerfile``'s ``dev`` stage) instead of a separate image with the
  Poetry feature, so Python and Poetry versions are set only in ``.env``.
  Dependencies are installed when the image is built; rebuild the container
  or run ``poetry install`` after changing them.
- The template's own dev container works the same way and takes its Python
  and Poetry versions from ``.env``.

0.25.2 (2026-11-08)
------------------------------

0.25.1 (2026-11-08)
------------------------------

Changed
~~~~~~~

- The default ``poetry_version`` for generated projects is now 2.5.1
  (was 2.1.4). The template's own Docker image and dev container use Poetry
  2.5.1 as well (was 2.3.1).

0.25.0 (2026-11-07)
------------------------------

Added
~~~~~

- Generated projects are type-checked with mypy in strict mode: in the
  ``lint`` CI job (GitHub and GitLab) and as a pre-commit hook. They also
  ship a ``py.typed`` marker, so projects that use the package get its type
  hints.

0.24.0 (2026-11-07)
------------------------------

Fixed
~~~~~

- A ``project_short_description`` longer than about 70 characters made the
  generated package fail ``ruff check`` (line too long). The docstring in
  the package's ``__init__.py`` is now wrapped.
- A ``full_name`` or ``email`` with more double than single quotes made the
  generated package fail ``ruff format --check`` and its pre-commit hook.
  These values are now written with the quotes Ruff prefers.

0.23.0 (2026-11-07)
------------------------------

Changed
~~~~~~~

- ``python_version`` is now a choice between 3.11, 3.12, 3.13 and 3.14,
  defaulting to 3.11. The previous default, 3.10, has reached end of life,
  and free text allowed values that broke the CI test matrix.
- The generated docs read ``pyproject.toml`` with the standard library's
  ``tomllib``, so the ``docs`` dependency group no longer needs ``tomli``.
- Running the template now requires Python 3.11 or later.

0.22.0 (2026-11-07)
------------------------------

Added
~~~~~

- Generated projects get a ``docs`` CI job (GitHub and GitLab) that builds
  the Sphinx docs with warnings treated as errors. Publishing to PyPI and
  the container registry waits for it.

Fixed
~~~~~

- The generated API docs page tried to import a nonexistent
  ``<slug>.<slug>`` module, so it came out empty. It now documents the
  package itself.
- Title underlines in the generated docs had a fixed length, so most project
  names triggered "Title underline too short" warnings. The index page now
  uses ``project_name`` as its only title.
- ``version`` and ``release`` were swapped in the generated ``conf.py``.

0.21.0 (2026-11-07)
------------------------------

Fixed
~~~~~

- The ``prod`` Docker image failed to build because Poetry tried to install
  the template repo as a package.
- The Docker image now includes ``poetry.lock``, so dependency versions match
  the lock file, and ``cookiecutter.json`` and ``local_extensions.py``, so it
  can render the template without the repository mounted.
- The README badges pointed at an unrelated project. They now show this
  repository's CI status and license.

0.20.0 (2026-11-07)
------------------------------

Changed
~~~~~~~

- Generation now stops with a clear error, before any file is written, when
  ``project_slug`` isn't a valid package name: lowercase ASCII letters,
  digits and underscores, not starting with a digit and not a Python
  keyword. Previously names like "2D Tools" produced a package that couldn't
  be imported.

Fixed
~~~~~

- Quotes and backslashes in ``full_name``, ``email`` and
  ``project_short_description`` no longer break the generated
  ``pyproject.toml`` and package ``__init__.py``.
- Choosing "Not open source" produced an empty ``LICENSE``. It now contains
  a copyright notice with "All rights reserved."
- The BSD ``LICENSE`` no longer starts with a blank line.

0.19.0 (2026-11-07)
------------------------------

Added
~~~~~

- ``ci_provider`` prompt (``github``, ``gitlab``, ``both`` or ``none``) and
  CI/CD configs for generated projects: ``.github/workflows/ci.yml`` and
  ``.gitlab-ci.yml``. Both lint with Ruff, run the tests with coverage on
  every Python version from ``python_version`` to 3.14, and build the
  package. On final release tags (``vX.Y.Z``) they publish to PyPI and, with
  ``use_docker_compose=yes``, push the ``prod`` Docker image to GHCR or the
  GitLab container registry. With ``both``, only GitHub publishes to PyPI.
- Generated projects tag releases as ``vX.Y.Z`` when ``bump-my-version``
  commits (``use_devcontainer=yes``).
- Dependabot keeps GitHub Actions up to date in generated projects that use
  GitHub CI.

Changed
~~~~~~~

- README badges and links in generated projects follow ``ci_provider``
  (GitHub Actions + Codecov, or GitLab pipeline + coverage) and point at the
  ``main`` branch instead of ``master``.

Fixed
~~~~~

- The "Running tests" section of the generated README referred to a
  nonexistent ``requirements-tests.txt``. It now uses
  ``poetry install --with dev`` and ``poetry run pytest``, and the Docker
  command uses ``docker compose`` instead of the old ``docker-compose``.

0.18.0 (2026-11-07)
------------------------------

Added
~~~~~

- ``CHANGES.rst`` changelog for the template and for generated projects.
  In generated projects it is included in the Sphinx docs, and
  ``bump-my-version bump release`` turns its "Unreleased" section into a
  dated version section.

0.17.0 (2026-11-07)
------------------------------

Removed
~~~~~~~

- Unused ``create_author_file`` prompt.
- ``MANIFEST.in`` from generated projects: Poetry does not read it.

Fixed
~~~~~

- ``use_devcontainer=no`` no longer renders ``commit = true`` in
  ``.bumpversion.toml`` or a ``devcontainers`` entry in ``dependabot.yml``.
- ``use_docker_compose=no``: ``bump-my-version`` no longer fails on the
  missing ``compose.yaml``, ``.env`` is removed along with the other Docker
  files, and the README no longer shows Docker instructions.
- The generated dev container now runs ``setup_user.sh`` from the project's
  own path instead of the template repo's path.
- ``authors`` and ``description`` in the generated ``pyproject.toml`` now use
  the ``full_name``, ``email`` and ``project_short_description`` prompts
  instead of hardcoded values.
- The Codecov badge in the generated README now points at the project instead
  of an unrelated repository.
