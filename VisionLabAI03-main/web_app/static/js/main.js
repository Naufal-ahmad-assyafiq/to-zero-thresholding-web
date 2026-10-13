
/**
 * TO-ZERO THRESHOLDING
 * Naufal Ahmad Assyafiq
 * NIM: 20241020054
 *
 * Fitur:
 * - Upload gambar
 * - Sampel gambar
 * - To-Zero Thresholding real-time
 * - Gaussian Blur ON/OFF
 * - Histogram
 * - Canvas tanpa flicker
 */

// ================= STATE =================

const state = {
    activeImageId: 'bimodal_coins.png',
    activeImageData: null,
    activeImageWidth: 600,
    activeImageHeight: 450,

    rawGrayBuffer: null,
    blurredGrayBuffer: null,

    cachedHistogram: null,

    resultCtx: null,
    resultImageData: null,

    currentThreshold: 89,
    pendingAnimFrame: null,
    currentRequestId: 0,
    isServerLoading: false
};

// ================= ELEMENTS =================

const elements = {
    sampleCarousel: document.getElementById('sampleCarousel'),
    fileInput: document.getElementById('fileInput'),
    activeImagePreview: document.getElementById('activeImagePreview'),
    activeImageMeta: document.getElementById('activeImageMeta'),

    globalThresholdSlider: document.getElementById('globalThresholdSlider'),
    globalThresholdVal: document.getElementById('globalThresholdVal'),
    threshBlurToggle: document.getElementById('threshBlurToggle'),

    histogramCanvas: document.getElementById('histogramCanvas'),
    histLegendText: document.getElementById('histLegendText'),
    btnRunThreshold: document.getElementById('btnRunThreshold'),

    threshOriginalImg: document.getElementById('threshOriginalImg'),
    threshResultCanvas: document.getElementById('threshResultCanvas'),
    threshResultImg: document.getElementById('threshResultImg'),
    threshResultTag: document.getElementById('threshResultTag')
};

// ================= INITIALIZATION =================

function initializeApp() {
    if (elements.threshResultCanvas) {
        state.resultCtx =
            elements.threshResultCanvas.getContext('2d');
    }

    if (elements.globalThresholdSlider) {
        state.currentThreshold =
            Number(elements.globalThresholdSlider.value);
    }

    initSampleImages();
    initUpload();
    initThresholdControls();
}

if (document.readyState === 'loading') {
    document.addEventListener(
        'DOMContentLoaded',
        initializeApp
    );
} else {
    initializeApp();
}

// ================= SAMPLE IMAGES =================

async function initSampleImages() {
    try {
        const response = await fetch('/api/samples');

        if (!response.ok) {
            throw new Error('Gagal mengambil sampel');
        }

        const data = await response.json();

        if (data.samples && data.samples.length > 0) {
            renderSampleCarousel(data.samples);
            selectSample(data.samples[0]);
        } else {
            loadActiveImage(true);
        }

    } catch (error) {
        console.error('Gagal memuat sampel:', error);
        loadActiveImage(true);
    }
}

function safeSampleId(id) {
    return 'sample-' +
        String(id).replace(/[^a-zA-Z0-9_-]/g, '_');
}

function createSampleElement(sample) {
    const item = document.createElement('div');

    item.className = 'sample-item';
    item.id = safeSampleId(sample.id);

    const img = document.createElement('img');
    img.src = sample.thumb;
    img.alt = sample.name;
    img.className = 'sample-thumb';

    const meta = document.createElement('div');
    meta.className = 'sample-meta';

    const name = document.createElement('div');
    name.className = 'sample-name';
    name.textContent = sample.name;

    const dim = document.createElement('div');
    dim.className = 'sample-dim';
    dim.textContent =
        `${sample.width}x${sample.height} px`;

    meta.appendChild(name);
    meta.appendChild(dim);

    item.appendChild(img);
    item.appendChild(meta);

    item.addEventListener('click', () => {
        selectSample(sample);
    });

    return item;
}

function renderSampleCarousel(samples) {
    if (!elements.sampleCarousel) return;

    elements.sampleCarousel.innerHTML = '';

    samples.forEach(sample => {
        elements.sampleCarousel.appendChild(
            createSampleElement(sample)
        );
    });
}

function selectSample(sample) {
    state.activeImageId = sample.id;
    state.activeImageData = sample.image_data || null;

    state.activeImageWidth = sample.width || 600;
    state.activeImageHeight = sample.height || 450;

    // Kosongkan buffer lama supaya tidak tertukar
    state.rawGrayBuffer = null;
    state.blurredGrayBuffer = null;

    document.querySelectorAll('.sample-item')
        .forEach(item => {
            item.classList.remove('active');
        });

    const selected = document.getElementById(
        safeSampleId(sample.id)
    );

    if (selected) {
        selected.classList.add('active');
    }

    if (elements.activeImagePreview) {
        elements.activeImagePreview.src = sample.thumb;
    }

    if (elements.activeImageMeta) {
        elements.activeImageMeta.textContent =
            `${sample.name} (${sample.width}x${sample.height} px)`;
    }

    loadActiveImage(true);
}

// ================= UPLOAD =================

function initUpload() {
    if (!elements.fileInput) return;

    elements.fileInput.addEventListener(
        'change',
        async event => {
            const file = event.target.files[0];

            if (!file) return;

            const maxBytes = 4 * 1024 * 1024;

            if (file.size > maxBytes) {
                alert(
                    'Ukuran file maksimal 4 MB.'
                );
                elements.fileInput.value = '';
                return;
            }

            const ext = file.name
                .split('.')
                .pop()
                .toLowerCase();

            if (
                !['png', 'jpg', 'jpeg', 'bmp'].includes(ext)
            ) {
                alert(
                    'Gunakan PNG, JPG, JPEG, atau BMP.'
                );
                elements.fileInput.value = '';
                return;
            }

            const formData = new FormData();
            formData.append('file', file);

            try {
                if (elements.activeImageMeta) {
                    elements.activeImageMeta.textContent =
                        'Mengunggah gambar...';
                }

                const response = await fetch(
                    '/api/upload',
                    {
                        method: 'POST',
                        body: formData
                    }
                );

                const data = await response.json();

                if (!response.ok || !data.success) {
                    throw new Error(
                        data.error || 'Upload gagal'
                    );
                }

                const sample = {
                    id: data.id,
                    name: data.name,
                    thumb: data.thumb,
                    image_data: data.image_data,
                    width: data.width,
                    height: data.height
                };

                addUploadedSampleToCarousel(sample);
                selectSample(sample);

            } catch (error) {
                console.error(error);
                alert(
                    'Gagal upload: ' + error.message
                );
            } finally {
                elements.fileInput.value = '';
            }
        }
    );
}

function addUploadedSampleToCarousel(sample) {
    if (!elements.sampleCarousel) return;

    const existing = document.getElementById(
        safeSampleId(sample.id)
    );

    if (existing) {
        existing.remove();
    }

    elements.sampleCarousel.prepend(
        createSampleElement(sample)
    );
}

// ================= IMAGE BUFFER =================

function extractGrayscaleBuffer(dataUri) {
    return new Promise((resolve, reject) => {
        if (!dataUri) {
            reject(new Error('Data gambar kosong'));
            return;
        }

        const img = new Image();

        img.onload = () => {
            const width = img.naturalWidth;
            const height = img.naturalHeight;

            const canvas =
                document.createElement('canvas');

            canvas.width = width;
            canvas.height = height;

            const ctx = canvas.getContext(
                '2d',
                { willReadFrequently: true }
            );

            ctx.drawImage(img, 0, 0);

            const pixels = ctx.getImageData(
                0, 0, width, height
            ).data;

            const gray = new Uint8Array(
                width * height
            );

            for (let i = 0; i < gray.length; i++) {
                // Gambar dari backend sudah grayscale
                gray[i] = pixels[i * 4];
            }

            resolve({
                buffer: gray,
                width,
                height
            });
        };

        img.onerror = () => {
            reject(
                new Error('Gagal membaca buffer gambar')
            );
        };

        img.src = dataUri;
    });
}

// ================= GAUSSIAN BLUR =================

/**
 * Gaussian Blur 5x5
 * Kernel:
 * [1, 4, 6, 4, 1] / 16
 *
 * Dipakai sebagai fallback bila buffer
 * Gaussian Blur dari OpenCV tidak tersedia.
 */

function reflect101(index, size) {
    if (size <= 1) return 0;

    while (index < 0 || index >= size) {
        if (index < 0) {
            index = -index;
        }

        if (index >= size) {
            index = 2 * size - index - 2;
        }
    }

    return index;
}

function computeGaussianBlur5x5(
    src,
    width,
    height
) {
    const kernel = [1, 4, 6, 4, 1];

    const temp = new Float32Array(
        width * height
    );

    const output = new Uint8Array(
        width * height
    );

    // Horizontal
    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            let sum = 0;

            for (let k = -2; k <= 2; k++) {
                const xx = reflect101(
                    x + k,
                    width
                );

                sum +=
                    src[y * width + xx] *
                    kernel[k + 2];
            }

            temp[y * width + x] = sum / 16;
        }
    }

    // Vertical
    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            let sum = 0;

            for (let k = -2; k <= 2; k++) {
                const yy = reflect101(
                    y + k,
                    height
                );

                sum +=
                    temp[yy * width + x] *
                    kernel[k + 2];
            }

            output[y * width + x] =
                Math.round(sum / 16);
        }
    }

    return output;
}

// ================= LOAD IMAGE =================

async function loadActiveImage(isNewImage = false) {
    const requestId = ++state.currentRequestId;

    state.isServerLoading = true;

    // Hentikan frame dari gambar sebelumnya
    if (state.pendingAnimFrame !== null) {
        cancelAnimationFrame(
            state.pendingAnimFrame
        );

        state.pendingAnimFrame = null;
    }

    const payload = {
        threshold: state.currentThreshold,
        apply_blur: false
    };

    if (state.activeImageData) {
        payload.image_data = state.activeImageData;
    } else {
        payload.image_id =
            state.activeImageId;
    }

    try {
        const response = await fetch(
            '/api/threshold',
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            }
        );

        if (!response.ok) {
            throw new Error(
                'Server gagal memproses gambar'
            );
        }

        const data = await response.json();

        if (requestId !== state.currentRequestId) {
            return;
        }

        if (data.error) {
            throw new Error(data.error);
        }

        // Ambil grayscale asli dan hasil Gaussian Blur
        const rawSource = data.gray;
        const blurSource = data.gray_blur;

        if (!rawSource) {
            throw new Error(
                'Backend tidak mengirim field gray'
            );
        }

        // Decode keduanya terlebih dahulu
        const rawDecoded =
            await extractGrayscaleBuffer(rawSource);

        let blurDecoded = null;

        if (blurSource) {
            blurDecoded =
                await extractGrayscaleBuffer(blurSource);
        }

        if (requestId !== state.currentRequestId) {
            return;
        }

        const width = rawDecoded.width;
        const height = rawDecoded.height;

        state.activeImageWidth = width;
        state.activeImageHeight = height;

        state.rawGrayBuffer = rawDecoded.buffer;

        // Prioritaskan hasil Gaussian Blur asli OpenCV
        if (
            blurDecoded &&
            blurDecoded.width === width &&
            blurDecoded.height === height &&
            blurDecoded.buffer.length ===
                rawDecoded.buffer.length
        ) {
            state.blurredGrayBuffer =
                blurDecoded.buffer;
        } else {
            state.blurredGrayBuffer =
                computeGaussianBlur5x5(
                    state.rawGrayBuffer,
                    width,
                    height
                );
        }

        state.cachedHistogram =
            data.histogram || null;

        // Canvas disiapkan satu kali per gambar
        const canvas = elements.threshResultCanvas;

        if (!canvas) {
            throw new Error(
                'Elemen threshResultCanvas tidak ditemukan'
            );
        }

        canvas.width = width;
        canvas.height = height;

        state.resultCtx = canvas.getContext('2d');

        state.resultImageData =
            state.resultCtx.createImageData(
                width,
                height
            );

        // Jangan tampilkan gambar hasil lama di atas Canvas
        if (elements.threshResultImg) {
            elements.threshResultImg.style.display =
                'none';
        }

        canvas.style.display = 'block';

        if (isNewImage && data.original) {
            elements.threshOriginalImg.src =
                data.original;
        }

        state.isServerLoading = false;

        // Pemeriksaan numerik
        logBlurDifference();

        // Render mengikuti status toggle saat ini
        renderToZeroRealtime(
            state.currentThreshold
        );

    } catch (error) {
        if (requestId !== state.currentRequestId) {
            return;
        }

        state.isServerLoading = false;

        console.error(
            'Gagal memuat gambar:',
            error
        );
    }
}

// ================= BUFFER SELECTION =================

function getActivePixelBuffer() {
    if (!state.rawGrayBuffer) {
        return null;
    }

    const blurAktif =
        elements.threshBlurToggle &&
        elements.threshBlurToggle.checked;

    if (!blurAktif) {
        return state.rawGrayBuffer;
    }

    if (
        !state.blurredGrayBuffer ||
        state.blurredGrayBuffer.length !==
            state.rawGrayBuffer.length
    ) {
        state.blurredGrayBuffer =
            computeGaussianBlur5x5(
                state.rawGrayBuffer,
                state.activeImageWidth,
                state.activeImageHeight
            );
    }

    return state.blurredGrayBuffer;
}

// ================= DEBUG BLUR =================

function logBlurDifference() {
    const raw = state.rawGrayBuffer;
    const blur = state.blurredGrayBuffer;

    if (!raw || !blur) return;

    let different = 0;
    let totalDifference = 0;

    for (let i = 0; i < raw.length; i++) {
        const delta = Math.abs(
            raw[i] - blur[i]
        );

        if (delta > 0) {
            different++;
            totalDifference += delta;
        }
    }

    console.log(
        '[Gaussian Blur] Piksel berbeda:',
        different,
        'dari',
        raw.length
    );

    console.log(
        '[Gaussian Blur] Total selisih intensitas:',
        totalDifference
    );

    if (different === 0) {
        console.warn(
            'Buffer grayscale dan blur identik. ' +
            'Periksa citra atau respons backend.'
        );
    }
}

// ================= TO-ZERO REAL-TIME =================

function renderToZeroRealtime(threshold) {
    const gray = getActivePixelBuffer();

    if (
        !gray ||
        !state.resultImageData ||
        !state.resultCtx
    ) {
        return;
    }

    const output =
        state.resultImageData.data;

    if (output.length !== gray.length * 4) {
        console.error(
            'Ukuran buffer dan Canvas tidak sesuai'
        );
        return;
    }

    let p = 0;

    for (let i = 0; i < gray.length; i++) {
        const value = gray[i];

        // Aturan cv2.THRESH_TOZERO
        const result =
            value > threshold ? value : 0;

        output[p] = result;
        output[p + 1] = result;
        output[p + 2] = result;
        output[p + 3] = 255;

        p += 4;
    }

    state.resultCtx.putImageData(
        state.resultImageData,
        0,
        0
    );

    const blurAktif =
        elements.threshBlurToggle &&
        elements.threshBlurToggle.checked;

    if (elements.threshResultTag) {
        elements.threshResultTag.textContent =
            `After: TOZERO (T=${threshold})` +
            (blurAktif ? ' + Blur' : '');
    }

    if (state.cachedHistogram) {
        renderHistogram(
            state.cachedHistogram,
            threshold
        );
    }
}

// ================= CONTROLS =================

function initThresholdControls() {
    const slider =
        elements.globalThresholdSlider;

    const toggle =
        elements.threshBlurToggle;

    const button =
        elements.btnRunThreshold;

    // Slider real-time
    if (slider) {
        slider.addEventListener('input', event => {
            const threshold =
                Number(event.target.value);

            state.currentThreshold = threshold;

            if (elements.globalThresholdVal) {
                elements.globalThresholdVal.textContent =
                    threshold;
            }

            if (state.pendingAnimFrame !== null) {
                cancelAnimationFrame(
                    state.pendingAnimFrame
                );
            }

            state.pendingAnimFrame =
                requestAnimationFrame(() => {
                    renderToZeroRealtime(
                        state.currentThreshold
                    );

                    state.pendingAnimFrame = null;
                });
        });
    }

    // Gaussian Blur ON/OFF
    if (toggle) {
        toggle.addEventListener('change', () => {
            console.log(
                'Gaussian Blur:',
                toggle.checked ? 'ON' : 'OFF'
            );

            if (state.pendingAnimFrame !== null) {
                cancelAnimationFrame(
                    state.pendingAnimFrame
                );

                state.pendingAnimFrame = null;
            }

            // Pastikan gambar sudah selesai dimuat
            if (!state.rawGrayBuffer) {
                console.warn(
                    'Buffer gambar belum siap'
                );
                return;
            }

            // Siapkan buffer blur bila belum ada
            if (
                toggle.checked &&
                !state.blurredGrayBuffer
            ) {
                state.blurredGrayBuffer =
                    computeGaussianBlur5x5(
                        state.rawGrayBuffer,
                        state.activeImageWidth,
                        state.activeImageHeight
                    );
            }

            logBlurDifference();

            // Render langsung dengan buffer pilihan
            renderToZeroRealtime(
                state.currentThreshold
            );
        });
    }

    // Tombol proses
    if (button) {
        button.addEventListener('click', () => {
            renderToZeroRealtime(
                state.currentThreshold
            );
        });
    }
}

// ================= HISTOGRAM =================

function renderHistogram(
    histogram,
    threshold
) {
    const canvas =
        elements.histogramCanvas;

    if (!canvas || !histogram) return;

    const ctx = canvas.getContext('2d');

    const width = canvas.width;
    const height = canvas.height;

    ctx.clearRect(
        0, 0, width, height
    );

    ctx.fillStyle = '#FFFFFF';
    ctx.fillRect(
        0, 0, width, height
    );

    const maxValue = Math.max(
        ...histogram,
        1
    );

    const barWidth = width / 256;

    ctx.fillStyle = '#5865F2';

    for (let i = 0; i < 256; i++) {
        const barHeight =
            histogram[i] / maxValue *
            (height - 18);

        ctx.fillRect(
            i * barWidth,
            height - barHeight,
            Math.max(1.2, barWidth),
            barHeight
        );
    }

    // Garis merah penanda T
    const lineX =
        threshold / 255 * width;

    ctx.strokeStyle = '#EF4444';
    ctx.lineWidth = 2.5;

    ctx.beginPath();
    ctx.moveTo(lineX, 0);
    ctx.lineTo(lineX, height);
    ctx.stroke();

    // Label T
    ctx.fillStyle = '#000000';
    ctx.font =
        'bold 11px JetBrains Mono, monospace';

    ctx.textAlign = 'center';

    const labelX = Math.min(
        Math.max(lineX, 24),
        width - 24
    );

    ctx.fillText(
        `T=${threshold}`,
        labelX,
        12
    );

    if (elements.histLegendText) {
        elements.histLegendText.textContent =
            `Nilai Ambang Terpilih (T) = ${threshold}`;
    }
}
