/**
 * Visual Studio Segmentasi Citra Digital - Modern Neo-Brutalism
 * Praktikum 05: Komputer Visi & NLP
 * Identitas: Naufal Ahmad Assyafiq (NIM: 20241020054)
 * Khusus metode To-Zero Thresholding (cv2.THRESH_TOZERO)
 * Dioptimalkan untuk Vercel Serverless (In-Memory Processing)
 */

// Global State
const state = {
    activeImageId: 'bimodal_coins.png',
    activeImageData: null, // Menyimpan base64 data URL untuk citra upload di memori
    activeImageUrl: '',
    activeImageWidth: 600,
    activeImageHeight: 450
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
    threshOriginalImg: document.getElementById('threshOriginalImg'),
    threshResultImg: document.getElementById('threshResultImg'),
    threshResultTag: document.getElementById('threshResultTag')
};

// ================= INITIALIZATION =================
document.addEventListener('DOMContentLoaded', () => {
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
            console.warn('Tidak ada sampel citra yang diterima dari server.');
            // Fallback default trigger
            runThresholding();
        }
    } catch (err) {
        console.error('Gagal memuat sampel citra:', err);
        // Tetap jalankan thresholding default agar Before/After dan histogram muncul
        runThresholding();
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
    state.activeImageData = sample.image_data || null; // Jika ada image_data (hasil upload di memori)
    state.activeImageWidth = sample.width;
    state.activeImageHeight = sample.height;

    // Update highlight aktif di sidebar
    document.querySelectorAll('.sample-item').forEach(el => el.classList.remove('active'));
    const safeId = `sample-${sample.id.replace(/[^a-zA-Z0-9_-]/g, '_')}`;
    const currentEl = document.getElementById(safeId);
    if (currentEl) currentEl.classList.add('active');

    elements.activeImagePreview.src = sample.thumb;
    elements.activeImageMeta.textContent = `${sample.name} (${sample.width}x${sample.height} px)`;

    // Otomatis jalankan thresholding
    runThresholding();
}

function initUpload() {
    elements.fileInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        // Validasi ukuran file: Maksimal 4 MB (Sesuai instruksi)
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
            // Tampilkan indikator status upload
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
                    image_data: data.image_data, // Disimpan langsung di memori client
                    width: data.width,
                    height: data.height
                };

                // Sisipkan citra upload ke daftar sampel carousel
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
    // Hapus jika sudah ada elemen dengan ID yang sama
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
    elements.sampleCarousel.prepend(item); // Tempatkan di posisi teratas
}

// ================= TO-ZERO THRESHOLDING LOGIC =================
function initThresholdControls() {
    // Slider T: update label real-time
    elements.globalThresholdSlider.addEventListener('input', (e) => {
        elements.globalThresholdVal.textContent = e.target.value;
    });

    // Jalankan thresholding saat slider selesai digeser
    elements.globalThresholdSlider.addEventListener('change', () => {
        runThresholding();
    });

    // Toggle Gaussian Blur
    elements.threshBlurToggle.addEventListener('change', () => {
        runThresholding();
    });

    // Tombol Terapkan Thresholding
    elements.btnRunThreshold.addEventListener('click', () => {
        runThresholding();
    });
}

async function runThresholding() {
    const threshVal = parseInt(elements.globalThresholdSlider.value);
    const applyBlur = elements.threshBlurToggle.checked;

    const payload = {
        threshold: threshVal,
        apply_blur: applyBlur
    };

    // Jika citra saat ini berasal dari upload, kirim image_data (base64 di memori)
    // Jika dari sampel bawaan, kirim image_id
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
            console.error('Error thresholding dari server:', data.error);
            return;
        }

        if (data.result) {
            // Tampilkan citra Before & After
            elements.threshOriginalImg.src = data.original;
            elements.threshResultImg.src = data.result;

            // Update badge label hasil Before & After
            const blurLabel = applyBlur ? ' + Blur' : '';
            elements.threshResultTag.textContent = `After: TOZERO (T=${data.calculated_threshold})${blurLabel}`;

            // Render histogram dari citra aktif
            if (data.histogram) {
                renderHistogram(data.histogram, data.calculated_threshold);
            }
        }
    } catch (err) {
        console.error('Error thresholding fetch:', err);
    }
}

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

    // Gambar garis vertikal merah sebagai penanda nilai ambang T
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
