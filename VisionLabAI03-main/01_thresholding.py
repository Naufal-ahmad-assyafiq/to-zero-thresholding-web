"""
Modul Praktikum 05 - Bagian 1: Teknik Penambangan Ambang (Thresholding)
Topik:
1. Global Thresholding (Binary, Binary Inv, Trunc, ToZero)
2. Otsu's Thresholding (Penentuan ambang otomatis berbasis histogram bimodal)
3. Adaptive Thresholding (Mean-C vs Gaussian-C) untuk menangani variasi pencahayaan
"""

import os
import cv2
import numpy as np
import matplotlib.pyplot as plt

def demo_global_thresholding(img_gray):
    """
    Mendemonstrasikan berbagai mode Global Thresholding dengan nilai ambang tetap (T=127).
    """
    threshold_value = 127
    max_value = 255

    ret, thresh_bin = cv2.threshold(img_gray, threshold_value, max_value, cv2.THRESH_BINARY)
    ret, thresh_bin_inv = cv2.threshold(img_gray, threshold_value, max_value, cv2.THRESH_BINARY_INV)
    ret, thresh_trunc = cv2.threshold(img_gray, threshold_value, max_value, cv2.THRESH_TRUNC)
    ret, thresh_tozero = cv2.threshold(img_gray, threshold_value, max_value, cv2.THRESH_TOZERO)
    ret, thresh_tozero_inv = cv2.threshold(img_gray, threshold_value, max_value, cv2.THRESH_TOZERO_INV)

    results = {
        "Original Grayscale": img_gray,
        "THRESH_BINARY (T=127)": thresh_bin,
        "THRESH_BINARY_INV": thresh_bin_inv,
        "THRESH_TRUNC": thresh_trunc,
        "THRESH_TOZERO": thresh_tozero,
        "THRESH_TOZERO_INV": thresh_tozero_inv
    }
    return results

def demo_otsu_thresholding(img_bimodal):
    """
    Mendemonstrasikan Otsu's Binarization.
    Algoritma Otsu secara otomatis mencari threshold T optimal yang memaksimalkan
    variansi antar-kelas (between-class variance) pada citra berhistogram bimodal.
    """
    # 1. Global Thresholding biasa (T=127 acak)
    ret_global, thresh_global = cv2.threshold(img_bimodal, 127, 255, cv2.THRESH_BINARY)

    # 2. Otsu's Thresholding langsung pada citra grayscale
    ret_otsu, thresh_otsu = cv2.threshold(img_bimodal, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 3. Otsu's Thresholding setelah Gaussian Blur (mengurangi noise)
    blurred = cv2.GaussianBlur(img_bimodal, (5, 5), 0)
    ret_otsu_blur, thresh_otsu_blur = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    print(f"[Otsu Demo] Optimal Threshold tanpa filter: {ret_otsu:.2f}")
    print(f"[Otsu Demo] Optimal Threshold setelah Gaussian Blur: {ret_otsu_blur:.2f}")

    return {
        "original": img_bimodal,
        "global": thresh_global,
        "otsu": thresh_otsu,
        "otsu_blur": thresh_otsu_blur,
        "t_otsu": ret_otsu,
        "t_otsu_blur": ret_otsu_blur
    }

def demo_adaptive_thresholding(img_uneven):
    """
    Mendemonstrasikan keunggulan Adaptive Thresholding dibandingkan Global Thresholding
    pada citra dengan pencahayaan tidak seragam (non-uniform illumination).
    """
    # 1. Global Otsu (akan gagal karena bagian terang dan gelap memiliki nilai dasar berbeda)
    ret_otsu, thresh_otsu = cv2.threshold(img_uneven, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 2. Adaptive Mean Thresholding
    # T(x,y) = rata-rata area blok 11x11 dikurangi konstanta C (2)
    thresh_adapt_mean = cv2.adaptiveThreshold(
        img_uneven, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, blockSize=15, C=4
    )

    # 3. Adaptive Gaussian Thresholding
    # T(x,y) = bobot Gaussian area blok 11x11 dikurangi C
    thresh_adapt_gauss = cv2.adaptiveThreshold(
        img_uneven, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, blockSize=15, C=4
    )

    return {
        "Citra Pencahayaan Tidak Merata": img_uneven,
        f"Global Otsu (Gagal, T={ret_otsu:.1f})": thresh_otsu,
        "Adaptive Mean (Block=15, C=4)": thresh_adapt_mean,
        "Adaptive Gaussian (Block=15, C=4)": thresh_adapt_gauss
    }

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sample_dir = os.path.join(base_dir, "sample_images")
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    print("==================================================")
    print("PRAKTIKUM 05: SEGMENTASI CITRA DENGAN THRESHOLDING")
    print("==================================================")

    # Load citra uji
    path_coins = os.path.join(sample_dir, "bimodal_coins.png")
    path_uneven = os.path.join(sample_dir, "uneven_light.png")

    img_coins = cv2.imread(path_coins, cv2.IMREAD_GRAYSCALE)
    img_uneven = cv2.imread(path_uneven, cv2.IMREAD_GRAYSCALE)

    if img_coins is None or img_uneven is None:
        raise FileNotFoundError("Citra sampel belum ditemukan. Jalankan 00_generate_samples.py terlebih dahulu.")

    # Eksekusi Demo
    global_results = demo_global_thresholding(img_coins)
    otsu_results = demo_otsu_thresholding(img_coins)
    adaptive_results = demo_adaptive_thresholding(img_uneven)

    # --- Plotting Visualisasi Komprehensif ---
    fig = plt.figure(figsize=(16, 12))
    plt.suptitle("Praktikum 05: Eksplorasi Teknik Thresholding pada Segmentasi Citra", fontsize=16, fontweight='bold')

    # Bagian 1: Global Thresholding
    keys1 = list(global_results.keys())
    for i, k in enumerate(keys1):
        ax = plt.subplot(3, 4, i + 1)
        ax.imshow(global_results[k], cmap='gray')
        ax.set_title(k, fontsize=10, fontweight='bold')
        ax.axis('off')

    # Bagian 2: Otsu's Thresholding & Histogram
    ax_hist = plt.subplot(3, 4, 7)
    ax_hist.hist(img_coins.ravel(), 256, [0, 256], color='darkblue', alpha=0.7)
    ax_hist.axvline(127, color='r', linestyle='--', label='Global T=127')
    # Ambil nilai threshold otsu dari demo
    ret_otsu, _ = cv2.threshold(img_coins, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    ax_hist.axvline(ret_otsu, color='g', linestyle='-', linewidth=2, label=f'Otsu T={ret_otsu:.1f}')
    ax_hist.set_title("Histogram Koin & Nilai Ambang", fontsize=10, fontweight='bold')
    ax_hist.legend(fontsize=8)
    ax_hist.set_xlabel("Intensitas Piksel")
    ax_hist.set_ylabel("Frekuensi")

    ax_otsu = plt.subplot(3, 4, 8)
    ax_otsu.imshow(otsu_results["otsu_blur"], cmap='gray')
    ax_otsu.set_title(f"Hasil Otsu + Blur (T={otsu_results['t_otsu_blur']:.1f})", fontsize=10, fontweight='bold')
    ax_otsu.axis('off')

    # Bagian 3: Adaptive Thresholding
    keys3 = list(adaptive_results.keys())
    for i, k in enumerate(keys3):
        ax = plt.subplot(3, 4, 9 + i)
        ax.imshow(adaptive_results[k], cmap='gray')
        ax.set_title(k, fontsize=10, fontweight='bold')
        ax.axis('off')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    out_path = os.path.join(output_dir, "01_thresholding_comparison.png")
    plt.savefig(out_path, dpi=200)
    plt.close()

    print(f"[SUCCESS] Hasil komparasi thresholding disimpan di: {out_path}")

if __name__ == "__main__":
    main()
