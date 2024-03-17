ARG PYTHON_IMAGE_VERSION

FROM python:${PYTHON_IMAGE_VERSION}

ARG POETRY_VERSION
ARG DEV_IMAGE

WORKDIR /opt/cookiecutter-pypackage

RUN pip install "poetry==${POETRY_VERSION}" && \
    poetry config virtualenvs.create false

COPY README.md .
COPY tests/ tests/
COPY {{cookiecutter.project_slug}}/ {{cookiecutter.project_slug}}/
COPY pyproject.toml .
COPY hooks/ hooks/

RUN if [ "${DEV_IMAGE}" = "true" ]; then \
        poetry install; \
    elif [ "${DEV_IMAGE}" = "false" ]; then \
        poetry install --without dev; \
    else \
        echo "Invalid value specified for DEV_IMAGE: '${DEV_IMAGE}'"; \
        exit 1; \
    fi