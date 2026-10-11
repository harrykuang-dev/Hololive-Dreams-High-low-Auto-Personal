基於 https://github.com/mwty-0415/Hololive-Dreams-Auto-High-Low 開發和測試一些亂七八糟的功能

比大小遊戲留牌階段的識牌與策略計算來自 https://github.com/Oreki0504/hololive-dreams-helper 。快捷鍵與前端形式參照 [Jump Rope Auto](https://github.com/harrykuang-dev/Hololive-Dreams-Jump-Rope-Auto)。

# Hololive Dreams — High & Low Auto (Personal)

[English](#english) · [繁體中文](#繁體中文) · [日本語](#日本語) · [한국어](#한국어) · [Indonesian](#indonesian) · [简体中文](#简体中文)

[下載最新單文件 EXE](https://github.com/harrykuang-dev/Hololive-Dreams-High-low-Auto-Personal/releases/latest)

## 繁體中文

自動比大小工具，提供 1.0.1 原版與三階段策略。開啟遊戲的比大小畫面後開始；預設 **F8 開始、INSERT 停止**。點選開始／停止快捷鍵欄位即可錄製新按鍵或 Ctrl、Alt、Shift 組合；Esc 取消錄製。兩個快捷鍵不可相同。

介面支援六種語言，無背景切換或開發者模式，不保存日誌或截圖。今日硬幣保持原始確認入帳總額；淨利為「入帳 − 50 ×（勝局 + 敗局）」，不影響遊戲決策。

下載 `HololiveDreamsHighLowAuto.exe` 即可執行，不需 `_internal` 資料夾。升級前停止掛機，保留並將 `daily_coins.json` 放在新 EXE 同級。舊版當日記錄缺少勝局次數時，不估算過去投入，淨利顯示無法確認；隔日正常統計。`settings.json` 保存語言、策略及快捷鍵。

## 简体中文

自动猜高低工具，保留原版与三阶段策略。默认 **F8 开始、INSERT 停止**；点击快捷键栏位后按下新按键或 Ctrl、Alt、Shift 组合，Esc 取消。六语言界面，无背景切换、开发者模式、日志或截图保存。

今日代币显示确认入账总额；净利扣除每个胜局和败局各 50 投入，游戏决策不变。运行单文件 EXE；升级时保留同级的 `daily_coins.json`。旧记录缺少胜局次数时不会估算当日净利，隔日正常统计。偏好设置保存于 `settings.json`。

## English

High & Low Auto keeps the original and three-stage strategies. Open the game screen, then start. Default shortcuts: **F8 starts, INSERT stops**. Click either shortcut field to capture a key or Ctrl/Alt/Shift combination; Esc cancels. Six interface languages; no background toggle, developer mode, saved logs or screenshots.

Coins today shows confirmed gross rewards. Net profit deducts 50 Coins for every winning and losing round without changing decisions. Run the single EXE. Preserve `daily_coins.json` beside it when upgrading. Old same-day records without win counts show unavailable net profit instead of an estimate; the next day has complete accounting. Preferences are stored in `settings.json`.

## 日本語

自動ハイ&ロー。従来と3段階の戦略を維持します。**F8 で開始、INSERT で停止**。ショートカット欄をクリックしてキーや Ctrl/Alt/Shift の組み合わせを登録できます。Esc でキャンセル。6言語に対応し、背景切替・開発者モード・ログや画像の保存はありません。

今日のコインは確認済み報酬の合計です。純利益から勝利・敗北の各ラウンドの参加費 50 コインを差し引きます。戦略は変更しません。単一 EXE を実行し、更新時は同じフォルダの `daily_coins.json` を保持してください。勝利回数のない以前の当日記録では純利益を推定せず、翌日から完全に計算します。設定は `settings.json` に保存します。

## 한국어

하이&로 자동 플레이. 기본 및 3단계 전략을 유지합니다. **F8 시작, INSERT 중지**. 단축키 칸을 클릭해 키 또는 Ctrl/Alt/Shift 조합을 설정하고 Esc로 취소하세요. 6개 언어 지원. 배경 전환, 개발자 모드, 로그나 화면 저장 기능은 없습니다.

오늘의 코인은 확인된 보상 합계입니다. 순이익은 승리와 패배마다 참가 비용 50 코인을 차감하며 전략은 그대로입니다. 단일 EXE를 실행하고 업데이트할 때 같은 폴더의 `daily_coins.json`을 보존하세요. 승리 횟수가 없는 이전 당일 기록의 순이익은 추정하지 않으며 다음 날부터 정확히 계산합니다. 설정은 `settings.json`에 저장됩니다.

## Indonesian

High & Low Otomatis mempertahankan strategi asli dan tiga tahap. **F8 mulai, INSERT berhenti**. Klik kolom pintasan untuk merekam tombol atau kombinasi Ctrl/Alt/Shift; Esc membatalkan. Enam bahasa antarmuka, tanpa penggantian latar, mode pengembang, penyimpanan log atau gambar.

Koin hari ini adalah total hadiah terkonfirmasi. Laba bersih mengurangi biaya masuk 50 Koin untuk setiap ronde menang maupun kalah; keputusan strategi tetap sama. Jalankan satu EXE. Pertahankan `daily_coins.json` di samping EXE saat memperbarui. Catatan lama pada hari yang sama tanpa jumlah kemenangan tidak diberi estimasi laba bersih; pencatatan lengkap dimulai hari berikutnya. Preferensi disimpan di `settings.json`.

## 源碼與打包 / Build

```powershell
python -m pip install -r requirements.txt pyinstaller
python main_ui.py
python -m PyInstaller --noconfirm "Hololive Dreams-Auto.spec"
python -m unittest discover -s tests -v
```

輸出：`dist/HololiveDreamsHighLowAuto.exe`。模板、OCR 模型、圖示和授權資料均包含在 EXE，封裝器會在執行時暫時解壓資源。

[三階段規則](THREE_STAGE.md) · [用詞來源](docs/GAME_TERMS.md) · [v1.1.0 更新](docs/RELEASE-1.1.0.md)
