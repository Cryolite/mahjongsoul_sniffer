#!/usr/bin/env bash

set -euo pipefail

# `build` が `/opt/mahjongsoul-sniffer/*` を削除するまで待つ．
sleep 10

# ビルドが終了するまで待つ．
while [[ ! -f build.timestamp ]]; do sleep 1; done

set -x

# `api-visualizer/sniffer.py` を addon として mitmproxy を起動する．
mitmdump -qs api-visualizer/sniffer.py &
sleep 10

# 一度 mitmproxy を起動すると `~/.mitmproxy` ディレクトリが作成されるので，
# そこに作成される mitmproxy の証明書を Web server が読める場所にコピーする．
openssl x509 -in ~/.mitmproxy/mitmproxy-ca-cert.pem -inform PEM \
        -out api-visualizer/web-server/vue/dist/mitmproxy-ca-cert.crt

# Web server を起動する．
flask run --host=0.0.0.0
