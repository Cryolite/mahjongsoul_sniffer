FROM ubuntu:latest

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
      npm && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    (npm install -g @vue/cli || true) && \
    (npm install -g @vue/cli-service-global || true) && \
    useradd -ms /bin/bash ubuntu && \
    mkdir -p /usr/local/share/mahjongsoul-sniffer && \
    chown -R ubuntu /usr/local/share/mahjongsoul-sniffer

USER ubuntu

WORKDIR /opt/mahjongsoul-sniffer

ENTRYPOINT ["vue", "build", "game-abstract-crawler-monitor/vue/app.vue", "-d", "/usr/local/share/mahjongsoul-sniffer/game-abstract-crawler-monitor"]
