# 遊戲用詞核對（2026-10-11）

使用遊戲解包 master 表的公開鏡像核對，沒有自行翻譯遊戲名稱。
名稱對應 `LangParkHighLow_*` 的 `la-park_high_low-001-name`；
貨幣全稱對應 `LangClientCommon_*` 的 `client_id=356121562931200`。
介面省略場地前綴，依各語言顯示貨幣簡稱。

| 語言 | 遊戲名稱 | 貨幣全稱 | 介面簡稱 | 解包表 |
|---|---|---|---|---|
| 繁體中文 | 比大小 | 電玩巨蛋城硬幣 | 硬幣 | [cht](https://github.com/HolodoriDB/holodori-db-cht-diff/blob/main/LangParkHighLow_Cht.json) |
| 简体中文 | 猜高低 | 电玩巨蛋城代币 | 代币 | [chs](https://github.com/HolodoriDB/holodori-db-chs-diff/blob/main/LangParkHighLow_Chs.json) |
| English | High & Low | Mega Sphere Coin | Coins | [eng](https://github.com/HolodoriDB/holodori-db-eng-diff/blob/main/LangParkHighLow_Eng.json) |
| 日本語 | ハイ&ロー | メガスフィアコイン | コイン | [jpn](https://github.com/HolodoriDB/holodori-db-jpn-diff/blob/main/LangParkHighLow_Jpn.json) |
| 한국어 | 하이&로 | 메가 스피어 코인 | 코인 | [kor](https://github.com/HolodoriDB/holodori-db-kor-diff/blob/main/LangParkHighLow_Kor.json) |
| Indonesian | High & Low | Koin Mega Sphere | Koin | [ind](https://github.com/HolodoriDB/holodori-db-ind-diff/blob/main/LangParkHighLow_Ind.json) |

視窗標題依上述名稱切換；執行檔統一命名 `HololiveDreamsHighLowAuto.exe`。

快捷鍵捕獲與 Windows 註冊形式參照 Jump Rope Auto 的
[`bc476f8`](https://github.com/harrykuang-dev/Hololive-Dreams-Jump-Rope-Auto/tree/bc476f830f7858f252fe35ce49a66ed3772b5243)。
沿用其 Windows Tk 的 Alt 位元 `0x20000`，而 `0x8` 是 Num Lock，避免錄製普通鍵時加入 Alt。
