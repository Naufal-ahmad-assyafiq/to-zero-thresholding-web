"""
Modul Praktikum 05 - Bagian 6: Segmentasi Citra Berbasis Clustering
Topik:
1. K-Means Clustering (Crisp / Hard Partitioning)
2. Fuzzy C-Means / FCM (Soft / Fuzzy Partitioning)

Konsep:
"Clustering: Mengelompokkan piksel berdasarkan kedekatan nilai fitur,
seperti algoritma K-Means atau Fuzzy C-Means."
"""

import os
import sys
import time
import cv2
import numpy as np
import matplotlib.pyplot as plt

def run_kmeans_clustering(img_bgr, k=4, max_iter=20):
    """
    K-Means Clustering:
    Mengelompokkan piksel secara tegas (hard clustering) ke dalam K kluster
    berdasarkan jarak Euclidean terdekat pada ruang fitur warna (R, G, B).
    """
    t0 = time.perf_counter()
    h, w = img_bgr.shape[:2]
    pixels = img_bgr.reshape((-1, 3)).astype(np.float32)

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, max_iter, 0.2)
    ret, labels, centers = cv2.kmeans(pixels, k, None, criteria, 5, cv2.KMEANS_RANDOM_CENTERS)

    centers = np.uint8(centers)
    labels = labels.flatten()
    segmented_pixels = centers[labels]
    segmented_img = segmented_pixels.reshape((h, w, 3))

    elapsed = (time.perf_counter() - t0) * 1000
    return segmented_img, labels.reshape((h, w)), centers, elapsed

def run_fcm_clustering(img_bgr, c=4, m=2.0, max_iter=20, epsilon=0.01):
    """
    Fuzzy C-Means (FCM):
    Mengelompokkan piksel dengan derajat keanggotaan probabilistik (soft clustering),
    di mana u_ij berada dalam rentang [0, 1] dan jumlah keanggotaan tiap piksel = 1.
    """
    t0 = time.perf_counter()
    h, w = img_bgr.shape[:2]
    N = h * w
    pixels_norm = img_bgr.reshape((-1, 3)).astype(np.float32) / 255.0

    np.random.seed(42)
    u = np.random.dirichlet(np.ones(c), size=N).T  # shape: (c, N)

    for _ in range(max_iter):
        u_m = u ** m
        denom = np.sum(u_m, axis=1, keepdims=True) + 1e-8
        centers = (u_m @ pixels_norm) / denom

        diff = pixels_norm[None, :, :] - centers[:, None, :]
        dist = np.linalg.norm(diff, axis=2) + 1e-8

        inv_dist = dist ** (-2.0 / (m - 1.0))
        u_new = inv_dist / (np.sum(inv_dist, axis=0, keepdims=True) + 1e-8)

        if np.linalg.norm(u_new - u) < epsilon:
            break
        u = u_new

    labels = np.argmax(u, axis=0)
    centers_bgr = np.uint8(np.clip(centers * 255.0, 0, 255))
    segmented_pixels = centers_bgr[labels]
    segmented_img = segmented_pixels.reshape((h, w, 3))

    # Peta Ambiguitas Batas (1 - max membership)
    max_u = np.max(u, axis=0).reshape((h, w))
    uncert = np.uint8(np.clip((1.0 - max_u) * c * 255.0, 0, 255))
    uncertainty_map = cv2.applyColorMap(uncert, cv2.COLORMAP_JET)

    elapsed = (time.perf_counter() - t0) * 1000
    return segmented_img, labels.reshape((h, w)), centers_bgr, elapsed, uncertainty_map

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sample_img_path = os.path.join(base_dir, "sample_images", "fruits_color.png")
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        sample_img_path = sys.argv[1]

    if not os.path.exists(sample_img_path):
        sample_img_path = os.path.join(base_dir, "sample_images", "bimodal_coins.png")

    img_bgr = cv2.imread(sample_img_path)
    if img_bgr is None:
        print(f"[ERROR] Gagal memuat citra dari {sample_img_path}")
        return

    output_dir = os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    k_clusters = 4
    print("\n" + "=" * 80)
    print("  EKSPERIMEN SEGMENTASI CITRA BERBASIS CLUSTERING (PRAKTIKUM 05)")
    print("=" * 80)
    print(f"Citra Uji      : {sample_img_path}")
    print(f"Jumlah Kluster : K = {k_clusters}")

    # 1. Jalankan K-Means
    km_img, km_labels, km_centers, km_time = run_kmeans_clustering(img_bgr, k=k_clusters)
    print(f"[K-Means] Selesai dalam {km_time:.2f} ms")

    # 2. Jalankan Fuzzy C-Means (FCM)
    fcm_img, fcm_labels, fcm_centers, fcm_time, fcm_uncert = run_fcm_clustering(img_bgr, c=k_clusters, m=2.0)
    print(f"[FCM]     Selesai dalam {fcm_time:.2f} ms")

    # Cetak tabel perbandingan
    print("\n" + "-" * 105)
    print(f"{'Metode':<22} | {'Tipe Partisi':<18} | {'Waktu (ms)':<11} | {'Karakteristik & Kelebihan'}")
    print("-" * 105)
    print(f"{'K-Means Clustering':<22} | {'Hard / Crisp':<18} | {km_time:<11.2f} | {'Partisi tegas, konvergensi cepat, batas kaku'}")
    print(f"{'Fuzzy C-Means (FCM)':<22} | {'Soft / Fuzzy':<18} | {fcm_time:<11.2f} | {'Derajat keanggotaan kontinu u_ij, luwes pd batas kabur'}")
    print("-" * 105 + "\n")

    # Visualisasi Matplotlib
    plt.figure(figsize=(15, 10))

    # Citra Asli
    plt.subplot(2, 2, 1)
    plt.imshow(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
    plt.title("Citra Asli (RGB Masukan)", fontsize=12, fontweight='bold')
    plt.axis('off')

    # Hasil K-Means
    plt.subplot(2, 2, 2)
    plt.imshow(cv2.cvtColor(km_img, cv2.COLOR_BGR2RGB))
    plt.title(f"Segmentasi K-Means (K={k_clusters})\n[{km_time:.2f} ms]", fontsize=12, fontweight='bold')
    plt.axis('off')

    # Hasil Fuzzy C-Means
    plt.subplot(2, 2, 3)
    plt.imshow(cv2.cvtColor(fcm_img, cv2.COLOR_BGR2RGB))
    plt.title(f"Segmentasi Fuzzy C-Means / FCM (C={k_clusters}, m=2.0)\n[{fcm_time:.2f} ms]", fontsize=12, fontweight='bold')
    plt.axis('off')

    # Peta Ketidakpastian FCM
    plt.subplot(2, 2, 4)
    plt.imshow(cv2.cvtColor(fcm_uncert, cv2.COLOR_BGR2RGB))
    plt.title("Peta Ketidakpastian Batas FCM (Heatmap Jet)\n[Warna Panas = Piksel Transisi Ambigu]", fontsize=12, fontweight='bold')
    plt.axis('off')

    plt.tight_layout()
    save_path = os.path.join(output_dir, "06_clustering_comparison.png")
    plt.savefig(save_path, dpi=180, bbox_inches='tight')
    plt.close()
    print(f"[OK] Plot perbandingan clustering disimpan di: {save_path}\n")

if __name__ == "__main__":
    main()
