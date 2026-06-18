/**
 * ProcrastinaAI — Shared Utility Script
 *
 * Provides: API helpers, session management, chip selection, notifications.
 * Page-specific logic lives in inline <script> tags in each template.
 */

// ============================================================
// Configuration
// ============================================================
const API_BASE = '/projects/procrastina-ai/api';

// ============================================================
// Session Storage (localStorage)
// ============================================================

function getSession() {
    const raw = localStorage.getItem('procrastina_ai_session');
    return raw ? JSON.parse(raw) : null;
}

function storeSession(data) {
    localStorage.setItem('procrastina_ai_session', JSON.stringify(data));
}

function clearSession() {
    localStorage.removeItem('procrastina_ai_session');
}

function getSessionId() {
    const s = getSession();
    return s ? s.sessionId : null;
}

// ============================================================
// CSRF Token
// ============================================================

function getCsrfToken() {
    // 1. Try meta tag (added in base.html)
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta && meta.content) return meta.content;
    // 2. Try hidden input
    const input = document.querySelector('[name=csrfmiddlewaretoken]');
    if (input && input.value) return input.value;
    // 3. Try Django's csrftoken cookie
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    if (match) return match[1];
    return '';
}

// ============================================================
// API Helpers
// ============================================================

async function apiPost(endpoint, data) {
    try {
        const csrfToken = getCsrfToken();
        const response = await fetch(`${API_BASE}/${endpoint}/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        return await response.json();
    } catch (error) {
        console.error(`API POST ${endpoint} error:`, error);
        return { success: false, error: error.message };
    }
}

async function apiGet(endpoint, params = {}) {
    try {
        const qs = new URLSearchParams(params).toString();
        const url = `${API_BASE}/${endpoint}/${qs ? '?' + qs : ''}`;
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        return await response.json();
    } catch (error) {
        console.error(`API GET ${endpoint} error:`, error);
        return { success: false, error: error.message };
    }
}

async function fetchSessionData() {
    const sessionId = getSessionId();
    if (!sessionId) return null;
    const result = await apiGet('session-data', { sessionId });
    return result.success ? result.data : null;
}

// ============================================================
// Notifications
// ============================================================

function showNotification(message, type = 'info') {
    let container = document.querySelector('.notifications-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'notifications-container';
        document.body.appendChild(container);
    }
    const notif = document.createElement('div');
    notif.className = `notification notification-${type} show`;
    notif.textContent = message;
    container.appendChild(notif);
    setTimeout(() => {
        notif.classList.remove('show');
        setTimeout(() => notif.remove(), 300);
    }, 4000);
}

// ============================================================
// Chip Selection (for setup page)
// ============================================================

function initChipSelection() {
    document.querySelectorAll('.chip').forEach(chip => {
        chip.addEventListener('click', function (e) {
            e.preventDefault();
            const group = this.getAttribute('data-group');
            if (group === 'mood') {
                document.querySelectorAll('.chip[data-group="mood"]').forEach(c => c.classList.remove('active'));
                this.classList.add('active');
            } else if (group === 'interest') {
                this.classList.toggle('active');
            }
        });
    });
}

// ============================================================
// State Helpers
// ============================================================

function showLoading(container, message = 'The AI is thinking about your failures...') {
    if (!container) return;
    container.innerHTML = `
        <div class="loading-state">
            <div class="loading-dots"><span></span><span></span><span></span></div>
            <p>${message}</p>
        </div>`;
}

function showError(container, message = 'Something went wrong.\nEven the AI needs a break sometimes.') {
    if (!container) return;
    container.innerHTML = `
        <div class="error-state">
            <h3>Something broke.</h3>
            <p>${message}</p>
            <a href="/projects/procrastina-ai/setup/" class="btn btn-primary" style="margin-top:1rem;">Start Over</a>
        </div>`;
}

function showEmpty(container, message = "Nothing here yet.\nStart procrastinating and check back later.") {
    if (!container) return;
    container.innerHTML = `
        <div class="empty-state">
            <div class="empty-icon">🦗</div>
            <h3>It's quiet... too quiet.</h3>
            <p>${message}</p>
        </div>`;
}

// ============================================================
// Copy to clipboard
// ============================================================

function copyText(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Copied! Now paste it somewhere equally unproductive. 📋', 'success');
    }).catch(() => {
        showNotification('Copy failed. At least something failed today.', 'error');
    });
}

// ============================================================
// Activity Tracker — Real browser activity detection
// Tracks mousemove, click, keydown, scroll to measure active time.
// Only seconds with detected activity count toward "active seconds".
// ============================================================

const ActivityTracker = (function() {
    let activeSeconds = 0;
    let isRunning = false;
    let tickInterval = null;
    let heartbeatInterval = null;
    let activityThisSecond = false;
    let lastActivityTime = 0;
    const IDLE_THRESHOLD_MS = 60000; // 60 seconds of no events = idle

    function onActivity() {
        activityThisSecond = true;
        lastActivityTime = Date.now();
    }

    function tick() {
        // Called every 1 second
        const now = Date.now();
        const timeSinceLastActivity = now - lastActivityTime;

        if (activityThisSecond || timeSinceLastActivity < IDLE_THRESHOLD_MS) {
            // Count this second as active if:
            // 1. An event fired this second, OR
            // 2. Last activity was within idle threshold (user might be reading/thinking)
            if (activityThisSecond) {
                activeSeconds++;
            }
        }
        activityThisSecond = false;
    }

    function sendHeartbeat() {
        const session = getSession();
        if (!session || !session.sessionId) return;
        apiPost('activity-heartbeat', {
            sessionId: session.sessionId,
            activeSeconds: activeSeconds
        });
    }

    function start() {
        if (isRunning) return;
        isRunning = true;
        activityThisSecond = false;
        lastActivityTime = Date.now();

        // Listen to activity events
        document.addEventListener('mousemove', onActivity, { passive: true });
        document.addEventListener('click', onActivity, { passive: true });
        document.addEventListener('keydown', onActivity, { passive: true });
        document.addEventListener('scroll', onActivity, { passive: true });
        document.addEventListener('touchstart', onActivity, { passive: true });

        // Tick every second to accumulate active time
        tickInterval = setInterval(tick, 1000);

        // Send heartbeat to server every 30 seconds
        heartbeatInterval = setInterval(sendHeartbeat, 30000);
    }

    function stop() {
        if (!isRunning) return;
        isRunning = false;

        document.removeEventListener('mousemove', onActivity);
        document.removeEventListener('click', onActivity);
        document.removeEventListener('keydown', onActivity);
        document.removeEventListener('scroll', onActivity);
        document.removeEventListener('touchstart', onActivity);

        if (tickInterval) {
            clearInterval(tickInterval);
            tickInterval = null;
        }
        if (heartbeatInterval) {
            clearInterval(heartbeatInterval);
            heartbeatInterval = null;
        }

        // Send final heartbeat
        sendHeartbeat();
    }

    function getActiveSeconds() {
        return activeSeconds;
    }

    function setActiveSeconds(val) {
        activeSeconds = val;
    }

    return { start, stop, getActiveSeconds, setActiveSeconds, sendHeartbeat };
})();


// ============================================================
// AgentPoller — Polls agent status every 15 seconds
// Updates the dashboard agent panel with live data.
// Detects agent disconnect and shows reconnection banner.
// ============================================================

const AgentPoller = (function() {
    let pollInterval = null;
    let wasConnected = false;
    let wasIdle = false;
    let onReturnFromIdle = null; // callback set by dashboard

    function poll() {
        const sessionId = getSessionId();
        if (!sessionId) return;

        apiGet('session-data', { sessionId }).then(result => {
            if (!result.success || !result.data) return;
            const data = result.data;
            const agentStatus = data.agentStatus;

            // Detect idle return: was idle -> now not idle
            if (agentStatus) {
                const isNowConnected = agentStatus.agentConnected;
                const isNowIdle = agentStatus.isIdle;

                if (wasIdle && !isNowIdle && onReturnFromIdle) {
                    // User returned from idle
                    onReturnFromIdle();
                }

                wasConnected = isNowConnected;
                wasIdle = isNowIdle;
            }

            // Update agent panel if visible
            _updateAgentPanel(data);
        }).catch(() => {}); // Silently fail on poll errors
    }

    function _updateAgentPanel(data) {
        const panel = document.getElementById('agentPanel');
        if (!panel) return;

        // Update pending disappearances badge if function exists
        if (typeof updatePendingBadge === 'function' && data.pendingDisappearanceCount !== undefined) {
            updatePendingBadge(data.pendingDisappearanceCount);
        }

        const activityData = data.activitySummary;
        const agentStatus = data.agentStatus;
        const isConnected = data.hasActivityData && agentStatus && agentStatus.agentConnected;

        // Toggle manual distraction button based on agent connection
        const btnDistracted = document.getElementById('btnDistracted');
        const btnFallback = document.getElementById('btnManualFallback');
        if (btnDistracted && btnFallback) {
            if (isConnected) {
                btnDistracted.style.display = 'none';
                btnFallback.style.display = '';
                const modeLabel = document.getElementById('agentModeLabel');
                if (modeLabel) modeLabel.style.display = 'none';
            } else {
                btnDistracted.style.display = '';
                btnFallback.style.display = 'none';
                const modeLabel = document.getElementById('agentModeLabel');
                if (modeLabel) modeLabel.style.display = '';
            }
        }

        if (data.hasActivityData && agentStatus && agentStatus.agentConnected) {
            document.getElementById('agentWaiting').style.display = 'none';
            document.getElementById('agentGrid').style.display = '';

            const appEl = document.getElementById('agentActiveApp');
            if (appEl) appEl.textContent = activityData ? activityData.currentApp || '—' : '—';

            // Connection status with proper states
            const connEl = document.getElementById('agentConnectionStatus');
            const badgeEl = document.getElementById('agentBadge');
            if (connEl && badgeEl) {
                if (agentStatus.isIdle) {
                    connEl.textContent = 'Idle';
                    connEl.style.color = 'var(--text-muted)';
                    badgeEl.textContent = 'IDLE';
                    badgeEl.classList.remove('info');
                } else {
                    connEl.textContent = 'Connected';
                    connEl.style.color = 'var(--success)';
                    badgeEl.textContent = 'CONNECTED';
                    badgeEl.classList.add('info');
                }
            }

            // Last App
            const lastAppEl = document.getElementById('agentLastApp');
            if (lastAppEl) lastAppEl.textContent = agentStatus.activeApp || '—';

            const eventsEl = document.getElementById('agentEvents');
            if (eventsEl) eventsEl.textContent = agentStatus.eventCount || 0;
            const focusEl = document.getElementById('agentFocusChanges');
            if (focusEl) focusEl.textContent = agentStatus.focusChanges || 0;

            // Last Activity
            const lastActEl = document.getElementById('agentLastActivity');
            if (lastActEl) {
                if (agentStatus.isIdle && agentStatus.idleSince) {
                    const idleMins = Math.round((Date.now() - new Date(agentStatus.idleSince).getTime()) / 60000);
                    lastActEl.textContent = idleMins > 0 ? `${idleMins}m ago` : 'Just now';
                } else {
                    lastActEl.textContent = 'Just now';
                }
            }

        } else if (wasConnected && (!agentStatus || !agentStatus.agentConnected)) {
            // Agent was connected but now disconnected — show Reconnecting
            const badgeEl = document.getElementById('agentBadge');
            if (badgeEl) {
                badgeEl.textContent = 'RECONNECTING';
                badgeEl.classList.remove('info');
            }
            const connEl = document.getElementById('agentConnectionStatus');
            if (connEl) {
                connEl.textContent = 'Reconnecting...';
                connEl.style.color = 'var(--danger)';
            }
            const lastActEl = document.getElementById('agentLastActivity');
            if (lastActEl) lastActEl.textContent = 'Connection lost';
        }
    }

    function start(callback) {
        if (pollInterval) return;
        onReturnFromIdle = callback || null;
        pollInterval = setInterval(poll, 15000); // 15 seconds
    }

    function stop() {
        if (pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
        }
    }

    return { start, stop, poll };
})();


// ============================================================
// SessionRecovery — Restores active session on page load
// Checks localStorage, validates with server, recovers if needed.
// ============================================================

const SessionRecovery = (function() {
    /**
     * Attempt to recover an active session.
     * Returns: {recovered: bool, session: object|null}
     */
    async function recover() {
        const existing = getSession();

        // If we already have a session in localStorage, validate it with the server
        if (existing && existing.sessionId) {
            const result = await apiGet('session-data', { sessionId: existing.sessionId });
            if (result.success && result.data && result.data.isActive !== false) {
                // Session is still active on server — valid
                return { recovered: true, session: existing, source: 'localStorage' };
            }
            // Session no longer active or doesn't exist — clear localStorage
            clearSession();
        }

        // Try to recover from server
        const recoverResult = await apiGet('recover-session');
        if (recoverResult.success && recoverResult.data && recoverResult.data.hasActiveSession) {
            const recovered = {
                sessionId: recoverResult.data.sessionId,
                mood: recoverResult.data.mood,
                interests: recoverResult.data.interests,
                tasks: recoverResult.data.tasks,
            };
            storeSession(recovered);
            return { recovered: true, session: recovered, source: 'server' };
        }

        return { recovered: false, session: null, source: null };
    }

    return { recover };
})();


// ============================================================
// Global exports
// ============================================================
window.procrastinaAI = {
    apiPost, apiGet, fetchSessionData,
    getSession, storeSession, clearSession, getSessionId,
    showNotification, showLoading, showError, showEmpty,
    initChipSelection, copyText,
    ActivityTracker,
    AgentPoller,
    SessionRecovery,
};
