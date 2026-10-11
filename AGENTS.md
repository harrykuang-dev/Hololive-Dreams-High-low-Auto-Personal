# Maintenance rules

- Publish only to `harrykuang-dev/Hololive-Dreams-High-low-Auto-Personal`.
- Preserve Conservative and Aggressive game rules. Profit display changes must not affect rewards or decisions.
- Preserve `daily_coins.json` on upgrades. Never estimate historical rewards or round counts; missing win counts mean unavailable net profit.
- Store records and preferences in LocalAppData/HololiveDreamsHighLowAuto. Migrate legacy files without overwriting existing data.
- Reset records and strategy progress at local 04:00 or after manual confirmation.
- Persist only records and preferences; no runtime logs, screenshots or OCR dumps.
- Build in a fresh staging folder, outside active installations.

## Documentation

- Use concise, objective product descriptions and short English commit subjects; omit internal work and test narratives.
- Keep README content aligned in this order: English, Traditional Chinese, Japanese, Korean, Indonesian, Simplified Chinese. Use README.md for English and README.zh-TW.md for Traditional Chinese. Verify localized terminology. Call the software a program: `program`, `程式`, `プログラム`, `프로그램`, `program`, `程序`.
- Release titles are English; notes are English then Traditional Chinese. Describe the current release. Keep meaningful history and superseded versions in HISTORY.md; omit history dates and reserve `v` for formal versions.
- Retain required license notices. Public history rewrites require a backup, a verified preview and explicit approval. Replacing released binaries, assets or tag targets requires explicit authorization.
