# Reward OCR

Challenge amounts are yellow and describe the reward after the next successful
double. Result amounts are cyan and describe the amount credited. The result
reader isolates cyan digits before OCR, excluding the grey caption and unit.
Mixed OCR text is rejected rather than stripped down to a smaller number.

The existing animation delay, stability checks and expected-cashout comparison
still control when a result is credited. An intermediate animation value such
as 80 is not evidence that the final reward was misread as 80.

The user-facing application does not save logs, OCR images, readings or card
tracking screenshots. Image processing stays in memory. Necessary status
messages are displayed only in the interface's bounded in-memory buffer;
no diagnostic files or directories are created. The daily coin record is
still saved to `daily_coins.json` so restarting preserves confirmed credits.

## Captured-frame regression and live verification

The September 30 investigation confirmed the running EXE matched source commit
`ed69c9c61e5b248186f957640380785b2dc5ff52`, including its challenge validation.
Two actual 400-result screenshots produced `400ö` and `40oö` with the previous
grayscale crop; deleting non-digit characters changed the latter to 40. The
expected-cashout check stopped the run without crediting that result. The new
cyan crop reads both as 400.

`tests/test_live_reward.py` includes game-only captures for challenge 800,
result 400 in two character-animation frames, challenge/result 12800, and a
genuine count-up animation value of 80. Run from the repository root:

```powershell
python -m unittest discover -s tests -v
```

The repaired original strategy credited 400, 400, 12800, 800, 3200, 1600 and
12000 on September 30, totaling 31200, then stopped. The existing daily record
was retained throughout; the final failure count was 26. Window-size operation
was separately confirmed by the user. The 11200 case was not captured in this
session. Both original and three-stage decision rules remain unchanged.
