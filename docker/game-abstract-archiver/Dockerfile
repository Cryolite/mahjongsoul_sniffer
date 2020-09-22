FROM ubuntu:latest

RUN apt-get update && apt-get install -y \
      python3 \
      python3-pip \
      protobuf-compiler && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    pip3 install -U pip && pip3 install -U \
      boto3 \
      jsonschema \
      pyyaml \
      redis && \
    pip3 install -U protobuf && \
    useradd -ms /bin/bash ubuntu && \
    mkdir -p /var/log/mahjongsoul-sniffer && \
    chown -R ubuntu /var/log/mahjongsoul-sniffer

COPY --chown=ubuntu . /opt/mahjongsoul-sniffer/

USER ubuntu

WORKDIR /opt/mahjongsoul-sniffer

RUN protoc --python_out=. mahjongsoul_sniffer/sniffer/websocket/mahjongsoul.proto

ENV PYTHONPATH /opt/mahjongsoul-sniffer

ENTRYPOINT ["game-abstract-crawler/archiver.py"]
