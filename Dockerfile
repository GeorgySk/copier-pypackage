ARG PYTHON_IMAGE_VERSION

FROM python:${PYTHON_IMAGE_VERSION}

ARG POETRY_VERSION
ARG ENVIRONMENT

WORKDIR /opt/cookiecutter-pypackage

COPY pyproject.toml .
COPY README.md .
COPY tests/ tests/
COPY hooks/ hooks/
COPY {{cookiecutter.project_slug}}/ {{cookiecutter.project_slug}}/

RUN pip install --upgrade pip
RUN if [ "${ENVIRONMENT}" = "development" ]; then \
        pip install "poetry==${POETRY_VERSION}" && \
        poetry config virtualenvs.create false && \
        poetry install; \
    elif [ "${ENVIRONMENT}" = "production" ]; then \
        pip install -e .; \
    else \
        echo "Invalid environment specified: '${POETRY_VERSION}'"; \
        exit 1; \
    fi