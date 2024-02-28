FROM ubuntu:latest

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
      curl \
      gnupg \
      protobuf-compiler && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get update && apt-get install -y --no-install-recommends nodejs && \
    curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - && \
    echo 'deb https://dl.yarnpkg.com/debian/ stable main' >/etc/apt/sources.list.d/yarn.list && \
    apt-get update && apt-get install -y yarn && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    useradd -ms /bin/bash ubuntu && \
    mkdir -p /opt/mahjongsoul-sniffer && \
    chown -R ubuntu /opt/mahjongsoul-sniffer && \
    mkdir -p /srv/mahjongsoul-sniffer && \
    chown -R ubuntu /srv/mahjongsoul-sniffer

COPY --chown=ubuntu . /opt/mahjongsoul-sniffer.orig/

USER ubuntu

WORKDIR /opt/mahjongsoul-sniffer

ENTRYPOINT ["/opt/mahjongsoul-sniffer.orig/api-visualizer/build.sh"]
