"""
Script Runner Otomatis untuk Praktikum 05
Menjalankan seluruh tahapan modul:
1. Generator Citra Sampel (00_generate_samples.py)
2. Eksplorasi Thresholding (01_thresholding.py)
3. Region Growing (02_region_growing.py)
4. Pemisahan Objek dan Latar Belakang (03_pemisahan_objek_background.py)
5. Deteksi dan Analisis Objek (04_deteksi_dan_analisis_objek.py)
"""

import subprocess
import sys
import os

SCRIPTS = [
    ("00_generate_samples.py", "Menyiapkan Citra Sampel Sintetis"),
    ("01_thresholding.py", "Eksplorasi Global, Otsu, dan Adaptive Thresholding"),
    ("02_region_growing.py", "Segmentasi Citra Berbasis Wilayah (Region Growing)"),
    ("03_pemisahan_objek_background.py", "Pemisahan Foreground-Background (HSV, Morfologi, GrabCut)"),
    ("04_deteksi_dan_analisis_objek.py", "Studi Kasus Deteksi dan Analisis Objek Koin"),
    ("05_deteksi_tepi.py", "Perbandingan Metode Deteksi Tepi (Canny, Sobel, Prewitt, Roberts)"),
    ("06_clustering.py", "Segmentasi Citra Berbasis Clustering (K-Means & Fuzzy C-Means)")
]

def main():
    print("=" * 70)
    print("  MENJALANKAN SELURUH MODUL PRAKTIKUM 05: SEGMENTASI CITRA DIGITAL")
    print("=" * 70)

    base_dir = os.path.dirname(os.path.abspath(__file__))

    for idx, (script, desc) in enumerate(SCRIPTS, start=1):
        print(f"\n[{idx}/{len(SCRIPTS)}] Menjalankan: {script} -> {desc}")
        print("-" * 70)
        script_path = os.path.join(base_dir, script)
        result = subprocess.run([sys.executable, script_path], cwd=base_dir)
        if result.returncode != 0:
            print(f"[ERROR] Skrip {script} gagal dieksekusi dengan kode: {result.returncode}")
            sys.exit(result.returncode)

    print("\n" + "=" * 70)
    print("  SEMUA TAHAPAN PRAKTIKUM 05 SELESAI DIEKSEKUSI DENGAN SUKSES!")
    print(f"  Silakan periksa folder hasil plot di: {os.path.join(base_dir, 'output')}")
    print("=" * 70)

if __name__ == "__main__":
    main()
