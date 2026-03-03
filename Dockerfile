ARG PYTHON_IMAGE_VERSION
ARG IMAGE_TYPE

FROM python:${PYTHON_IMAGE_VERSION} AS base
ARG POETRY_VERSION

WORKDIR /opt/cookiecutter-pypackage

RUN pip install "poetry==${POETRY_VERSION}" && \
    poetry config virtualenvs.create false

COPY README.md .
COPY {{cookiecutter.project_slug}}/ {{cookiecutter.project_slug}}/
COPY pyproject.toml .
COPY hooks/ hooks/
COPY LICENSE .

FROM base AS prod
RUN poetry install

FROM base AS dev
RUN poetry install --with dev

FROM ${IMAGE_TYPE}
