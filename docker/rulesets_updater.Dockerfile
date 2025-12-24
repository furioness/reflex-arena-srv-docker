FROM debian:12

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get install -y git inotify-tools \
 && rm -rf /var/lib/apt/lists/*
