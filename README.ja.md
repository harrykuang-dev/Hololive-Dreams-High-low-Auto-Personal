# Hololive Dreams — 自動ハイ&ロー

[English](README.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Indonesian](README.id.md) · [简体中文](README.zh-CN.md)

Windows 向けのハイ&ロー自動化プログラムです。「慎重」と「積極」の戦略に対応します。表示言語は英語、繁体字中国語、日本語、韓国語、インドネシア語、簡体字中国語です。

## ダウンロードと実行

[最新リリース](https://github.com/harrykuang-dev/Hololive-Dreams-High-low-Auto-Personal/releases/latest)から **HololiveDreamsHighLowAuto.exe** をダウンロードして実行します。テンプレート、OCR モデル、必要なリソースは単一の実行ファイルに含まれ、起動時に一時展開されます。

1. ゲームのハイ&ロー画面を開きます。
2. 「慎重」または「積極」を選びます。既定は「慎重」です。
3. **F8** で開始、**INSERT** で停止します。画面のボタンでも操作できます。

ショートカット欄をクリックし、キーまたは Ctrl / Alt / Shift の組み合わせを押すと変更できます。**Esc** で登録をキャンセルします。開始と停止には異なるキーを設定します。

## 記録と純利益

今日のコインは確認済み報酬の合計です。純利益は **確認済み報酬 − 50 ×（勝利ラウンド数 + 敗北ラウンド数）** です。

`daily_coins.json` に当日の報酬、ラウンド数、積極戦略の進行状況を保存し、`settings.json` に言語、戦略、ショートカットを保存します。両ファイルは `%LOCALAPPDATA%\HololiveDreamsHighLowAuto\` に保存されます。更新前にプログラムを停止して EXE を置き換えてください。初回起動時に EXE と同じフォルダーの既存の記録と設定を移行します。AppData にある既存のファイルは上書きしません。

当日の記録と積極戦略の進行状況は、**パソコンのローカル時刻の午前4時**にリセットされます。「**当日の記録をリセット**」ボタンは、確認後に報酬、純利益、ラウンド数、積極戦略の進行状況をリセットします。サーバーとパソコンのタイムゾーンが異なる場合は、手動リセットを利用できます。

## ソースからの実行とビルド

```powershell
python -m pip install -r requirements.txt pyinstaller
python main_ui.py
python -m PyInstaller --noconfirm "Hololive Dreams-Auto.spec"
```

出力：`dist/HololiveDreamsHighLowAuto.exe`。

## ドキュメントとライセンス

[積極戦略](THREE_STAGE.md#ja) · [ゲーム用語](docs/GAME_TERMS.md) · [報酬 OCR](docs/OCR.md) · [v1.1.2 リリースノート](docs/RELEASE-1.1.2.md) · [バージョン履歴](HISTORY.md)

カード認識と保持するカードの選択戦略は [hololive-dreams-helper](https://github.com/Oreki0504/hololive-dreams-helper) に基づきます。[MIT ライセンス表記](licenses/poker-core-MIT.txt)とその他の必要なライセンス表記は [licenses](licenses/) に含まれます。
