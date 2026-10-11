# Reward OCR

The yellow challenge amount describes the reward after the next successful double. The cyan result amount describes the reward to be credited. These amounts are read separately; the result amount is not divided by two.

The result reader isolates cyan digits before OCR, excluding the grey caption and currency unit. It rejects text containing mixed characters instead of deleting characters to produce a smaller number.

Settlement waits for the reward animation, requires stable readings and checks the amount against the expected cashout. A mismatch stops the program without crediting an unconfirmed amount. Repeated settlement frames do not create duplicate credits.

Image processing and a bounded status buffer stay in memory. Logs, screenshots and OCR crops are not written to disk. Confirmed daily rewards remain in `daily_coins.json`.
