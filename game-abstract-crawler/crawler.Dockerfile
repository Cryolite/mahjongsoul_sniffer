FROM ubuntu:jammy

SHELL ["/bin/bash", "-c"]

RUN set -exuo pipefail; \
    apt-get update && apt-get install -y \
      ca-certificates \
      fonts-ipafont \
      jq \
      libnss3-tools \
      python3 \
      python3-pip \
      unzip \
      wget; \
    wget -q -O - 'https://dl-ssl.google.com/linux/linux_signing_key.pub' | apt-key add -; \
    echo 'deb http://dl.google.com/linux/chrome/deb/ stable main' >> /etc/apt/sources.list.d/google.list; \
    apt-get update; \
    DEBIAN_FRONTEND=noninteractive apt-get install -y google-chrome-stable; \
    apt-get clean && rm -rf /var/lib/apt/lists/*; \
    pip3 install -U pip && pip3 install -U \
      boto3 \
      jsonschema \
      mitmproxy \
      pyyaml \
      redis \
      selenium; \
    wget "$(wget -qO - 'https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json' | jq -r '.channels.Stable.downloads.chromedriver[]|select(.platform == "linux64").url')"; \
    unzip chromedriver-linux64.zip -d /usr/local/bin; \
    rm chromedriver-linux64.zip; \
    useradd -ms /bin/bash ubuntu; \
    mkdir -p /opt/mahjongsoul-sniffer; \
    chown -R ubuntu /opt/mahjongsoul-sniffer; \
    mkdir -p /var/log/mahjongsoul-sniffer; \
    chown -R ubuntu /var/log/mahjongsoul-sniffer

USER ubuntu

WORKDIR /opt/mahjongsoul-sniffer

ENV PYTHONPATH=/opt/mahjongsoul-sniffer
ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

ENTRYPOINT ["bin/run-with-sniffer", "game-abstract-crawler/sniffer.py", "game-abstract-crawler/crawler.py"]
