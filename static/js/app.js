document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const urlInput = document.getElementById('url-input');
    const fetchBtn = document.getElementById('fetch-btn');
    const fetchBtnText = document.getElementById('fetch-btn-text');
    const fetchSpinner = document.getElementById('fetch-spinner');

    const playlistBanner = document.getElementById('playlist-banner');
    const bannerThumb = document.getElementById('banner-thumb');
    const bannerTitle = document.getElementById('banner-title');
    const bannerUploader = document.getElementById('banner-uploader');
    const bannerCount = document.getElementById('banner-count');

    const toolbarCard = document.getElementById('toolbar-card');
    const formatSelect = document.getElementById('format-select');
    const qualitySelect = document.getElementById('quality-select');
    const outputFolderInput = document.getElementById('output-folder');
    const openFolderBtn = document.getElementById('open-folder-btn');
    const selectAllCheckbox = document.getElementById('select-all-checkbox');
    const startDownloadBtn = document.getElementById('start-download-btn');

    const videosContainer = document.getElementById('videos-container');

    const overallCard = document.getElementById('overall-progress-card');
    const overallFill = document.getElementById('overall-progress-fill');
    const overallText = document.getElementById('overall-text');
    const cancelJobBtn = document.getElementById('cancel-job-btn');

    // Cookie Modal Elements
    const cookieGuideBtn = document.getElementById('cookie-guide-btn');
    const cookieStatusDot = document.getElementById('cookie-status-dot');
    const cookieStatusText = document.getElementById('cookie-status-text');
    const cookieModal = document.getElementById('cookie-modal');
    const closeCookieModalBtn = document.getElementById('close-cookie-modal');
    const cookieTextarea = document.getElementById('cookie-textarea');
    const saveCookiesBtn = document.getElementById('save-cookies-btn');

    let playlistData = null;
    let activeJobId = null;
    let pollInterval = null;

    let isCloudDeployment = false;
    let defaultOutputDir = '';

    function getBase64Cookie() {
        const c = localStorage.getItem('youtube_cookies') || '';
        if (!c) return '';
        try {
            return btoa(unescape(encodeURIComponent(c)));
        } catch (e) {
            return '';
        }
    }

    function getCookieHeaders() {
        const b64 = getBase64Cookie();
        return b64 ? { 'X-YouTube-Cookies': b64 } : {};
    }

    function getCookieParam() {
        const c = localStorage.getItem('youtube_cookies') || '';
        return c ? `&cookies=${encodeURIComponent(c)}` : '';
    }

    // Check Cookie Status
    async function checkCookieStatus() {
        const storedCookies = localStorage.getItem('youtube_cookies') || '';
        if (cookieTextarea && storedCookies && !cookieTextarea.value) {
            cookieTextarea.value = storedCookies;
        }

        if (storedCookies) {
            if (cookieStatusDot) cookieStatusDot.className = 'status-dot dot-green';
            if (cookieStatusText) cookieStatusText.textContent = '🍪 Cookies Active';
            return;
        }

        try {
            const res = await fetch('/api/cookies/status');
            const data = await res.json();
            if (data.has_cookies) {
                if (cookieStatusDot) cookieStatusDot.className = 'status-dot dot-green';
                if (cookieStatusText) cookieStatusText.textContent = '🍪 Cookies Active';
            } else {
                if (cookieStatusDot) cookieStatusDot.className = 'status-dot dot-amber';
                if (cookieStatusText) cookieStatusText.textContent = '🍪 Cloud Cookies Setup';
            }
        } catch (e) {
            console.error('Failed to check cookie status', e);
        }
    }
    checkCookieStatus();

    // Cookie Modal Listeners
    if (cookieGuideBtn) {
        cookieGuideBtn.addEventListener('click', () => {
            const storedCookies = localStorage.getItem('youtube_cookies') || '';
            if (cookieTextarea && storedCookies) cookieTextarea.value = storedCookies;
            if (cookieModal) cookieModal.style.display = 'flex';
        });
    }

    if (closeCookieModalBtn) {
        closeCookieModalBtn.addEventListener('click', () => {
            if (cookieModal) cookieModal.style.display = 'none';
        });
    }

    if (cookieModal) {
        cookieModal.addEventListener('click', (e) => {
            if (e.target === cookieModal) cookieModal.style.display = 'none';
        });
    }

    if (saveCookiesBtn) {
        saveCookiesBtn.addEventListener('click', async () => {
            const val = cookieTextarea ? cookieTextarea.value.trim() : '';
            if (!val) return alert('Please paste cookie file contents.');
            saveCookiesBtn.disabled = true;
            saveCookiesBtn.textContent = 'Saving...';
            try {
                localStorage.setItem('youtube_cookies', val);
                checkCookieStatus();

                const res = await fetch('/api/cookies/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', ...getCookieHeaders() },
                    body: JSON.stringify({ cookies: val })
                });
                await res.json();
                alert('Cookies saved successfully! Cloud bot check is now bypassed.');
                if (cookieModal) cookieModal.style.display = 'none';
            } catch (err) {
                alert('Cookies stored in browser session successfully!');
                if (cookieModal) cookieModal.style.display = 'none';
            } finally {
                saveCookiesBtn.disabled = false;
                saveCookiesBtn.textContent = 'Save Cookies for Session';
            }
        });
    }

    // Load default output folder
    fetch('/api/default-folder')
        .then(res => res.json())
        .then(data => {
            if (data.is_cloud) {
                isCloudDeployment = true;
                if (outputFolderInput) {
                    outputFolderInput.value = 'Browser Downloads Folder';
                    outputFolderInput.disabled = true;
                }
                if (openFolderBtn) openFolderBtn.style.display = 'none';
            } else if (data.path) {
                defaultOutputDir = data.path;
                if (outputFolderInput) outputFolderInput.value = data.path;
            }
        })
        .catch(console.error);

    // Fetch Playlist Info
    fetchBtn.addEventListener('click', handleFetchPlaylist);
    urlInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') handleFetchPlaylist();
    });

    async function handleFetchPlaylist() {
        const url = urlInput.value.trim();
        if (!url) return alert('Please enter a valid playlist or video URL');

        setFetchLoading(true);

        const storedCookies = localStorage.getItem('youtube_cookies') || '';

        try {
            const res = await fetch('/api/playlist-info', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    ...getCookieHeaders()
                },
                body: JSON.stringify({ url, cookies: storedCookies })
            });

            const contentType = res.headers.get('content-type') || '';
            if (!contentType.includes('application/json')) {
                throw new Error('Python server is not running on this port. Please open http://localhost:5050 in your browser.');
            }

            const json = await res.json();
            if (!res.ok || json.error) {
                if (json.error && json.error.includes('cookies')) {
                    if (cookieModal) cookieModal.style.display = 'flex';
                }
                throw new Error(json.error || 'Failed to extract playlist info');
            }

            playlistData = json.data;
            renderPlaylistBanner(playlistData);
            renderVideoList(playlistData.items);
            toolbarCard.classList.add('active');
        } catch (err) {
            alert(`Error: ${err.message}`);
        } finally {
            setFetchLoading(false);
        }
    }

    function setFetchLoading(isLoading) {
        fetchBtn.disabled = isLoading;
        if (isLoading) {
            fetchBtnText.textContent = 'Fetching...';
            fetchSpinner.style.display = 'block';
        } else {
            fetchBtnText.textContent = 'Fetch Media';
            fetchSpinner.style.display = 'none';
        }
    }

    function renderPlaylistBanner(data) {
        bannerThumb.src = data.thumbnail || 'https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=400';
        bannerTitle.textContent = data.title;
        bannerUploader.textContent = `By ${data.uploader}`;
        bannerCount.textContent = `${data.total_items} Item${data.total_items > 1 ? 's' : ''}`;
        playlistBanner.classList.add('active');
    }

    function renderVideoList(items) {
        videosContainer.innerHTML = '';
        selectAllCheckbox.checked = true;

        items.forEach((item, index) => {
            const durationFormatted = formatDuration(item.duration);
            const card = document.createElement('div');
            card.className = 'video-card';
            card.id = `video-card-${item.id}`;
            card.innerHTML = `
                <input type="checkbox" class="checkbox-custom item-checkbox" data-id="${item.id}" checked>
                <div class="video-thumb-wrapper">
                    <img src="${item.thumbnail}" class="video-thumb" alt="thumbnail" loading="lazy" />
                    <span class="video-duration">${durationFormatted}</span>
                </div>
                <div class="video-info">
                    <div class="video-title" title="${item.title}">${index + 1}. ${item.title}</div>
                    <div class="video-uploader">${item.uploader}</div>
                </div>
                <div class="item-progress-section">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="badge badge-queued" id="badge-${item.id}">Ready</span>
                        <button type="button" class="btn-primary direct-dl-btn" data-id="${item.id}" data-url="${encodeURIComponent(item.url)}" style="padding: 0.35rem 0.85rem; font-size: 0.8rem; display: inline-flex; align-items: center; gap: 0.35rem;">
                            <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                            <span>Download</span>
                        </button>
                    </div>
                    <div class="progress-bar-bg" style="margin-top: 0.5rem;">
                        <div class="progress-bar-fill" id="fill-${item.id}"></div>
                    </div>
                    <div class="progress-meta">
                        <span id="percent-${item.id}">0%</span>
                        <span id="speed-${item.id}">-</span>
                        <span id="eta-${item.id}">-</span>
                    </div>
                </div>
            `;
            videosContainer.appendChild(card);
        });

        // Checkbox events
        document.querySelectorAll('.item-checkbox').forEach(cb => {
            cb.addEventListener('change', updateSelectAllState);
        });

        // Individual item download button handlers
        document.querySelectorAll('.direct-dl-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.preventDefault();
                const itemId = btn.getAttribute('data-id');
                const encodedUrl = btn.getAttribute('data-url');
                const item = playlistData ? playlistData.items.find(i => i.id === itemId) : null;
                
                if (!item) return;

                if (isCloudDeployment) {
                    // In cloud mode, stream converted file directly as browser attachment
                    const streamUrl = `/api/download/stream?url=${encodedUrl}&format=${formatSelect.value}&quality=${qualitySelect.value}${getCookieParam()}`;
                    window.location.href = streamUrl;
                    return;
                }

                // In local mode, execute high-speed local download job for this single item
                const originalHtml = btn.innerHTML;
                btn.disabled = true;
                btn.innerHTML = `<span>Starting...</span>`;

                try {
                    const downloadPayload = {
                        items: [item],
                        format: formatSelect.value,
                        quality: qualitySelect.value,
                        output_dir: outputFolderInput ? outputFolderInput.value.trim() : defaultOutputDir
                    };

                    const res = await fetch('/api/download/start', {
                        method: 'POST',
                        headers: { 
                            'Content-Type': 'application/json',
                            ...getCookieHeaders()
                        },
                        body: JSON.stringify(downloadPayload)
                    });

                    const json = await res.json();
                    if (!res.ok || json.error) throw new Error(json.error || 'Failed to start download');

                    activeJobId = json.job_id;
                    overallCard.classList.add('active');
                    startPollingProgress();
                } catch (err) {
                    alert(`Download error: ${err.message}`);
                    btn.disabled = false;
                    btn.innerHTML = originalHtml;
                }
            });
        });
    }

    // Select all handler
    selectAllCheckbox.addEventListener('change', (e) => {
        const checked = e.target.checked;
        document.querySelectorAll('.item-checkbox').forEach(cb => cb.checked = checked);
    });

    function updateSelectAllState() {
        const checkboxes = Array.from(document.querySelectorAll('.item-checkbox'));
        selectAllCheckbox.checked = checkboxes.every(cb => cb.checked);
    }

    // Open Folder
    if (openFolderBtn) {
        openFolderBtn.addEventListener('click', () => {
            const path = outputFolderInput ? outputFolderInput.value.trim() : defaultOutputDir;
            fetch('/api/open-folder', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path })
            }).then(r => r.json()).then(data => {
                if (data.error) alert('Could not open folder: ' + data.error);
            }).catch(console.error);
        });
    }

    // Format selection dropdown update
    formatSelect.addEventListener('change', () => {
        if (formatSelect.value === 'audio') {
            qualitySelect.innerHTML = `
                <option value="best">320 kbps (High Quality)</option>
                <option value="192">192 kbps (Standard)</option>
            `;
        } else {
            qualitySelect.innerHTML = `
                <option value="best">Best Available</option>
                <option value="1080p">1080p Full HD</option>
                <option value="720p">720p HD</option>
                <option value="480p">480p SD</option>
                <option value="360p">360p Low</option>
            `;
        }
    });

    // Start Download (Batch)
    startDownloadBtn.addEventListener('click', async () => {
        if (!playlistData || !playlistData.items) return;

        const selectedIds = Array.from(document.querySelectorAll('.item-checkbox:checked')).map(cb => cb.getAttribute('data-id'));
        if (selectedIds.length === 0) return alert('Please select at least one item to download.');

        const selectedItems = playlistData.items.filter(item => selectedIds.includes(item.id));

        if (isCloudDeployment) {
            overallCard.classList.add('active');
            overallFill.style.width = '100%';
            overallText.textContent = `Opening browser download for ${selectedItems.length} item(s)...`;

            selectedItems.forEach((item, idx) => {
                setTimeout(() => {
                    const streamUrl = `/api/download/stream?url=${encodeURIComponent(item.url)}&format=${formatSelect.value}&quality=${qualitySelect.value}${getCookieParam()}`;
                    const a = document.createElement('a');
                    a.href = streamUrl;
                    a.target = '_blank';
                    document.body.appendChild(a);
                    a.click();
                    setTimeout(() => document.body.removeChild(a), 1000);
                }, idx * 1000);
            });

            setTimeout(() => {
                overallText.textContent = `Downloads initiated! Check your browser downloads.`;
                setTimeout(() => overallCard.classList.remove('active'), 5000);
            }, 2500);
            return;
        }

        const downloadPayload = {
            items: selectedItems,
            format: formatSelect.value,
            quality: qualitySelect.value,
            output_dir: outputFolderInput ? outputFolderInput.value.trim() : defaultOutputDir
        };

        try {
            startDownloadBtn.disabled = true;
            startDownloadBtn.innerHTML = `Downloading...`;

            const res = await fetch('/api/download/start', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    ...getCookieHeaders()
                },
                body: JSON.stringify(downloadPayload)
            });

            const json = await res.json();
            if (!res.ok || json.error) throw new Error(json.error || 'Failed to start download');

            activeJobId = json.job_id;
            overallCard.classList.add('active');
            startPollingProgress();
        } catch (err) {
            alert(`Download Error: ${err.message}`);
            startDownloadBtn.disabled = false;
            startDownloadBtn.innerHTML = `Start Download`;
        }
    });

    // Poll Download Progress
    function startPollingProgress() {
        if (pollInterval) clearInterval(pollInterval);

        pollInterval = setInterval(async () => {
            if (!activeJobId) return;

            try {
                const res = await fetch(`/api/download/status/${activeJobId}`);
                const json = await res.json();

                if (!json.success || !json.job) return;

                const job = json.job;
                updateProgressUI(job);

                if (job.status === 'completed' || job.status === 'cancelled' || job.status === 'error') {
                    clearInterval(pollInterval);
                    pollInterval = null;
                    startDownloadBtn.disabled = false;
                    startDownloadBtn.innerHTML = `
                        <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                        Start Download
                    `;
                    
                    if (job.status === 'completed') {
                        overallText.textContent = `Completed ${job.completed_items} of ${job.total_items} items! Saved to folder.`;
                        setTimeout(() => overallCard.classList.remove('active'), 5000);
                    }
                }
            } catch (err) {
                console.error('Polling error:', err);
            }
        }, 500);
    }

    function updateProgressUI(job) {
        // Overall bar
        const total = job.total_items;
        const finished = job.completed_items;
        const overallPercent = total > 0 ? Math.round((finished / total) * 100) : 0;

        overallFill.style.width = `${overallPercent}%`;
        overallText.textContent = `Downloaded ${finished} / ${total} items (${overallPercent}%)`;

        // Update items
        Object.values(job.items_status).forEach(item => {
            const fill = document.getElementById(`fill-${item.id}`);
            const percent = document.getElementById(`percent-${item.id}`);
            const badge = document.getElementById(`badge-${item.id}`);
            const speed = document.getElementById(`speed-${item.id}`);
            const eta = document.getElementById(`eta-${item.id}`);
            const card = document.getElementById(`video-card-${item.id}`);
            const btn = card ? card.querySelector('.direct-dl-btn') : null;

            if (fill) fill.style.width = `${item.progress}%`;
            if (percent) percent.textContent = `${item.progress}%`;
            if (speed) speed.textContent = item.speed || '-';
            if (eta) eta.textContent = item.eta ? `${item.eta}` : '-';

            if (badge) {
                badge.className = `badge badge-${item.status}`;
                badge.textContent = item.status.toUpperCase();
            }

            if (btn) {
                if (item.status === 'finished') {
                    btn.disabled = false;
                    btn.style.background = 'rgba(16, 185, 129, 0.2)';
                    btn.style.borderColor = 'rgba(16, 185, 129, 0.4)';
                    btn.innerHTML = `<span>Saved</span>`;
                } else if (item.status === 'downloading' || item.status === 'converting') {
                    btn.disabled = true;
                    btn.innerHTML = `<span>${item.status === 'converting' ? 'Converting...' : 'Downloading...'}</span>`;
                }
            }
        });
    }

    // Cancel Download
    cancelJobBtn.addEventListener('click', async () => {
        if (!activeJobId) return;

        fetch(`/api/download/cancel/${activeJobId}`, { method: 'POST' });
        clearInterval(pollInterval);
        overallCard.classList.remove('active');
        startDownloadBtn.disabled = false;
        startDownloadBtn.innerHTML = `
            <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
            Start Download
        `;
    });

    // Helper
    function formatDuration(seconds) {
        if (!seconds) return '--:--';
        const m = Math.floor(seconds / 60);
        const s = Math.floor(seconds % 60);
        const h = Math.floor(m / 60);
        const rm = m % 60;

        if (h > 0) {
            return `${h}:${rm < 10 ? '0' : ''}${rm}:${s < 10 ? '0' : ''}${s}`;
        }
        return `${m}:${s < 10 ? '0' : ''}${s}`;
    }
});
