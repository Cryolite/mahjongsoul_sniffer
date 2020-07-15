FROM ubuntu:latest

RUN apt-get update && apt-get install -y \
      ca-certificates \
      fonts-ipafont \
      libnss3-tools \
      protobuf-compiler \
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
      jsonschema \
      mitmproxy \
      pyyaml \
      redis \
      selenium && \
    pip3 install -U protobuf && \
    wget "https://chromedriver.storage.googleapis.com/`wget -O - https://chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip" && \
    unzip chromedriver_linux64.zip -d /usr/local/bin && \
    rm chromedriver_linux64.zip

WORKDIR /mahjongsoul_sniffer

ENTRYPOINT ["./run-with-sniffer.sh", "./mahjongsoul_game_abstract_crawler.py"]
