// API Service for Alternate History Engine Backend
const API_BASE_URL = 'https://825c58126580.ngrok-free.app';

/**
 * Generic fetch wrapper with error handling
 */
async function fetchAPI(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                'ngrok-skip-browser-warning': 'true',
                ...options.headers,
            },
            ...options,
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            throw new Error('Cannot connect to backend. Is the server running on port 8000?');
        }
        throw error;
    }
}

// ============================================================================
// PUBLIC ENDPOINTS
// ============================================================================

/**
 * Get paginated timeline events
 * @param {number} skip - Number of items to skip
 * @param {number} limit - Number of items to return (max 100)
 */
export async function getTimeline(skip = 0, limit = 10) {
    return fetchAPI(`/timeline?skip=${skip}&limit=${limit}`);
}

/**
 * Get the most recent timeline event
 */
export async function getLatestEvent() {
    return fetchAPI('/timeline/latest');
}

/**
 * Get a specific day's timeline event
 * @param {number} dayIndex - The day index to retrieve
 */
export async function getEventByDay(dayIndex) {
    return fetchAPI(`/timeline/${dayIndex}`);
}

/**
 * Get paginated subtopics
 * @param {number} skip - Number of items to skip
 * @param {number} limit - Number of items to return (max 100)
 */
export async function getSubtopics(skip = 0, limit = 10) {
    return fetchAPI(`/subtopics?skip=${skip}&limit=${limit}`);
}

/**
 * Get paginated proposals
 * @param {number} skip - Number of items to skip
 * @param {number} limit - Number of items to return (max 100)
 */
export async function getProposals(skip = 0, limit = 10) {
    return fetchAPI(`/proposals?skip=${skip}&limit=${limit}`);
}

/**
 * Get paginated judgements
 * @param {number} skip - Number of items to skip
 * @param {number} limit - Number of items to return (max 100)
 */
export async function getJudgements(skip = 0, limit = 10) {
    return fetchAPI(`/judgements?skip=${skip}&limit=${limit}`);
}

/**
 * Get basic health status
 */
export async function getHealth() {
    return fetchAPI('/health');
}

/**
 * Get scheduler health status
 */
export async function getSchedulerHealth() {
    return fetchAPI('/health/scheduler');
}

// ============================================================================
// ADMIN ENDPOINTS
// ============================================================================

/**
 * Trigger daily simulation
 * @param {string} adminKey - Admin API key
 */
export async function simulateDay(adminKey) {
    return fetchAPI('/admin/simulate/day', {
        method: 'POST',
        headers: {
            'x-admin-key': adminKey,
        },
    });
}

/**
 * Reset the entire simulation (DESTRUCTIVE)
 * @param {string} adminKey - Admin API key
 */
export async function resetSimulation(adminKey) {
    return fetchAPI('/admin/reset', {
        method: 'POST',
        headers: {
            'x-admin-key': adminKey,
        },
    });
}
