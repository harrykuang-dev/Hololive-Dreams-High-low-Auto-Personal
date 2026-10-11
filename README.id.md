# Hololive Dreams — High & Low Otomatis

[English](README.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Indonesian](README.id.md) · [简体中文](README.zh-CN.md)

Program Windows untuk memainkan High & Low secara otomatis dengan strategi asli 1.0.1 dan strategi tiga tahap. Antarmuka mendukung bahasa Inggris, Tionghoa Tradisional, Jepang, Korea, Indonesia dan Tionghoa Sederhana.

## Unduh dan jalankan

Unduh **HololiveDreamsHighLowAuto.exe** dari [rilis terbaru](https://github.com/harrykuang-dev/Hololive-Dreams-High-low-Auto-Personal/releases/latest) lalu jalankan. Templat, model OCR dan sumber daya yang diperlukan disertakan dalam satu berkas eksekusi dan diekstrak sementara saat program dimulai.

1. Buka layar High & Low di dalam game.
2. Pilih strategi; strategi asli adalah pilihan bawaan.
3. Tekan **F8** untuk mulai dan **INSERT** untuk berhenti, atau gunakan tombol antarmuka.

Klik kolom pintasan, lalu tekan tombol atau kombinasi Ctrl / Alt / Shift untuk mengubahnya. **Esc** membatalkan perekaman. Pintasan mulai dan berhenti harus berbeda. Num Lock tidak menambahkan pengubah Alt.

## Catatan dan laba bersih

Koin hari ini menunjukkan total hadiah terkonfirmasi. Laba bersih adalah **hadiah terkonfirmasi − 50 × (ronde menang + ronde kalah)**. Setiap ronde menang yang telah diselesaikan juga dikenai biaya masuk 50 Koin. Pengurangan ini memperbaiki tampilan laba bersih; jumlah hadiah dan keputusan strategi mengikuti aturan yang sama.

`daily_coins.json` menyimpan hadiah harian, jumlah ronde dan kemajuan tiga tahap. `settings.json` menyimpan bahasa, strategi dan pintasan. Hentikan program sebelum memperbarui, lalu simpan kedua berkas di folder yang sama dengan EXE baru.

Catatan lama pada hari yang sama tanpa jumlah kemenangan tetap mempertahankan hadiah, tetapi laba bersih ditampilkan sebagai tidak tersedia. Biaya masuk sebelumnya tidak diperkirakan; pencatatan lengkap dilanjutkan pada tanggal berikutnya. Log dan tangkapan layar tidak disimpan.

## Jalankan dari sumber dan buat paket

```powershell
python -m pip install -r requirements.txt pyinstaller
python main_ui.py
python -m PyInstaller --noconfirm "Hololive Dreams-Auto.spec"
```

Hasil: `dist/HololiveDreamsHighLowAuto.exe`.

## Dokumentasi dan lisensi

[Strategi tiga tahap](THREE_STAGE.md#id) · [Istilah game](docs/GAME_TERMS.md) · [OCR hadiah](docs/OCR.md) · [Catatan rilis v1.1.0](docs/RELEASE-1.1.0.md) · [Riwayat versi](HISTORY.md)

Pengenalan kartu dan strategi pemilihan kartu yang dipertahankan didasarkan pada [hololive-dreams-helper](https://github.com/Oreki0504/hololive-dreams-helper). [Pemberitahuan MIT](licenses/poker-core-MIT.txt) dan pemberitahuan lisensi lain yang diperlukan disertakan dalam [licenses](licenses/).
