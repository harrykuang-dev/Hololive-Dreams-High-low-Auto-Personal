# Personal repository

- Push fixes, tags and releases only to `harrykuang-dev/Hololive-Dreams-High-low-Auto-Personal`. Do not push to the public fork or the original author's repository.
- Preserve Conservative and Aggressive strategies. Display-only profit changes must not alter gross rewards or game decisions.
- Preserve `daily_coins.json` during upgrades and never infer historical credits, losses or wins. Reset daily totals and stage progress at the computer's local 04:00 boundary or after confirmation through the manual reset button. Legacy records without win counts cannot yield an exact daily profit.
- The user-facing application must not retain logs, screenshots, OCR images or diagnostic recordings. Preferences and the confirmed daily ledger are allowed.
- Build into a fresh staging directory, never into an active user installation.

## Documentation and publication

- Use short, objective English commit subjects describing the change. Avoid vague finalization wording and internal iteration or test narratives.
- Keep `README.md` in English and Traditional Chinese in `README.zh-TW.md`. Order language links and shared sections: English, Traditional Chinese, Japanese, Korean, Indonesian, Simplified Chinese. Synchronize common content and verify localized proper names and system terminology.
- Describe the software as a program: `program`, `程式`, `プログラム`, `프로그램`, `program`, `程序` in that language order.
- Use English release titles and English followed by Traditional Chinese in release descriptions. Describe current released features without internal validation reports, source hashes, push scope, experiment labels, or references to other personal projects.
- Keep current release information in README and release notes. Place superseded versions in a separate history file with distinct names and no dates; reserve `v` for formal releases.
- Retain meaningful development history and required third-party license notices. Rewriting public Git history requires a backup, a verified concrete preview, and explicit approval. Replacing released binaries, assets, or tag targets requires explicit authorization.
