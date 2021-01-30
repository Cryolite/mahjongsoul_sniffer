#!/usr/bin/env bash

set -euxo pipefail

rm -rf /opt/mahjongsoul-sniffer/*
rm -rf /srv/mahjongsoul-sniffer/*
cp -rf /opt/mahjongsoul-sniffer.orig/* .
protoc --python_out=. mahjongsoul_sniffer/mahjongsoul.proto
(cd api-visualizer/web-server/vue && yarn install && yarn build)
touch build.timestamp
