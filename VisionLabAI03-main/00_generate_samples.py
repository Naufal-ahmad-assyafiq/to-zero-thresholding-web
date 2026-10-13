"""
Script Generator Citra Sampel Sintetis untuk Praktikum 05: Segmentasi Citra
Menghasilkan berbagai citra uji untuk mendemonstrasikan:
1. uneven_light.png  - Citra dengan pencahayaan tidak merata (demonstrasi Adaptive Thresholding)
2. bimodal_coins.png - Citra koin dengan latar kontras dan noise (demonstrasi Otsu Thresholding)
3. shapes_noisy.png  - Citra aneka bentuk geometris bertekstur (demonstrasi Region Growing)
4. fruits_color.png  - Citra aneka objek warna-warni (demonstrasi HSV Masking & GrabCut)
"""

import os
import cv2
import numpy as np

def generate_uneven_light_image(output_path):
    """Menghasilkan citra teks/pola dengan gradien pencahayaan ekstrem."""
    h, w = 400, 600
    # Buat latar belakang dengan gradien intensitas (terang di kiri-atas, gelap di kanan-bawah)
    x = np.linspace(0, 1, w)
    y = np.linspace(0, 1, h)
    xx, yy = np.meshgrid(x, y)
    gradient = (1.0 - (0.7 * xx + 0.3 * yy)) * 255.0

    img = gradient.astype(np.uint8)

    # Tambahkan teks dengan warna abu-abu netral
    texts = [
        ("PRAKTIKUM 05", (40, 90), 1.6, 3),
        ("SEGMENTASI CITRA DIGITAL", (40, 160), 1.1, 2),
        ("Adaptive vs Global Threshold", (40, 230), 1.0, 2),
        ("Pencahayaan Tidak Merata", (40, 300), 1.0, 2),
        ("Laboratorium Visi Komputer", (40, 360), 0.9, 2),
    ]

    for text, pos, scale, thickness in texts:
        # Objek memiliki nilai intensitas konstan sekitar 50 (gelap)
        cv2.putText(img, text, pos, cv2.FONT_HERSHEY_SIMPLEX, scale, 30, thickness, cv2.LINE_AA)

    # Tambahkan sedikit noise gaussian
    noise = np.random.normal(0, 6, (h, w))
    img_noisy = np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)

    cv2.imwrite(output_path, img_noisy)
    print(f"[OK] Citra pencahayaan tidak merata disimpan di: {output_path}")

def generate_bimodal_coins_image(output_path):
    """Menghasilkan citra koin-koin sintetis dengan histogram bimodal untuk Otsu."""
    h, w = 450, 600
    # Background abu-abu gelap dengan intensitas ~45
    img = np.full((h, w), 45, dtype=np.uint8)

    # Posisi dan jari-jari koin
    coins = [
        (120, 130, 50, 195),
        (260, 110, 40, 210),
        (390, 140, 45, 185),
        (510, 110, 35, 200),
        (150, 290, 55, 190),
        (300, 280, 48, 215),
        (450, 290, 52, 205),
        (220, 390, 38, 180),
        (380, 395, 42, 220),
    ]

    for cx, cy, r, val in coins:
        # Lingkaran luar koin
        cv2.circle(img, (cx, cy), r, val, -1)
        # Efek tepi koin (ring)
        cv2.circle(img, (cx, cy), r - 5, val + 15, 2)
        cv2.circle(img, (cx, cy), r // 2, val - 20, 2)
        cv2.putText(img, "Rp", (cx - 15, cy + 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, val - 30, 2)

    # Noise gaussian
    noise = np.random.normal(0, 10, (h, w))
    img_noisy = np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)

    cv2.imwrite(output_path, img_noisy)
    print(f"[OK] Citra koin bimodal disimpan di: {output_path}")

def generate_shapes_noisy_image(output_path):
    """Menghasilkan citra aneka bentuk terisolasi untuk demonstrasi Region Growing."""
    h, w = 400, 500
    # Background gelap rata-rata 35
    img = np.full((h, w), 35, dtype=np.uint8)

    # Gambar region 1: Persegi panjang intensitas 170
    cv2.rectangle(img, (60, 60), (190, 180), 170, -1)

    # Gambar region 2: Lingkaran intensitas 210
    cv2.circle(img, (350, 120), 70, 210, -1)

    # Gambar region 3: Poligon / bintang intensitas 140
    pts = np.array([[120, 250], [180, 360], [60, 360]], np.int32)
    cv2.fillPoly(img, [pts], 140)

    # Gambar region 4: Elips intensitas 190
    cv2.ellipse(img, (350, 300), (90, 55), 30, 0, 360, 190, -1)

    # Noise gaussian halus
    noise = np.random.normal(0, 8, (h, w))
    img_noisy = np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)

    cv2.imwrite(output_path, img_noisy)
    print(f"[OK] Citra bentuk bernoise disimpan di: {output_path}")

def generate_fruits_color_image(output_path):
    """Menghasilkan citra aneka objek warna untuk segmentasi HSV dan GrabCut."""
    h, w = 450, 650
    # Background berwarna krem/kayu lembut (BGR)
    img = np.zeros((h, w, 3), dtype=np.uint8)
    img[:, :] = (210, 225, 235)  # Soft light-grayish cream

    # 1. Objek Merah (Apel) - BGR
    cv2.circle(img, (150, 220), 75, (30, 30, 220), -1)
    cv2.ellipse(img, (150, 210), (70, 65), 0, 0, 360, (20, 20, 200), -1)
    # Tangkai apel (cokelat)
    cv2.line(img, (150, 145), (145, 115), (20, 70, 120), 6)
    # Daun hijau kecil
    cv2.ellipse(img, (160, 125), (15, 8), 35, 0, 360, (40, 170, 40), -1)

    # 2. Objek Kuning (Jeruk Lemon / Jeruk Bali)
    cv2.circle(img, (330, 230), 80, (20, 215, 245), -1)
    cv2.circle(img, (330, 230), 75, (10, 195, 235), -1)

    # 3. Objek Hijau (Alpukat / Pear)
    cv2.ellipse(img, (510, 250), (60, 80), 0, 0, 360, (45, 160, 50), -1)
    cv2.circle(img, (510, 200), 45, (45, 175, 55), -1)

    # Tambahkan sedikit tekstur & bayangan lembut di bawah objek
    shadow_overlay = img.copy()
    cv2.ellipse(shadow_overlay, (150, 305), (70, 15), 0, 0, 360, (140, 150, 160), -1)
    cv2.ellipse(shadow_overlay, (330, 320), (75, 15), 0, 0, 360, (140, 150, 160), -1)
    cv2.ellipse(shadow_overlay, (510, 340), (60, 15), 0, 0, 360, (140, 150, 160), -1)
    img = cv2.addWeighted(shadow_overlay, 0.4, img, 0.6, 0)

    # Noise halus
    noise = np.random.normal(0, 4, (h, w, 3))
    img_noisy = np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)

    cv2.imwrite(output_path, img_noisy)
    print(f"[OK] Citra buah berwarna disimpan di: {output_path}")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sample_dir = os.path.join(base_dir, "sample_images")
    output_dir = os.path.join(base_dir, "output")

    os.makedirs(sample_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    print("=== Menghasilkan Citra Sampel untuk Praktikum 05 ===")
    generate_uneven_light_image(os.path.join(sample_dir, "uneven_light.png"))
    generate_bimodal_coins_image(os.path.join(sample_dir, "bimodal_coins.png"))
    generate_shapes_noisy_image(os.path.join(sample_dir, "shapes_noisy.png"))
    generate_fruits_color_image(os.path.join(sample_dir, "fruits_color.png"))
    print("=== Semua citra sampel berhasil dibuat! ===\n")

if __name__ == "__main__":
    main()
