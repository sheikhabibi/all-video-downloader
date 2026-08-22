document.addEventListener('DOMContentLoaded', () => {
    const urlInput = document.getElementById('url-input');
    const fetchBtn = document.getElementById('fetch-btn');
    const loading = document.getElementById('loading');
    const videoInfo = document.getElementById('video-info');
    const videoThumb = document.getElementById('video-thumb');
    const videoTitle = document.getElementById('video-title');
    const formatSelect = document.getElementById('format-select');
    const downloadBtn = document.getElementById('download-btn');
    const progressContainer = document.getElementById('progress-container');
    const progressBarFill = document.getElementById('progress-bar-fill');
    const progressText = document.getElementById('progress-text');
    const saveFileBtn = document.getElementById('save-file-btn');
    const errorMessage = document.getElementById('error-message');

    let currentUrl = '';

    const showError = (msg) => {
        errorMessage.textContent = msg;
        errorMessage.classList.remove('hidden');
    };

    const hideError = () => {
        errorMessage.classList.add('hidden');
    };

    fetchBtn.addEventListener('click', async () => {
        const url = urlInput.value.trim();
        if (!url) {
            showError("Please enter a valid video URL.");
            return;
        }

        currentUrl = url;
        hideError();
        videoInfo.classList.add('hidden');
        progressContainer.classList.add('hidden');
        loading.classList.remove('hidden');

        try {
            const res = await fetch('/api/info', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });

            const data = await res.json();
            
            if (!res.ok) throw new Error(data.error || 'Failed to fetch video info');

            // Populate UI
            videoTitle.textContent = data.title;
            if (data.thumbnail) {
                videoThumb.src = data.thumbnail;
                videoThumb.classList.remove('hidden');
            } else {
                videoThumb.classList.add('hidden');
            }

            // Populate Select
            formatSelect.innerHTML = '';
            data.options.forEach(opt => {
                const el = document.createElement('option');
                el.value = opt.id;
                el.textContent = opt.label;
                el.dataset.isAudio = opt.is_audio;
                formatSelect.appendChild(el);
            });

            loading.classList.add('hidden');
            videoInfo.classList.remove('hidden');
        } catch (err) {
            loading.classList.add('hidden');
            showError(err.message);
        }
    });

    downloadBtn.addEventListener('click', async () => {
        const selectedOption = formatSelect.options[formatSelect.selectedIndex];
        const formatId = selectedOption.value;
        const isAudio = selectedOption.dataset.isAudio === 'true';
        
        hideError();
        videoInfo.classList.add('hidden');
        progressContainer.classList.remove('hidden');
        saveFileBtn.classList.add('hidden');
        progressBarFill.style.width = '0%';
        progressText.textContent = 'Starting download...';

        try {
            const res = await fetch('/api/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: currentUrl, format_id: formatId, is_audio: isAudio })
            });

            const data = await res.json();
            if (!res.ok) throw new Error(data.error || 'Failed to start download');

            pollStatus(data.task_id);
        } catch (err) {
            progressContainer.classList.add('hidden');
            showError(err.message);
        }
    });

    const pollStatus = async (taskId) => {
        try {
            const res = await fetch(`/api/status/${taskId}`);
            const data = await res.json();

            if (!res.ok) throw new Error(data.error || 'Error fetching status');

            if (data.status === 'downloading') {
                progressBarFill.style.width = data.progress;
                progressText.textContent = `Downloading... ${data.progress}`;
                setTimeout(() => pollStatus(taskId), 1000);
            } else if (data.status === 'completed') {
                progressBarFill.style.width = '100%';
                progressText.textContent = 'Download Complete! Starting file save...';
                
                // Automatically trigger the download dialog
                window.location.href = `/api/file/${taskId}`;
                
                // Hide progress and return to info state after a few seconds
                setTimeout(() => {
                    progressContainer.classList.add('hidden');
                    videoInfo.classList.remove('hidden');
                }, 3000);
            } else if (data.status === 'error') {
                throw new Error(data.error || 'An error occurred during download');
            }
        } catch (err) {
            progressText.textContent = 'Download Failed';
            progressBarFill.style.backgroundColor = 'var(--danger)';
            showError(err.message);
        }
    };
});
