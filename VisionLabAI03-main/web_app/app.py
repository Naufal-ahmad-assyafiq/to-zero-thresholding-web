"""
Flask Web Application: Visual Studio Segmentasi Citra Digital
Aplikasi khusus To-Zero Thresholding untuk tugas praktikum Computer Vision & NLP.
Dioptimalkan untuk deployment Vercel (Serverless / Read-Only Filesystem) & Localhost.
Identitas Mahasiswa: Naufal Ahmad Assyafiq (NIM: 20241020054)
"""

import os
import sys
import base64
from flask import Flask, render_template, request, jsonify
import cv2
import numpy as np

# Konfigurasi path aplikasi
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)

app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, 'static'),
    template_folder=os.path.join(BASE_DIR, 'templates')
)

# Batas ukuran upload: 4 MB (Sesuai instruksi)
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Ekstensi file yang diperbolehkan
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def encode_image(img, ext=".png"):
    """Encode OpenCV image (BGR/Gray) ke base64 data URL."""
    if img is None:
        return ""
    is_success, buffer = cv2.imencode(ext, img)
    if not is_success:
        return ""
    return f"data:image/png;base64,{base64.b64encode(buffer).decode('utf-8')}"

def decode_base64_image(data_uri):
    """Decode base64 string / Data URI ke citra OpenCV numpy array di memori."""
    try:
        if not data_uri:
            return None
        if ',' in data_uri:
            data_uri = data_uri.split(',', 1)[1]
        img_bytes = base64.b64decode(data_uri)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        return cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    except Exception as e:
        print(f"Error decoding base64 image: {e}")
        return None

def find_sample_dir():
    """
    Mencari direktori sample_images dari berbagai lokasi yang mungkin:
    - web_app/sample_images (dibundle langsung dalam folder web_app)
    - ../sample_images (di root project VisionLabAI03)
    - ./sample_images (current working directory)
    - ./web_app/sample_images
    - /var/task/... (AWS Lambda / Vercel container paths)
    """
    candidates = [
        os.path.join(BASE_DIR, "sample_images"),
        os.path.join(PARENT_DIR, "sample_images"),
        os.path.join(os.getcwd(), "web_app", "sample_images"),
        os.path.join(os.getcwd(), "sample_images"),
        "/var/task/sample_images",
        "/var/task/web_app/sample_images"
    ]
    for d in candidates:
        if os.path.exists(d) and os.path.isdir(d):
            files = [f for f in os.listdir(d) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
            if files:
                return d
    return None

def generate_fallback_image(name):
    """
    Menghasilkan citra sampel sintetis langsung di memori
    sebagai fallback jika file fisik tidak dapat dibaca di environment Vercel.
    """
    name_lower = name.lower()
    if "coin" in name_lower or "bimodal" in name_lower:
        h, w = 450, 600
        img = np.full((h, w), 45, dtype=np.uint8)
        coins = [
            (120, 130, 50, 195),
            (260, 110, 40, 210),
            (390, 140, 45, 185),
            (510, 110, 35, 200),
            (150, 290, 55, 190),
            (300, 280, 48, 215),
            (450, 290, 52, 205),
            (220, 390, 38, 180),
            (370, 390, 42, 220),
        ]
        for cx, cy, r, val in coins:
            cv2.circle(img, (cx, cy), r, int(val), -1)
            cv2.circle(img, (cx, cy), r - 5, int(val - 15), 2)
            cv2.putText(img, "Rp", (cx - 15, cy + 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, int(val - 35), 2)
        noise = np.random.normal(0, 7, (h, w))
        return np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)

    elif "fruit" in name_lower or "color" in name_lower:
        h, w = 450, 650
        img = np.full((h, w, 3), (210, 225, 230), dtype=np.uint8)
        cv2.ellipse(img, (200, 260), (45, 15), 0, 0, 360, (170, 185, 190), -1)
        cv2.circle(img, (200, 240), 65, (40, 40, 210), -1)
        cv2.ellipse(img, (340, 275), (40, 12), 0, 0, 360, (170, 185, 190), -1)
        cv2.circle(img, (340, 255), 58, (30, 200, 235), -1)
        cv2.ellipse(img, (460, 285), (32, 10), 0, 0, 360, (170, 185, 190), -1)
        cv2.ellipse(img, (460, 265), (35, 50), 0, 0, 360, (50, 180, 50), -1)
        return img

    elif "shape" in name_lower or "noisy" in name_lower:
        h, w = 400, 500
        img = np.full((h, w), 50, dtype=np.uint8)
        cv2.rectangle(img, (60, 60), (190, 190), 190, -1)
        cv2.circle(img, (350, 130), 65, 210, -1)
        pts = np.array([[120, 250], [60, 350], [180, 350]], np.int32)
        cv2.fillPoly(img, [pts], 175)
        cv2.ellipse(img, (350, 290), (70, 45), 30, 0, 360, 200, -1)
        noise = np.random.normal(0, 12, (h, w))
        return np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)

    else:
        h, w = 400, 600
        x = np.linspace(0, 1, w)
        y = np.linspace(0, 1, h)
        xx, yy = np.meshgrid(x, y)
        gradient = (1.0 - (0.7 * xx + 0.3 * yy)) * 255.0
        img = gradient.astype(np.uint8)
        cv2.putText(img, "PRAKTIKUM 05", (40, 90), cv2.FONT_HERSHEY_SIMPLEX, 1.6, 30, 3)
        cv2.putText(img, "TO-ZERO THRESHOLD", (40, 160), cv2.FONT_HERSHEY_SIMPLEX, 1.1, 30, 2)
        cv2.putText(img, "Laboratorium Visi Komputer", (40, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.9, 30, 2)
        noise = np.random.normal(0, 6, (h, w))
        return np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)

def get_sample_image(img_id):
    """Mendapatkan array citra sampel dari disk atau generator in-memory."""
    if not img_id:
        img_id = "bimodal_coins.png"

    sample_dir = find_sample_dir()
    if sample_dir:
        base_id = os.path.basename(img_id)
        target_path = os.path.join(sample_dir, base_id)
        if os.path.exists(target_path):
            img = cv2.imread(target_path)
            if img is not None:
                return img

    return generate_fallback_image(img_id)

def generate_in_memory_samples():
    """Menghasilkan list sampel lengkap jika direktori fisik kosong / tidak ditemukan."""
    fallback_defs = [
        ("bimodal_coins.png", "Bimodal Coins", 600, 450),
        ("fruits_color.png", "Fruits Color", 650, 450),
        ("shapes_noisy.png", "Shapes Noisy", 500, 400),
        ("uneven_light.png", "Uneven Light", 600, 400)
    ]
    res = []
    for fname, name, w, h in fallback_defs:
        img = generate_fallback_image(fname)
        thumb = cv2.resize(img, (120, max(1, int(120 * h / w))))
        res.append({
            "id": fname,
            "name": name,
            "thumb": encode_image(thumb),
            "width": w,
            "height": h
        })
    return res

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/samples', methods=['GET'])
def get_samples():
    """Endpoint untuk mendapatkan daftar citra sampel dari disk atau in-memory."""
    sample_dir = find_sample_dir()
    samples = []

    if sample_dir and os.path.exists(sample_dir):
        for fname in sorted(os.listdir(sample_dir)):
            if fname.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                fpath = os.path.join(sample_dir, fname)
                img = cv2.imread(fpath)
                if img is not None:
                    h, w = img.shape[:2]
                    thumb = cv2.resize(img, (120, max(1, int(120 * h / w))))
                    clean_name = fname.replace(".png", "").replace(".jpg", "").replace(".jpeg", "").replace(".bmp", "")
                    samples.append({
                        "id": fname,
                        "name": clean_name.replace("_", " ").title(),
                        "thumb": encode_image(thumb),
                        "width": w,
                        "height": h
                    })

    # Jika folder belum ditemukan di Vercel, gunakan in-memory fallback generator
    if not samples:
        samples = generate_in_memory_samples()

    return jsonify({"samples": samples})

@app.route('/api/upload', methods=['POST'])
def upload_image():
    """
    Endpoint upload citra yang diproses 100% di MEMORI tanpa menulis ke folder uploads.
    Aman untuk Vercel Serverless (Read-only filesystem) dan batas ukuran 4 MB.
    """
    if 'file' not in request.files:
        return jsonify({"error": "File tidak ditemukan dalam request upload"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Tidak ada file yang dipilih"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Format file tidak didukung. Gunakan PNG, JPG, JPEG, atau BMP."}), 400

    # Baca byte citra langsung di memori
    file_bytes = file.read()
    
    # Validasi batas ukuran 4 MB
    if len(file_bytes) > 4 * 1024 * 1024:
        return jsonify({"error": "Ukuran file melebihi batas 4 MB"}), 400

    # Decode langsung menggunakan OpenCV di memori
    np_arr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if img is None:
        return jsonify({"error": "Format citra tidak valid atau file rusak"}), 400

    h, w = img.shape[:2]
    # Optimasi resolusi maksimum 1600px untuk efisiensi base64
    max_dim = 1600
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)))
        h, w = img.shape[:2]

    thumb_w = 120
    thumb_h = max(1, int(120 * h / w))
    thumb = cv2.resize(img, (thumb_w, thumb_h))

    return jsonify({
        "success": True,
        "id": f"upload_{file.filename}",
        "name": file.filename,
        "thumb": encode_image(thumb),
        "image_data": encode_image(img),
        "width": w,
        "height": h
    })

@app.route('/api/threshold', methods=['POST'])
def process_threshold():
    """
    Proses To-Zero Thresholding pada citra (cv2.THRESH_TOZERO).
    Menerima 'image_data' (base64 string dari memori upload)
    atau 'image_id' (nama file sampel).
    """
    data = request.json or {}
    img_data = data.get('image_data')
    img_id = data.get('image_id', 'bimodal_coins.png')
    thresh_val = int(data.get('threshold', 89))
    apply_blur = bool(data.get('apply_blur', False))

    img = None
    # Prioritaskan image_data (base64 di memori hasil upload)
    if img_data:
        img = decode_base64_image(img_data)

    # Jika bukan dari upload, muat citra sampel
    if img is None and img_id:
        img = get_sample_image(img_id)

    # Fallback terakhir jika citra gagal dimuat
    if img is None:
        img = generate_fallback_image("bimodal_coins.png")

    if img is None:
        return jsonify({"error": "Citra tidak dapat diproses"}), 404

    # Konversi ke grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img.copy()

    # Hitung histogram grayscale (256 bin, 0-256)
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).ravel().tolist()

    # Terapkan Gaussian Blur jika opsi dipilih
    proc_gray = cv2.GaussianBlur(gray, (5, 5), 0) if apply_blur else gray

    # Terapkan To-Zero Thresholding: cv2.THRESH_TOZERO
    # Aturan: piksel > T dipertahankan, piksel <= T diubah menjadi 0 (hitam)
    _, res = cv2.threshold(proc_gray, thresh_val, 255, cv2.THRESH_TOZERO)

    return jsonify({
        "original": encode_image(img),
        "gray": encode_image(proc_gray),
        "result": encode_image(res),
        "histogram": hist,
        "calculated_threshold": thresh_val,
        "method": "tozero"
    })

# Handler untuk Vercel WSGI
wsgi_app = app

if __name__ == '__main__':
    print("=" * 55)
    print("  VISUAL STUDIO SEGMENTASI CITRA - TO-ZERO THRESHOLDING")
    print("  Server Berjalan di http://localhost:5050 ...")
    print("=" * 55)
    app.run(host='0.0.0.0', port=5050, debug=False)
