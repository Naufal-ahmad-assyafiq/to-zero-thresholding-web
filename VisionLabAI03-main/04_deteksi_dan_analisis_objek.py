"""
Modul Praktikum 05 - Bagian 4: Studi Kasus Deteksi dan Analisis Objek Menggunakan Segmentasi
Topik:
1. End-to-End Pipeline: Citra -> Preprocessing -> Segmentasi Otsu -> Morfologi -> Kontur
2. Ekstraksi Fitur Objek: Area, Perimeter, Centroid (Moments), Bounding Box
3. Perhitungan Metrik Bentuk (Circularity / Roundness)
4. Perhitungan Jumlah Objek (Object Counting) dan Visualisasi Diagnostik
"""

import os
import cv2
import numpy as np
import matplotlib.pyplot as plt

def deteksi_dan_analisis_objek(img_gray, min_area=500):
    """
    Menjalankan pipeline deteksi objek pada citra biner segmentasi.

    Parameter:
    - img_gray: np.ndarray, citra grayscale
    - min_area: float, ambang batas minimum area untuk mengabaikan noise

    Return:
    - data_objek: list of dict berisi atribut masing-masing objek
    - step_images: dict gambar tahapan pemrosesan
    """
    step_images = {}
    step_images["1_grayscale"] = img_gray

    # 1. Preprocessing: Blur untuk menghilangkan noise frekuensi tinggi
    blurred = cv2.GaussianBlur(img_gray, (7, 7), 0)
    step_images["2_blurred"] = blurred

    # 2. Segmentasi: Otsu's Thresholding
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    step_images["3_threshold_otsu"] = thresh

    # 3. Morfologi: Opening (hilangkan bintik) lalu Closing (tutup lubang koin)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel, iterations=2)
    step_images["4_morphology_clean"] = cleaned

    # 4. Deteksi Kontur Eksternal
    contours, hierarchy = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 5. Analisis Fitur Setiap Objek
    data_objek = []
    annotated_img = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2RGB)

    obj_id = 1
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue  # Abaikan bercak/noise kecil

        perimeter = cv2.arcLength(cnt, True)

        # Hitung Centroid menggunakan Moments
        M = cv2.moments(cnt)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
        else:
            cx, cy = 0, 0

        # Bounding Box Tegak
        bx, by, bw, bh = cv2.boundingRect(cnt)

        # Metric Kebundaran (Circularity / Roundness): 4 * pi * Area / (Perimeter^2)
        # Nilai mendekati 1.0 berarti lingkaran sempurna
        circularity = (4 * np.pi * area) / (perimeter ** 2) if perimeter > 0 else 0

        data_objek.append({
            "id": obj_id,
            "centroid": (cx, cy),
            "area": area,
            "perimeter": perimeter,
            "bbox": (bx, by, bw, bh),
            "circularity": circularity
        })

        # Gambar Anotasi pada Citra
        # Kotak pembatas (Bounding Box warna biru)
        cv2.rectangle(annotated_img, (bx, by), (bx + bw, by + bh), (50, 150, 255), 2)
        # Kontur tepi (Warna hijau)
        cv2.drawContours(annotated_img, [cnt], -1, (50, 255, 50), 2)
        # Centroid (Titik merah)
        cv2.circle(annotated_img, (cx, cy), 4, (255, 50, 50), -1)
        # Teks ID Objek
        cv2.putText(annotated_img, f"#{obj_id}", (bx, by - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        obj_id += 1

    step_images["5_annotated"] = annotated_img
    return data_objek, step_images

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sample_dir = os.path.join(base_dir, "sample_images")
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    print("==================================================")
    print("PRAKTIKUM 05: DETEKSI DAN ANALISIS OBJEK CITRA")
    print("==================================================")

    # 1. Load Citra Koin
    path_coins = os.path.join(sample_dir, "bimodal_coins.png")
    img_gray = cv2.imread(path_coins, cv2.IMREAD_GRAYSCALE)
    if img_gray is None:
        raise FileNotFoundError("Citra bimodal_coins.png tidak ditemukan!")

    # 2. Eksekusi Analisis Objek
    daftar_objek, steps = deteksi_dan_analisis_objek(img_gray, min_area=500)

    print(f"\n[HASIL DETEKSI] Berhasil mendeteksi {len(daftar_objek)} objek!")
    print(f"{'ID':<4} | {'Centroid (X, Y)':<18} | {'Luas Area (px)':<15} | {'Keliling':<10} | {'Circularity':<12}")
    print("-" * 68)
    for obj in daftar_objek:
        cx, cy = obj["centroid"]
        print(f"#{obj['id']:<3} | ({cx:3d}, {cy:3d}){'':<8} | {obj['area']:<15.1f} | {obj['perimeter']:<10.1f} | {obj['circularity']:<12.3f}")

    # 3. Visualisasi Hasil Pipeline
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    plt.suptitle(f"Praktikum 05: Pipeline Segmentasi & Deteksi Objek ({len(daftar_objek)} Koin Terdeteksi)",
                 fontsize=15, fontweight='bold')

    axes[0, 0].imshow(steps["1_grayscale"], cmap='gray')
    axes[0, 0].set_title("1. Citra Input (Grayscale)", fontsize=11, fontweight='bold')
    axes[0, 0].axis('off')

    axes[0, 1].imshow(steps["2_blurred"], cmap='gray')
    axes[0, 1].set_title("2. Gaussian Blur (Denoise)", fontsize=11, fontweight='bold')
    axes[0, 1].axis('off')

    axes[0, 2].imshow(steps["3_threshold_otsu"], cmap='gray')
    axes[0, 2].set_title("3. Segmentasi Otsu Binarization", fontsize=11, fontweight='bold')
    axes[0, 2].axis('off')

    axes[1, 0].imshow(steps["4_morphology_clean"], cmap='gray')
    axes[1, 0].set_title("4. Pembersihan Morfologi (Open/Close)", fontsize=11, fontweight='bold')
    axes[1, 0].axis('off')

    axes[1, 1].imshow(steps["5_annotated"])
    axes[1, 1].set_title(f"5. Deteksi Objek: Bounding Box & Centroid ({len(daftar_objek)} Koin)", fontsize=11, fontweight='bold')
    axes[1, 1].axis('off')

    # Subplot Tabel Hasil Statistik
    ax_table = axes[1, 2]
    ax_table.axis('off')
    table_data = [
        [f"#{o['id']}", f"({o['centroid'][0]},{o['centroid'][1]})", f"{o['area']:.0f}", f"{o['circularity']:.2f}"]
        for o in daftar_objek[:7] # Ambil 7 teratas agar muat rapi di plot
    ]
    columns = ["ID", "Centroid", "Area", "Circularity"]
    table = ax_table.table(cellText=table_data, colLabels=columns, loc='center', cellLoc='center')
    table.scale(1.0, 1.4)
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    ax_table.set_title("Ringkasan Fitur Morfometri Objek", fontsize=11, fontweight='bold')

    plt.tight_layout()
    out_path = os.path.join(output_dir, "04_object_detection_analysis.png")
    plt.savefig(out_path, dpi=200)
    plt.close()

    print(f"\n[SUCCESS] Hasil visualisasi deteksi objek disimpan di: {out_path}")

if __name__ == "__main__":
    main()
