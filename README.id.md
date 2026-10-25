# Hololive Dreams — High & Low Otomatis

[English](README.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Indonesian](README.id.md) · [简体中文](README.zh-CN.md)

Program Windows untuk memainkan High & Low secara otomatis dengan strategi Konservatif dan Agresif. Antarmuka mendukung bahasa Inggris, Tionghoa Tradisional, Jepang, Korea, Indonesia dan Tionghoa Sederhana.

## Unduh dan jalankan

Unduh **HololiveDreamsHighLowAuto.exe** dari [rilis terbaru](https://github.com/harrykuang-dev/Hololive-Dreams-High-low-Auto-Personal/releases/latest) lalu jalankan. Templat, model OCR dan sumber daya yang diperlukan disertakan dalam satu berkas eksekusi dan diekstrak sementara saat program dimulai.

1. Buka layar High & Low di dalam game.
2. Pilih Konservatif atau Agresif; Konservatif adalah pilihan bawaan.
3. Tekan **F8** untuk mulai dan **INSERT** untuk berhenti, atau gunakan tombol antarmuka.

Klik kolom pintasan, lalu tekan tombol atau kombinasi Ctrl / Alt / Shift untuk mengubahnya. **Esc** membatalkan perekaman. Pintasan mulai dan berhenti harus berbeda.

## Catatan dan laba bersih

Koin hari ini menunjukkan total hadiah terkonfirmasi. Laba bersih adalah **hadiah terkonfirmasi − 50 × (ronde menang + ronde kalah)**.

`daily_coins.json` menyimpan hadiah harian, jumlah ronde dan kemajuan strategi Agresif. `settings.json` menyimpan bahasa, strategi dan pintasan. Kedua berkas disimpan di `%LOCALAPPDATA%\HololiveDreamsHighLowAuto\`. Hentikan program sebelum memperbarui dan ganti EXE. Saat pertama dijalankan, catatan dan pengaturan yang ada di sebelah EXE dipindahkan ke folder ini; berkas yang sudah ada di AppData tidak ditimpa.

Catatan harian dan kemajuan strategi Agresif direset pada **pukul 04.00 menurut waktu lokal komputer**. Tombol **Reset catatan harian** mereset hadiah, laba bersih, jumlah ronde dan kemajuan strategi Agresif setelah konfirmasi. Gunakan reset manual jika server dan komputer berada di zona waktu berbeda.

## Jalankan dari sumber dan buat paket

```powershell
python -m pip install -r requirements.txt pyinstaller
python main_ui.py
python -m PyInstaller --noconfirm "Hololive Dreams-Auto.spec"
```

Hasil: `dist/HololiveDreamsHighLowAuto.exe`.

## Dokumentasi dan lisensi

[Strategi Agresif](THREE_STAGE.md#id) · [Istilah game](docs/GAME_TERMS.md) · [OCR hadiah](docs/OCR.md) · [Catatan rilis v1.1.2](docs/RELEASE-1.1.2.md) · [Riwayat versi](HISTORY.md)

Pengenalan kartu dan strategi pemilihan kartu yang dipertahankan didasarkan pada [hololive-dreams-helper](https://github.com/Oreki0504/hololive-dreams-helper). [Pemberitahuan MIT](licenses/poker-core-MIT.txt) dan pemberitahuan lisensi lain yang diperlukan disertakan dalam [licenses](licenses/).
