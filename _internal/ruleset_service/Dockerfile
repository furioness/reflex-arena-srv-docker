FROM debian:12

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get install -y git inotify-tools \
 && rm -rf /var/lib/apt/lists/*

COPY --chmod=+x rulesets_updater.sh /

ENTRYPOINT ["/rulesets_updater.sh"]