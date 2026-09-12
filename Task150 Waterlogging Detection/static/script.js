/**
 * HydroVision AI - Client Dashboard Logic (script.js)
 * ----------------------------------------------------
 * Handles drag-and-drop file uploading (Image & Video), asynchronous API requests,
 * dynamic media preview switching, real-time alert feed population,
 * telemetry statistics update, and user toasts.
 */

document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const fileInput = document.getElementById('video-file-input');
    const btnUpload = document.getElementById('btn-upload');
    const btnBrowse = document.getElementById('btn-browse');
    const btnProcess = document.getElementById('btn-process');
    const btnDownload = document.getElementById('btn-download');
    const btnReset = document.getElementById('btn-reset');

    const dropzone = document.getElementById('dropzone');
    const videoWrapper = document.getElementById('video-wrapper');
    const inputVideoPlayer = document.getElementById('input-video-player');
    const outputVideoPlayer = document.getElementById('output-video-player');
    const inputImagePlayer = document.getElementById('input-image-player');
    const outputImagePlayer = document.getElementById('output-image-player');

    const processingOverlay = document.getElementById('processing-overlay');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');

    const tabUpload = document.getElementById('tab-upload');
    const tabOutput = document.getElementById('tab-output');
    const filenameTag = document.getElementById('current-filename-tag');

    const alertsContainer = document.getElementById('alerts-container');
    const alertsEmptyState = document.getElementById('alerts-empty-state');
    const alertCountBadge = document.getElementById('alert-count');

    // Stat Cards
    const valFloodStatus = document.getElementById('val-flood-status');
    const subFloodStatus = document.getElementById('sub-flood-status');
    const valVehicles = document.getElementById('val-vehicles');
    const valPersons = document.getElementById('val-persons');
    const valTime = document.getElementById('val-time');
    const subFps = document.getElementById('sub-fps');

    // --- State Variables ---
    let currentUploadedFile = null;
    let currentUploadedFilename = null;
    let currentProcessedFilename = null;
    let currentDownloadUrl = null;
    let isCurrentImage = false;
    let isProcessing = false;

    const imageExtensions = ['jpg', 'jpeg', 'png'];
    const videoExtensions = ['mp4', 'avi', 'mov', 'mkv', 'webm'];
    const validExtensions = [...imageExtensions, ...videoExtensions];

    // --- Toast Notification Helper ---
    function showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        let icon = 'ℹ️';
        if (type === 'success') icon = '✅';
        if (type === 'error') icon = '⚠️';

        toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(20px)';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }

    // --- File Upload Logic ---
    function triggerFileInput() {
        if (isProcessing) return;
        fileInput.click();
    }

    btnUpload.addEventListener('click', triggerFileInput);
    btnBrowse.addEventListener('click', triggerFileInput);

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });

    // Drag and Drop Events
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('drag-over');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('drag-over');
        }, false);
    });

    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleFileUpload(files[0]);
        }
    });

    function handleFileUpload(file) {
        const ext = file.name.split('.').pop().toLowerCase();
        if (!validExtensions.includes(ext)) {
            showToast(`Unsupported format (.${ext}). Upload MP4, AVI, MOV, MKV, WebM or JPG, PNG.`, 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('video', file);

        showToast(`Uploading ${imageExtensions.includes(ext) ? 'image' : 'video'} to server...`, 'info');

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                currentUploadedFile = file;
                currentUploadedFilename = data.filename;
                currentProcessedFilename = null;
                currentDownloadUrl = null;
                isCurrentImage = data.is_image || imageExtensions.includes(ext);

                filenameTag.textContent = file.name;

                // Hide all preview elements initially
                inputVideoPlayer.classList.add('hidden');
                outputVideoPlayer.classList.add('hidden');
                inputImagePlayer.classList.add('hidden');
                outputImagePlayer.classList.add('hidden');

                if (isCurrentImage) {
                    inputImagePlayer.src = data.file_url || data.video_url;
                    inputImagePlayer.classList.remove('hidden');
                } else {
                    inputVideoPlayer.src = data.file_url || data.video_url;
                    inputVideoPlayer.classList.remove('hidden');
                }
                
                dropzone.classList.add('hidden');
                videoWrapper.classList.remove('hidden');

                btnProcess.disabled = false;
                btnDownload.disabled = true;

                tabUpload.classList.add('active');
                tabOutput.classList.remove('active');

                // Reset previous alerts & telemetry immediately on new file upload (Requirement 3)
                alertsContainer.innerHTML = '';
                alertsContainer.appendChild(alertsEmptyState);
                alertsEmptyState.classList.remove('hidden');
                alertCountBadge.textContent = '0';

                valFloodStatus.textContent = 'Ready for Detection';
                valFloodStatus.style.color = 'var(--text-primary)';
                subFloodStatus.textContent = 'Coverage: 0%';
                valVehicles.textContent = '0';
                valPersons.textContent = '0';
                valTime.textContent = '0.0s';
                subFps.textContent = 'Speed: 0 FPS';

                showToast(`${isCurrentImage ? 'Image' : 'Video'} uploaded successfully! Ready for detection.`, 'success');
            } else {
                showToast(data.error || 'Upload failed.', 'error');
            }
        })
        .catch(err => {
            console.error(err);
            showToast('Error uploading file to server.', 'error');
        });
    }

    // --- Detection Processing Logic (Images & Videos) ---
    btnProcess.addEventListener('click', () => {
        if (!currentUploadedFilename || isProcessing) return;

        isProcessing = true;
        btnProcess.disabled = true;
        btnUpload.disabled = true;
        btnReset.disabled = true;

        processingOverlay.classList.remove('hidden');
        progressBar.style.width = '15%';
        progressText.textContent = `15% - Initializing YOLO11 ${isCurrentImage ? 'Image' : 'Video'} Engine...`;

        let progressVal = 15;
        const progressInterval = setInterval(() => {
            if (progressVal < 90) {
                progressVal += isCurrentImage ? 20 : Math.floor(Math.random() * 8) + 3;
                if (progressVal > 90) progressVal = 90;
                progressBar.style.width = `${progressVal}%`;
                progressText.textContent = `${progressVal}% - Running detection pipeline...`;
            }
        }, isCurrentImage ? 200 : 500);

        fetch('/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename: currentUploadedFilename })
        })
        .then(res => res.json())
        .then(data => {
            clearInterval(progressInterval);
            progressBar.style.width = '100%';
            progressText.textContent = '100% - Detection Completed!';

            setTimeout(() => {
                processingOverlay.classList.add('hidden');
                isProcessing = false;
                btnUpload.disabled = false;
                btnReset.disabled = false;

                if (data.success) {
                    currentProcessedFilename = data.output_filename;
                    currentDownloadUrl = data.download_url;
                    isCurrentImage = data.is_image || isCurrentImage;

                    // Hide input previews
                    inputVideoPlayer.classList.add('hidden');
                    inputImagePlayer.classList.add('hidden');
                    outputVideoPlayer.classList.add('hidden');
                    outputImagePlayer.classList.add('hidden');

                    if (isCurrentImage) {
                        outputImagePlayer.src = data.output_file_url || data.output_video_url;
                        outputImagePlayer.classList.remove('hidden');
                    } else {
                        outputVideoPlayer.src = data.output_file_url || data.output_video_url;
                        outputVideoPlayer.load();
                        outputVideoPlayer.classList.remove('hidden');
                    }

                    tabUpload.classList.remove('active');
                    tabOutput.classList.add('active');

                    btnDownload.disabled = false;
                    updateStatistics(data.stats);
                    renderAlerts(data.alerts);

                    showToast(`${isCurrentImage ? 'Image' : 'Video'} detection completed successfully!`, 'success');
                } else {
                    showToast(data.error || 'Processing failed.', 'error');
                    btnProcess.disabled = false;
                }
            }, 400);
        })
        .catch(err => {
            clearInterval(progressInterval);
            processingOverlay.classList.add('hidden');
            isProcessing = false;
            btnProcess.disabled = false;
            btnUpload.disabled = false;
            btnReset.disabled = false;
            console.error(err);
            showToast('Server error while processing detection.', 'error');
        });
    });

    outputVideoPlayer.addEventListener('error', (e) => {
        if (!isCurrentImage) {
            console.error('Output video element error:', outputVideoPlayer.error);
            showToast('Playback error: Unable to play processed video in browser.', 'error');
        }
    });

    // --- Tab Switching Logic ---
    tabUpload.addEventListener('click', () => {
        if (!currentUploadedFilename) return;
        tabUpload.classList.add('active');
        tabOutput.classList.remove('active');

        outputVideoPlayer.classList.add('hidden');
        outputImagePlayer.classList.add('hidden');

        if (isCurrentImage) {
            inputImagePlayer.classList.remove('hidden');
        } else {
            inputVideoPlayer.classList.remove('hidden');
        }
    });

    tabOutput.addEventListener('click', () => {
        if (!currentProcessedFilename) return;
        tabOutput.classList.add('active');
        tabUpload.classList.remove('active');

        inputVideoPlayer.classList.add('hidden');
        inputImagePlayer.classList.add('hidden');

        if (isCurrentImage) {
            outputImagePlayer.classList.remove('hidden');
        } else {
            outputVideoPlayer.classList.remove('hidden');
            outputVideoPlayer.load();
        }
    });

    // --- Download Output Media ---
    btnDownload.addEventListener('click', () => {
        if (currentDownloadUrl) {
            window.location.href = currentDownloadUrl;
        } else if (currentProcessedFilename) {
            window.location.href = `/download/${currentProcessedFilename}`;
        }
    });

    // --- Reset Dashboard ---
    btnReset.addEventListener('click', () => {
        if (isProcessing) return;

        fetch('/reset', { method: 'POST' })
            .then(res => res.json())
            .then(() => {
                currentUploadedFile = null;
                currentUploadedFilename = null;
                currentProcessedFilename = null;
                currentDownloadUrl = null;
                isCurrentImage = false;

                // Reset UI
                filenameTag.textContent = 'No media loaded';
                inputVideoPlayer.pause();
                outputVideoPlayer.pause();
                inputVideoPlayer.src = '';
                outputVideoPlayer.src = '';
                inputImagePlayer.src = '';
                outputImagePlayer.src = '';

                inputVideoPlayer.classList.add('hidden');
                outputVideoPlayer.classList.add('hidden');
                inputImagePlayer.classList.add('hidden');
                outputImagePlayer.classList.add('hidden');

                videoWrapper.classList.add('hidden');
                dropzone.classList.remove('hidden');

                btnProcess.disabled = true;
                btnDownload.disabled = true;

                // Reset Stat Cards
                valFloodStatus.textContent = 'Awaiting Media';
                valFloodStatus.style.color = 'var(--text-primary)';
                subFloodStatus.textContent = 'Coverage: 0%';
                valVehicles.textContent = '0';
                valPersons.textContent = '0';
                valTime.textContent = '0.0s';
                subFps.textContent = 'Speed: 0 FPS';

                // Reset Alerts Feed
                alertsContainer.innerHTML = '';
                alertsContainer.appendChild(alertsEmptyState);
                alertsEmptyState.classList.remove('hidden');
                alertCountBadge.textContent = '0';

                showToast('Dashboard reset successfully.', 'info');
            });
    });

    // --- Statistics Update Helper ---
    function updateStatistics(stats) {
        if (!stats) return;

        valFloodStatus.textContent = stats.flood_status || 'Analyzed';
        
        if (stats.flood_status.includes('Severe')) {
            valFloodStatus.style.color = 'var(--status-red)';
        } else if (stats.flood_status.includes('Moderate') || stats.flood_status.includes('Minor')) {
            valFloodStatus.style.color = 'var(--status-amber)';
        } else {
            valFloodStatus.style.color = 'var(--status-green)';
        }

        subFloodStatus.textContent = `Coverage: ${stats.water_coverage_pct}%`;
        valVehicles.textContent = stats.max_vehicles || 0;
        valPersons.textContent = stats.max_persons || 0;
        valTime.textContent = stats.processing_time || '0s';

        if (stats.fps === "N/A" || stats.fps === "N/A (Single Frame)") {
            subFps.textContent = `Frame: 1/1 (Image)`;
        } else {
            subFps.textContent = `Speed: ${stats.fps} FPS (${stats.total_frames} frames)`;
        }
    }

    // --- Alert Feed Renderer ---
    function renderAlerts(alerts) {
        if (!alerts || alerts.length === 0) return;

        alertsContainer.innerHTML = '';
        alertsEmptyState.classList.add('hidden');
        alertCountBadge.textContent = alerts.length;

        alerts.forEach(alert => {
            const alertItem = document.createElement('div');
            alertItem.className = `alert-item ${alert.type || 'info'}`;
            alertItem.innerHTML = `
                <div class="alert-item-header">
                    <span class="alert-title">${alert.title}</span>
                    <span class="alert-time">${alert.time}</span>
                </div>
                <div class="alert-msg">${alert.message}</div>
            `;
            alertsContainer.appendChild(alertItem);
        });
    }
});
