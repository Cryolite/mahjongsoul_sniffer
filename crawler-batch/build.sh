#!/usr/bin/env bash

set -euxo pipefail

rm -rf /opt/mahjongsoul-sniffer/*
cp -rf /opt/mahjongsoul-sniffer.orig/* .
protoc --python_out=. mahjongsoul_sniffer/mahjongsoul.proto
touch build.timestamp
