#!/usr/bin/env bash

set -uxo pipefail

protobuf_latest_releases_url='https://github.com/protocolbuffers/protobuf/releases/latest'

function print_error_message ()
{
  if [[ -t 2 ]] && type -t tput >/dev/null; then
    if (( "$(tput colors)" == 256 )); then
      echo "$(tput setaf 9)$1$(tput sgr0)" >&2
    else
      echo "$(tput setaf 1)$1$(tput sgr0)" >&2
    fi
  else
    echo "$1" >&2
  fi
}

if [[ $(uname -o) != GNU/Linux ]]; then
  print_error_message "Only support for Linux."
  exit 1
fi

tempdir=$(mktemp -d)
trap "rm -rf '$tempdir'" EXIT

if which wget >/dev/null 2>&1; then
  wget -O - "$protobuf_latest_releases_url" >"$tempdir/protobuf_latest_releases_page"
elif which curl >/dev/null 2>&1; then
  curl -L "$protobuf_latest_releases_url" >"$tempdir/protobuf_latest_releases_page"
else
  print_error_message "Either \`wget' or \`curl' is required."
  exit 1
fi
if (( $? != 0 )); then
  print_error_message 'Failed to download Protocol Buffers latest releases page.'
  exit 1
fi

architecture="$(uname -i)"
grep -Eo "protoc-[[:digit:]]+\.[[:digit:]]+\.[[:digit:]]+-linux-$architecture.zip" "$tempdir/protobuf_latest_releases_page" >"$tempdir/protoc_basenames"
if (( $? != 0 )); then
  print_error_message 'Failed to extract .zip file basename of Protocol Buffers compiler.'
  exit 1
fi

grep -Eo '[[:digit:]]+\.[[:digit:]]+\.[[:digit:]]+' "$tempdir/protoc_basenames" >"$tempdir/protoc_versions"
if (( $? != 0 )); then
  print_error_message 'Failed to extract release versions of Protocol Buffers compiler.'
  exit 1
fi

LANG=C.UTF-8 sort -V "$tempdir/protoc_versions" | tail -n 1 >"$tempdir/protoc_version"

protoc_version=$(< "$tempdir/protoc_version")
protoc_basename="protoc-$protoc_version-linux-$architecture.zip"
protoc_url="https://github.com/protocolbuffers/protobuf/releases/download/v$protoc_version/$protoc_basename"

if which wget >/dev/null 2>&1; then
  (cd "$tempdir" && wget "$protoc_url")
elif which curl >/dev/null 2>&1; then
  (cd "$tempdir" && curl -o "$protoc_basename" -L "$protoc_url")
else
  print_error_message "Either \`wget' or \`curl' is required."
  exit 1
fi

python3 -m venv .local
. .local/bin/activate
pip install -U pip
pip install -U setuptools
pip install -U wheel
pip install -U pyyaml
pip install -U jsonschema
pip install -U mitmproxy
pip install -U protobuf

unzip "$tempdir/$protoc_basename" -d .local
protoc --python_out=. mahjongsoul_sniffer/sniffer/websocket/mahjongsoul.proto
