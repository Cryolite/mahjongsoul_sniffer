FROM ubuntu:jammy

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
      curl \
      protobuf-compiler && \
    curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && \
    apt-get update && apt-get install -y \
      nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    npm install --location=global npm@latest && \
    npm init vue@latest && \
    useradd -ms /bin/bash ubuntu && \
    mkdir -p /opt/mahjongsoul-sniffer && \
    chown -R ubuntu /opt/mahjongsoul-sniffer && \
    mkdir -p /srv/mahjongsoul-sniffer && \
    chown -R ubuntu /srv/mahjongsoul-sniffer

COPY --chown=ubuntu . /opt/mahjongsoul-sniffer.orig/

USER ubuntu

WORKDIR /opt/mahjongsoul-sniffer

ENTRYPOINT ["/opt/mahjongsoul-sniffer.orig/game-detail-crawler/build.sh"]
