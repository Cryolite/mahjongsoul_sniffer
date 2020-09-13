FROM ubuntu:latest

RUN apt-get update && apt-get install -y \
      python3 \
      python3-pip && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    pip3 install -U pip && pip3 install -U \
      Flask && \
    useradd -ms /bin/bash ubuntu && \
    mkdir -p /usr/local/share/mahjongsoul-sniffer && \
    chown -R ubuntu /usr/local/share/mahjongsoul-sniffer && \
    mkdir -p /var/log/mahjongsoul-sniffer && \
    chown -R ubuntu /var/log/mahjongsoul-sniffer

USER ubuntu

WORKDIR /opt/mahjongsoul-sniffer

ENV FLASK_APP=/opt/mahjongsoul-sniffer/game-abstract-crawler-monitor

ENTRYPOINT ["flask", "run", "--host=0.0.0.0"]
