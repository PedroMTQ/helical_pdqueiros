FROM python:3.11.3-bullseye AS build

# installs uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
# This makes sure that logs show up immediately instead of being buffered
ENV PYTHONUNBUFFERED=1

WORKDIR /opt/airflow/app
COPY ./uv.lock /opt/airflow/app/uv.lock
COPY ./pyproject.toml /opt/airflow/app/pyproject.toml
COPY ./README.md /opt/airflow/app/README.md

# Extract version and add to a __version__ file which will be read by the service later
RUN echo $(grep -m 1 'version' /opt/airflow/app/pyproject.toml | sed -E 's/version = "(.*)"/\1/') > /opt/airflow/app/__version__

# copying source code
COPY ./src/ /opt/airflow/app/src/
# installs package
RUN uv sync --frozen
ENV PATH="/opt/airflow/app/.venv/bin:$PATH"


# Final
FROM build
RUN apt autoremove -y && apt clean -y






