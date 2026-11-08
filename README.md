copier-pypackage
================

[![CI](https://github.com/GeorgySk/copier-pypackage/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/GeorgySk/copier-pypackage/actions/workflows/ci.yml "CI")
[![](https://img.shields.io/github/license/GeorgySk/copier-pypackage.svg)](https://github.com/GeorgySk/copier-pypackage/blob/main/LICENSE "License")

Summary
-------

Copier-pypackage is a [Copier](https://copier.readthedocs.io) template for developing a Python library using such tools as Docker, Poetry, bump-my-version, pytest, pytest-cov, and Hypothesis library for testing.

Projects generated from it can later pull in improvements to the template with `copier update`.

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
