Changelog
=========

All notable changes to this template are documented in this file.
The format is based on `Keep a Changelog <https://keepachangelog.com/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/>`_.

Unreleased
----------

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
