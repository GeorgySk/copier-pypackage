Changelog
=========

All notable changes to this template are documented in this file.
The format is based on `Keep a Changelog <https://keepachangelog.com/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/>`_.

Unreleased
----------

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
