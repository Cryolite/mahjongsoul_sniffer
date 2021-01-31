# API Visualizer

## 概要

[雀魂](https://mahjongsoul.com/)の API サーバとゲームクライアントとの間の API のやり取りを可視化する．

![mahjongsoul-sniffer api-visualizer game-example](https://user-images.githubusercontent.com/180041/106376258-e9b47100-63d6-11eb-926c-ba29e2b6b816.png)

![mahjongsoul-sniffer api-visualizer example](https://user-images.githubusercontent.com/180041/106376286-2bddb280-63d7-11eb-8e35-5ad149652e9e.png)

## 必要なもの

- [Docker](https://www.docker.com/) をインストールできる x86_64 ホスト1つ (x86_64 アーキテクチャしかサポートしていない)．雀魂のゲームクライアントを実行しているホストと同じホストでも異なるホストでもどちらでも構わない．

## 実行方法

### 1. Docker をインストールする

[Install Docker Engine](https://docs.docker.com/engine/install/) に記述されている手順に従って Docker をインストールする．

### 2. Docker Compose をインストールする

(Docker Desktop をインストールした場合は Docker Compose が付属しているのでこの手順は不要)

[Install Docker Compose](https://docs.docker.com/compose/install/) に記述されている手順に従って Docker Compose をインストールする．

### 3. mahjongsoul_sniffer リポジトリを git clone する

```bash
$ git clone https://github.com/Cryolite/mahjongsoul_sniffer.git
$ cd mahjongsoul_sniffer
```

### 4. API Visualizer を実行する

カレントディレクトが `api-visualizer` ディレクトリでないと実行に失敗する．

```bash
$ cd api-visualizer
$ docker-compose up
```

ビルドにしばらく時間がかかるので，以下のような出力が表示されて Web サーバが起動するまで待つ．

```
web_server_1  | + flask run --host=0.0.0.0
web_server_1  |  * Serving Flask app "/opt/mahjongsoul-sniffer/api-visualizer/web-server"
web_server_1  |  * Environment: production
web_server_1  |    WARNING: This is a development server. Do not use it in a production deployment.
web_server_1  |    Use a production WSGI server instead.
web_server_1  |  * Debug mode: off
web_server_1  |  * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)
```

### 5. Web サーバにアクセスしてサーバ証明書をダウンロードする

雀魂のゲームクライアントを実行するホストから API Visualizer を実行したホストのポート番号5000に Web ブラウザでアクセスする．以下は API Visualizer を実行したホストの IP アドレスが 192.168.247.129 の場合の例．

![mahjongsoul-sniffer api-visualizer initial](https://user-images.githubusercontent.com/180041/106376020-950ff680-63d4-11eb-8df4-2145bbc54475.png)

`Certificate` をクリックして証明書をダウンロードし，雀魂のゲームクライアントを実行するホストで信頼されたルート証明機関の証明書としてインストールする．

### 6. 雀魂を実行する

API Visualizer を実行したホストのポート番号8080をプロキシとして雀魂のゲームクライアントを起動する．「5. Web サーバにアクセスしてサーバ証明書をダウンロードする」でアクセスした Web ページに雀魂 API のやり取りが表示される．
