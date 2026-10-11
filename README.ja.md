# Hololive Dreams — 自動ハイ&ロー

[English](README.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Indonesian](README.id.md) · [简体中文](README.zh-CN.md)

Windows 向けのハイ&ロー自動化プログラムです。「慎重」（オリジナル）と「積極」（3段階）の戦略に対応します。表示言語は英語、繁体字中国語、日本語、韓国語、インドネシア語、簡体字中国語です。

Fluent スタイルの画面には白いショートカット欄と分かりやすい開始・停止ボタンがあり、戦略の説明はプログラムのウィンドウ中央に表示されます。言語ラベルには選択中の言語での「言語」の訳語と「Language」を表示します。

## ダウンロードと実行

[最新リリース](https://github.com/harrykuang-dev/Hololive-Dreams-High-low-Auto-Personal/releases/latest)から **HololiveDreamsHighLowAuto.exe** をダウンロードして実行します。テンプレート、OCR モデル、必要なリソースは単一の実行ファイルに含まれ、起動時に一時展開されます。

1. ゲームのハイ&ロー画面を開きます。
2. 「慎重」または「積極」を選びます。既定は「慎重」です。戦略の右にある疑問符をクリックすると説明が表示されます。
3. **F8** で開始、**INSERT** で停止します。画面のボタンでも操作できます。

ショートカット欄をクリックし、キーまたは Ctrl / Alt / Shift の組み合わせを押すと変更できます。**Esc** で登録をキャンセルします。開始と停止には異なるキーを設定します。Num Lock によって Alt 修飾キーが追加されることはありません。

## 記録と純利益

今日のコインは確認済み報酬の合計です。純利益は **確認済み報酬 − 50 ×（勝利ラウンド数 + 敗北ラウンド数）** です。精算済みの勝利ラウンドにも参加費 50 コインが必要です。この差し引きは純利益の表示に適用され、報酬額や戦略の判断は従来どおりです。

`daily_coins.json` に当日の報酬、ラウンド数、3段階の進行状況を保存し、`settings.json` に言語、戦略、ショートカットを保存します。更新前にプログラムを停止し、両ファイルを新しい EXE と同じフォルダーに置いてください。

当日の記録と3段階の進行状況は、**パソコンのローカル時刻の午前4時**にリセットされます。「**当日の記録をリセット**」ボタンは、確認後に報酬、純利益、ラウンド数、3段階の進行状況をリセットします。サーバーとパソコンのタイムゾーンが異なる場合は、手動リセットを利用できます。

以前の当日記録に勝利回数がない場合、報酬を保持し、純利益は算出不可と表示します。過去の参加費は推定せず、次の当日記録のリセット後に完全な集計を再開します。ログやスクリーンショットは保存しません。

## ソースからの実行とビルド

```powershell
python -m pip install -r requirements.txt pyinstaller
python main_ui.py
python -m PyInstaller --noconfirm "Hololive Dreams-Auto.spec"
```

出力：`dist/HololiveDreamsHighLowAuto.exe`。

## ドキュメントとライセンス

[3段階戦略](THREE_STAGE.md#ja) · [ゲーム用語](docs/GAME_TERMS.md) · [報酬 OCR](docs/OCR.md) · [v1.1.1 リリースノート](docs/RELEASE-1.1.1.md) · [バージョン履歴](HISTORY.md)

カード認識と保持するカードの選択戦略は [hololive-dreams-helper](https://github.com/Oreki0504/hololive-dreams-helper) に基づきます。[MIT ライセンス表記](licenses/poker-core-MIT.txt)とその他の必要なライセンス表記は [licenses](licenses/) に含まれます。
