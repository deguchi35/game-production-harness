# 参考資料と採用理由

調査日：2026-10-15。記事の説明と、本プロジェクトへの応用案を分けて記載します。記事の文章・画像・有料部分を転載する資料ではありません。作者の推薦・協賛を受けたという意味でもありません。

## 主軸とする国内外の制作事例

### npaka／布留川英一

- [CGWORLD Blender Fes講師紹介](https://cgworld.jp/special/blenderfes/vol6/?channel=channel-946)
- [CLIとMCPを使う制作手順](https://note.com/npaka/n/n7f7531e7b9ed)
- [画像確認を伴う制作の考察](https://note.com/npaka/n/n2780a7f4494a)

**資料から得る原則：** CLIによる生成、MCPによる対話的な調整、CLIによる複数カメラ出力・書き出し・検査を使い分ける。画像取得機能が存在するだけでは、画像を見て修正する工程は保証されない。

**採用する設計：** 繰り返し処理をスクリプトにし、各工程に撮影・実画像の確認・指摘・修正・再撮影を明示する。

**限界：** 作者の別の事例にはTripoやCodexもある。すべてがOpusだけで作られた、全工程が自動だった、とまとめない。

### SeaGate／繁戸和幸

- [OpusとBlender MCPの制作事例](https://note.com/sigmode21/n/n688c22d54f82)

**資料から得る原則：** 参考画像と段階的に比較する。細部や素材に限界が残ること、手作業が速い局面も認めている。

**採用する設計：** 代表アセット1個を先に合格させる。失敗を重ねても自動化し続けず、局所的な手作業も選べるようにする。

**限界：** この制作事例は、今回のUnity Android向け負荷・音同期・ゲーム性を保証しない。

### Max Novak

- [I connected Claude AI to Blender 3D...Mind-Blowing Results (MCP)](https://www.youtube.com/watch?v=r7H60u0kHRA)

**確認した位置付け：** 作者自身によるClaudeとBlender MCPの制作紹介。手続き的な生成や専用ツール、シーン構成を考える参考。

**採用する設計：** コース沿いの建物、柵、路面などを、再利用できるパラメトリックな部品として整理する。

**限界：** 全字幕・全手順の再現検証は行っていない。紹介動画だけから、特定の接続版、完全な自律制作、制作費や再現性まで断定しない。

## 今回追加調査したハーネス記事 3本

### 1 Anthropic 長時間開発のハーネス設計

[Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps)

著者：Prithvi Rajasekaran。公開：2026-03-24。

**記事の内容：** 生成担当と評価担当を分離し、評価者が実際のアプリを操作・撮影する。合格条件を実装前に決める。モデルの改善に応じて工程を減らす検討も行っている。

**今回の採用：** 実装担当＋節目の読み取り専用レビューから始める。固定カメラの画像とUnity内の録画を別々に評価する。

**注意：** Webアプリの実験であり、3Dゲームの実証ではない。多エージェント化は費用を増やす場合がある。この記事を理由に常時大人数のレビューを起動しない。

### 2 OpenAI ハーネスエンジニアリング

[Harness engineering: leveraging Codex in an agent-first world](https://openai.com/index/harness-engineering/)

著者：Ryan Lopopolo。公開：2026-02-11。

**記事の内容：** 短い入口文書から、リポジトリに保存した仕様・計画・判断記録へ案内する。スクリーンショット、ログ、メトリクスをエージェントが観測できるようにする。制約をlint・テスト等で確認する。

**今回の採用：** CLAUDE.mdは案内に限定。環境情報、合格条件、実行結果、再開地点を別ファイルに保存する。画像と機械可読の検査結果をセットにする。

**注意：** Codexによる社内製品の事例。著者側の生産性推計を、ClaudeやBlenderの期待削減率に転用しない。

### 3 Anthropic MCPとコード実行による効率化

[Code execution with MCP: Building more efficient agents](https://www.anthropic.com/engineering/code-execution-with-mcp)

著者：Adam Jones、Conor Kelly。公開：2025-11-04。

**記事の内容：** 必要なツールだけを読み、途中データをコード側で処理して必要な結果だけ返す。再利用する処理や状態をファイルへ保存する。

**今回の採用：** Blenderの全オブジェクトを会話で逐次処理せず、一括検査と生成スクリプトへ寄せる。返すのは失敗項目、件数、対象名、成果物の場所。必要な画像だけレビュー時に渡す。

**注意：** 記事にある98.7%削減は特定例であり、このゲームでの削減率ではない。コード実行の隔離、制限、監視が必要。

## 接続ツールの候補と役割

| 候補 | 役割 | 導入前に確認すること |
|---|---|---|
| [Superpowers](https://github.com/obra/superpowers) | 計画、TDD、レビューなどの開発手順 | 必要な機能だけ使う。芸術品質や自動合格判定は保証しない |
| [ahujasid MCP for Blender](https://github.com/ahujasid/mcp-for-blender) | コミュニティ製Blender操作 | Python実行範囲、アドオンとサーバーの対応版、ローカル接続、安全性 |
| [Blender公式MCP](https://www.blender.org/lab/mcp-server/) | 別実装の公式接続候補 | Blender対応版、警告事項、Coplayとの互換性を別途検証 |
| [Coplay Unity MCP](https://github.com/CoplayDev/unity-mcp) | Unityの操作・検査・Blender Bridge | 安定版を固定。既存Unityプロジェクトでの動作確認 |
| [Coplay Blender Bridge](https://coplaydev.github.io/unity-mcp/reference/tools/asset_gen/blender_bridge) | Blender出力からUnity取り込みをつなぐ | 対応アドオンを確認。画像比較機能と自動品質判定を混同しない |

Blender Game Skillsは必須採用を取り下げ、参考候補へ変更。採用数・スター・有名人の動画だけで選ばず、メンテナンス、依存関係、ライセンス、代表アセットの往復テストを基準にする。

## 引用と公開

この記事群は参考文献としてリンクし、独自に要約する。第三者の文章・画像・コードをそのまま公開リポジトリへ入れない。引用の範囲を超える再利用には個別のライセンス・許諾確認が必要。参考画像をAIへ渡せる権利と、公開配布できる権利も分けて確認する。
