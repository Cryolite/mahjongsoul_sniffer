#!/usr/bin/env bash

set -euxo pipefail

python3 -m pip install -U pip

python3 -m pip install -U boto3 boto3-stubs[s3]
python3 -m pip install -U Flask
python3 -m pip install -U jsonschema types-jsonschema
python3 -m pip install -U mitmproxy
python3 -m pip install -U protobuf types-protobuf
python3 -m pip install -U pyyaml types-PyYAML
python3 -m pip install -U redis
python3 -m pip install -U selenium

python3 -m pip install -U mypy
python3 -m pip install -U ruff

sudo apt-get update
sudo apt-get install -y unzip
sudo apt-get clean
sudo rm -rf /var/lib/apt/lists/*

PROTOC_VERSION=$(curl -s "https://api.github.com/repos/protocolbuffers/protobuf/releases/latest" | grep -Po '"tag_name": "v\K[0-9.]+')
curl -Lo protoc.zip "https://github.com/protocolbuffers/protobuf/releases/latest/download/protoc-${PROTOC_VERSION}-linux-x86_64.zip"
sudo unzip -q protoc.zip bin/protoc -d /usr/local/
sudo chmod a+x /usr/local/bin/protoc
rm -rf protoc.zip

protoc --python_out=./ --pyi_out=./ ./mahjongsoul_sniffer/mahjongsoul.proto
