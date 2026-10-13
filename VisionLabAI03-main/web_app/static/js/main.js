/**
 * Visual Studio Segmentasi Citra Digital - Modern Neo-Brutalism
 * Praktikum 05: Komputer Visi & NLP
 * Identitas: Naufal Ahmad Assyafiq (NIM: 20241020054)
 * Khusus metode To-Zero Thresholding (cv2.THRESH_TOZERO)
 *
 * Real-time In-Memory Client-side Thresholding Engine:
 * - Menggunakan JavaScript Canvas ImageData & requestAnimationFrame
 * - 0ms latency & tanpa flicker pada pergeseran slider T
 * - Bebas request jaringan saat slider digeser
 * - Identik 100% secara matematis dengan cv2.THRESH_TOZERO
 */

// Global State
const state = {
    activeImageId: 'bimodal_coins.png',
    activeImageData: null,       // Base64 untuk citra upload
    activeImageWidth: 600,
    activeImageHeight: 450,

    // In-Memory Pixel Caching
    cachedGrayBuffer: null,      // Uint8Array: piksel grayscale (ukuran w * h)
    resultImageData: null,       // ImageData untuk canvas hasil
    cachedHistogram: null,       // 256 array histogram
    resultCtx: null,             // 2D context canvas hasil
    currentThreshold: 89,        // Nilai T saat ini
    currentBlur: false,          // Status toggle Gaussian Blur
    pendingAnimFrame: null,      // ID requestAnimationFrame
    isServerLoading: false       // Flag request server aktif
};

// DOM Elements
const elements = {
    // Sidebar
    sampleCarousel: document.getElementById('sampleCarousel'),
    fileInput: document.getElementById('fileInput'),
    activeImagePreview: document.getElementById('activeImagePreview'),
    activeImageMeta: document.getElementById('activeImageMeta'),

    // Thresholding Controls
    globalThresholdSlider: document.getElementById('globalThresholdSlider'),
    globalThresholdVal: document.getElementById('globalThresholdVal'),
    threshBlurToggle: document.getElementById('threshBlurToggle'),
    histogramCanvas: document.getElementById('histogramCanvas'),
    histLegendText: document.getElementById('histLegendText'),
    btnRunThreshold: document.getElementById('btnRunThreshold'),

    // Viewport Elements
    threshOriginalImg: document.getElementById('threshOriginalImg'),
    threshResultCanvas: document.getElementById('threshResultCanvas'),
    threshResultImg: document.getElementById('threshResultImg'),
    threshResultTag: document.getElementById('threshResultTag')
};

// ================= INITIALIZATION =================
document.addEventListener('DOMContentLoaded', () => {
    // Inisialisasi canvas konteks
    if (elements.threshResultCanvas) {
        state.resultCtx = elements.threshResultCanvas.getContext('2d', { willReadFrequently: true });
    }

    initSampleImages();
    initUpload();
    initThresholdControls();
});

// ================= SAMPLE IMAGES & UPLOAD =================
async function initSampleImages() {
    try {
        const res = await fetch('/api/samples');
        const data = await res.json();
        if (data.samples && data.samples.length > 0) {
            renderSampleCarousel(data.samples);
            selectSample(data.samples[0]);
        } else {
            console.warn('Sampel kosong, memuat citra default...');
            loadActiveImage(true);
        }
    } catch (err) {
        console.error('Gagal memuat sampel citra:', err);
        loadActiveImage(true);
    }
}

function renderSampleCarousel(samples) {
    elements.sampleCarousel.innerHTML = '';
    samples.forEach(sample => {
        const item = document.createElement('div');
        const safeId = `sample-${sample.id.replace(/[^a-zA-Z0-9_-]/g, '_')}`;
        item.className = `sample-item ${sample.id === state.activeImageId ? 'active' : ''}`;
        item.id = safeId;
        item.innerHTML = `
            <img src="${sample.thumb}" alt="${sample.name}" class="sample-thumb">
            <div class="sample-meta">
                <div class="sample-name">${sample.name}</div>
                <div class="sample-dim">${sample.width}x${sample.height} px</div>
            </div>
        `;
        item.addEventListener('click', () => selectSample(sample));
        elements.sampleCarousel.appendChild(item);
    });
}

function selectSample(sample) {
    state.activeImageId = sample.id;
    state.activeImageData = sample.image_data || null;
    state.activeImageWidth = sample.width || 600;
    state.activeImageHeight = sample.height || 450;

    // Update highlight aktif di sidebar
    document.querySelectorAll('.sample-item').forEach(el => el.classList.remove('active'));
    const safeId = `sample-${sample.id.replace(/[^a-zA-Z0-9_-]/g, '_')}`;
    const currentEl = document.getElementById(safeId);
    if (currentEl) currentEl.classList.add('active');

    elements.activeImagePreview.src = sample.thumb;
    elements.activeImageMeta.textContent = `${sample.name} (${sample.width}x${sample.height} px)`;

    // Muat citra baru dari server (hanya 1 kali saat gambar berganti)
    loadActiveImage(true);
}

function initUpload() {
    elements.fileInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        // Validasi ukuran file: Maksimal 4 MB
        const maxBytes = 4 * 1024 * 1024;
        if (file.size > maxBytes) {
            alert('Ukuran file melebihi batas 4 MB. Silakan pilih file yang lebih kecil.');
            elements.fileInput.value = '';
            return;
        }

        // Validasi format file
        const ext = file.name.split('.').pop().toLowerCase();
        if (!['png', 'jpg', 'jpeg', 'bmp'].includes(ext)) {
            alert('Format file tidak didukung. Gunakan PNG, JPG, JPEG, atau BMP.');
            elements.fileInput.value = '';
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            elements.activeImageMeta.textContent = 'Mengunggah & memproses di memori...';

            const res = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();

            if (data.success) {
                const newSample = {
                    id: data.id,
                    name: data.name,
                    thumb: data.thumb,
                    image_data: data.image_data, // Simpan Data URL di memori client
                    width: data.width,
                    height: data.height
                };

                addUploadedSampleToCarousel(newSample);
                selectSample(newSample);
            } else {
                alert('Gagal mengunggah citra: ' + (data.error || 'Terjadi kesalahan'));
            }
        } catch (err) {
            console.error('Error saat upload:', err);
            alert('Terjadi kesalahan koneksi saat mengunggah file.');
        } finally {
            elements.fileInput.value = '';
        }
    });
}

function addUploadedSampleToCarousel(sample) {
    const safeId = `sample-${sample.id.replace(/[^a-zA-Z0-9_-]/g, '_')}`;
    const existing = document.getElementById(safeId);
    if (existing) existing.remove();

    const item = document.createElement('div');
    item.className = 'sample-item';
    item.id = safeId;
    item.innerHTML = `
        <img src="${sample.thumb}" alt="${sample.name}" class="sample-thumb">
        <div class="sample-meta">
            <div class="sample-name">${sample.name}</div>
            <div class="sample-dim">${sample.width}x${sample.height} px</div>
        </div>
    `;
    item.addEventListener('click', () => selectSample(sample));
    elements.sampleCarousel.prepend(item);
}

// ================= CORE ENGINE: IMAGE LOADING & PIXEL CACHING =================
/**
 * Memuat citra aktif dari server satu kali (saat ganti gambar atau toggle blur),
 * kemudian menyimpan buffer intensitas grayscale di memori browser.
 */
async function loadActiveImage(isNewImage = false) {
    state.isServerLoading = true;
    state.currentThreshold = parseInt(elements.globalThresholdSlider.value);
    state.currentBlur = elements.threshBlurToggle.checked;

    const payload = {
        threshold: state.currentThreshold,
        apply_blur: state.currentBlur
    };

    if (state.activeImageData) {
        payload.image_data = state.activeImageData;
    } else {
        payload.image_id = state.activeImageId || 'bimodal_coins.png';
    }

    try {
        const res = await fetch('/api/threshold', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (data.error) {
            console.error('Error dari backend:', data.error);
            state.isServerLoading = false;
            return;
        }

        // 1. Perbarui gambar Before HANYA jika gambar baru dipilih
        if (isNewImage && data.original) {
            elements.threshOriginalImg.src = data.original;
        }

        // 2. Simpan histogram
        if (data.histogram) {
            state.cachedHistogram = data.histogram;
        }

        // 3. Ekstrak data piksel grayscale (OpenCV proc_gray) ke memori browser
        const graySource = data.gray || data.result;
        if (graySource) {
            const tempImg = new Image();
            tempImg.crossOrigin = 'anonymous';
            tempImg.onload = () => {
                const w = tempImg.naturalWidth;
                const h = tempImg.naturalHeight;
                state.activeImageWidth = w;
                state.activeImageHeight = h;

                // Konfigurasi canvas hasil sesuai resolusi citra asli
                elements.threshResultCanvas.width = w;
                elements.threshResultCanvas.height = h;
                state.resultCtx = elements.threshResultCanvas.getContext('2d', { willReadFrequently: true });
                state.resultImageData = state.resultCtx.createImageData(w, h);

                // Baca piksel grayscale menggunakan offscreen canvas
                const offCanvas = document.createElement('canvas');
                offCanvas.width = w;
                offCanvas.height = h;
                const offCtx = offCanvas.getContext('2d', { willReadFrequently: true });
                offCtx.drawImage(tempImg, 0, 0);

                const rawData = offCtx.getImageData(0, 0, w, h).data;
                const totalPixels = w * h;

                // Alokasikan Uint8Array 1 dimensi (1 byte per piksel)
                state.cachedGrayBuffer = new Uint8Array(totalPixels);
                for (let i = 0; i < totalPixels; i++) {
                    state.cachedGrayBuffer[i] = rawData[i * 4]; // Channel R (R=G=B pada grayscale)
                }

                // Render To-Zero secara instan di browser
                renderToZeroRealtime(state.currentThreshold);
                state.isServerLoading = false;
            };
            tempImg.src = graySource;
        }
    } catch (err) {
        console.error('Gagal memuat citra:', err);
        state.isServerLoading = false;
    }
}

// ================= REAL-TIME TO-ZERO THRESHOLDING (IN-MEMORY) =================
/**
 * Menghitung To-Zero Thresholding secara langsung di browser
 * Aturan matematis cv2.THRESH_TOZERO:
 * dst(x, y) = src(x, y)  jika src(x, y) > T
 * dst(x, y) = 0          jika src(x, y) <= T
 */
function renderToZeroRealtime(t) {
    if (!state.cachedGrayBuffer || !state.resultImageData || !state.resultCtx) {
        return;
    }

    const gray = state.cachedGrayBuffer;
    const len = gray.length;
    const outputPixels = state.resultImageData.data; // Uint8ClampedArray RGBA

    let p = 0;
    // Loop intensitas piksel kecepatan tinggi
    for (let i = 0; i < len; i++) {
        const v = gray[i];
        // Aturan pasti cv2.THRESH_TOZERO
        const val = (v > t) ? v : 0;

        outputPixels[p]     = val; // R
        outputPixels[p + 1] = val; // G
        outputPixels[p + 2] = val; // B
        outputPixels[p + 3] = 255; // Alpha penuh (tidak transparan)
        p += 4;
    }

    // Gambar langsung ke Canvas secara instan tanpa decoding flicker
    state.resultCtx.putImageData(state.resultImageData, 0, 0);

    // Perbarui label status After
    const blurLabel = elements.threshBlurToggle.checked ? ' + Blur' : '';
    elements.threshResultTag.textContent = `After: TOZERO (T=${t})${blurLabel}`;

    // Perbarui histogram responsif (menggeser garis merah indikator T)
    if (state.cachedHistogram) {
        renderHistogram(state.cachedHistogram, t);
    }
}

// ================= CONTROLS & EVENT LISTENERS =================
function initThresholdControls() {
    // Slider T: Respon real-time 60fps dengan requestAnimationFrame
    elements.globalThresholdSlider.addEventListener('input', (e) => {
        const t = parseInt(e.target.value);
        state.currentThreshold = t;
        elements.globalThresholdVal.textContent = t;

        // Batalkan frame sebelumnya jika masih antri
        if (state.pendingAnimFrame) {
            cancelAnimationFrame(state.pendingAnimFrame);
        }

        // Jadwalkan render pada frame browser berikutnya
        state.pendingAnimFrame = requestAnimationFrame(() => {
            renderToZeroRealtime(state.currentThreshold);
            state.pendingAnimFrame = null;
        });
    });

    // Toggle Gaussian Blur: Update buffer grayscale yang di-blur dari server
    elements.threshBlurToggle.addEventListener('change', () => {
        state.currentBlur = elements.threshBlurToggle.checked;
        loadActiveImage(false); // Ambil versi blur baru, Before image tidak diubah
    });

    // Tombol Terapkan Thresholding: Render langsung
    elements.btnRunThreshold.addEventListener('click', () => {
        renderToZeroRealtime(state.currentThreshold);
    });
}

// ================= HISTOGRAM RENDERING =================
function renderHistogram(histData, calculatedT) {
    const canvas = elements.histogramCanvas;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;

    // Bersihkan canvas
    ctx.clearRect(0, 0, width, height);

    // Latar belakang putih bersih
    ctx.fillStyle = '#FFFFFF';
    ctx.fillRect(0, 0, width, height);

    const maxVal = Math.max(...histData);
    const barWidth = width / 256;

    // Gambar batang histogram (Electric Blue #5865F2)
    ctx.fillStyle = '#5865F2';
    for (let i = 0; i < 256; i++) {
        const barHeight = (histData[i] / (maxVal || 1)) * (height - 18);
        ctx.fillRect(i * barWidth, height - barHeight, Math.max(1.2, barWidth), barHeight);
    }

    // Gambar garis vertikal merah penanda nilai ambang T
    if (calculatedT !== undefined && calculatedT >= 0) {
        const lineX = (calculatedT / 255) * width;
        ctx.strokeStyle = '#EF4444';
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        ctx.moveTo(lineX, 0);
        ctx.lineTo(lineX, height);
        ctx.stroke();

        // Label T di dekat garis
        ctx.fillStyle = '#000000';
        ctx.font = 'bold 11px JetBrains Mono, monospace';
        ctx.textAlign = 'center';
        const labelX = Math.min(Math.max(lineX, 24), width - 24);
        ctx.fillText(`T=${calculatedT}`, labelX, 12);

        // Update teks legend
        if (elements.histLegendText) {
            elements.histLegendText.textContent = `Nilai Ambang Terpilih (T) = ${calculatedT}`;
        }
    }
}
