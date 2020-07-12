#!/usr/bin/env bash


set -uxo pipefail

# mitmproxy を起動する．
AWS_PROFILE=mahjongsoul-sniffer mitmdump -q -s mahjongsoul_sniffer.py &
sleep 5

# 一度 mitmproxy を起動すると ~/.mitmproxy ディレクトリが作成されるので，そこに
# 作成される mitmproxy の証明書をシステムにインストールする．
openssl x509 -in ~/.mitmproxy/mitmproxy-ca-cert.pem -inform PEM -out /usr/local/share/ca-certificates/mitmproxy-ca-cert.crt
update-ca-certificates

# Headless Chrome を起動してすぐに終了する．
./run-chromedriver-once.py

# 一度 Chrome を起動すると ~/.pki/nssdb ディレクトリが作成されるので，そこに
# 作成される証明書ストアに mitmproxy の証明書をインストールする．
certutil -A -n mitmproxy -t 'TCu,Cu,Tu' -i /usr/local/share/ca-certificates/mitmproxy-ca-cert.crt -d "sql:$HOME/.pki/nssdb"

# mitmproxy をプロキシとして対象のプログラムを起動する．
http_proxy='http://localhost:8080' https_proxy='https://localhost:8080' "$1"
