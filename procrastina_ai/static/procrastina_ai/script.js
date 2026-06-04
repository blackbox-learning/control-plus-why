/**
 * ProcrastinaAI Frontend JavaScript
 * 
 * This script handles all frontend interactivity and API calls.
 * API base is: /projects/procrastina-ai/api/
 * 
 * Features:
 * - Chip selection for mood and interests
 * - Session management with localStorage
 * - API calls to backend for AI generation
 * - Notification system
 * - Copy-to-clipboard functionality
 */

// ============================================================
// Configuration
// ============================================================

// API base URL for Django backend
const API_BASE = '/projects/procrastina-ai/api';

// Store current session ID in browser
let currentSessionId = localStorage.getItem('procrastina_ai_session_id') || null;

// ============================================================
// Helper Functions
// ============================================================

/**
 * Make API request to backend.
 * Automatically includes CSRF token for security.
 * 
 * @param {string} endpoint - API endpoint (e.g., 'create-session')
 * @param {object} data - Request body data
 * @returns {Promise<object>} - API response
 */
async function apiRequest(endpoint, data) {
    try {
        // Get CSRF token from meta tag (Django security)
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                         document.querySelector('meta[name="csrf-token"]')?.content || '';

        const response = await fetch(`${API_BASE}/${endpoint}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`);
        }

        const result = await response.json();
        return result;
    } catch (error) {
        console.error('API Request Error:', error);
        return {
            success: false,
            error: error.message
        };
    }
}

/**
 * Show notification message with auto-dismiss.
 * 
 * @param {string} message - Message to show
 * @param {string} type - Type: 'success', 'error', 'info'
 */
function showNotification(message, type = 'info') {
    const container = document.querySelector('.notifications-container') || 
                     document.body.appendChild(document.createElement('div'));
    container.className = 'notifications-container';

    const notification = document.createElement('div');
    notification.className = `notification notification-${type} show`;
    notification.textContent = message;

    container.appendChild(notification);

    // Auto-dismiss after 4 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}

/**
 * Store session ID in localStorage.
 * 
 * @param {string} sessionId - Session ID from API
 */
function storeSessionId(sessionId) {
    currentSessionId = sessionId;
    localStorage.setItem('procrastina_ai_session_id', sessionId);
}

/**
 * Get current session ID.
 * 
 * @returns {string|null} - Current session ID or null
 */
function getSessionId() {
    return currentSessionId;
}

/**
 * Clear session from storage.
 */
function clearSession() {
    currentSessionId = null;
    localStorage.removeItem('procrastina_ai_session_id');
}

// ============================================================
// Chip Selection Handling
// ============================================================

/**
 * Initialize chip selection for mood and interests.
 * Should be called on page load for setup page.
 */
function initChipSelection() {
    const chips = document.querySelectorAll('.chip');
    
    chips.forEach(chip => {
        chip.addEventListener('click', function(e) {
            e.preventDefault();
            
            const group = this.getAttribute('data-group');
            const value = this.getAttribute('data-value');
            
            // Mood: single selection (radio button behavior)
            if (group === 'mood') {
                // Deselect other mood chips
                document.querySelectorAll('.chip[data-group="mood"]').forEach(c => {
                    c.classList.remove('active');
                });
                // Select this chip
                this.classList.add('active');
            }
            // Interests: multiple selection (checkbox behavior)
            else if (group === 'interest') {
                this.classList.toggle('active');
            }
        });
    });
}

// ============================================================
// Session Management
// ============================================================

/**
 * Create a new session with user's mood, interests, and tasks.
 * Called from the setup form.
 * 
 * @param {string} mood - Selected mood
 * @param {array} interests - Selected interests
 * @param {array} tasks - User's tasks
 * @returns {Promise<boolean>} - Success/failure
 */
async function createNewSession(mood, interests, tasks) {
    console.log('Creating new session...', { mood, interests, tasks });
    
    const result = await apiRequest('create-session', {
        mood,
        interests,
        tasks
    });

    if (result.success) {
        storeSessionId(result.data.sessionId);
        console.log('✅ Session created:', result.data.sessionId);
        showNotification('Session created! Let the procrastination begin! 🎉', 'success');
        return true;
    } else {
        console.error('❌ Failed to create session:', result.error);
        showNotification('Failed to create session: ' + result.error, 'error');
        return false;
    }
}

// ============================================================
// Prediction API
// ============================================================

/**
 * Generate procrastination prediction.
 * Called from prediction page.
 * 
 * @param {string} mood - User's mood
 * @param {array} interests - User's interests
 * @param {array} tasks - User's tasks
 * @returns {Promise<object>} - Prediction data or null
 */
async function generateProcrastinationPrediction(mood, interests, tasks) {
    console.log('Generating prediction...');
    
    const result = await apiRequest('generate-prediction', {
        sessionId: getSessionId(),
        mood,
        interests,
        tasks
    });

    if (result.success) {
        console.log('✅ Prediction generated');
        return {
            steps: result.data.prediction,
            confidence: result.data.confidence
        };
    } else {
        console.error('❌ Prediction failed:', result.error);
        showNotification('Failed to generate prediction', 'error');
        return null;
    }
}

/**
 * Display prediction steps on timeline page.
 * 
 * @param {array} steps - Array of prediction steps
 */
function displayPredictionSteps(steps) {
    const stepsContainer = document.querySelector('.timeline-journey');
    if (!stepsContainer) return;

    stepsContainer.innerHTML = '';
    steps.forEach((step, index) => {
        const stepElement = document.createElement('div');
        stepElement.className = 'timeline-step';
        stepElement.innerHTML = `
            <div class="step-number">${index + 1}</div>
            <div class="step-text">${step}</div>
        `;
        stepsContainer.appendChild(stepElement);
    });
}

// ============================================================
// Disappearance API
// ============================================================

/**
 * Save disappearance and get AI response.
 * Called from disappearance modal form.
 * 
 * @param {string} disappearanceType - Type of disappearance
 * @param {string} customLocation - Custom location if 'other'
 * @param {string} mood - User's mood
 * @param {array} interests - User's interests
 * @returns {Promise<object>} - Response data or null
 */
async function saveDisappearance(disappearanceType, customLocation, mood, interests) {
    console.log('Saving disappearance...', { disappearanceType, customLocation });
    
    const result = await apiRequest('save-disappearance', {
        sessionId: getSessionId(),
        disappearanceType,
        customLocation: customLocation || null,
        mood,
        interests
    });

    if (result.success) {
        console.log('✅ Disappearance saved');
        return {
            type: disappearanceType,
            aiResponse: result.data.aiResponse
        };
    } else {
        console.error('❌ Disappearance save failed:', result.error);
        showNotification('Failed to save disappearance', 'error');
        return null;
    }
}

/**
 * Display AI response in disappearance modal.
 * 
 * @param {string} response - AI-generated response
 */
function displayDisappearanceResponse(response) {
    const responseContainer = document.getElementById('responseContainer');
    const aiResponseCard = responseContainer?.querySelector('.ai-response-card');
    
    if (aiResponseCard) {
        aiResponseCard.innerHTML = `
            <div class="response-text">
                <p>${response}</p>
            </div>
        `;
    }
}

// ============================================================
// Report API
// ============================================================

/**
 * Generate daily procrastination report.
 * Called from report page.
 * 
 * @param {number} tasksPlanned - Number of tasks planned
 * @param {number} tasksCompleted - Number of tasks completed
 * @param {number} disappearances - Number of disappearances
 * @param {string} commonExcuse - Most common excuse
 * @returns {Promise<object>} - Report data or null
 */
async function generateDailyReport(tasksPlanned, tasksCompleted, disappearances, commonExcuse) {
    console.log('Generating report...');
    
    const result = await apiRequest('generate-report', {
        sessionId: getSessionId(),
        tasksPlanned,
        tasksCompleted,
        disappearances,
        commonExcuse
    });

    if (result.success) {
        console.log('✅ Report generated');
        return {
            score: result.data.procrastinationScore,
            summary: result.data.aiSummary,
            date: result.data.date
        };
    } else {
        console.error('❌ Report generation failed:', result.error);
        showNotification('Failed to generate report', 'error');
        return null;
    }
}

/**
 * Display report summary on page.
 * 
 * @param {object} report - Report data with summary
 */
function displayReportSummary(report) {
    const summaryContainer = document.querySelector('.ai-summary-card');
    if (!summaryContainer) return;

    summaryContainer.innerHTML = `
        <div class="summary-title">📊 AI Summary</div>
        <div class="summary-text">${report.summary}</div>
        <div class="summary-score">Procrastination Score: ${report.score}/100</div>
    `;
}

// ============================================================
// Funny Reasons API
// ============================================================

/**
 * Generate funny reasons to procrastinate on a task.
 * Called from funny reasons page.
 * 
 * @param {string} taskName - Name of the task
 * @param {string} mood - User's mood
 * @returns {Promise<array>} - Array of reasons or null
 */
async function generateFunnyReasons(taskName, mood) {
    console.log('Generating funny reasons for:', taskName);
    
    const result = await apiRequest('generate-funny-reasons', {
        sessionId: getSessionId(),
        taskName,
        mood
    });

    if (result.success) {
        console.log('✅ Funny reasons generated');
        return result.data.reasons;
    } else {
        console.error('❌ Funny reasons generation failed:', result.error);
        showNotification('Failed to generate reasons', 'error');
        return null;
    }
}

/**
 * Display funny reasons on page.
 * 
 * @param {string} taskName - Task name
 * @param {array} reasons - Array of funny reasons
 */
function displayFunnyReasons(taskName, reasons) {
    const container = document.querySelector('.reason-card');
    if (!container) return;

    const reasonsList = reasons.map(reason => `<li>${reason}</li>`).join('');
    
    container.innerHTML = `
        <h4>${taskName}</h4>
        <ul class="reason-list">
            ${reasonsList}
        </ul>
    `;
}

/**
 * Copy text to clipboard and show feedback.
 * 
 * @param {string} text - Text to copy
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Copied to clipboard! 📋', 'success');
    }).catch(() => {
        showNotification('Failed to copy', 'error');
    });
}

// ============================================================
// Page Initialization
// ============================================================

/**
 * Initialize page on DOMContentLoaded.
 * Detects current page and sets up appropriate handlers.
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 ProcrastinaAI Frontend Initialized');
    
    // Restore session from localStorage if it exists
    if (localStorage.getItem('procrastina_ai_session_id')) {
        currentSessionId = localStorage.getItem('procrastina_ai_session_id');
        console.log('✅ Session restored:', currentSessionId);
    }
    
    // Initialize chip selection on setup page
    if (document.querySelector('.chip-group')) {
        initChipSelection();
    }
    
    // Initialize disappearance modal if on disappearance page
    if (document.getElementById('disappearanceModal')) {
        setupDisappearanceModal();
    }
});

/**
 * Setup disappearance modal form handling.
 * Shows/hides custom input based on "other" selection.
 */
function setupDisappearanceModal() {
    const form = document.getElementById('disappearanceForm');
    const otherInput = document.getElementById('otherInput');
    const radios = document.querySelectorAll('input[name="disappearance"]');
    
    if (!form) return;
    
    // Toggle custom input visibility
    radios.forEach(radio => {
        radio.addEventListener('change', function() {
            if (this.value === 'other') {
                otherInput.style.display = 'block';
            } else {
                otherInput.style.display = 'none';
            }
        });
    });
    
    // Handle form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const selectedRadio = document.querySelector('input[name="disappearance"]:checked');
        if (!selectedRadio) return;
        
        const disappearanceType = selectedRadio.value;
        const customLocation = disappearanceType === 'other' ? 
            document.getElementById('otherText').value : null;
        const mood = 'sleepy'; // Get from session if available
        const interests = []; // Get from session if available
        
        const response = await saveDisappearance(disappearanceType, customLocation, mood, interests);
        if (response) {
            displayDisappearanceResponse(response.aiResponse);
        }
    });
}

// ============================================================
// Export Functions (for use in other scripts/modules)
// ============================================================

// Make functions available globally if needed
window.procrastinaAI = {
    createNewSession,
    generateProcrastinationPrediction,
    displayPredictionSteps,
    saveDisappearance,
    displayDisappearanceResponse,
    generateDailyReport,
    displayReportSummary,
    generateFunnyReasons,
    displayFunnyReasons,
    copyToClipboard,
    getSessionId,
    clearSession,
    showNotification,
    apiRequest
};

