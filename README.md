# MahjongSoul Sniffer

## 主な機能

- [API Visualizer](api-visualizer): [雀魂](https://mahjongsoul.com/) API サーバとクライアントとの間の WebSocket メッセージの内容を可視化する．
- [Game Abstract Crawler](game-abstract-crawler): 雀魂の「観戦」機能から対局 UUID （金の間以上の段位戦，四麻のみ）をクロールして [Amazon S3](https://aws.amazon.com/jp/s3/) に保存する．
- [Game Detail Crawler](game-detail-crawler): (ドキュメント未整備) Game Abstract Crawler でクロールした各対局の牌譜詳細をダウンロード・解析して Amazon S3 に保存する．
