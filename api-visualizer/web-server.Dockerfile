FROM ubuntu:latest

RUN apt-get update && apt-get install -y \
      protobuf-compiler \
      python3 \
      python3-pip && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    pip3 install -U pip && pip3 install -U \
      Flask \
      jsonschema \
      mitmproxy \
      pyyaml \
      redis && \
    useradd -ms /bin/bash ubuntu && \
    mkdir -p /opt/mahjongsoul-sniffer && \
    chown -R ubuntu /opt/mahjongsoul-sniffer && \
    mkdir -p /var/log/mahjongsoul-sniffer && \
    chown -R ubuntu /var/log/mahjongsoul-sniffer && \
    mkdir -p /srv/mahjongsoul-sniffer && \
    chown -R ubuntu /srv/mahjongsoul-sniffer

USER ubuntu

WORKDIR /opt/mahjongsoul-sniffer

ENV PYTHONPATH /opt/mahjongsoul-sniffer
ENV FLASK_APP /opt/mahjongsoul-sniffer/api-visualizer/web-server

ENTRYPOINT ["api-visualizer/run-web-server.sh"]
