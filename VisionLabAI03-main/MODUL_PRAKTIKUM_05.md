# MODUL PRAKTIKUM 05: SEGMENTASI CITRA DIGITAL & PEMISAHAN OBJEK

**Mata Kuliah:** Komputer Visi dan Pemrosesan Bahasa Alami (NLP)  
**Tahun Akademik:** 2025/2026  
**Topik:** Teknik Segmentasi Citra (Thresholding, Region Growing), Pemisahan Objek dari Latar Belakang, dan Deteksi Objek  

---

## 1. Capaian Pembelajaran Praktikum (CPMK)

Setelah menyelesaikan modul praktikum ini, mahasiswa diharapkan mampu:
1. **Memahami Konsep Dasar Segmentasi Citra:** Menjelaskan pembagian citra menjadi region-region yang homogen berdasarkan kesamaan intensitas, warna, atau tekstur.
2. **Menguasai Teknik Thresholding:** Menerapkan dan membandingkan *Global Thresholding*, *Otsu's Binarization*, serta *Adaptive Thresholding* (*Mean-C* dan *Gaussian-C*) pada berbagai kondisi pencahayaan.
3. **Menerapkan Algoritma Region Growing:** Merancang algoritma segmentasi berbasis wilayah (*region-based*) menggunakan penentuan *seed point*, kriteria batas toleransi (*similarity threshold*), dan antrean (*BFS Queue*).
4. **Memisahkan Objek dari Latar Belakang:** Mengisolasi objek spesifik menggunakan ruang warna HSV (*Color Masking*), operasi morfologi (*Opening* & *Closing*), serta algoritma canggih *GrabCut*.
5. **Membangun Pipeline Deteksi Objek:** Mengintegrasikan hasil segmentasi dengan ekstraksi kontur, ekstraksi fitur morfometri (*area*, *perimeter*, *centroid*, *bounding box*, *circularity*), serta perhitungan jumlah objek (*object counting*).

---

## 2. Landasan Teori

### 2.1 Definisi Segmentasi Citra
Secara formal, jika $R$ merepresentasikan seluruh domain citra, segmentasi mempartisi $R$ menjadi $n$ subwilayah $R_1, R_2, \dots, R_n$ sedemikian rupa sehingga:
1. $\bigcup_{i=1}^{n} R_i = R$ (seluruh piksel terpartisi).
2. $R_i \cap R_j = \emptyset, \forall i \ne j$ (antar-wilayah saling lepas/disjoint).
3. $P(R_i) = \text{TRUE}$ untuk semua $i$ (semua piksel dalam satu wilayah memenuhi kriteria kesamaan/homogenitas).
4. $P(R_i \cup R_j) = \text{FALSE}$ untuk wilayah bersebelahan (tidak ada dua wilayah berdampingan yang memiliki properti homogen yang sama).

---

### 2.2 Penambangan Ambang (Thresholding)

Thresholding mengubah citra skala abu-abu $f(x, y)$ menjadi citra biner $g(x, y)$ dengan nilai ambang $T$:

$$
g(x, y) = 
\begin{cases} 
255, & \text{jika } f(x, y) \ge T \\
0, & \text{jika } f(x, y) < T 
\end{cases}
$$

#### A. Global Thresholding
Menggunakan nilai ambang tunggal $T$ konstan untuk seluruh citra. Macam-macam operasi ambang di OpenCV:
* `THRESH_BINARY`: Piksel $> T$ menjadi nilai maksimum (255), sisanya 0.
* `THRESH_BINARY_INV`: Piksel $> T$ menjadi 0, sisanya 255.
* `THRESH_TRUNC`: Piksel $> T$ dipotong menjadi $T$, sisanya tetap.
* `THRESH_TOZERO`: Piksel $< T$ diset ke 0, sisanya tetap.
* `THRESH_TOZERO_INV`: Piksel $> T$ diset ke 0, sisanya tetap.

#### B. Otsu's Binarization
Otsu adalah metode non-parametrik tanpa supervisi untuk menentukan nilai ambang optimal $T^*$ secara otomatis pada citra dengan histogram bimodal. Otsu memaksimalkan variansi antar-kelas (*between-class variance* $\sigma_B^2$):

$$
\sigma_B^2(T) = \omega_0(T) \omega_1(T) [\mu_0(T) - \mu_1(T)]^2
$$

di mana:
* $\omega_0(T)$ dan $\omega_1(T)$ adalah probabilitas kemunculan kelas latar belakang dan latar depan pada threshold $T$.
* $\mu_0(T)$ dan $\mu_1(T)$ adalah rata-rata nilai intensitas kedua kelas tersebut.

#### C. Adaptive Thresholding
Ketika citra memiliki pencahayaan tidak seragam (*non-uniform / gradient illumination*), satu nilai ambang global akan gagal. Adaptive thresholding menghitung nilai ambang lokal $T(x,y)$ untuk setiap piksel berdasarkan ketetanggaan berukuran $b \times b$:
* **Adaptive Mean:** $T(x,y) = \text{Mean}(N_{b \times b}(x,y)) - C$
* **Adaptive Gaussian:** $T(x,y) = \text{WeightedGaussian}(N_{b \times b}(x,y)) - C$

---

### 2.3 Segmentasi Berbasis Wilayah (Region Growing)

Region Growing mengelompokkan piksel tetangga ke dalam wilayah yang sama jika memenuhi kriteria kesamaan (*homogeneity/similarity criterion*).

```
[Titik Awal: Seed (x0, y0)]
            │
            ▼
   [Periksa Tetangga] ── (Konektivitas 4 atau 8)
            │
            ▼
    [Uji Kriteria]  ──> |I(x,y) - I_ref| <= Threshold?
      ├── YA  : Tandai piksel, masukkan ke antrean BFS, perbarui statistik
      └── TIDAK: Abaikan piksel
            │
            ▼
   [Ulangi hingga antrean kosong]
```

* **Seed Selection:** Pemilihan titik awal dapat dilakukan manual (titik minat) atau otomatis (titik lokal ekstrim pada histogram/citra).
* **Kriteria Penghentian (*Stopping Criteria*):** Ukuran region maksimum tercapai, atau tidak ada lagi piksel tetangga yang memenuhi toleransi $\Delta I \le T$.
* **Tantangan Region Growing:**
  * *Under-segmentation:* Threshold terlalu kecil sehingga region berhenti sebelum mencakup seluruh objek.
  * *Over-segmentation / Leakage:* Threshold terlalu besar sehingga segmentasi "bocor" merembes ke latar belakang melalui celah intensitas yang mirip.

---

### 2.4 Pemisahan Objek dan Latar Belakang

#### A. Segmentasi Warna HSV
Ruang warna RGB menggabungkan informasi kromatik (warna) dan luminansi (kecerahan) dalam tiap kanalnya, membuatnya sangat sensitif terhadap bayangan. Ruang warna HSV memisahkan:
* **H (Hue):** Corak warna murni (0–179 di OpenCV).
* **S (Saturation):** Kemurnian/kejenuhan warna (0–255).
* **V (Value):** Kecerahan warna (0–255).

Dengan memanfaatkan `cv2.inRange(img_hsv, lower_bound, upper_bound)`, objek dapat diisolasi tanpa terpengaruh variasi pencahayaan.

#### B. Operasi Morfologi Citra
Setelah thresholding atau masking warna, mask sering mengandung noise:
* **Opening ($A \circ B = (A \ominus B) \oplus B$):** Erosi diikuti Dilasi. Efektif menghapus bintik-bintik putih kecil (*false foreground*) di luar objek.
* **Closing ($A \bullet B = (A \oplus B) \ominus B$):** Dilasi diikuti Erosi. Efektif menutup lubang-lubang kecil (*holes*) di dalam tubuh objek.

#### C. Algoritma GrabCut
GrabCut memanfaatkan pendekatan *Gaussian Mixture Models* (GMM) dan optimasi graf (*Min-Cut/Max-Flow graph cut*) untuk mengekstraksi objek latar depan bertekstur kompleks hanya dengan mendefinisikan *bounding box* awal.

---

### 2.5 Ekstraksi Fitur dan Deteksi Objek

Setelah citra biner yang bersih terbentuk, kontur objek dideteksi (`cv2.findContours`). Fitur morfometri yang diekstraksi meliputi:
1. **Luas Area ($A$):** `cv2.contourArea(cnt)`
2. **Keliling ($P$):** `cv2.arcLength(cnt, closed=True)`
3. **Centroid $(C_x, C_y)$:** Dihitung dari momen spasial citra (*Image Moments*):
   $$C_x = \frac{m_{10}}{m_{00}}, \quad C_y = \frac{m_{01}}{m_{00}}$$
4. **Bounding Box:** Kotak pembatas tegak $(x, y, w, h)$ menggunakan `cv2.boundingRect(cnt)`.
5. **Kebundaran / Circularity ($C$):**
   $$C = \frac{4 \pi \cdot A}{P^2}$$
   Nilai $C \approx 1.0$ mengindikasikan bentuk lingkaran sempurna (misal koin atau sel darah).

---

### 2.6 Metode Deteksi Tepi (Edge Detection)

Deteksi tepi mengidentifikasi titik-titik diskontinuitas intensitas piksel yang tajam pada citra untuk mendeteksi batas fisik objek.

#### Tabel Perbandingan Metode Deteksi Tepi

| Metode | Karakteristik Hasil Gambar | Kelebihan / Kekurangan |
| :--- | :--- | :--- |
| **Canny** | Menghasilkan garis tepi yang paling halus, tipis, kontinu (menyambung), dan bersih dari derau (noise). | Terbaik untuk deteksi objek presisi, tetapi proses komputasinya lebih rumit. |
| **Sobel** | Garis tepi yang dihasilkan cukup jelas dan tebal, terutama pada sudut diagonal. | Bagus untuk mendeteksi pola bentuk dasar objek, namun sensitif terhadap gangguan noise. |
| **Prewitt** | Mirip dengan Sobel, tetapi garis tepi yang dihasilkan cenderung sedikit lebih kaku dan kurang tajam dibanding Sobel. | Sangat mudah diimplementasikan untuk mendeteksi tepi vertikal dan horizontal. |
| **Roberts** | Menghasilkan garis tepi yang sangat sederhana dan hanya mendeteksi perubahan intensitas yang sangat tajam. | Proses komputasinya paling cepat, tetapi hasilnya sering kali kurang detail atau putus-putus. |

---

### 2.7 Segmentasi Berbasis Clustering (K-Means & Fuzzy C-Means)

**Clustering:** Mengelompokkan piksel berdasarkan kedekatan nilai fitur, seperti algoritma *K-Means* atau *Fuzzy C-Means* (FCM).

#### A. K-Means Clustering (Crisp / Hard Partitioning)
Mengelompokkan $N$ piksel ke dalam $K$ kelompok secara tegas sedemikian hingga jarak Euclidean antara nilai warna piksel dan pusat kluster (*centroid*) diminimalkan:
$$J = \sum_{j=1}^K \sum_{i=1}^{N_j} \|x_i^{(j)} - c_j\|^2$$
* Tiap piksel memiliki label diskrit tunggal: $u_{ij} \in \{0, 1\}$.
* Sangat cepat dan efisien untuk kuantisasi warna dan segmentasi wilayah homogen.

#### B. Fuzzy C-Means (Soft / Fuzzy Partitioning)
Setiap piksel memiliki derajat keanggotaan probabilistik $u_{ij} \in [0, 1]$ pada setiap kluster $j$:
$$J_m = \sum_{i=1}^N \sum_{j=1}^C u_{ij}^m \|x_i - c_j\|^2, \quad \sum_{j=1}^C u_{ij} = 1$$
* Parameter $m > 1$ mengontrol tingkat kekaburan (*fuzziness*, standar $m=2.0$).
* Sangat unggul memodelkan ketidakpastian pada batas objek alami (*fuzzy transition boundary*).

---

## 3. Struktur Berkas Praktikum

Folder praktikum ini terorganisir sebagai berikut:

```
Praktikum05/
├── README.md                          # Ringkasan cepat & petunjuk eksekusi
├── MODUL_PRAKTIKUM_05.md              # Buku panduan lengkap (berkas ini)
├── run_all.py                         # Skrip runner otomatis seluruh materi
├── 00_generate_samples.py             # Generator citra sampel sintetis
├── 01_thresholding.py                 # Demonstrasi Global, Otsu, & Adaptive Thresholding
├── 02_region_growing.py               # Implementasi algoritma Region Growing dari awal
├── 03_pemisahan_objek_background.py   # Pemisahan objek via HSV, Morfologi, & GrabCut
├── 04_deteksi_dan_analisis_objek.py   # Studi kasus deteksi koin, centroid, & counting
├── 05_deteksi_tepi.py                 # Perbandingan deteksi tepi Canny, Sobel, Prewitt, Roberts
├── 06_clustering.py                   # Segmentasi K-Means dan Fuzzy C-Means (FCM)
├── sample_images/                     # Folder kumpulan citra uji (*.png)
├── output/                            # Folder hasil plot visualisasi eksperimen (*.png)
└── web_app/                           # Visual Studio Segmentasi Citra Interaktif (Port 5050)
```

---

## 4. Langkah-Langkah Praktikum (Hands-On)

### Langkah 1: Persiapan Lingkungan & Generator Sampel
Buka terminal dan pastikan pustaka yang diperlukan telah terpasang:
```bash
pip install opencv-python numpy matplotlib scipy
```

Jalankan skrip generator citra sampel:
```bash
python3 00_generate_samples.py
```
*Output yang dihasilkan:*
* `sample_images/uneven_light.png`: Citra bergradien pencahayaan ekstrem.
* `sample_images/bimodal_coins.png`: Citra koin dengan latar kontras dan noise.
* `sample_images/shapes_noisy.png`: Citra aneka bentuk untuk pengujian region growing.
* `sample_images/fruits_color.png`: Citra aneka buah berwarna untuk pengujian HSV dan GrabCut.

---

### Langkah 2: Eksperimen Thresholding
Jalankan skrip bagian 1:
```bash
python3 01_thresholding.py
```
* **Amati:** Bandingkan histogram citra koin dengan nilai threshold Otsu yang dihitung secara matematis.
* **Perhatikan:** Buka berkas `output/01_thresholding_comparison.png`. Mengapa Global Otsu mengalami kegagalan pada citra `uneven_light.png` sementara Adaptive Thresholding mampu memisahkan teks dengan jelas?

---

### Langkah 3: Eksperimen Region Growing
Jalankan skrip bagian 2:
```bash
python3 02_region_growing.py
```
* **Eksperimen Parameter:** 
  * Pelajari implementasi fungsi `region_growing()` menggunakan struktur data `collections.deque`.
  * Bandingkan hasil dengan nilai threshold $T=5$ (terlalu kaku), $T=15$ (optimal), dan $T=90$ (terjadi *leakage* / kebocoran wilayah ke latar belakang).
  * Amati hasil *Multi-Seed Region Growing* yang mampu memberikan label unik pada 4 objek geometris berbeda secara simultan.

---

### Langkah 4: Pemisahan Objek dan Latar Belakang
Jalankan skrip bagian 3:
```bash
python3 03_pemisahan_objek_background.py
```
* **Pahami Ruang Warna HSV:** Mengapa warna merah perlu didefinisikan dalam dua rentang nilai Hue (rentang 0–10 dan 160–180)?
* **Pembersihan Morfologi:** Perhatikan bagaimana operasi `MORPH_OPEN` dan `MORPH_CLOSE` menyempurnakan mask biner.
* **Algoritma GrabCut:** Perhatikan bagaimana GrabCut secara akurat mengekstrak bentuk apel dan mengganti latar belakangnya dengan warna putih bersih.

---

### Langkah 5: Pipeline Deteksi & Analisis Objek
Jalankan skrip bagian 4:
```bash
python3 04_deteksi_dan_analisis_objek.py
```
* **Alur End-to-End:** 
  $\text{Citra Input} \rightarrow \text{Gaussian Blur} \rightarrow \text{Otsu Binarization} \rightarrow \text{Morfologi} \rightarrow \text{findContours} \rightarrow \text{Ekstraksi Fitur}$
* **Statistik Objek:** Skrip akan mencetak tabel statistik 9 objek koin (ID, koordinat centroid, luas area piksel, keliling, dan metrik *circularity*).

---

## 5. Tugas dan Latihan Mandiri Mahasiswa

### Tugas 1: Analisis Sensitivitas Parameter Adaptive Thresholding (Bobot: 30%)
Modifikasi berkas `01_thresholding.py` untuk menguji parameter `blockSize` (misal 7, 15, 31, 51) dan nilai konstanta `C` (misal 2, 5, 10) pada metode `ADAPTIVE_THRESH_GAUSSIAN_C`.
* **Pertanyaan:** Bagaimana pengaruh ukuran blok terhadap detail tepi teks kecil dan ketahanan terhadap noise latar belakang? Tuliskan temuan Anda dalam laporan.

### Tugas 2: Segmentasi Objek Kuning & Hijau via HSV (Bobot: 35%)
Pada berkas `03_pemisahan_objek_background.py`, lengkapi fungsi untuk mengekstrak buah kuning (lemon) dan buah hijau (alpukat/pear):
1. Tentukan batas bawah (*lower bound*) dan batas atas (*upper bound*) nilai HSV untuk masing-masing buah.
2. Terapkan operasi morfologi untuk membersihkan mask.
3. Buat citra gabungan di mana hanya buah kuning dan hijau yang ditampilkan dengan warna aslinya, sedangkan latar belakang dan buah merah diubah menjadi grayscale.

### Tugas 3: Deteksi dan Klasifikasi Bentuk Geometris (Bobot: 35%)
Gunakan citra `sample_images/shapes_noisy.png` dan terapkan pipeline dari `04_deteksi_dan_analisis_objek.py`.
1. Ekstraksi fitur metrik `circularity` dan aproksimasi poligon (`cv2.approxPolyDP`).
2. Klasifikasikan masing-masing objek ke dalam:
   * **Lingkaran:** Jika $C > 0.85$
   * **Segitiga:** Jika jumlah titik simpul poligon = 3
   * **Kotak / Persegi:** Jika jumlah titik simpul poligon = 4
3. Tampilkan label nama bentuk pada masing-masing objek di atas citra visualisasi.

---

## 6. Pertanyaan Evaluasi Pemahaman

1. **Jelaskan perbedaan mendasar antara segmentasi berbasis batas (*edge-based*) dan segmentasi berbasis wilayah (*region-based*)! Kapan Region Growing lebih unggul dibandingkan deteksi tepi Canny?**
2. **Mengapa pada metode Otsu sering kali disarankan untuk menerapkan filter pelembut (misal Gaussian Blur) sebelum proses binarisasi?**
3. **Apa yang menyebabkan terjadinya fenomena *leakage* (kebocoran region) pada algoritma Region Growing, dan sebutkan 2 strategi untuk mencegahnya!**
4. **Jelaskan mengapa representasi warna HSV sering kali lebih disukai daripada RGB dalam tugas pemisahan objek di dunia nyata!**

---

## 7. Referensi

1. Gonzalez, R. C., & Woods, R. E. (2018). *Digital Image Processing* (4th ed.). Pearson. (Chapter 10: Image Segmentation).
2. Bradski, G., & Kaehler, A. (2008). *Learning OpenCV: Computer Vision with the OpenCV Library*. O'Reilly Media.
3. Otsu, N. (1979). *A threshold selection method from gray-level histograms*. IEEE Transactions on Systems, Man, and Cybernetics, 9(1), 62-66.
4. Rother, C., Kolmogorov, V., & Blake, A. (2004). *"GrabCut": interactive foreground extraction using iterated graph cuts*. ACM Transactions on Graphics (TOG), 23(3), 309-314.
