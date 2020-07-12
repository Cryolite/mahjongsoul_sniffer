FROM ubuntu:latest

RUN apt-get update && apt-get install -y \
      ca-certificates \
      git \
      libnss3-tools \
      python3 \
      python3-pip \
      unzip \
      wget && \
    wget -q -O - 'https://dl-ssl.google.com/linux/linux_signing_key.pub' | apt-key add - && \
    echo 'deb http://dl.google.com/linux/chrome/deb/ stable main' >> /etc/apt/sources.list.d/google.list && \
    apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y google-chrome-stable && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    pip3 install -U pip && pip3 install -U \
      pyyaml \
      jsonschema \
      mitmproxy \
      boto3 \
      selenium && \
    pip3 install -U protobuf && \
    git clone 'https://github.com/Cryolite/mahjongsoul_sniffer.git' && \
    /mahjongsoul_sniffer/install-protoc.sh && \
    /mahjongsoul_sniffer/install-chromedriver.sh && \
    protoc --python_out=. mahjongsoul_sniffer/mahjongsoul_sniffer/sniffer/websocket/mahjongsoul.proto

WORKDIR /mahjongsoul_sniffer

ENTRYPOINT ["./run-with-sniffer.sh", "./mahjongsoul_game_abstract_crawler.py"]
