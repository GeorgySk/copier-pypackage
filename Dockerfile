ARG PYTHON_IMAGE_VERSION
ARG IMAGE_TYPE

FROM python:${PYTHON_IMAGE_VERSION} AS base
ARG POETRY_VERSION

WORKDIR /opt/copier-pypackage

# An environment variable, unlike `poetry config`, applies to every user,
# including the dev container's non-root user.
ENV POETRY_VIRTUALENVS_CREATE=false
RUN pip install "poetry==${POETRY_VERSION}"

COPY README.md LICENSE pyproject.toml poetry.lock ./
COPY copier.yml macros.jinja ./
COPY template/ template/

FROM base AS prod
RUN poetry install --no-root

FROM base AS dev
RUN poetry install --with dev --no-root

FROM ${IMAGE_TYPE}
