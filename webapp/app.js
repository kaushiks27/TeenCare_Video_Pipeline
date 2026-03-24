/* ─── TeenCare Reel Pipeline — Dashboard App ───────────────────────────── */

const API_BASE = '';  // Same origin
let pollInterval = null;

// ─── View Switching ──────────────────────────────────────────────────────
function switchView(viewName) {
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));

    document.getElementById(`view-${viewName}`).classList.add('active');
    event.currentTarget.classList.add('active');

    // Start/stop pipeline polling based on active tab
    if (viewName === 'pipeline') {
        loadPipelineVideos();
        startPipelinePolling();
    } else {
        stopPipelinePolling();
    }
}

// ─── Init ────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    loadConfig();
    loadSavedState();

    // Slider
    const slider = document.getElementById('video-count');
    const display = document.getElementById('video-count-display');
    slider.addEventListener('input', () => {
        display.textContent = slider.value;
    });
});

// ─── Load Config (API Keys) ──────────────────────────────────────────────
async function loadConfig() {
    try {
        const resp = await fetch(`${API_BASE}/api/config`);
        const data = await resp.json();

        const grid = document.getElementById('api-keys-grid');
        grid.innerHTML = '';

        const keyNames = {
            'APIFY_API_KEY': 'Apify',
            'OPENAI_API_KEY': 'OpenAI',
            'GOOGLE_AI_STUDIO_API_KEY': 'Google AI',
            'KLING_ACCESS_KEY': 'Kling',
            'HIGGSFIELD_API_KEY': 'Higgsfield',
            'ELEVENLABS_API_KEY': 'ElevenLabs',
        };

        for (const [key, isSet] of Object.entries(data.api_keys)) {
            const item = document.createElement('div');
            item.className = `api-key-item ${isSet ? 'set' : 'missing'}`;
            item.innerHTML = `
                <span class="api-key-dot"></span>
                <span class="api-key-name">${keyNames[key] || key}</span>
            `;
            grid.appendChild(item);
        }
    } catch (e) {
        console.log('Config not loaded yet:', e.message);
    }
}

// ─── Load Saved State ────────────────────────────────────────────────────
async function loadSavedState() {
    try {
        const resp = await fetch(`${API_BASE}/api/status`);
        const state = await resp.json();

        if (state.status !== 'idle') {
            updateUI(state);
            if (state.status !== 'complete' && state.status !== 'error') {
                startPolling();
            }
            switchViewDirect('dashboard');
        }
    } catch (e) {
        console.log('No saved state');
    }
}

function switchViewDirect(viewName) {
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(`view-${viewName}`).classList.add('active');
    // Highlight correct nav button
    const btns = document.querySelectorAll('.nav-btn');
    const viewMap = { 'config': 0, 'dashboard': 1, 'pipeline': 2 };
    if (viewMap[viewName] !== undefined) {
        btns[viewMap[viewName]].classList.add('active');
    }
}

// ─── Start Research ──────────────────────────────────────────────────────
async function startResearch() {
    const maxVideos = parseInt(document.getElementById('video-count').value);
    const btn = document.getElementById('btn-start');

    btn.disabled = true;
    btn.innerHTML = '<span class="btn-icon">⏳</span> Starting...';

    try {
        const resp = await fetch(`${API_BASE}/api/start-research`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ max_videos: maxVideos }),
        });

        if (!resp.ok) {
            const err = await resp.json();
            alert(err.error || 'Failed to start');
            btn.disabled = false;
            btn.innerHTML = '<span class="btn-icon">🔍</span> Start Viral Research';
            return;
        }

        // Switch to dashboard view
        switchViewDirect('dashboard');
        startPolling();

    } catch (e) {
        alert('Connection error: ' + e.message);
        btn.disabled = false;
        btn.innerHTML = '<span class="btn-icon">🔍</span> Start Viral Research';
    }
}

// ─── Polling ─────────────────────────────────────────────────────────────
function startPolling() {
    if (pollInterval) clearInterval(pollInterval);
    pollInterval = setInterval(pollStatus, 1500);
    pollStatus(); // Immediate first call
}

async function pollStatus() {
    try {
        const resp = await fetch(`${API_BASE}/api/status`);
        const state = await resp.json();
        updateUI(state);

        if (state.status === 'complete' || state.status === 'error') {
            clearInterval(pollInterval);
            pollInterval = null;
            loadPipelineVideos();

            // Re-enable start button
            const btn = document.getElementById('btn-start');
            btn.disabled = false;
            btn.innerHTML = '<span class="btn-icon">🔍</span> Start Viral Research';
        }
    } catch (e) {
        console.error('Poll error:', e);
    }
}

// ─── Update UI ───────────────────────────────────────────────────────────
function updateUI(state) {
    // Global status
    const statusEl = document.getElementById('global-status');
    const dot = statusEl.querySelector('.status-dot');
    const text = statusEl.querySelector('.status-text');

    dot.className = 'status-dot';
    if (['researching', 'scoring', 'generating_captions', 'writing_sheets', 'starting'].includes(state.status)) {
        dot.classList.add('running');
        text.textContent = state.current_step || 'Running...';
    } else if (state.status === 'complete') {
        dot.classList.add('complete');
        text.textContent = 'Complete';
    } else if (state.status === 'error') {
        dot.classList.add('error');
        text.textContent = 'Error';
    } else {
        dot.classList.add('idle');
        text.textContent = 'Ready';
    }

    // Progress
    document.getElementById('progress-percent').textContent = `${state.progress}%`;
    document.getElementById('progress-bar').style.width = `${state.progress}%`;
    document.getElementById('progress-detail').textContent =
        state.current_step_detail || state.current_step || 'Waiting...';

    // Steps list
    renderSteps(state.steps);

    // Topics
    if (state.topics && state.topics.length > 0) {
        renderTopics(state.topics, state.selected_topics);
    }
}

function renderSteps(steps) {
    const container = document.getElementById('steps-list');
    container.innerHTML = '';

    steps.forEach((step, i) => {
        const item = document.createElement('div');
        item.className = `step-item ${step.status}`;

        let icon = '⏸️';
        if (step.status === 'running') icon = '⚡';
        else if (step.status === 'done') icon = '✅';
        else if (step.status === 'error') icon = '❌';
        else if (step.status === 'blocked') icon = '🚫';
        else icon = `${i + 1}️⃣`;

        item.innerHTML = `
            <div class="step-icon">${icon}</div>
            <div class="step-content">
                <div class="step-name">${step.name}</div>
                <div class="step-detail">${step.detail || (step.status === 'pending' ? 'Waiting...' : step.status === 'blocked' ? 'Blocked by previous failure' : '')}</div>
            </div>
            <div class="step-progress-mini">
                <div class="step-progress-mini-bar" style="width: ${step.progress}%"></div>
            </div>
        `;

        container.appendChild(item);
    });
}

function renderTopics(allTopics, selectedTopics) {
    const grid = document.getElementById('topics-grid');
    const count = document.getElementById('topic-count');

    const selectedSet = new Set((selectedTopics || []).map(t => t.topic));
    count.textContent = `${allTopics.length} topics`;

    grid.innerHTML = '';

    allTopics.forEach((topic, i) => {
        const isSelected = selectedSet.has(topic.topic);
        const card = document.createElement('div');
        card.className = `topic-card ${isSelected ? 'selected' : ''}`;

        card.innerHTML = `
            <div class="topic-rank">${i + 1}</div>
            <div class="topic-info">
                <div class="topic-title">${topic.topic}</div>
                <div class="topic-meta">
                    <span>📱 ${(topic.platforms || []).join(', ')}</span>
                    <span>📝 ${topic.post_count || 1} post${(topic.post_count || 1) > 1 ? 's' : ''}</span>
                    <span>⚡ V:${(topic.velocity_score || 0).toFixed(0)}</span>
                    <span>💬 R:${(topic.resonance_score || 0).toFixed(0)}</span>
                    <span>🔄 S:${(topic.shareability_score || 0).toFixed(0)}</span>
                </div>
            </div>
            <div class="topic-score">
                <div class="score-value">${(topic.virality_score || 0).toFixed(0)}</div>
                <div class="score-label">virality</div>
            </div>
        `;

        grid.appendChild(card);
    });
}

// ─── Pipeline Videos ─────────────────────────────────────────────────────
let pipelinePollInterval = null;

function startPipelinePolling() {
    if (!pipelinePollInterval) {
        pipelinePollInterval = setInterval(loadPipelineVideos, 3000);
    }
}

function stopPipelinePolling() {
    if (pipelinePollInterval) {
        clearInterval(pipelinePollInterval);
        pipelinePollInterval = null;
    }
}

async function loadPipelineVideos() {
    try {
        const resp = await fetch(`${API_BASE}/api/pipeline-videos`);
        const videos = await resp.json();
        renderPipelineVideos(videos);
    } catch (e) {
        console.log('No pipeline data');
    }
}

async function startPipeline(videoId) {
    const btn = document.getElementById(`btn-start-pipeline-${videoId}`);
    if (btn) {
        btn.disabled = true;
        btn.textContent = '⏳ Starting...';
    }

    try {
        const resp = await fetch(`${API_BASE}/api/start-pipeline`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ video_id: videoId, step: 1 }),
        });

        const result = await resp.json();

        if (!resp.ok) {
            alert(result.error || 'Failed to start pipeline');
            if (btn) {
                btn.disabled = false;
                btn.textContent = '▶ Start';
            }
            return;
        }

        // Start polling for updates
        if (!pipelinePollInterval) {
            pipelinePollInterval = setInterval(loadPipelineVideos, 3000);
        }
        // Immediate refresh
        setTimeout(loadPipelineVideos, 500);

    } catch (e) {
        alert('Connection error: ' + e.message);
        if (btn) {
            btn.disabled = false;
            btn.textContent = '▶ Start';
        }
    }
}

function renderPipelineVideos(videos) {
    const grid = document.getElementById('pipeline-grid');
    grid.innerHTML = '';

    if (videos.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">🎬</div>
                <div class="empty-state-text">No videos in pipeline yet.<br>Run research first to discover topics.</div>
            </div>
        `;
        return;
    }

    videos.forEach(video => {
        const card = document.createElement('div');
        card.className = 'pipeline-card';

        const isRunning = video.steps.some(s => s.status === 'running');
        const isDone = video.steps.every(s => s.status === 'done');
        const hasError = video.steps.some(s => s.status === 'error');

        const stepsHtml = video.steps.map(step => {
            let icon = step.step;
            let detailHtml = '';
            if (step.status === 'done') icon = '✓';
            else if (step.status === 'running') icon = '⚡';
            else if (step.status === 'error') icon = '✗';

            if (step.detail && step.status !== 'pending') {
                detailHtml = `<div class="pipeline-step-detail">${step.detail}</div>`;
            }

            return `
                <div class="pipeline-step ${step.status}">
                    <div class="pipeline-step-dot">${icon}</div>
                    <div class="pipeline-step-info">
                        <div class="pipeline-step-label">${step.name}</div>
                        ${detailHtml}
                    </div>
                </div>
            `;
        }).join('');

        // Button: Start / Running / Done
        let btnHtml = '';
        if (isDone) {
            btnHtml = `<button class="btn-pipeline-status done" disabled>✅ Done</button>`;
        } else if (isRunning) {
            btnHtml = `<button class="btn-pipeline-status running" disabled>⚡ Running...</button>`;
        } else if (hasError) {
            btnHtml = `<button class="btn-pipeline-start" id="btn-start-pipeline-${video.video_id}" onclick="startPipeline(${video.video_id})">🔄 Retry</button>`;
        } else {
            btnHtml = `<button class="btn-pipeline-start" id="btn-start-pipeline-${video.video_id}" onclick="startPipeline(${video.video_id})">▶ Start Pipeline</button>`;
        }

        card.innerHTML = `
            <div class="pipeline-card-header">
                <span class="pipeline-video-id">Video ${video.video_id}</span>
                <span class="score-value" style="font-size: 16px">${(video.virality_score || 0).toFixed(0)}</span>
            </div>
            <div class="pipeline-topic">${video.topic}</div>
            <div class="pipeline-steps">${stepsHtml}</div>
            <div class="pipeline-card-actions">${btnHtml}</div>
        `;

        grid.appendChild(card);
    });
}
