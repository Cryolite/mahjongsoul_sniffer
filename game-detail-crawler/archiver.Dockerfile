FROM ubuntu:jammy

RUN apt-get update && apt-get install -y \
      python3 \
      python3-pip && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    pip3 install -U pip && pip3 install -U \
      boto3 \
      jsonschema \
      protobuf \
      pyyaml \
      redis && \
    useradd -ms /bin/bash ubuntu && \
    mkdir -p /opt/mahjongsoul-sniffer && \
    chown -R ubuntu /opt/mahjongsoul-sniffer && \
    mkdir -p /var/log/mahjongsoul-sniffer && \
    chown -R ubuntu /var/log/mahjongsoul-sniffer

USER ubuntu

WORKDIR /opt/mahjongsoul-sniffer

ENV PYTHONPATH /opt/mahjongsoul-sniffer

# Workaround until `build.Dockerfile` uses protoc 3.19.0 or above.
ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION python

ENTRYPOINT ["game-detail-crawler/archiver.py"]
