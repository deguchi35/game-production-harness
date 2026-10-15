# game-production-harness

### 「生成できた」を、検証できる制作へ。

3Dゲーム制作の**手順書と、小さなローカル検証CLI**です。KOUが最初の実装を進めています。制作前の設定確認と成果物のファイル検査を、AIサービスなしで試せます。

![設計キット。独自文書・図のライセンスはCC BY 4.0](assets/status.svg)

> **実装済みなのは設定・ファイル検査とJSON記録だけです。** Blenderの起動、モデル生成、Unity連携、音同期、Android性能、画像・音の品質評価は未検証です。ダミーファイルの検査成功をゲーム制作成功とは扱いません。

[はじめる](#はじめる) · [制作の流れ](#制作の流れ) · [完了の基準](#完了の基準) · [資料](#資料) · [ライセンス](#ライセンス)

## はじめる

既存のPython 3.10以降が必要です。外部パッケージ、Claude Code、API契約は不要です。以下はリポジトリのルートからPowerShellで実行します。`python`は手元で使えるPythonのコマンド名または実行ファイルに置き換えてください。

```powershell
$demo = Join-Path ([System.IO.Path]::GetTempPath()) ('harness-demo-' + [guid]::NewGuid().ToString('N'))
Copy-Item -LiteralPath examples/demo -Destination $demo -Recurse
python harness.py preflight --config "$demo/config.json"
python harness.py run --config "$demo/config.json"
python harness.py run --config "$demo/config.json" --write-report
Get-ChildItem -LiteralPath "$demo/reports"
python -m unittest discover -s tests -v
```

初めの2コマンドは読み取りだけです。`--write-report`を付けたときだけ、コピー先の`reports/<run-id>.json`へ新規保存します。サンプルは架空のテキストで、Blender不要です。正常時も`engine_validation`と全体の`status`は`not_run`です。終了コード0はファイル確認が完了したことだけを示します。

設定項目、失敗の再現、終了コードは[ローカルCLIの使い方](docs/LOCAL_HARNESS.md)へ。まだ提供していない生成処理や制作工程の設計を読む場合は、以下へ進みます。Claude Code用の既存指示テンプレートは任意の参考資料で、CLIの実行条件ではありません。

1. **[導入ガイドを読む](docs/QUICKSTART.md)** — 環境と権限を確認し、最初の作業範囲を決める。
2. **[合格条件を決める](docs/WORKFLOW.md)** — 代表アセット1個と、30〜60秒の短いプレイ区間に絞る。
3. **[準備指示を渡す](prompts/PREFLIGHT.md)** — バックアップと接続確認から始める。夜間運転はその後。

最初の適用対象はAndroid先行のペンギン滑走ゲーム。ゲーム本体やアセットは、この設計キットに含みません。接続ツールも導入済みではなく、[候補ごとに対応版・権限・安全性を確認](docs/SOURCES.md)します。

## 制作の流れ

![提案する制作ループ。CLIで生成し、観察・局所修正（MCPは任意）、画像レビューと数値検査、Unityで表示・音確認、Android実機で計測。各工程の証拠を残し、不合格箇所だけ修正する。](assets/production-loop.svg)

**CLIで生成 → 観察・局所修正（MCPは任意） → 画像＋数値で点検 → Unityで表示・音を確認 → 実機で計測。** 図はこれから実装する工程であり、実行結果ではありません。

- **CLI：繰り返しを再現可能に。** 入力、seed、版、コマンドを保存する。
- **観察・修正：必要ならMCPを使う。** 大量の処理を会話だけで管理しない。
- **レビュー：証拠を開いて判断する。** 画像の保存だけで「見た」と扱わない。
- **編集：同じファイルは一人で。** 同一Scene／.blendへの同時書き込みを避ける。

## 完了の基準

コンパイルだけで完了にはしません。各項目を別々に確認します。

- **見た目** — 固定カメラの比較画像と、実際に見た指摘・判断
- **動作と音** — Unity内の音入り実プレイ録画とイベント時刻ログ
- **実機性能** — Android端末でのフレーム時間・メモリ・発熱傾向
- **再現性** — 日時、コミット、環境、実行ログ、最後の検証済み地点

未実施は「未確認」、進めない項目は「ブロック」。失敗した箇所だけ直し、証拠を取り直します。**Pixel 8で60fpsは暫定目標であり、達成値ではありません。**

## 資料

- [制作手順と合格条件](docs/WORKFLOW.md) — 環境確認から朝のレビューまで
- [ローカルCLIの使い方](docs/LOCAL_HARNESS.md) — 設定確認、ファイル検査、JSON記録
- [ハーネス実装仕様](docs/HARNESS_SPEC.md) — 状態、証拠、排他編集、段階的な実装順
- [参考資料と採用理由](docs/SOURCES.md) — 制作事例・技術記事と、それぞれの限界
- [夜間作業の指示](prompts/OVERNIGHT.md) — 承認済みの範囲、停止条件、報告
- [公開前レビュー結果](docs/REVIEW.md) — 修正点と、まだ検証していないこと
- [公開前チェック](docs/PUBLISH_CHECKLIST.md) — 秘密情報、権利、実証範囲を確認
- [リポジトリの入口](CLAUDE.md) — 必要な文書だけを読むための案内

## ライセンス

本リポジトリの**独自文書・独自図・コード・サンプルはCC BY 4.0**です（[ライセンス](LICENSE.md)／[日本語の概要](https://creativecommons.org/licenses/by/4.0/deed.ja)）。再利用時は出典、ライセンスへのリンク、変更の有無を示してください。

第三者の記事・画像・コード・音源・モデルには適用されません。

更新：2026-10-15 · 実行結果は、日時・コミット・環境・証拠とともに追記予定。
