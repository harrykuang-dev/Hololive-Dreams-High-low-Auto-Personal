# Hololive Dreams — 自動ハイ&ロー

[English](README.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Indonesian](README.id.md) · [简体中文](README.zh-CN.md)

Windows 向けのハイ&ロー自動化プログラムです。1.0.1 オリジナル戦略と3段階戦略に対応します。表示言語は英語、繁体字中国語、日本語、韓国語、インドネシア語、簡体字中国語です。

## ダウンロードと実行

[最新リリース](https://github.com/harrykuang-dev/Hololive-Dreams-High-low-Auto-Personal/releases/latest)から **HololiveDreamsHighLowAuto.exe** をダウンロードして実行します。テンプレート、OCR モデル、必要なリソースは単一の実行ファイルに含まれ、起動時に一時展開されます。

1. ゲームのハイ&ロー画面を開きます。
2. 戦略を選びます。既定はオリジナル戦略です。
3. **F8** で開始、**INSERT** で停止します。画面のボタンでも操作できます。

ショートカット欄をクリックし、キーまたは Ctrl / Alt / Shift の組み合わせを押すと変更できます。**Esc** で登録をキャンセルします。開始と停止には異なるキーを設定します。Num Lock によって Alt 修飾キーが追加されることはありません。

## 記録と純利益

今日のコインは確認済み報酬の合計です。純利益は **確認済み報酬 − 50 ×（勝利ラウンド数 + 敗北ラウンド数）** です。精算済みの勝利ラウンドにも参加費 50 コインが必要です。この差し引きは純利益の表示に適用され、報酬額や戦略の判断は従来どおりです。

`daily_coins.json` に当日の報酬、ラウンド数、3段階の進行状況を保存し、`settings.json` に言語、戦略、ショートカットを保存します。更新前にプログラムを停止し、両ファイルを新しい EXE と同じフォルダーに置いてください。

以前の当日記録に勝利回数がない場合、報酬を保持し、純利益は算出不可と表示します。過去の参加費は推定せず、翌日から完全な集計を再開します。ログやスクリーンショットは保存しません。

## ソースからの実行とビルド

```powershell
python -m pip install -r requirements.txt pyinstaller
python main_ui.py
python -m PyInstaller --noconfirm "Hololive Dreams-Auto.spec"
```

出力：`dist/HololiveDreamsHighLowAuto.exe`。

## ドキュメントとライセンス

[3段階戦略](THREE_STAGE.md#ja) · [ゲーム用語](docs/GAME_TERMS.md) · [報酬 OCR](docs/OCR.md) · [v1.1.0 リリースノート](docs/RELEASE-1.1.0.md) · [バージョン履歴](HISTORY.md)

カード認識と保持するカードの選択戦略は [hololive-dreams-helper](https://github.com/Oreki0504/hololive-dreams-helper) に基づきます。[MIT ライセンス表記](licenses/poker-core-MIT.txt)とその他の必要なライセンス表記は [licenses](licenses/) に含まれます。
