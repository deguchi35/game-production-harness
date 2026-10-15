# このリポジトリの読み方

まずREADME.mdを読み、実装済みのローカル検査と未実装の制作工程を区別する。現在の開発担当はKOU。Claude Codeや外部AIの起動は不要。

- 初めて使う：docs/QUICKSTART.md
- 実装済みCLI：docs/LOCAL_HARNESS.md
- 制作手順：docs/WORKFLOW.md
- 実装仕様：docs/HARNESS_SPEC.md
- 出典と限界：docs/SOURCES.md
- 環境確認：prompts/PREFLIGHT.md
- 合意後の夜間作業：prompts/OVERNIGHT.md
- 公開前の確認：docs/PUBLISH_CHECKLIST.md

全ファイルを毎ターン読み直さず、担当工程に必要なものだけ参照する。

既存データを保護し、同じScene／.blendの書き込みは一担当にする。
未実施・失敗・ブロックを成功と報告しない。完了には対応する実行証拠が必要。
画像の保存と画像のレビュー、Editor再生と実機実行、音設定と録音確認を区別する。
新規ソフトの導入・権限拡張・課金・外部公開は、別途明示された許可の範囲に従う。
他のゲームの非公開コードやアセットをこの公開用リポジトリへコピーしない。

実装済みなのはharness.pyのpreflight／runとローカルテスト。doctor、generate、resume等の設計上の機能名を存在するコマンドとして実行しない。Blender／Unity／Android実機検証は未完了。
