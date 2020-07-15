FROM ubuntu:latest

RUN apt-get update && apt-get install -y \
      python3 \
      python3-pip && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    pip3 install -U pip && pip3 install -U \
      boto3 \
      jsonschema \
      pyyaml \
      redis

WORKDIR /mahjongsoul_sniffer

ENTRYPOINT ["bin/game_abstract_archiver.py"]
