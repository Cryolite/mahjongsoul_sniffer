FROM ubuntu:jammy

RUN apt-get update && \
    apt-get -y dist-upgrade && \
    apt-get -y install \
      protobuf-compiler && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    useradd -ms /bin/bash ubuntu && \
    mkdir /opt/mahjongsoul-sniffer && \
    chown ubuntu /opt/mahjongsoul-sniffer

COPY --chown=ubuntu . /opt/mahjongsoul-sniffer.orig/

USER ubuntu

WORKDIR /opt/mahjongsoul-sniffer

ENTRYPOINT ["/opt/mahjongsoul-sniffer.orig/crawler-batch/build.sh"]
