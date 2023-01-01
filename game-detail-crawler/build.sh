#!/usr/bin/env bash

set -euxo pipefail

rm -rf /opt/mahjongsoul-sniffer/*
rm -rf /srv/mahjongsoul-sniffer/*
cp -rf /opt/mahjongsoul-sniffer.orig/* .
protoc --python_out=. mahjongsoul_sniffer/mahjongsoul.proto
pushd game-detail-crawler/monitor
yes 'y' | npm init vue@latest vue || true
cp vue_/src/* vue/src
cp vue_/index.html vue
pushd vue
npm install
npm run build
mv dist /srv/mahjongsoul-sniffer/game-detail-crawler
popd
popd
