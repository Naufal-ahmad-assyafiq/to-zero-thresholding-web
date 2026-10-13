"""
Modul Praktikum 05 - Bagian 5: Perbandingan Metode Deteksi Tepi
Metode yang diimplementasikan:
1. Canny
2. Sobel
3. Prewitt
4. Roberts

Sesuai tabel karakteristik & komparasi:
- Canny: Menghasilkan garis tepi paling halus, tipis, kontinu, dan bersih dari derau (noise).
- Sobel: Garis tepi cukup jelas dan tebal, terutama pada sudut diagonal.
- Prewitt: Mirip Sobel, sedikit lebih kaku dan kurang tajam dibanding Sobel.
- Roberts: Menghasilkan garis tepi sangat sederhana, deteksi perubahan intensitas sangat tajam (paling cepat).
"""

import os
import sys
import time
import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import convolve

def run_edge_detection(input_path, output_dir="output"):
    # 1. Muat gambar sampel dalam skala abu-abu
    if not os.path.exists(input_path):
        print(f"[ERROR] Berkas citra tidak ditemukan di: {input_path}")
        return

    img = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"[ERROR] Gagal membaca citra dari: {input_path}")
        return

    os.makedirs(output_dir, exist_ok=True)
    total_pixels = img.shape[0] * img.shape[1]

    print("\n" + "=" * 80)
    print("  EKSPERIMEN PERBANDINGAN METODE DETEKSI TEPI (PRAKTIKUM 05)")
    print("=" * 80)
    print(f"Citra Uji  : {input_path}")
    print(f"Resolusi   : {img.shape[1]}x{img.shape[0]} piksel ({total_pixels:,} total piksel)\n")

    # A. Deteksi Tepi Canny
    t0 = time.perf_counter()
    canny_edges = cv2.Canny(img, threshold1=100, threshold2=200)
    t_canny = (time.perf_counter() - t0) * 1000

    # B. Deteksi Tepi Sobel
    t0 = time.perf_counter()
    sobel_x = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=3)
    sobel_edges = np.hypot(sobel_x, sobel_y)
    t_sobel = (time.perf_counter() - t0) * 1000

    # C. Deteksi Tepi Prewitt
    t0 = time.perf_counter()
    kernel_prewitt_x = np.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]], dtype=float)
    kernel_prewitt_y = np.array([[-1, -1, -1], [0, 0, 0], [1, 1, 1]], dtype=float)
    prewitt_x = convolve(img.astype(float), kernel_prewitt_x)
    prewitt_y = convolve(img.astype(float), kernel_prewitt_y)
    prewitt_edges = np.hypot(prewitt_x, prewitt_y)
    t_prewitt = (time.perf_counter() - t0) * 1000

    # D. Deteksi Tepi Roberts
    t0 = time.perf_counter()
    kernel_roberts_x = np.array([[1, 0], [0, -1]], dtype=float)
    kernel_roberts_y = np.array([[0, 1], [-1, 0]], dtype=float)
    roberts_x = convolve(img.astype(float), kernel_roberts_x)
    roberts_y = convolve(img.astype(float), kernel_roberts_y)
    roberts_edges = np.hypot(roberts_x, roberts_y)
    t_roberts = (time.perf_counter() - t0) * 1000

    # Hitung statistik piksel tepi (>50 threshold untuk representasi visual)
    canny_cnt = int(np.count_nonzero(canny_edges > 0))
    sobel_cnt = int(np.count_nonzero(sobel_edges > 50))
    prewitt_cnt = int(np.count_nonzero(prewitt_edges > 50))
    roberts_cnt = int(np.count_nonzero(roberts_edges > 50))

    # Tampilkan tabel perbandingan di konsol
    print("-" * 115)
    print(f"{'Metode':<10} | {'Waktu (ms)':<11} | {'Piksel Tepi':<12} | {'Karakteristik Hasil Gambar':<45} | {'Kelebihan / Kekurangan'}")
    print("-" * 115)
    print(f"{'Canny':<10} | {t_canny:<11.2f} | {canny_cnt:<12} | {'Paling halus, tipis, kontinu, bebas noise':<45} | {'Presisi tinggi, komputasi rumit'}")
    print(f"{'Sobel':<10} | {t_sobel:<11.2f} | {sobel_cnt:<12} | {'Cukup jelas dan tebal, tajam pd diagonal':<45} | {'Bagus utk bentuk dasar, sensitif noise'}")
    print(f"{'Prewitt':<10} | {t_prewitt:<11.2f} | {prewitt_cnt:<12} | {'Sedikit lebih kaku & kurang tajam vs Sobel':<45} | {'Mudah implementasi tepi vertikal/horiz'}")
    print(f"{'Roberts':<10} | {t_roberts:<11.2f} | {roberts_cnt:<12} | {'Sangat sederhana, deteksi gradien tajam':<45} | {'Komputasi paling cepat, sering putus-putus'}")
    print("-" * 115)

    # Plot dan tampilkan perbandingan (5 Subplot)
    plt.figure(figsize=(14, 9))
    titles = [
        'Gambar Asli Grayscale',
        f'Metode Canny (T1=100, T2=200)\n[{t_canny:.2f} ms]',
        f'Metode Sobel (Kernel 3x3)\n[{t_sobel:.2f} ms]',
        f'Metode Prewitt (Kernel 3x3)\n[{t_prewitt:.2f} ms]',
        f'Metode Roberts (Kernel 2x2)\n[{t_roberts:.2f} ms]'
    ]
    images = [img, canny_edges, sobel_edges, prewitt_edges, roberts_edges]

    for i in range(5):
        plt.subplot(2, 3, i + 1)
        plt.imshow(images[i], cmap='gray')
        plt.title(titles[i], fontsize=11, fontweight='bold')
        plt.axis('off')

    # Subplot ke-6: Tabel Ringkasan Komparasi
    ax_table = plt.subplot(2, 3, 6)
    ax_table.axis('off')
    table_data = [
        ["Canny", f"{t_canny:.2f} ms", "Halus, tipis, kontinu", "Presisi tinggi"],
        ["Sobel", f"{t_sobel:.2f} ms", "Cukup jelas & tebal", "Sensitif noise"],
        ["Prewitt", f"{t_prewitt:.2f} ms", "Sedikit lebih kaku", "Mudah h/v"],
        ["Roberts", f"{t_roberts:.2f} ms", "Sederhana/tajam", "Paling cepat"]
    ]
    col_labels = ["Metode", "Waktu", "Karakteristik", "Kelebihan"]
    table = ax_table.table(cellText=table_data, colLabels=col_labels, loc='center', cellLoc='left')
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.1, 2.0)
    ax_table.set_title("Ringkasan Metrik Komparasi", fontsize=11, fontweight='bold')

    plt.tight_layout()
    save_path = os.path.join(output_dir, "05_deteksi_tepi_comparison.png")
    plt.savefig(save_path, dpi=180, bbox_inches='tight')
    plt.close()
    print(f"\n[OK] Plot perbandingan deteksi tepi berhasil disimpan di: {save_path}\n")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sample_img = os.path.join(base_dir, "sample_images", "bimodal_coins.png")
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        sample_img = sys.argv[1]
    run_edge_detection(sample_img)
