#!/usr/bin/env bash

set -euxo pipefail

rm -rf /opt/mahjongsoul-sniffer/*
rm -rf /srv/mahjongsoul-sniffer/*
cp -rf /opt/mahjongsoul-sniffer.orig/* .
protoc --python_out=. mahjongsoul_sniffer/mahjongsoul.proto
vue build game-abstract-crawler/monitor/vue/app.vue -d /srv/mahjongsoul-sniffer/game-abstract-crawler
