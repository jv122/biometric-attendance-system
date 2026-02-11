let video = null;
let canvas = null;
// Used for scaling calculations
let currentScale = 1;
let overlayCanvas = null;
let overlayContext = null;
let stream = null;
let attendanceLog = [];
let markedStudents = new Set();
let isProcessing = false;
// Smoothing & performance config
const SMOOTHING_ENABLED = true; // feature-flag: safe to toggle
const FRAME_SKIP = 2; // process every Nth capture frame for recognition
let frameCounter = 0;

// overlay smoothing structures
let detectedBoxes = []; // {id, target:{x,y,w,h}, current:{x,y,w,h}, name, status}

// Session State
let currentSessionId = null;
let sessionEndTime = null;
let timerInterval = null;

document.addEventListener('DOMContentLoaded', function () {
    video = document.getElementById('video');
    canvas = document.getElementById('canvas');
    overlayCanvas = document.getElementById('overlay-canvas');
    if (overlayCanvas) overlayContext = overlayCanvas.getContext('2d');

    // Start overlay render loop
    requestAnimationFrame(renderOverlayLoop);

    // Check for active session on load
    checkSessionStatus();
});

function getCSRFToken() {
    // Try to get from meta tag first (standard in base.html now)
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) return meta.getAttribute('content');

    // Fallback: try hidden input if available (less reliable for fetch but ok)
    const input = document.querySelector('input[name="csrf_token"]');
    if (input) return input.value;

    return '';
}

function updateUIState(state, data = {}) {
    const startBtn = document.getElementById('startSessionBtn');
    const endBtn = document.getElementById('endSessionBtn');
    const reopenBtn = document.getElementById('reopenSessionBtn');
    const statusDisplay = document.getElementById('session-status-display');
    const statusBadge = document.getElementById('status-badge');

    // Reset defaults
    startBtn.style.display = 'inline-block';
    endBtn.disabled = true;
    endBtn.style.display = 'inline-block';
    reopenBtn.style.display = 'none';
    statusDisplay.style.display = 'none';
    document.getElementById('class_name').disabled = false;
    document.getElementById('subject_id').disabled = false;
    document.getElementById('duration').disabled = false;

    if (state === 'Active' || state === 'Reopened') {
        startBtn.style.display = 'none';
        endBtn.disabled = false;
        reopenBtn.style.display = 'none';
        statusDisplay.style.display = 'flex';

        document.getElementById('class_name').disabled = true;
        document.getElementById('subject_id').disabled = true;
        document.getElementById('duration').disabled = true;

        if (state === 'Active') {
            statusBadge.innerText = 'Active';
            statusBadge.style.background = 'var(--success)';
            startTimer(data.remaining_minutes);
        } else {
            statusBadge.innerText = 'Reopened (Late Marking)';
            statusBadge.style.background = '#f59e0b';
            document.getElementById('timer-display').innerText = '--:--';
            stopTimer(); // No timer for reopened session
        }

        if (state === 'Active' || state === 'Reopened') {
            // Ensure camera is running ONLY if active
            if (!stream) startCameraInternal();
        }

    } else if (state === 'Ended') {
        startBtn.style.display = 'inline-block';
        startBtn.innerText = 'Start New Session';
        endBtn.style.display = 'none';
        reopenBtn.style.display = 'inline-block';
        statusDisplay.style.display = 'flex';

        statusBadge.innerText = 'Ended';
        statusBadge.style.background = '#ef4444';
        stopTimer();
        stopCamera();
    }
}

function checkSessionStatus() {
    fetch('/api/session_status')
        .then(res => {
            if (res.headers.get('content-type').includes('text/html')) {
                // Session expired or not logged in - just return inactive state or handle gracefully
                return { active: false };
            }
            return res.json();
        })
        .then(data => {
            if (data.active) {
                currentSessionId = data.session_id;
                // Pre-fill fields
                document.getElementById('class_name').value = data.class_name;
                // Trigger loadSubjects to populate subject (async needs handling) but for now just set ID might fail if options not loaded.
                // Simplified: Just set state.
                updateUIState(data.status, data);
            }
        });
}

function startSession() {
    const classSelect = document.getElementById('class_name');
    const subjectSelect = document.getElementById('subject_id');
    const durationInput = document.getElementById('duration');

    if (!classSelect.value || !subjectSelect.value) {
        alert('Please select class and subject first');
        return;
    }

    const duration = parseInt(durationInput.value) || 10;

    console.log("Starting session with:", {
        class_name: classSelect.value,
        subject_id: subjectSelect.value,
        duration: duration
    });

    fetch('/api/start_session', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        credentials: 'include',
        body: JSON.stringify({
            class_name: classSelect.value,
            subject_id: subjectSelect.value,
            duration: duration
        })
    })
        .then(res => {
            if (res.status === 401 || res.status === 403 || res.url.includes('/login')) {
                throw new Error('Session expired');
            }
            if (!res.ok) {
                // Try to parse error text if JSON fails
                return res.text().then(text => { throw new Error('Server Error: ' + res.status + ' ' + text.substring(0, 100)); });
            }
            return res.json();
        })
        .then(data => {
            console.log("Start Session Response:", data);
            if (data.success) {
                currentSessionId = data.session_id;
                updateUIState('Active', { remaining_minutes: duration });
                showResult('Session Started', 'success');
            } else {
                alert('Error starting session: ' + data.message);
            }
        })
        .catch(err => {
            console.error("Start Session Fetch Error:", err);
            if (err.message === 'Session expired') {
                alert("Session expired. Redirecting to login...");
                window.location.href = '/login';
            } else {
                alert("Failed to connect to server: " + err.message);
            }
        });
}

function endSession() {
    if (!confirm('Are you sure you want to end the session? This will mark all unmarked students as Absent.')) return;

    fetch('/api/end_session', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        credentials: 'include',
        body: JSON.stringify({ session_id: currentSessionId })
    })
        .then(res => {
            if (res.status === 401 || res.status === 403 || res.url.includes('/login')) {
                throw new Error('Session expired');
            }
            if (!res.ok) {
                return res.text().then(text => { throw new Error('Server Error: ' + res.status + ' '); });
            }
            return res.json();
        })
        .then(data => {
            if (data.success) {
                currentSessionId = null; // Prevent camera restart loop
                updateUIState('Ended');
                showResult('Session Ended. Absentees Marked.', 'info');
            } else {
                alert(data.message || 'Failed to end session');
            }
        })
        .catch(err => {
            console.error("End Session Error:", err);
            if (err.message === 'Session expired') {
                alert('Session expired. Please login again.');
                window.location.reload();
            } else {
                alert('Error connecting to server: ' + err.message);
            }
        });
}

function reopenSession() {
    fetch('/api/reopen_session', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        credentials: 'include',
        body: JSON.stringify({ session_id: currentSessionId })
    })
        .then(res => {
            if (res.status === 401 || res.status === 403 || res.url.includes('/login')) {
                throw new Error('Session expired');
            }
            if (!res.ok) {
                return res.text().then(text => { throw new Error('Server Error: ' + res.status + ' '); });
            }
            return res.json();
        })
        .then(data => {
            if (data.success) {
                updateUIState('Reopened');
                showResult('Session Reopened. Marking as Late.', 'warning');
            }
        })
        .catch(err => {
            console.error("Reopen Session Error:", err);
            if (err.message === 'Session expired') {
                alert('Session expired. Please login again.');
                window.location.reload();
            }
        });
}

// Timer Logic
function startTimer(minutes) {
    stopTimer();
    const now = new Date().getTime();
    sessionEndTime = now + (minutes * 60 * 1000);

    updateTimerDisplay(); // Initial
    timerInterval = setInterval(updateTimerDisplay, 1000);
}

function stopTimer() {
    if (timerInterval) clearInterval(timerInterval);
    timerInterval = null;
}

function updateTimerDisplay() {
    const now = new Date().getTime();
    const distance = sessionEndTime - now;

    if (distance < 0) {
        stopTimer();
        document.getElementById('timer-display').innerText = "00:00";
        document.getElementById('timer-display').style.color = 'red';
        // Optional: Auto-end? User wanted "marked absent by default", implying end.
        // But also "faculty can reopen".
        // Let's just alert visually.
        showResult('Time Expired. Please End Session.', 'error');
        return;
    }

    const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((distance % (1000 * 60)) / 1000);

    document.getElementById('timer-display').innerText =
        (minutes < 10 ? "0" + minutes : minutes) + ":" + (seconds < 10 ? "0" + seconds : seconds);
    document.getElementById('timer-display').style.color = 'inherit';
}

// Camera Logic (Simplified helpers)
function toggleCamera() {
    if (stream) stopCamera();
    else startCameraInternal();
}

function startCameraInternal() {
    const placeholder = document.getElementById('camera-placeholder');
    const overlay = document.getElementById('scanner-overlay');

    // Safety check for localhost/https
    if (location.protocol !== 'https:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
        alert('Camera requires Secure Context (HTTPS) or Localhost.');
        return;
    }

    navigator.mediaDevices.getUserMedia({ video: { width: { ideal: 1280 }, height: { ideal: 720 } } })
        .then(mediaStream => {
            stream = mediaStream;
            video.srcObject = mediaStream;

            // Monitor stream for disconnection
            mediaStream.getVideoTracks().forEach(track => {
                track.onended = () => {
                    console.log('Camera track ended');
                    if (currentSessionId) {
                        // Try to restart if session is still active
                        setTimeout(() => {
                            if (currentSessionId && !stream) {
                                console.log('Attempting to restart camera after track ended...');
                                startCameraInternal();
                            }
                        }, 1000);
                    }
                };
            });

            video.onloadedmetadata = () => {
                video.play().catch(err => {
                    console.error('Video play error:', err);
                });

                // Set overlay canvas size to match video source resolution
                if (overlayCanvas) {
                    overlayCanvas.width = video.videoWidth;
                    overlayCanvas.height = video.videoHeight;
                }

                captureAndRecognize();
                placeholder.style.display = 'none';
                overlay.style.display = 'block';
            };

            video.onerror = (err) => {
                console.error('Video error:', err);
                if (currentSessionId) {
                    showResult('Camera error. Attempting to restart...', 'error');
                    setTimeout(() => {
                        if (currentSessionId) startCameraInternal();
                    }, 2000);
                }
            };
        })
        .catch(err => {
            console.error("Camera Error:", err);
            showResult("Could not access camera: " + err.message, 'error');
            // Retry after delay if session is active
            if (currentSessionId) {
                setTimeout(() => {
                    if (currentSessionId) startCameraInternal();
                }, 3000);
            }
        });
}

function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
        video.srcObject = null;

        document.getElementById('camera-placeholder').style.display = 'block';
        document.getElementById('scanner-overlay').style.display = 'none';

        if (overlayContext && overlayCanvas) {
            overlayContext.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
        }
    }
}

// Recognition Loop
function captureAndRecognize() {
    if (!video || !canvas) {
        // Retry after a delay if elements not ready
        setTimeout(() => requestAnimationFrame(captureAndRecognize), 100);
        return;
    }

    // Check if stream is active, restart if needed (but only if session is active)
    if (!stream && currentSessionId) {
        console.log('Stream lost, attempting to restart camera...');
        startCameraInternal();
        setTimeout(() => requestAnimationFrame(captureAndRecognize), 500);
        return;
    }

    if (!stream) {
        // No stream and no active session - don't continue
        return;
    }

    // Frame skipping to reduce CPU/network
    frameCounter = (frameCounter + 1) % FRAME_SKIP;
    if (frameCounter !== 0 && !isProcessing) {
        // Still continue loop but don't do heavy capture
        requestAnimationFrame(captureAndRecognize);
        return;
    }

    // Ensure video is ready
    if (video.videoWidth === 0 || video.videoHeight === 0) {
        requestAnimationFrame(captureAndRecognize);
        return;
    }

    // Check if video stream is actually playing
    if (video.readyState < 2) {
        requestAnimationFrame(captureAndRecognize);
        return;
    }

    const context = canvas.getContext('2d');

    // Downscale for performance (max width 800px)
    const MAX_WIDTH = 800;
    const originalWidth = video.videoWidth;
    const originalHeight = video.videoHeight;

    if (originalWidth > MAX_WIDTH) {
        currentScale = MAX_WIDTH / originalWidth;
        canvas.width = MAX_WIDTH;
        canvas.height = originalHeight * currentScale;
    } else {
        currentScale = 1;
        canvas.width = originalWidth;
        canvas.height = originalHeight;
    }

    // draw scaled frame for recognition
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    const imageData = canvas.toDataURL('image/jpeg', 0.7);

    // Only send if session active (or reopened)
    if (!currentSessionId) {
        requestAnimationFrame(captureAndRecognize);
        return;
    }

    isProcessing = true;

    fetch('/api/recognize_face', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        credentials: 'include',
        body: JSON.stringify({
            image: imageData,
            class_name: document.getElementById('class_name').value,
            subject_id: document.getElementById('subject_id').value
        })
    })
        .then(res => {
            if (res.status === 401 || res.status === 403 || res.url.includes('/login')) {
                throw new Error('Session expired');
            }
            if (!res.ok) {
                return res.text().then(text => { throw new Error('Server Error: ' + res.status + ' '); });
            }
            return res.json();
        })
        .then(data => {
            if (data.success) {
                // Update detectedBoxes targets for smooth overlay
                updateDetectedBoxesFromResults(data.results);
                processResults(data.results);
            } else {
                showResult(data.error || data.message || 'Recognition Error', 'error');
                // Clear overlay if error
                if (overlayContext && overlayCanvas) {
                    overlayContext.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
                }
            }
        })
        .catch(err => {
            console.error('Recognition error:', err);

            if (err.message === 'Session expired') {
                isProcessing = false;
                alert("Session expired. Please log in again.");
                window.location.reload();
                return;
            }

            showResult('Connection error. Retrying...', 'error');
            isProcessing = false;
            // Continue loop even on error, but with a small delay
            if (stream && currentSessionId) {
                setTimeout(() => requestAnimationFrame(captureAndRecognize), 500);
            }
        })
        .finally(() => {
            // isProcessing = false; // Moved out to fix loop
            isProcessing = false;
            // Always continue the loop if stream exists and session is active
            if (stream && currentSessionId) {
                requestAnimationFrame(captureAndRecognize);
            } else if (currentSessionId && !stream) {
                // Session active but stream lost - try to restart
                console.log('Stream lost during recognition, attempting restart...');
                setTimeout(() => {
                    if (currentSessionId) startCameraInternal();
                }, 1000);
            }
        });
}

function processResults(results) {
    if (!results) return; // Safety check

    // Debug log
    console.log("Processed Results:", results);

    // Clear previous drawings
    // overlay cleared in render loop - keep processing minimal here

    if (!results || results.length === 0) {
        showResult('', 'none');
        return;
    }

    let msgParts = [];
    results.forEach(res => {
        // Draw Box
        if (res.location && overlayContext) {
            // compute scaled coordinates
            const [top, right, bottom, left] = res.location.map(val => val / currentScale);
            const width = right - left;
            const height = bottom - top;

            // push/update detectedBoxes target
            const id = res.enrollment || (res.name + '_' + left + '_' + top);
            updateOrCreateBox(id, left, top, width, height, res.name, res.status);
        }

        if (res.status === 'marked' || res.status === 'existing') {
            if (!markedStudents.has(res.enrollment)) {
                markedStudents.add(res.enrollment);
                addLog(res.name, res.enrollment, res.message, res.status === 'marked' ? 'var(--success)' : 'var(--warning)');
                msgParts.push(res.name + ' ✓');
            }
        } else if (res.status === 'liveness_failed') {
            msgParts.push('Please Smile 😊');
        } else if (res.status === 'unknown') {
            // Optional: msgParts.push('Unknown');
            console.log("Unknown face detected");
        }
    });

    if (msgParts.length > 0) {
        showResult(msgParts.join(', '), 'success');
    } else {
        // If only unknown faces
        const unknownCount = results.filter(r => r.status === 'unknown').length;
        if (unknownCount > 0) showResult(`${unknownCount} Face(s) Detected (Unknown)`, 'error');
        else showResult('', 'none');
    }
}

// Update or create smoothing box
function updateOrCreateBox(id, x, y, w, h, name, status) {
    let box = detectedBoxes.find(b => b.id === id);
    if (!box) {
        box = {
            id,
            target: { x, y, w, h },
            current: { x: x, y: y, w: w, h: h },
            name: name || '',
            status: status || 'unknown',
            lastSeen: Date.now()
        };
        detectedBoxes.push(box);
    } else {
        box.target.x = x;
        box.target.y = y;
        box.target.w = w;
        box.target.h = h;
        box.name = name || box.name;
        box.status = status || box.status;
        box.lastSeen = Date.now();
    }
}

function updateDetectedBoxesFromResults(results) {
    const seenIds = new Set();
    if (results && results.length) {
        results.forEach(res => {
            if (res.location) {
                const [top, right, bottom, left] = res.location.map(val => val / currentScale);
                const width = right - left;
                const height = bottom - top;
                const id = res.enrollment || (res.name + '_' + left + '_' + top);
                updateOrCreateBox(id, left, top, width, height, res.name, res.status);
                seenIds.add(id);
            }
        });
    }

    // fade out boxes not seen recently
    const now = Date.now();
    detectedBoxes = detectedBoxes.filter(b => (now - b.lastSeen) < 3000 || seenIds.has(b.id));
}

// Overlay render loop - runs every animation frame and interpolates positions
function renderOverlayLoop() {
    if (!overlayCanvas || !overlayContext) {
        requestAnimationFrame(renderOverlayLoop);
        return;
    }

    overlayContext.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);

    const smoothing = SMOOTHING_ENABLED ? 0.2 : 1.0; // lerp factor

    detectedBoxes.forEach(box => {
        // interpolate current toward target
        box.current.x += (box.target.x - box.current.x) * smoothing;
        box.current.y += (box.target.y - box.current.y) * smoothing;
        box.current.w += (box.target.w - box.current.w) * smoothing;
        box.current.h += (box.target.h - box.current.h) * smoothing;

        // draw using GPU-accelerated styles
        overlayContext.save();
        overlayContext.lineWidth = 3;

        let stroke = '#ef4444';
        let fill = 'rgba(239, 68, 68, 0.12)';
        if (box.status === 'marked' || box.status === 'existing') {
            stroke = '#16a34a';
            fill = 'rgba(16,163,127,0.08)';
        } else if (box.status === 'liveness_failed') {
            stroke = '#f59e0b';
            fill = 'rgba(245,158,11,0.08)';
        }

        // rounded box with soft shadow
        overlayContext.strokeStyle = stroke;
        overlayContext.fillStyle = fill;
        const r = 10; // corner radius
        roundRect(overlayContext, box.current.x, box.current.y, box.current.w, box.current.h, r, true, true);

        // label
        const labelPad = 8;
        overlayContext.font = '600 14px Inter, system-ui, sans-serif';
        overlayContext.fillStyle = 'rgba(255,255,255,0.9)';
        const labelText = box.name || 'Unknown';
        const textWidth = overlayContext.measureText(labelText).width;
        const labelX = box.current.x + 6;
        const labelY = Math.max(20, box.current.y - 10);

        // background pill
        overlayContext.fillStyle = stroke;
        overlayContext.globalAlpha = 0.95;
        const pillW = textWidth + (labelPad * 2);
        const pillH = 20;
        roundRect(overlayContext, labelX - 4, labelY - pillH + 6, pillW, pillH, 10, true, false);

        overlayContext.globalAlpha = 1;
        overlayContext.fillStyle = '#fff';
        overlayContext.fillText(labelText, labelX + labelPad, labelY + 2);

        overlayContext.restore();
    });

    requestAnimationFrame(renderOverlayLoop);
}

// utility: rounded rectangle drawing
function roundRect(ctx, x, y, width, height, radius, fill, stroke) {
    if (typeof stroke === 'undefined') stroke = true;
    if (typeof radius === 'undefined') radius = 5;
    if (typeof radius === 'number') {
        radius = { tl: radius, tr: radius, br: radius, bl: radius };
    } else {
        const defaultRadius = { tl: 0, tr: 0, br: 0, bl: 0 };
        for (let side in defaultRadius) {
            radius[side] = radius[side] || defaultRadius[side];
        }
    }
    ctx.beginPath();
    ctx.moveTo(x + radius.tl, y);
    ctx.lineTo(x + width - radius.tr, y);
    ctx.quadraticCurveTo(x + width, y, x + width, y + radius.tr);
    ctx.lineTo(x + width, y + height - radius.br);
    ctx.quadraticCurveTo(x + width, y + height, x + width - radius.br, y + height);
    ctx.lineTo(x + radius.bl, y + height);
    ctx.quadraticCurveTo(x, y + height, x, y + height - radius.bl);
    ctx.lineTo(x, y + radius.tl);
    ctx.quadraticCurveTo(x, y, x + radius.tl, y);
    ctx.closePath();
    if (fill) ctx.fill();
    if (stroke) ctx.stroke();
}

function showResult(msg, type) {
    const el = document.getElementById('recognition-result');
    if (type === 'none') {
        el.style.display = 'none';
        return;
    }
    el.style.display = 'flex';
    el.innerHTML = msg;

    // Reset styles
    el.style.backgroundColor = type === 'success' ? '#dcfce7' : (type === 'error' ? '#fee2e2' : '#fef3c7');
    el.style.color = type === 'success' ? '#166534' : (type === 'error' ? '#991b1b' : '#92400e');
}

function addLog(name, enrollment, status, color) {
    const logContent = document.getElementById('log-content');
    const time = new Date().toLocaleTimeString();

    // Clear placeholder
    if (logContent.innerText.includes('No records')) logContent.innerHTML = '';

    const div = document.createElement('div');
    div.style.padding = '0.5rem';
    div.style.borderBottom = '1px solid #eee';
    div.innerHTML = `<b>${name}</b> (${enrollment}) <span style="float:right; color:${color}">${status}</span>`;

    logContent.insertBefore(div, logContent.firstChild);
    document.getElementById('log-count').innerText = logContent.children.length;
}
