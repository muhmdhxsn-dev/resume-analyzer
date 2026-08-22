document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('dropZone');
    const resumeInput = document.getElementById('resumeInput');
    const dropZonePrompt = document.getElementById('dropZonePrompt');
    const filePreview = document.getElementById('filePreview');
    const fileNameDisplay = document.getElementById('fileName');
    const fileSizeDisplay = document.getElementById('fileSize');
    const fileIconDisplay = document.getElementById('fileIcon');
    const btnRemoveFile = document.getElementById('btnRemoveFile');
    const btnSubmit = document.getElementById('btnSubmit');
    const uploadForm = document.getElementById('uploadForm');
    const uploadCard = document.getElementById('uploadCard');
    const loadingCard = document.getElementById('loadingCard');
    const analyzeCtaBtn = document.getElementById('analyzeCtaBtn');

    const ALLOWED_EXTENSIONS = ['pdf', 'docx'];
    const MAX_FILE_SIZE_BYTES = 16 * 1024 * 1024; // 16 MB

    // Smooth scroll from Hero CTA to upload card
    if (analyzeCtaBtn && uploadCard) {
        analyzeCtaBtn.addEventListener('click', (e) => {
            e.preventDefault();
            uploadCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
        });
    }

    // Format bytes into human readable string
    function formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }

    // Handle file selection logic
    function handleFileSelection(file) {
        if (!file) {
            resetFileSelection();
            return;
        }

        const ext = file.name.split('.').pop().toLowerCase();
        
        if (!ALLOWED_EXTENSIONS.includes(ext)) {
            alert(`Invalid file extension '.${ext}'. Only PDF and DOCX files are allowed.`);
            resetFileSelection();
            return;
        }

        if (file.size > MAX_FILE_SIZE_BYTES) {
            alert(`File size exceeds 16MB limit (${formatBytes(file.size)}).`);
            resetFileSelection();
            return;
        }

        // Display file preview card
        if (fileNameDisplay) fileNameDisplay.textContent = file.name;
        if (fileSizeDisplay) fileSizeDisplay.textContent = formatBytes(file.size);
        if (fileIconDisplay) fileIconDisplay.textContent = ext === 'pdf' ? '📕' : '📘';

        if (dropZonePrompt) dropZonePrompt.classList.add('hidden');
        if (filePreview) filePreview.classList.remove('hidden');
        if (btnSubmit) btnSubmit.disabled = false;
    }

    // Reset file input & UI state
    function resetFileSelection() {
        if (resumeInput) resumeInput.value = '';
        if (dropZonePrompt) dropZonePrompt.classList.remove('hidden');
        if (filePreview) filePreview.classList.add('hidden');
        if (btnSubmit) btnSubmit.disabled = true;
    }

    // Drag & Drop event handlers
    if (dropZone) {
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.remove('dragover');
            }, false);
        });

        dropZone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files && files.length > 0) {
                if (resumeInput) resumeInput.files = files;
                handleFileSelection(files[0]);
            }
        });
    }

    // File input change listener
    if (resumeInput) {
        resumeInput.addEventListener('change', (e) => {
            if (e.target.files && e.target.files.length > 0) {
                handleFileSelection(e.target.files[0]);
            } else {
                resetFileSelection();
            }
        });
    }

    // Remove file button handler
    if (btnRemoveFile) {
        btnRemoveFile.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            resetFileSelection();
        });
    }

    // Form submission interactive loading state
    if (uploadForm && uploadCard && loadingCard) {
        uploadForm.addEventListener('submit', () => {
            uploadCard.classList.add('hidden');
            loadingCard.classList.remove('hidden');

            const steps = [
                document.getElementById('step1'),
                document.getElementById('step2'),
                document.getElementById('step3'),
                document.getElementById('step4')
            ];

            let stepIdx = 0;
            const interval = setInterval(() => {
                if (stepIdx < steps.length) {
                    const step = steps[stepIdx];
                    if (step) {
                        step.classList.remove('active');
                        step.classList.add('completed');
                        step.innerHTML = step.innerHTML.replace('●', '✓');
                    }
                    stepIdx++;
                    if (stepIdx < steps.length && steps[stepIdx]) {
                        steps[stepIdx].classList.add('active');
                        steps[stepIdx].innerHTML = steps[stepIdx].innerHTML.replace('○', '●');
                    }
                } else {
                    clearInterval(interval);
                }
            }, 600);
        });
    }

    // Animate Category Progress Bars on Result Page
    const catFills = document.querySelectorAll('.cat-bar-fill');
    if (catFills.length > 0) {
        catFills.forEach(fill => {
            const targetWidth = fill.style.width;
            fill.style.width = '0%';
            setTimeout(() => {
                fill.style.width = targetWidth;
            }, 150);
        });
    }
});
