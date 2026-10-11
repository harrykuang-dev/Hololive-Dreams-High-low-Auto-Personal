# Hololive Dreams — 自動比大小

[English](README.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Indonesian](README.id.md) · [简体中文](README.zh-CN.md)

Windows 自動比大小程式，提供「穩健」（原版）與「激進」（三階段）策略。介面支援英文、繁體中文、日文、韓文、印尼語與簡體中文。

## 下載與執行

從[最新版本](https://github.com/harrykuang-dev/Hololive-Dreams-High-low-Auto-Personal/releases/latest)下載 **HololiveDreamsHighLowAuto.exe** 後執行。模板、OCR 模型及必要資源包含在單一執行檔中，啟動時暫時解壓。

1. 開啟遊戲的比大小畫面。
2. 選擇穩健或激進策略，預設為穩健。
3. 按 **F8** 開始、**INSERT** 停止，或使用介面按鈕。

點選快捷鍵欄位，按下按鍵或 Ctrl / Alt / Shift 組合即可修改。**Esc** 取消錄製。開始與停止快捷鍵不可相同。

## 記錄與淨利

今日硬幣顯示已確認的入帳總額。淨利為 **確認入帳 − 50 ×（勝局 + 敗局）**。

`daily_coins.json` 保存當日入帳、局數及三階段進度；`settings.json` 保存語言、策略及快捷鍵。升級前停止程式，保留這兩個檔案並放在新 EXE 同級目錄。

當日記錄與三階段進度依**電腦本地時間凌晨 4 點**歸零。「**重設當日記錄**」按鈕經確認後，會將入帳、淨利、局數及三階段進度歸零。伺服器與電腦時區不同時，可使用手動重設。

舊版當日記錄若缺少勝局次數，保留既有入帳並將淨利顯示為無法確認，不估算過去投入；下一次每日歸零後恢復完整統計。不保存日誌或截圖。

## 從原始碼執行與打包

```powershell
python -m pip install -r requirements.txt pyinstaller
python main_ui.py
python -m PyInstaller --noconfirm "Hololive Dreams-Auto.spec"
```

輸出：`dist/HololiveDreamsHighLowAuto.exe`。

## 文件與授權

[三階段策略](THREE_STAGE.md#zh-tw) · [遊戲用詞](docs/GAME_TERMS.md) · [獎金 OCR](docs/OCR.md) · [v1.1.1 更新說明](docs/RELEASE-1.1.1.md#繁體中文) · [版本歷史](HISTORY.md)

識牌與留牌策略來自 [hololive-dreams-helper](https://github.com/Oreki0504/hololive-dreams-helper)。其 [MIT 聲明](licenses/poker-core-MIT.txt)與其他必要授權聲明保留於 [licenses](licenses/)。
