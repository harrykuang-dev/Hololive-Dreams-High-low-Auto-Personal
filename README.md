# Hololive Dreams — High & Low Auto

[English](README.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Indonesian](README.id.md) · [简体中文](README.zh-CN.md)

A Windows program that automates High & Low with Conservative and Aggressive strategies. The interface supports English, Traditional Chinese, Japanese, Korean, Indonesian and Simplified Chinese.

## Download and run

Download **HololiveDreamsHighLowAuto.exe** from the [latest release](https://github.com/harrykuang-dev/Hololive-Dreams-High-low-Auto-Personal/releases/latest) and run it. Templates, OCR models and required resources are bundled in the single executable and extracted temporarily at startup.

1. Open High & Low in the game.
2. Select Conservative or Aggressive; Conservative is the default.
3. Press **F8** to start and **INSERT** to stop, or use the interface buttons.

Click a shortcut field and press a key or a Ctrl / Alt / Shift combination to change it. **Esc** cancels capture. Start and stop shortcuts must differ.

## Records and net profit

Coins today shows confirmed rewards. Net profit is **confirmed rewards − 50 × (winning rounds + losing rounds)**.

`daily_coins.json` stores the daily rewards, round counts and Aggressive strategy progress. `settings.json` stores the language, strategy and shortcuts. Both files are stored in `%LOCALAPPDATA%\HololiveDreamsHighLowAuto\`. Before upgrading, stop the program and replace the EXE. On first launch, existing records and preferences beside the EXE are moved to this folder; existing AppData files are not overwritten.

Daily records and Aggressive strategy progress reset at **04:00 on the computer’s local clock**. The **Reset daily records** button resets rewards, net profit, round counts and Aggressive strategy progress after confirmation. Use manual reset when the server and computer use different time zones.

## Run from source and build

```powershell
python -m pip install -r requirements.txt pyinstaller
python main_ui.py
python -m PyInstaller --noconfirm "Hololive Dreams-Auto.spec"
```

Output: `dist/HololiveDreamsHighLowAuto.exe`.

## Documentation and licenses

[Aggressive strategy](THREE_STAGE.md) · [Game terminology](docs/GAME_TERMS.md) · [Reward OCR](docs/OCR.md) · [v1.1.2 release notes](docs/RELEASE-1.1.2.md) · [Version history](HISTORY.md)

Card recognition and hold-card strategy are based on [hololive-dreams-helper](https://github.com/Oreki0504/hololive-dreams-helper). Its [MIT notice](licenses/poker-core-MIT.txt) and other required license notices are retained in [licenses](licenses/).
