cookiecutter-pypackage
===========


[![](https://travis-ci.org/LostFan123/npd.svg?branch=master)](https://travis-ci.org/LostFan123/npd "Travis CI")
[![](https://codecov.io/gh/LostFan123/npd/branch/master/graph/badge.svg)](https://codecov.io/gh/LostFan123/npd "Codecov")
[![](https://img.shields.io/github/license/LostFan123/npd.svg)](https://github.com/LostFan123/npd/blob/master/LICENSE "License")
[![](https://badge.fury.io/py/npd.svg)](https://badge.fury.io/py/npd "PyPI")

Summary
-------

Cookiecutter-pypackage is a Cookiecutter template for developing a Python library using such tools as Docker, Docker
Compose, Poetry, bump-my-version, pytest, pytest-cov, and Hypothesis library for testing.

---

In what follows `python` is an alias for `python3.8` or any later
version.

Usage
------------

### Without Docker

1. [Install Cookiecutter](https://github.com/cookiecutter/cookiecutter?tab=readme-ov-file#installation)

2. Clone the current repository
    ```shell
    git clone https://github.com/GeorgySk/cookiecutter-pypackage.git
    cd cookiecutter-pypackage
    ```
3. Run Cookiecutter
    ```shell
    cookiecutter cookiecutter-pypackage/
    ```

### With Docker
...

Development
-----------
...

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


### Running tests
...