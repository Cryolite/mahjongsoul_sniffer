FROM ubuntu:latest

RUN apt-get update && \
    apt-get -y dist-upgrade && \
    apt-get -y install \
      python3 \
      python3-pip && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    pip3 install -U pip && pip3 install -U \
      boto3 \
      google-api-python-client \
      jsonschema \
      oauth2client \
      pyyaml \
      redis && \
    useradd -ms /bin/bash ubuntu && \
    mkdir /opt/mahjongsoul-sniffer && \
    chown ubuntu /opt/mahjongsoul-sniffer && \
    mkdir /var/log/mahjongsoul-sniffer && \
    chown ubuntu /var/log/mahjongsoul-sniffer

USER ubuntu

WORKDIR /opt/mahjongsoul-sniffer

ENV PYTHONPATH /opt/mahjongsoul-sniffer

ENTRYPOINT ["python3", "crawler-batch/main.py"]
