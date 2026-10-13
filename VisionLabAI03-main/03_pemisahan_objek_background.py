"""
Modul Praktikum 05 - Bagian 3: Pemisahan Objek dari Latar Belakang (Background Subtraction & Extraction)
Topik:
1. Pemisahan Berbasis Ruang Warna HSV (Color Thresholding dengan cv2.inRange)
2. Pembersihan Mask dengan Operasi Morfologi (Opening & Closing)
3. Pemisahan Foreground Kompleks dengan Algoritma GrabCut
4. Ekstraksi Objek Transparan / Latar Belakang Putih
"""

import os
import cv2
import numpy as np
import matplotlib.pyplot as plt

def segmentasi_warna_hsv(img_bgr):
    """
    Memisahkan objek spesifik (misal buah merah dan buah kuning)
    menggunakan ruang warna HSV yang lebih kebal terhadap intensitas cahaya.
    """
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

    # 1. Definisikan Rentang Warna Merah dalam HSV
    # Catatan: Nilai H untuk warna merah terbagi dua (mendekati 0 dan mendekati 180)
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 100, 100])
    upper_red2 = np.array([180, 255, 255])

    mask_red1 = cv2.inRange(img_hsv, lower_red1, upper_red1)
    mask_red2 = cv2.inRange(img_hsv, lower_red2, upper_red2)
    mask_red = cv2.bitwise_or(mask_red1, mask_red2)

    # 2. Definisikan Rentang Warna Kuning dalam HSV (H: ~18-35)
    lower_yellow = np.array([18, 100, 100])
    upper_yellow = np.array([35, 255, 255])
    mask_yellow = cv2.inRange(img_hsv, lower_yellow, upper_yellow)

    # 3. Operasi Morfologi untuk Membersihkan Mask Merah
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    # Opening: menghilangkan noise bintik putih di luar objek
    mask_red_clean = cv2.morphologyEx(mask_red, cv2.MORPH_OPEN, kernel)
    # Closing: menutup lubang hitam di dalam objek
    mask_red_clean = cv2.morphologyEx(mask_red_clean, cv2.MORPH_CLOSE, kernel)

    # 4. Ekstraksi Objek Merah (Foreground Isolated)
    extracted_red = cv2.bitwise_and(img_rgb, img_rgb, mask=mask_red_clean)

    return {
        "img_rgb": img_rgb,
        "mask_red_raw": mask_red,
        "mask_red_clean": mask_red_clean,
        "mask_yellow": mask_yellow,
        "extracted_red": extracted_red
    }

def segmentasi_grabcut(img_bgr, bbox_rect):
    """
    Memisahkan objek latar depan menggunakan algoritma GrabCut
    berdasarkan inisialisasi Bounding Box persegi panjang (x, y, w, h).
    """
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    mask = np.zeros(img_bgr.shape[:2], np.uint8)

    # Model sementara background dan foreground untuk algoritma GrabCut
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    # Jalankan GrabCut dengan iterasi = 5
    cv2.grabCut(img_bgr, mask, bbox_rect, bgd_model, fgd_model, iterCount=5, mode=cv2.GC_INIT_WITH_RECT)

    # Piksel yang pasti foreground (1) atau probable foreground (3) diubah menjadi 1
    # Piksel pasti background (0) atau probable background (2) diubah menjadi 0
    grabcut_mask = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 1, 0).astype('uint8')

    # Buat latar belakang menjadi putih bersih
    foreground_only = img_rgb * grabcut_mask[:, :, np.newaxis]
    white_bg = np.ones_like(img_rgb) * 255
    background_cut = np.where(grabcut_mask[:, :, np.newaxis] == 1, img_rgb, white_bg)

    return grabcut_mask * 255, foreground_only, background_cut

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sample_dir = os.path.join(base_dir, "sample_images")
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    print("==================================================")
    print("PRAKTIKUM 05: PEMISAHAN OBJEK DARI LATAR BELAKANG")
    print("==================================================")

    # 1. Load Citra Buah Berwarna
    path_fruits = os.path.join(sample_dir, "fruits_color.png")
    img_bgr = cv2.imread(path_fruits)
    if img_bgr is None:
        raise FileNotFoundError("Citra fruits_color.png tidak ditemukan!")

    # 2. Demo Segmentasi HSV
    hsv_results = segmentasi_warna_hsv(img_bgr)

    # 3. Demo GrabCut pada Apel Merah
    # Bounding box sekitar apel merah: x=65, y=100, w=170, h=220
    bbox_apple = (65, 100, 170, 220)
    gc_mask, gc_fg, gc_white_bg = segmentasi_grabcut(img_bgr, bbox_apple)

    # 4. Visualisasi Komparasi Hasil
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    plt.suptitle("Praktikum 05: Pemisahan Objek Menggunakan HSV Masking, Morfologi, dan GrabCut", fontsize=15, fontweight='bold')

    # Citra Asli + Bounding Box GrabCut
    img_box = hsv_results["img_rgb"].copy()
    x, y, w, h = bbox_apple
    cv2.rectangle(img_box, (x, y), (x + w, y + h), (0, 255, 0), 2)
    cv2.putText(img_box, "ROI GrabCut", (x, y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    axes[0, 0].imshow(img_box)
    axes[0, 0].set_title("Citra Asli + ROI GrabCut", fontsize=11, fontweight='bold')
    axes[0, 0].axis('off')

    # Mask HSV Mentah
    axes[0, 1].imshow(hsv_results["mask_red_raw"], cmap='gray')
    axes[0, 1].set_title("Mask HSV Merah (Sebelum Morfologi)", fontsize=11, fontweight='bold')
    axes[0, 1].axis('off')

    # Mask HSV Setelah Morfologi
    axes[0, 2].imshow(hsv_results["mask_red_clean"], cmap='gray')
    axes[0, 2].set_title("Mask Bersih (Opening + Closing)", fontsize=11, fontweight='bold')
    axes[0, 2].axis('off')

    # Ekstraksi Berbasis HSV
    axes[1, 0].imshow(hsv_results["extracted_red"])
    axes[1, 0].set_title("Hasil Ekstraksi Objek Merah (HSV)", fontsize=11, fontweight='bold')
    axes[1, 0].axis('off')

    # Mask GrabCut
    axes[1, 1].imshow(gc_mask, cmap='gray')
    axes[1, 1].set_title("Mask Biner GrabCut (Iter=5)", fontsize=11, fontweight='bold')
    axes[1, 1].axis('off')

    # Ekstraksi GrabCut (Latar Putih)
    axes[1, 2].imshow(gc_white_bg)
    axes[1, 2].set_title("Hasil GrabCut (Background Diganti Putih)", fontsize=11, fontweight='bold')
    axes[1, 2].axis('off')

    plt.tight_layout()
    out_path = os.path.join(output_dir, "03_background_separation.png")
    plt.savefig(out_path, dpi=200)
    plt.close()

    print(f"[SUCCESS] Hasil pemisahan background disimpan di: {out_path}")

if __name__ == "__main__":
    main()
