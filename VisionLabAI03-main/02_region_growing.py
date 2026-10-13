"""
Modul Praktikum 05 - Bagian 2: Segmentasi Citra Berbasis Wilayah (Region Growing)
Topik:
1. Konsep Dasar Region Growing (Seed Points, Similarity Criterion, Connectivity)
2. Implementasi Queue-based (Breadth-First Search) Region Growing dari Scratch
3. Pengaruh Nilai Threshold / Toleransi Kesamaan
4. Multi-Seed Region Growing untuk Segmentasi Multi-Objek
"""

import os
from collections import deque
import cv2
import numpy as np
import matplotlib.pyplot as plt

def region_growing(img_gray, seed_point, threshold=15, connectivity=8, dynamic_mean=True):
    """
    Algoritma Region Growing Tunggal Berbasis Queue (BFS).

    Parameter:
    - img_gray: np.ndarray, citra grayscale 2D
    - seed_point: tuple (x, y), koordinat titik awal (seed)
    - threshold: int/float, batas toleransi perbedaan intensitas piksel
    - connectivity: 4 atau 8 tetangga
    - dynamic_mean: bool, jika True membandingkan dengan rata-rata region terkini;
                   jika False membandingkan langsung dengan intensitas titik seed awal.

    Return:
    - mask: np.ndarray uint8 (nilai 255 untuk region terpilih, 0 untuk lainnya)
    """
    h, w = img_gray.shape
    segmented_mask = np.zeros((h, w), dtype=np.uint8)
    visited = np.zeros((h, w), dtype=bool)

    sx, sy = seed_point
    if sx < 0 or sx >= w or sy < 0 or sy >= h:
        raise ValueError(f"Titik seed {seed_point} di luar batas citra ({w}x{h})")

    # Tentukan orientasi tetangga
    if connectivity == 4:
        neighbors_offset = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    else:  # 8-connectivity
        neighbors_offset = [(-1, -1), (-1, 0), (-1, 1),
                            (0, -1),           (0, 1),
                            (1, -1),  (1, 0),  (1, 1)]

    # Inisialisasi Antrean BFS
    queue = deque()
    queue.append((sx, sy))
    visited[sy, sx] = True
    segmented_mask[sy, sx] = 255

    region_sum = float(img_gray[sy, sx])
    region_count = 1
    seed_intensity = float(img_gray[sy, sx])

    while queue:
        cx, cy = queue.popleft()

        # Nilai acuan perbandingan
        current_ref = (region_sum / region_count) if dynamic_mean else seed_intensity

        for dx, dy in neighbors_offset:
            nx, ny = cx + dx, cy + dy

            # Cek boundary citra
            if 0 <= nx < w and 0 <= ny < h:
                if not visited[ny, nx]:
                    visited[ny, nx] = True
                    pixel_val = float(img_gray[ny, nx])

                    # Kriteria kesamaan: selisih absolut <= threshold
                    if abs(pixel_val - current_ref) <= threshold:
                        segmented_mask[ny, nx] = 255
                        queue.append((nx, ny))
                        region_sum += pixel_val
                        region_count += 1

    return segmented_mask

def multi_seed_region_growing(img_gray, seed_points_dict, threshold=15):
    """
    Region Growing untuk banyak objek dengan seed berbeda secara simultan.

    Parameter:
    - seed_points_dict: dict label_id -> (x, y)

    Return:
    - labeled_mask: np.ndarray int32, setiap region memiliki label unik
    """
    h, w = img_gray.shape
    labeled_mask = np.zeros((h, w), dtype=np.int32)
    visited = np.zeros((h, w), dtype=bool)

    # Inisialisasi BFS untuk setiap seed
    queue = deque()
    stats = {}

    for label_id, (sx, sy) in seed_points_dict.items():
        queue.append((sx, sy, label_id))
        visited[sy, sx] = True
        labeled_mask[sy, sx] = label_id
        stats[label_id] = {
            "sum": float(img_gray[sy, sx]),
            "count": 1,
            "seed_val": float(img_gray[sy, sx])
        }

    neighbors_offset = [(-1, -1), (-1, 0), (-1, 1),
                        (0, -1),           (0, 1),
                        (1, -1),  (1, 0),  (1, 1)]

    while queue:
        cx, cy, label_id = queue.popleft()
        ref_val = stats[label_id]["sum"] / stats[label_id]["count"]

        for dx, dy in neighbors_offset:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < w and 0 <= ny < h:
                if not visited[ny, nx]:
                    visited[ny, nx] = True
                    pixel_val = float(img_gray[ny, nx])

                    if abs(pixel_val - ref_val) <= threshold:
                        labeled_mask[ny, nx] = label_id
                        queue.append((nx, ny, label_id))
                        stats[label_id]["sum"] += pixel_val
                        stats[label_id]["count"] += 1

    return labeled_mask

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sample_dir = os.path.join(base_dir, "sample_images")
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    print("==================================================")
    print("PRAKTIKUM 05: SEGMENTASI CITRA REGION GROWING")
    print("==================================================")

    # 1. Load Citra Uji
    img_path = os.path.join(sample_dir, "shapes_noisy.png")
    img_gray = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    if img_gray is None:
        raise FileNotFoundError("Citra shapes_noisy.png tidak ditemukan!")

    # 2. Definisikan Titik Seed untuk masing-masing objek
    # Bentuk objek: Kotak (120, 120), Lingkaran (350, 120), Segitiga (120, 320), Elips (350, 300)
    seed_kotak = (120, 120)
    seed_lingkaran = (350, 120)
    seed_segitiga = (120, 320)
    seed_elips = (350, 300)

    print(f"[Seed Info] Titik Seed Kotak: {seed_kotak}, Intensitas: {img_gray[seed_kotak[1], seed_kotak[0]]}")
    print(f"[Seed Info] Titik Seed Lingkaran: {seed_lingkaran}, Intensitas: {img_gray[seed_lingkaran[1], seed_lingkaran[0]]}")

    # 3. Uji Pengaruh Variasi Threshold pada Kotak
    mask_t5 = region_growing(img_gray, seed_kotak, threshold=5)    # Terlalu ketat (under-segmentation)
    mask_t15 = region_growing(img_gray, seed_kotak, threshold=15)  # Optimal
    mask_t90 = region_growing(img_gray, seed_kotak, threshold=90)  # Terlalu longgar (leaking / over-segmentation)

    # 4. Multi-Seed Region Growing untuk memisahkan semua 4 objek sekaligus
    seeds_dict = {
        1: seed_kotak,
        2: seed_lingkaran,
        3: seed_segitiga,
        4: seed_elips
    }
    multi_mask = multi_seed_region_growing(img_gray, seeds_dict, threshold=20)

    # 5. Visualisasi Hasil
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    plt.suptitle("Praktikum 05: Implementasi dan Eksperimen Region Growing", fontsize=16, fontweight='bold')

    # Citra Asli + Titik Seed
    img_rgb_seeds = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
    for sid, (sx, sy) in seeds_dict.items():
        cv2.circle(img_rgb_seeds, (sx, sy), 5, (255, 0, 0), -1)
        cv2.putText(img_rgb_seeds, f"S{sid}", (sx + 8, sy + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

    axes[0, 0].imshow(img_rgb_seeds)
    axes[0, 0].set_title("Citra Input + Titik Seed (S1-S4)", fontsize=11, fontweight='bold')
    axes[0, 0].axis('off')

    # Threshold = 5 (Under-segmentation)
    axes[0, 1].imshow(mask_t5, cmap='gray')
    axes[0, 1].set_title("Region Growing (T=5) - Under-segmented", fontsize=11, fontweight='bold')
    axes[0, 1].axis('off')

    # Threshold = 15 (Optimal)
    axes[0, 2].imshow(mask_t15, cmap='gray')
    axes[0, 2].set_title("Region Growing (T=15) - Optimal", fontsize=11, fontweight='bold')
    axes[0, 2].axis('off')

    # Threshold = 90 (Leaking)
    axes[1, 0].imshow(mask_t90, cmap='gray')
    axes[1, 0].set_title("Region Growing (T=90) - Bocor/Leaking", fontsize=11, fontweight='bold')
    axes[1, 0].axis('off')

    # Multi-Seed Segmented Map (Colormap)
    axes[1, 1].imshow(multi_mask, cmap='tab10')
    axes[1, 1].set_title("Multi-Seed Region Growing (4 Objek)", fontsize=11, fontweight='bold')
    axes[1, 1].axis('off')

    # Overlay Segmentasi pada Citra Asli
    overlay = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)
    colors = [(255, 50, 50), (50, 255, 50), (50, 150, 255), (255, 200, 50)]
    for sid in range(1, 5):
        obj_mask = (multi_mask == sid).astype(np.uint8)
        contours, _ = cv2.findContours(obj_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(overlay, contours, -1, colors[sid - 1], 2)

    axes[1, 2].imshow(overlay)
    axes[1, 2].set_title("Overlay Kontur Segmentasi Multi-Objek", fontsize=11, fontweight='bold')
    axes[1, 2].axis('off')

    plt.tight_layout()
    out_path = os.path.join(output_dir, "02_region_growing.png")
    plt.savefig(out_path, dpi=200)
    plt.close()

    print(f"[SUCCESS] Hasil Region Growing disimpan di: {out_path}")

if __name__ == "__main__":
    main()
