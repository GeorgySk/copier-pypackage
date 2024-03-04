ARG PYTHON_IMAGE_VERSION

FROM python:${IMAGE_VERSION}

ARG POETRY_VERSION
ARG ENVIRONMENT

WORKDIR /opt/{{ cookiecutter.project_slug }}

COPY pyproject.toml .
COPY README.md .
COPY {{ cookiecutter.project_slug }}/ {{ cookiecutter.project_slug }}/
COPY tests/ tests/

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
