/**
 * ProcrastinaAI Frontend Integration Example
 * Shows how to connect HTML/CSS/JavaScript frontend with Node.js backend
 * 
 * Add this to your procrastina_ai/static/procrastina_ai/script.js or create a new file
 */

// ============================================================
// Configuration
// ============================================================

const API_BASE = 'http://localhost:5000/api';

// Store session ID in localStorage
let currentSessionId = localStorage.getItem('procrastina_ai_session_id') || null;

// ============================================================
// Helper Functions
// ============================================================

/**
 * Make API request to backend
 */
async function apiRequest(endpoint, data) {
  try {
    const response = await fetch(`${API_BASE}/${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
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
 * Check if backend is running
 */
async function checkBackendHealth() {
  try {
    const response = await fetch('http://localhost:5000/health');
    const data = await response.json();
    return data.status === 'ok';
  } catch (error) {
    console.error('Backend health check failed:', error);
    return false;
  }
}

// ============================================================
// Session Management
// ============================================================

/**
 * Create a new session (called from setup page)
 * @param {string} mood - User's mood
 * @param {array} interests - Array of selected interests
 * @param {array} tasks - Array of tasks
 */
async function createNewSession(mood, interests, tasks) {
  console.log('Creating new session...', { mood, interests, tasks });
  
  const result = await apiRequest('create-session', {
    mood,
    interests,
    tasks
  });

  if (result.success) {
    currentSessionId = result.data.sessionId;
    localStorage.setItem('procrastina_ai_session_id', currentSessionId);
    console.log('✅ Session created:', currentSessionId);
    return result.data;
  } else {
    console.error('❌ Failed to create session:', result.error);
    return null;
  }
}

/**
 * Get current session ID
 */
function getSessionId() {
  if (!currentSessionId) {
    console.warn('No active session. Create one first.');
  }
  return currentSessionId;
}

/**
 * Clear session
 */
function clearSession() {
  currentSessionId = null;
  localStorage.removeItem('procrastina_ai_session_id');
  console.log('Session cleared');
}

// ============================================================
// Prediction API
// ============================================================

/**
 * Generate procrastination prediction
 * Called from prediction.html page
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
      fullText: result.data.fullText,
      confidence: result.data.confidence
    };
  } else {
    console.error('❌ Prediction failed:', result.error);
    return null;
  }
}

/**
 * Display prediction steps on page
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
 * Save disappearance and get AI response
 * Called from disappearance.html modal
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
    return null;
  }
}

/**
 * Display AI response in modal
 */
function displayAiResponse(response) {
  const responseContainer = document.getElementById('responseContainer');
  const aiResponseCard = responseContainer.querySelector('.ai-response-card');
  
  if (aiResponseCard) {
    aiResponseCard.innerHTML = `
      <div class="response-text">
        <p>${response}</p>
      </div>
      <div class="response-actions">
        <button type="button" class="btn btn-primary btn-large" onclick="askAgain()">
          Ask Again
        </button>
        <button type="button" class="btn btn-secondary btn-large" onclick="backToDashboard()">
          Back to Dashboard
        </button>
      </div>
    `;
  }
}

// ============================================================
// Report API
// ============================================================

/**
 * Generate daily report
 * Called from report.html page
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
    return null;
  }
}

/**
 * Display report summary on page
 */
function displayReportSummary(report) {
  const summaryContainer = document.querySelector('.ai-summary-card');
  if (!summaryContainer) return;

  summaryContainer.innerHTML = `
    <div class="summary-title">📊 Today's Summary</div>
    <div class="summary-text">${report.summary}</div>
    <div class="summary-date">${new Date(report.date).toLocaleDateString()}</div>
  `;
}

// ============================================================
// Funny Reasons API
// ============================================================

/**
 * Generate funny reasons to procrastinate
 * Called from funny_reasons.html page
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
    return null;
  }
}

/**
 * Display funny reasons on page
 */
function displayFunnyReasons(taskName, reasons) {
  const container = document.querySelector('.reason-card');
  if (!container) return;

  const reasonsList = reasons.map(reason => `<li>${reason}</li>`).join('');
  
  const reasonsHtml = `
    <h4>${taskName}</h4>
    <ul class="reason-list">
      ${reasonsList}
    </ul>
  `;
  
  container.innerHTML = reasonsHtml;
}

// ============================================================
// Example: Integration with HTML Event Handlers
// ============================================================

/**
 * Example: Handle setup form submission
 * Attach to setup.html form's submit button
 */
async function handleSetupFormSubmit() {
  const mood = document.querySelector('input[name="mood"]:checked')?.value;
  const interests = Array.from(document.querySelectorAll('input[name="interests"]:checked'))
    .map(el => el.value);
  const tasks = Array.from(document.querySelectorAll('input[name="tasks"]'))
    .map(el => el.value)
    .filter(v => v);

  if (!mood || !interests.length || !tasks.length) {
    alert('Please fill in all fields');
    return;
  }

  const sessionData = await createNewSession(mood, interests, tasks);
  if (sessionData) {
    // Redirect to next page or show success message
    console.log('Session ready, redirect to prediction page');
    window.location.href = '/projects/procrastina-ai/prediction/';
  }
}

/**
 * Example: Handle disappearance modal submission
 */
async function handleDisappearanceSubmit() {
  const disappearanceType = document.querySelector('input[name="disappearance"]:checked')?.value;
  const customLocation = document.getElementById('otherText')?.value;
  const mood = 'Sleepy'; // Get from session data
  const interests = ['YouTube', 'AI']; // Get from session data

  if (!disappearanceType) {
    alert('Please select where you went');
    return;
  }

  const result = await saveDisappearance(disappearanceType, customLocation, mood, interests);
  if (result) {
    displayAiResponse(result.aiResponse);
  }
}

/**
 * Example: Handle generate report button
 */
async function handleGenerateReport() {
  const report = await generateDailyReport(4, 1, 7, 'Researching optimal workflow');
  if (report) {
    displayReportSummary(report);
  }
}

// ============================================================
// Initialization
// ============================================================

/**
 * Initialize frontend on page load
 * Check if backend is available, restore session if exists
 */
document.addEventListener('DOMContentLoaded', async function() {
  console.log('Initializing ProcrastinaAI Frontend...');
  
  const backendHealthy = await checkBackendHealth();
  if (!backendHealthy) {
    console.warn('⚠️  Backend appears to be offline. Some features may not work.');
  } else {
    console.log('✅ Backend is healthy');
  }

  // Restore session if exists
  if (localStorage.getItem('procrastina_ai_session_id')) {
    currentSessionId = localStorage.getItem('procrastina_ai_session_id');
    console.log('Restored session:', currentSessionId);
  }
});

// ============================================================
// Export for use in other scripts
// ============================================================

// Make functions available globally if using as module
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    createNewSession,
    generateProcrastinationPrediction,
    saveDisappearance,
    generateDailyReport,
    generateFunnyReasons,
    getSessionId,
    clearSession,
    apiRequest
  };
}
