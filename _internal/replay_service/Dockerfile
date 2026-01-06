FROM python:3.13-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get install -y zip \
 && rm -rf /var/lib/apt/lists/*

COPY backend/ /replay_service/

ENTRYPOINT ["/replay_service/main.py"]
