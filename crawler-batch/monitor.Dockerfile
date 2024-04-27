FROM ubuntu:jammy

RUN apt-get update && \
    apt-get -y dist-upgrade && \
    apt-get -y install \
      python3 \
      python3-pip && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    pip3 install -U pip && pip3 install -U \
      Flask \
      jsonschema \
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
ENV FLASK_APP /opt/mahjongsoul-sniffer/crawler-batch/monitor

ENTRYPOINT ["flask", "run", "--host=0.0.0.0"]
