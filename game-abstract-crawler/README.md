# Game Abstract Crawler

## 概要

[雀魂](https://mahjongsoul.com/)の「観戦」機能から対局 UUID (金の間以上の段位戦，四麻のみ) をクロールして [Amazon S3](https://aws.amazon.com/jp/s3/) に保存する．

![mahjongsoul-s3-bucket-game-abstract](https://user-images.githubusercontent.com/180041/106374841-04ccb400-63ca-11eb-8c53-bc139e3f3dc5.png)

## 必要なもの

- 雀魂アカウントを作成するためのメールアドレス1つ
- [Amazon Web Services](https://aws.amazon.com/) のアカウント1つ
- 雀魂へログインする際に Yostar から送られてくる「認証コード」が書かれたメールを Amazon S3 のオブジェクトとして保存する何らかの実装
- [Docker](https://www.docker.com/) をインストールできる x86_64 マシン1つ (x86_64 アーキテクチャしかサポートしていません)

## 実行方法

### 1. 対局 UUID をクロールするための雀魂アカウントを作成する

(メールアドレスによる Yostar ログインにのみ対応しています． Google や Twitter のサービス ID によるログインには対応していません．)

使用したメールアドレスを控えておく．

### 2. クロール結果を保存するための S3 バケットを作成する

(既存の S3 バケットを使用する場合，この手順は不要)

作成した S3 バケット名を控えておく．

### 3. S3 バケットにアクセスするためのユーザーを AWS Identity and Access Management (IAM) で作成する

(既存の IAM ユーザーを使用する場合，この手順は不要)

[AWS Identity and Access Management (IAM)](https://aws.amazon.com/iam/) で Amazon S3 に接続するための (ポリシーとグループと) ユーザーを作成する．
必要な権限は「2. クロール結果を保存するための S3 バケットを作成する」で作成した S3 バケットの全オブジェクトに対する `s3:PutObject`, `s3:GetObject`, および `s3:DeleteObject` のみ．

作成した IAM ユーザーのアクセスキー ID とシークレットアクセスキーを控えておく．

### 4. Yostar からの認証コードメールを S3 バケットへ転送するよう実装

雀魂へログインする際に Yostar から「1. 対局 UUID をクロールするための雀魂アカウントを作成する」で使用したメールアドレスへ送られてくる「認証コード」が書かれたメールを，「2. クロール結果を保存するための S3 バケットを作成する」で作成した S3 バケットの適当なプレフィックス下に保存する実装を行う．実装の内容は問わない．具体的な実装例として， [Amazon Simple Email Service](https://aws.amazon.com/jp/ses/) でメールアドレスのドメインを管理して https://aws.amazon.com/jp/premiumsupport/knowledge-center/ses-receive-inbound-emails/ を使う，等が挙げられる．

メールが保存される S3 バケットのプレフィックスを控えておく．

### 5. Docker をインストールする

[Install Docker Engine](https://docs.docker.com/engine/install/) に記述されている手順に従って Docker をインストールする．

### 6. Docker Compose をインストールする

(Docker Desktop をインストールした場合は Docker Compose が付属しているのでこの手順は不要)

[Install Docker Compose](https://docs.docker.com/compose/install/) に記述されている手順に従って Docker Compose をインストールする．

### 7. AWS の認証情報ファイルを作成する

適当なディレクトリ (`~/.aws` ディレクトリでなくても良い) を作成しそこに AWS の認証情報ファイル `credentials` を作成する．
「3. S3 バケットにアクセスするためのユーザーを AWS Identity and Access Management (IAM) で作成する」で控えておいた IAM ユーザーのアクセスキー ID とシークレットアクセスキーを `credentials` ファイルに設定する．
(同じディレクトリに `config` ファイルを作成すれば， AWS の構成設定も可能)
AWS 認証情報ファイル `credentials` と構成設定ファイル `config` の詳細については
[Configuration and credential file settings](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html) を参照すること．

作成したディレクトリの絶対パスとプロファイル名を控えておく．

### 8. mahjongsoul_sniffer リポジトリを git clone する

```bash
$ git clone https://github.com/Cryolite/mahjongsoul_sniffer.git
$ cd mahjongsoul_sniffer
```

### 9. game-abstract-crawler の設定ファイルを書き換える

`game-abstract-archiver/config.yaml` を以下のように書き換える．

- `yostar_login` > `email_address` キーの値を「1. 対局 UUID をクロールするための雀魂アカウントを作成する」で使用したメールアドレスに書き換える．
- `s3` > `bucket_name` キーの値を「2. クロール結果を保存するための S3 バケットを作成する」で作成した S3 バケット名に書き換える．
- `s3` > `authentication_email_key_prefix` キーの値を「4. Yostar からの認証コードメールを S3 バケットへ転送するよう実装」で指定したプレフィックスに書き換える．

### 10. Game Abstract Crawler を実行する

- `${DOT_AWS_DIR}`: 「7. AWS の認証情報ファイルを作成する」で作成したディレクトリの絶対パス，
- `${AWS_PROFILE}`: 「7. AWS の認証情報ファイルを作成する」で作成した認証情報ファイルのプロファイル名，

として以下のコマンドを実行する．カレントディレクトが `game-abstract-crawler` ディレクトリでないと実行に失敗する．

```bash
$ cd game-abstract-crawler
$ DOT_AWS_DIR=${DOT_AWS_DIR} AWS_PROFILE=${AWS_PROFILE} docker-compose up
```

## 実装概念図

![mahjongsoul-sniffer game-crawler architecture](https://user-images.githubusercontent.com/180041/106375535-3cd6f580-63d0-11eb-9654-4da90d8be3f7.png)
