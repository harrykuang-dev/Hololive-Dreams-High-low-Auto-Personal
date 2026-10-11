# Three-stage strategy

[English](#en) · [繁體中文](#zh-tw) · [日本語](#ja) · [한국어](#ko) · [Indonesian](#id) · [简体中文](#zh-cn)

<a id="en"></a>

## English

Select “3 stages: Max → Win count → Max”. The original strategy remains the default.

- Stages one and three keep challenging until the game settles automatically. There is no software cashout target such as 12,800.
- Stage two confirms the initial payout once and sets a win-count target. Ongoing reward readings do not decide whether to double.
- A successful High/Low click followed by a success prompt counts once. Ties, repeated frames, and click retries do not add wins. A final win leading directly to settlement also counts once.
- A loss resets the round’s count but keeps the stage. A confirmed successful settlement advances the stage.

| Initial payout | Stage-two wins | Payout |
|---|---:|---:|
| 200 | 5 | 6,400 |
| 400 | 4 | 6,400 |
| 700 | 3 | 5,600 |
| 800 | 3 | 6,400 |
| 1,500 | 2 | 6,000 |
| 3,000 | 1 | 6,000 |
| 7,000 / 10,000 | 0 | 7,000 / 10,000 |

At the start of stage two, exclude win counts that would bring the daily total to 20,000 or more, preserving stage three. Existing earnings may therefore reduce the target count. If even an immediate cashout would cross the cap, stop for manual handling. The program cannot override a daily limit imposed by the game during stage one.

Settlement amounts are checked against the initial payout and confirmed wins to prevent missing digits from corrupting the ledger. Stage progress and coins are saved in `daily_coins.json`, preserved on same-day restarts and reset on a new date. Restarting mid-round without its count stops the program and asks for a fresh round rather than guessing progress. Stop after stage three. Updating does not reconstruct historical earnings.

<a id="zh-tw"></a>

## 繁體中文

在策略選單選擇「三階段：最大 → 計次 → 最大」。原版仍為預設選項。

- 第一、第三階段：持續挑戰直到遊戲自動結算，不設定 12,800 等軟體止盈金額。
- 第二階段：只在本局開始時確認一次起手獎勵，確定目標成功次數，之後不再根據當前獎金判斷翻倍。
- 只有點擊猜高／低後出現成功詢問，才增加一次成功；平手、重複畫面、點擊重試不增加次數。遊戲達到上限直接結算時，最後一次成功也只計算一次。
- 失敗後成功次數歸零，重試同一階段；確認結算入帳後才前進。

| 起手獎勵 | 第二階段成功次數 | 對應獎金 |
|---|---:|---:|
| 200 | 5 | 6,400 |
| 400 | 4 | 6,400 |
| 700 | 3 | 5,600 |
| 800 | 3 | 6,400 |
| 1,500 | 2 | 6,000 |
| 3,000 | 1 | 6,000 |
| 7,000 / 10,000 | 0 | 7,000 / 10,000 |

第二階段會在起手時排除入帳後累計達到 20,000 的次數選項，以保留第三階段；因此已有收益較高時，次數可能低於表中數值。若立即收手也會跨上限，則停止等待手動處理。第一階段若被遊戲提前結束當日遊玩，程式無法繞過每日限制。

結算時以起手獎勵及成功次數核對金額，不允許缺位數字造成錯誤入帳。三階段進度與硬幣保存在 `daily_coins.json`，當日重開保留，下一日期重置。中途重新啟動而缺少本局計數時，停止提示從新一局開始，不猜測已成功次數。第三階段成功後停止。更新不會自動推算歷史收益。

<a id="ja"></a>

## 日本語

「3段階：最大 → 成功回数 → 最大」を選びます。既定はオリジナル戦略です。

- 第1・第3段階はゲームが自動精算するまで挑戦を続けます。プログラム側に 12,800 などの精算目標額は設定しません。
- 第2段階はラウンド開始時の報酬を一度確認し、目標成功回数を決めます。その後の報酬表示はダブルアップの判断に使いません。
- ハイ／ローをクリックして成功の確認画面が出た場合に1回加算します。引き分け、同じ画面、クリックの再試行では加算しません。上限到達で直接精算される最後の成功も1回だけ数えます。
- 敗北時はラウンドの成功回数をリセットして同じ段階を再試行します。報酬の精算を確認すると次の段階に進みます。

| 開始時の報酬 | 第2段階の成功回数 | 報酬 |
|---|---:|---:|
| 200 | 5 | 6,400 |
| 400 | 4 | 6,400 |
| 700 | 3 | 5,600 |
| 800 | 3 | 6,400 |
| 1,500 | 2 | 6,000 |
| 3,000 | 1 | 6,000 |
| 7,000 / 10,000 | 0 | 7,000 / 10,000 |

第2段階の開始時に、当日の合計が 20,000 以上になる成功回数を除外し、第3段階を残します。既存の報酬によって目標回数が表より少なくなる場合があります。即時精算でも上限に達する場合は停止し、手動操作を待ちます。第1段階でゲーム側の当日制限に達した場合、プログラムはその制限を回避できません。

精算額は開始時の報酬と確認済み成功回数で照合します。段階とコインは `daily_coins.json` に保存し、同日の再起動では保持し、翌日にリセットします。ラウンド途中の再起動で成功回数が不明な場合は停止し、新しいラウンドからの開始を求めます。進行状況は推定しません。第3段階の成功後に停止します。更新によって過去の報酬は再計算しません。

<a id="ko"></a>

## 한국어

“3단계: 최대 → 성공 횟수 → 최대”를 선택합니다. 기본값은 기본 전략입니다.

- 1단계와 3단계는 게임이 자동 정산할 때까지 도전을 계속합니다. 프로그램에 12,800 등의 정산 목표 금액을 설정하지 않습니다.
- 2단계는 라운드 시작 보상을 한 번 확인하여 목표 성공 횟수를 정합니다. 이후의 보상 표시는 더블업 판단에 사용하지 않습니다.
- 하이/로 클릭 후 성공 확인 화면이 나오면 한 번 가산합니다. 무승부, 반복 화면, 클릭 재시도는 횟수를 늘리지 않습니다. 상한 도달로 바로 정산되는 마지막 성공도 한 번만 셉니다.
- 패배하면 라운드 성공 횟수를 초기화하고 같은 단계를 다시 시도합니다. 보상 정산이 확인되면 다음 단계로 진행합니다.

| 시작 보상 | 2단계 성공 횟수 | 보상 |
|---|---:|---:|
| 200 | 5 | 6,400 |
| 400 | 4 | 6,400 |
| 700 | 3 | 5,600 |
| 800 | 3 | 6,400 |
| 1,500 | 2 | 6,000 |
| 3,000 | 1 | 6,000 |
| 7,000 / 10,000 | 0 | 7,000 / 10,000 |

2단계 시작 시 당일 합계가 20,000 이상이 되는 성공 횟수를 제외하여 3단계를 남겨 둡니다. 기존 보상에 따라 목표 횟수가 표보다 줄어들 수 있습니다. 즉시 정산해도 상한에 도달하면 중지하고 수동 조작을 기다립니다. 1단계에서 게임의 일일 제한에 도달하면 프로그램이 이를 우회할 수 없습니다.

정산 금액은 시작 보상과 확인된 성공 횟수로 대조합니다. 단계와 코인은 `daily_coins.json`에 저장되며 같은 날 재시작하면 유지되고 다음 날짜에 초기화됩니다. 라운드 중간 재시작으로 성공 횟수를 알 수 없으면 중지하고 새 라운드에서 시작하도록 안내합니다. 진행 상황은 추정하지 않습니다. 3단계 성공 후 중지합니다. 업데이트는 과거 보상을 재구성하지 않습니다.

<a id="id"></a>

## Indonesian

Pilih “3 tahap: Maks → Jumlah menang → Maks”. Strategi asli tetap menjadi pilihan bawaan.

- Tahap pertama dan ketiga terus menantang hingga game menyelesaikan ronde secara otomatis. Program tidak menetapkan target pencairan seperti 12.800.
- Tahap kedua mengonfirmasi hadiah awal sekali dan menentukan target jumlah kemenangan. Pembacaan hadiah selanjutnya tidak menentukan keputusan penggandaan.
- Klik High/Low yang berhasil dan diikuti konfirmasi keberhasilan dihitung sekali. Seri, layar berulang dan percobaan klik ulang tidak menambah hitungan. Kemenangan terakhir yang langsung menghasilkan penyelesaian juga dihitung sekali.
- Kekalahan mengatur ulang hitungan ronde dan mengulangi tahap yang sama. Penyelesaian hadiah yang terkonfirmasi memajukan tahap.

| Hadiah awal | Kemenangan tahap kedua | Hadiah |
|---|---:|---:|
| 200 | 5 | 6,400 |
| 400 | 4 | 6,400 |
| 700 | 3 | 5,600 |
| 800 | 3 | 6,400 |
| 1,500 | 2 | 6,000 |
| 3,000 | 1 | 6,000 |
| 7,000 / 10,000 | 0 | 7,000 / 10,000 |

Pada awal tahap kedua, jumlah kemenangan yang akan membuat total harian mencapai 20.000 atau lebih dikecualikan agar tahap ketiga tetap tersedia. Hadiah sebelumnya dapat mengurangi target dari angka pada tabel. Jika pencairan langsung pun akan mencapai batas, program berhenti untuk penanganan manual. Program tidak dapat melewati batas harian yang ditetapkan game pada tahap pertama.

Jumlah penyelesaian diperiksa berdasarkan hadiah awal dan kemenangan terkonfirmasi. Kemajuan tahap dan Koin disimpan dalam `daily_coins.json`, dipertahankan saat dimulai ulang pada hari yang sama dan diatur ulang pada tanggal berikutnya. Jika dimulai ulang di tengah ronde tanpa hitungan kemenangan, program berhenti dan meminta ronde baru tanpa memperkirakan kemajuan. Program berhenti setelah tahap ketiga berhasil. Pembaruan tidak merekonstruksi hadiah sebelumnya.

<a id="zh-cn"></a>

## 简体中文

在策略选单选择「三阶段：最大 → 计次 → 最大」。原版仍为默认选项。

- 第一、第三阶段：持续挑战直到游戏自动结算，不设置 12,800 等软件止盈金额。
- 第二阶段：只在本局开始时确认一次起手奖励，确定目标成功次数，随后不再根据当前奖金判断翻倍。
- 只有点击猜高／低后出现成功询问，才增加一次成功；平手、重复画面、点击重试不增加次数。游戏达到上限直接结算时，最后一次成功也只计算一次。
- 失败后成功次数归零，重试同一阶段；确认结算入账后才推进阶段。

| 起手奖励 | 第二阶段成功次数 | 对应奖金 |
|---|---:|---:|
| 200 | 5 | 6,400 |
| 400 | 4 | 6,400 |
| 700 | 3 | 5,600 |
| 800 | 3 | 6,400 |
| 1,500 | 2 | 6,000 |
| 3,000 | 1 | 6,000 |
| 7,000 / 10,000 | 0 | 7,000 / 10,000 |

第二阶段会在起手时排除入账后累计达到 20,000 的次数选项，以保留第三阶段；因此已有收益较高时，次数可能低于表中数值。若立即收手也会跨上限，则停止等待手动处理。第一阶段若被游戏提前结束当日游玩，程序无法绕过每日限制。

结算时以起手奖励及成功次数核对金额，不允许缺位数字造成错误入账。三阶段进度与代币保存在 `daily_coins.json`，当日重开保留，下一日期重置。中途重新启动而缺少本局计数时，停止提示从新一局开始，不猜测已成功次数。第三阶段成功后停止。更新不会自动推算历史收益。
