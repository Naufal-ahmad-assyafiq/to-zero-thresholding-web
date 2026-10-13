# Praktikum 05: Teknik Segmentasi Citra dan Deteksi Objek

Repository ini memuat materi ajar lengkap, modul praktikum, dan implementasi kode Python untuk mata kuliah **Komputer Visi dan NLP** (Praktikum 05).

## Topik Pembelajaran
1. **Thresholding:**
   - Global Thresholding (Binary, Binary Inverted, Truncate, ToZero, ToZero Inverted)
   - Otsu's Thresholding (Pencarian nilai ambang optimal berbasis variansi antar-kelas)
   - Adaptive Thresholding (Mean-C dan Gaussian-C untuk pencahayaan tidak merata)
2. **Region Growing:**
   - Segmentasi berbasis wilayah dari titik *seed*
   - Implementasi antrean BFS (*Breadth-First Search*) dari awal (scratch)
   - Analisis toleransi ambang dan *Multi-Seed Region Growing*
3. **Pemisahan Objek dari Latar Belakang (*Background Separation*):**
   - Segmentasi warna berbasis ruang warna HSV (*Color Masking*)
   - Pembersihan derau mask dengan operasi morfologi (*Opening* & *Closing*)
   - Segmentasi *foreground* kompleks dengan algoritma *GrabCut*
4. **Contoh Penggunaan dalam Deteksi Objek:**
   - Pipeline deteksi objek terintegrasi
   - Ekstraksi kontur dan fitur morfometri (*Area*, *Perimeter*, *Centroid*, *Bounding Box*, *Circularity*)
   - Perhitungan jumlah objek otomatis (*Object Counting*)
5. **Perbandingan Metode Deteksi Tepi (*Edge Detection*):**
   - **Canny:** Garis tepi paling halus, tipis, kontinu, bebas noise (terbaik untuk presisi, komputasi rumit).
   - **Sobel:** Garis tepi jelas dan tebal, tajam pada sudut diagonal (bagus pola bentuk dasar, sensitif noise).
   - **Prewitt:** Sedikit lebih kaku dan kurang tajam dibanding Sobel (mudah implementasi tepi vertikal/horizontal).
   - **Roberts:** Garis tepi sangat sederhana, deteksi perubahan tajam (komputasi paling cepat, sering putus-putus).
6. **Segmentasi Citra Berbasis Clustering:**
   - **K-Means Clustering:** Mengelompokkan piksel berdasarkan kedekatan nilai fitur ke centroid secara tegas (*crisp / hard clustering*).
   - **Fuzzy C-Means (FCM):** Mengelompokkan piksel dengan derajat keanggotaan probabilistik ($u_{ij} \in [0, 1]$), memodelkan ketidakpastian pada batas objek (*soft / fuzzy clustering*).

---

## Struktur Berkas

```text
Praktikum05/
├── README.md                          # Dokumentasi ringkas dan petunjuk awal
├── MODUL_PRAKTIKUM_05.md              # Buku panduan lengkap praktikum & tugas mahasiswa
├── run_all.py                         # Eksekusi seluruh materi praktikum sekaligus
├── 00_generate_samples.py             # Pembuat citra sampel sintetis otomatis
├── 01_thresholding.py                 # Eksplorasi teknik thresholding
├── 02_region_growing.py               # Eksplorasi algoritma region growing
├── 03_pemisahan_objek_background.py   # Pemisahan objek via HSV, Morfologi, dan GrabCut
├── 04_deteksi_dan_analisis_objek.py   # Studi kasus end-to-end deteksi koin dan statistik
├── 05_deteksi_tepi.py                 # Eksperimen komparasi Canny, Sobel, Prewitt, & Roberts
├── 06_clustering.py                   # Segmentasi K-Means dan Fuzzy C-Means (FCM)
├── sample_images/                     # Citra masukan pengujian (.png)
├── output/                            # Visualisasi hasil eksekusi (.png)
└── web_app/                           # Visual Studio Web Application (Flask, JS, CSS)
```

---

## Panduan Menjalankan Kode

### 1. Instalasi Dependensi
Pastikan Python 3 telah terpasang bersama paket-paket pendukung:
```bash
pip install opencv-python numpy matplotlib scipy
```

### 2. Menjalankan Aplikasi Web Studio (Single Menu Web Version)
Aplikasi menyediakan antarmuka web interaktif terpadu (dashboard single-menu) untuk pembelajaran visual langsung:
```bash
python3 web_app/app.py
```
Buka peramban (browser) di: **[http://localhost:5050](http://localhost:5050)**

Fitur pada Versi Web:
* **Thresholding Studio:** Pilihan metode instan (Otsu, Global Binary, Adaptive Mean/Gaussian), slider nilai ambang interaktif, dan grafik live histogram.
* **Region Growing:** Klik langsung pada kanvas citra untuk memilih *seed point*, atur toleransi $\Delta I$, dan amati pemuaian wilayah secara real-time.
* **Pemisahan Latar (HSV & GrabCut):** Preset warna cepat (*Apel Merah*, *Jeruk Kuning*, *Alpukat Hijau*), pembersihan morfologi, serta segmentasi latar depan *GrabCut*.
* **Deteksi & Analisis Objek:** Deteksi kontur otomatis, bounding box, titik berat (centroid), metrik kebundaran (*circularity*), serta tabel data morfometri interaktif.
* **Citra Sampel & Unggah Berkas:** Pilihan 4 citra sampel praktikum atau unggah citra Anda sendiri (drag-and-drop / file upload).

### 3. Menjalankan Seluruh Modul CLI Sekaligus
```bash
python3 run_all.py
```

### 4. Menjalankan Per Bagian Secara Terpisah
```bash
# Tahap 0: Generate citra sampel
python3 00_generate_samples.py

# Tahap 1: Eksperimen Thresholding
python3 01_thresholding.py

# Tahap 2: Eksperimen Region Growing
python3 02_region_growing.py

# Tahap 3: Pemisahan Objek Latar Belakang (HSV, Morfologi, GrabCut)
python3 03_pemisahan_objek_background.py

# Tahap 4: Deteksi & Karakterisasi Objek
python3 04_deteksi_dan_analisis_objek.py

# Tahap 5: Perbandingan Deteksi Tepi (Canny, Sobel, Prewitt, Roberts)
python3 05_deteksi_tepi.py

# Tahap 6: Segmentasi Clustering (K-Means & Fuzzy C-Means)
python3 06_clustering.py
```

Semua visualisasi grafik dan perbandingan akan tersimpan secara otomatis dalam format gambar beresolusi tinggi di direktori `output/`.
Silakan buka [MODUL_PRAKTIKUM_05.md](file:///Users/mac/Documents/Materi%20Pengajaran-2025/14.%20Komputer%20Visi%20dan%20NLP/Praktikum/Praktikum05/MODUL_PRAKTIKUM_05.md) untuk panduan teori lengkap, langkah hands-on, dan penugasan mandiri.
