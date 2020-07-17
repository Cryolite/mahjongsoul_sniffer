# mahjongsoul_sniffer

## 主な機能

- `game_abstract_crawler`: [雀魂](https://mahjongsoul.com/)の「観戦」機能から対局 UUID （金の間以上の段位戦のみ）をクロールして [Amazon S3](https://aws.amazon.com/jp/s3/) に保存する．
- `game_detail_crawler`: [実装中]`game_abstract_crawler` でクロールした各対局（四麻のみ）の牌譜全体をダウンロード・解析して Amazon S3 に保存する．

## game_abstract_crawler

### 動作に必要なもの

- 雀魂アカウントを作成するためのメールアドレス1つ
- [Amazon Web Services](https://aws.amazon.com/) のアカウント1つ
- [Docker](https://www.docker.com/) をインストールできる x86_64 マシン1つ（x86_64 アーキテクチャしかサポートしていません）

### 実行方法

#### 1. 対局 UUID をクロールするための雀魂アカウントを作成する

（メールアドレスによる Yostar ログインにのみ対応しています． Google や Twitter のサービス ID によるログインには対応していません．）

使用したメールアドレスを控えておく．

#### 2. クロール結果を保存するための S3 バケットを作成する

（既存の S3 バケットを使用する場合，この手順は不要）

作成した S3 バケット名を控えておく．

#### 3. S3 バケットにアクセスするためのユーザーを AWS Identity and Access Management (IAM) で作成する

（既存の IAM ユーザーを使用する場合，この手順は不要）

[AWS Identity and Access Management (IAM)](https://aws.amazon.com/iam/) で Amazon S3 に接続するための（ポリシーとグループと）ユーザーを作成する．
必要な権限は，「2. クロール結果を保存するための S3 バケットを作成する」で作成した S3 バケットの全オブジェクトに対する `s3:PutObject` のみ．

作成した IAM ユーザーのアクセスキー ID とシークレットアクセスキーを控えておく．

#### 4. Docker をインストールする

[Install Docker Engine](https://docs.docker.com/engine/install/) に記述されている手順に従って Docker をインストールする．

#### 5. Docker Compose をインストールする

（Docker Desktop をインストールした場合は Docker Compose が付属しているのでこの手順は不要）

[Install Docker Compose](https://docs.docker.com/compose/install/) に記述されている手順に従って Docker Compose をインストールする．

#### 6. AWS の認証情報ファイルを作成する

適当なディレクトリ（`~/.aws` ディレクトリでなくても良い）を作成しそこに AWS の認証情報ファイル `credentials` を作成する．
「3. AWS Identity and Access Management (IAM) でユーザーを作成する」で控えておいた IAM ユーザーのアクセスキー ID とシークレットアクセスキーを `credentials` ファイルに設定する．
（同じディレクトリに `config` ファイルを作成すれば， AWS の構成設定も可能）
AWS 認証情報ファイル `credentials` と構成設定ファイル `config` の詳細については
[Configuration and credential file settings](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html) を参照すること．

作成したディレクトリの絶対パスとプロファイル名を控えておく．

#### 7. mahjongsoul_sniffer リポジトリを git clone する

```bash
$ git clone https://github.com/Cryolite/mahjongsoul_sniffer.git
$ cd mahjongsoul_sniffer
```

#### 8. game_abstract_crawler の設定ファイルを書き換える

`config/game_abstract_archiver.yaml` の `bucket` キーの値を「2. クロール結果を保存するための S3 バケットを作成する」で作成した S3 バケット名に書き換える．

#### 9. game_abstract_crawler を実行する

- `${DOT_AWS_DIR}`: 「6. AWS の認証情報ファイルを作成する」で作成したディレクトリの絶対パス，
- `${AWS_PROFILE}`: 「6. AWS の認証情報ファイルを作成する」で作成した認証情報ファイルのプロファイル名，

として以下のコマンドを実行する．カレントディレクトが `docker/game_abstract_crawler` ディレクトリでないと実行に失敗する．

```bash
$ cd docker/game_abstract_crawler
$ DOT_AWS_DIR=${DOT_AWS_DIR} AWS_PROFILE=${AWS_PROFILE} docker-compose run --rm crawler
```

クローラが起動するまで待つ．

クローラが起動すると `メールアドレス: ` というプロンプトが表示されるので，「1. 対局 UUID をクロールするための雀魂アカウントを作成する」で使用したメールアドレスを入力する．

メールアドレスを入力すると `認証コード: ` というプロンプトが表示されるので，入力したメールアドレスに送られてくる認証コードを入力する．
