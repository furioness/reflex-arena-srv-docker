FROM python:3.14-slim-bookworm


ENV DEBIAN_FRONTEND=noninteractive

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN apt-get update \
 && apt-get upgrade -y

WORKDIR /replay_service/

COPY backend/ ./

RUN uv sync

ENTRYPOINT ["uv", "run", "python", "-m", "src.main"]
