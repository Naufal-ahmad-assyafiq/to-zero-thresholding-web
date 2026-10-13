"""
Flask Web Application: Visual Studio Segmentasi Citra Digital
Aplikasi khusus To-Zero Thresholding untuk tugas praktikum Computer Vision & NLP.
Menggunakan metode cv2.THRESH_TOZERO untuk pengolahan intensitas citra.
"""

import os
import base64
from flask import Flask, render_template, request, jsonify
import cv2
import numpy as np

app = Flask(__name__, static_folder='static', template_folder='templates')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
SAMPLE_DIR = os.path.join(PARENT_DIR, "sample_images")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Batas ukuran upload: 5 MB
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Ekstensi file yang diperbolehkan
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Helper: encode OpenCV image to base64 png
def encode_image(img, ext=".png"):
    is_success, buffer = cv2.imencode(ext, img)
    if not is_success:
        return ""
    return f"data:image/png;base64,{base64.b64encode(buffer).decode('utf-8')}"

# Helper: get image array from path or upload
def get_image(img_source):
    if not img_source:
        img_source = "bimodal_coins.png"

    # Cek di uploads terlebih dahulu
    upload_path = os.path.join(UPLOAD_DIR, img_source)
    if os.path.exists(upload_path):
        return cv2.imread(upload_path)

    # Cek di sample_images
    sample_path = os.path.join(SAMPLE_DIR, img_source)
    if os.path.exists(sample_path):
        return cv2.imread(sample_path)

    # Fallback jika full path
    if os.path.exists(img_source):
        return cv2.imread(img_source)

    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/samples', methods=['GET'])
def get_samples():
    samples = []
    if os.path.exists(SAMPLE_DIR):
        for fname in sorted(os.listdir(SAMPLE_DIR)):
            if fname.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                fpath = os.path.join(SAMPLE_DIR, fname)
                img = cv2.imread(fpath)
                if img is not None:
                    h, w = img.shape[:2]
                    # Create thumbnail
                    thumb = cv2.resize(img, (120, int(120 * h / w)))
                    samples.append({
                        "id": fname,
                        "name": fname.replace(".png", "").replace("_", " ").title(),
                        "thumb": encode_image(thumb),
                        "width": w,
                        "height": h
                    })
    return jsonify({"samples": samples})

@app.route('/api/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Format file tidak didukung. Gunakan PNG, JPG, atau BMP."}), 400

    filename = f"upload_{len(os.listdir(UPLOAD_DIR))}_{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    file.save(filepath)

    img = cv2.imread(filepath)
    if img is None:
        return jsonify({"error": "Format citra tidak valid"}), 400

    h, w = img.shape[:2]
    thumb = cv2.resize(img, (120, int(120 * h / w)))
    return jsonify({
        "success": True,
        "id": filename,
        "name": file.filename,
        "thumb": encode_image(thumb),
        "width": w,
        "height": h
    })

@app.route('/api/threshold', methods=['POST'])
def process_threshold():
    """
    Proses To-Zero Thresholding pada citra.
    Aturan To-Zero: piksel dengan intensitas > T dipertahankan,
    piksel dengan intensitas <= T diubah menjadi 0.
    Menggunakan cv2.THRESH_TOZERO.
    """
    data = request.json or {}
    img_id = data.get('image_id', 'bimodal_coins.png')
    thresh_val = int(data.get('threshold', 89))
    apply_blur = bool(data.get('apply_blur', False))

    img = get_image(img_id)
    if img is None:
        return jsonify({"error": "Citra tidak ditemukan"}), 404

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img.copy()

    # Hitung histogram grayscale dari citra aktif
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).ravel().tolist()

    # Terapkan Gaussian Blur jika dipilih (opsional denoise)
    proc_gray = cv2.GaussianBlur(gray, (5, 5), 0) if apply_blur else gray

    # Terapkan To-Zero Thresholding: cv2.THRESH_TOZERO
    # Piksel > T → dipertahankan, piksel <= T → 0
    _, res = cv2.threshold(proc_gray, thresh_val, 255, cv2.THRESH_TOZERO)

    return jsonify({
        "original": encode_image(img),
        "result": encode_image(res),
        "histogram": hist,
        "calculated_threshold": thresh_val,
        "method": "tozero"
    })

if __name__ == '__main__':
    # Running locally on port 5050
    print("=" * 55)
    print("  VISUAL STUDIO SEGMENTASI CITRA - TO-ZERO THRESHOLDING")
    print("=" * 55)
    print("Membuka server di http://localhost:5050 ...")
    print("Tekan Ctrl+C untuk menghentikan server.")
    app.run(host='0.0.0.0', port=5050, debug=False)
