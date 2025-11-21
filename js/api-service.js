// API Service for Test Plan Generator
// Handles all communication with AWS Lambda functions via API Gateway

class APIService {
    constructor() {
        this.baseURL = 'https://2xlh113423.execute-api.eu-west-1.amazonaws.com/prod';
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };
    }

    // Generic HTTP request method with error handling
    async request(endpoint, method = 'GET', data = null, additionalHeaders = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const headers = { ...this.defaultHeaders, ...additionalHeaders };
        
        const config = {
            method,
            headers,
            mode: 'cors'
        };

        if (data && method !== 'GET') {
            config.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(url, config);
            
            // Handle different response types
            let responseData;
            const contentType = response.headers.get('content-type');
            
            if (contentType && contentType.includes('application/json')) {
                responseData = await response.json();
            } else {
                responseData = { message: await response.text() };
            }

            // Check if response is successful
            if (!response.ok) {
                // Extract error message from various possible formats
                let errorMessage = `HTTP ${response.status}`;
                
                if (responseData.error) {
                    if (typeof responseData.error === 'string') {
                        errorMessage = responseData.error;
                    } else if (responseData.error.message) {
                        errorMessage = responseData.error.message;
                    } else if (responseData.error.error) {
                        errorMessage = responseData.error.error;
                    } else {
                        errorMessage = JSON.stringify(responseData.error);
                    }
                } else if (responseData.message) {
                    errorMessage = responseData.message;
                }
                
                throw new APIError(
                    errorMessage,
                    response.status,
                    responseData
                );
            }

            return responseData;
        } catch (error) {
            console.error('API Request failed:', error);
            
            if (error instanceof APIError) {
                throw error;
            }

            // Network or other errors
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new APIError('Network error: Please check your internet connection', 0);
            }

            throw new APIError(error.message || 'Unknown error occurred', 0);
        }
    }

    // Test Plans API methods

    /**
     * Get all test plans
     * @param {number} limit - Maximum number of plans to retrieve
     * @param {number} offset - Offset for pagination
     * @returns {Promise<Object>} Plans data
     */
    async getTestPlans(limit = 50, offset = 0) {
        const params = new URLSearchParams({ limit: limit.toString(), offset: offset.toString() });
        const response = await this.request(`/api/plans?${params}`);
        
        // Normalize response format - API returns {test_plans: [...], pagination: {...}}
        if (response.test_plans) {
            return {
                plans: response.test_plans,
                pagination: response.pagination
            };
        }
        
        return response;
    }

    /**
     * Get a specific test plan by ID
     * @param {string} planId - Test plan ID
     * @returns {Promise<Object>} Plan data
     */
    async getTestPlan(planId) {
        const response = await this.request(`/api/plans/${planId}`);
        
        // Normalize test cases format if they exist
        if (response.test_cases && Array.isArray(response.test_cases)) {
            response.test_cases = response.test_cases.map(testCase => ({
                id: testCase.case_id || testCase.id,
                name: testCase.name,
                description: testCase.description,
                priority: testCase.priority,
                preconditions: testCase.preconditions,
                expectedResult: testCase.expected_result || testCase.expectedResult,
                testData: testCase.test_data || testCase.testData,
                steps: testCase.steps || [] // Will need to fetch steps separately if needed
            }));
        }
        
        return response;
    }

    /**
     * Create a new test plan
     * @param {Object} planData - Test plan data
     * @returns {Promise<Object>} Created plan data
     */
    async createTestPlan(planData) {
        const response = await this.request('/api/plans', 'POST', planData);
        
        // Normalize response format - API returns {message: "...", test_plan: {...}}
        if (response.test_plan) {
            return response.test_plan;
        }
        
        return response;
    }

    /**
     * Update an existing test plan
     * @param {string} planId - Test plan ID
     * @param {Object} planData - Updated plan data
     * @returns {Promise<Object>} Updated plan data
     */
    async updateTestPlan(planId, planData) {
        return await this.request(`/api/plans/${planId}`, 'PUT', planData);
    }

    /**
     * Delete a test plan
     * @param {string} planId - Test plan ID
     * @returns {Promise<Object>} Deletion confirmation
     */
    async deleteTestPlan(planId) {
        return await this.request(`/api/plans/${planId}`, 'DELETE');
    }

    // Test Cases API methods

    /**
     * Get test cases for a specific test plan
     * @param {string} planId - Test plan ID
     * @returns {Promise<Object>} Test cases data
     */
    async getTestCases(planId) {
        return await this.request(`/api/plans/${planId}/cases`);
    }

    /**
     * Create a new test case
     * @param {string} planId - Test plan ID
     * @param {Object} caseData - Test case data
     * @returns {Promise<Object>} Created case data
     */
    async createTestCase(planId, caseData) {
        return await this.request(`/api/plans/${planId}/cases`, 'POST', caseData);
    }

    /**
     * Update a test case
     * @param {string} caseId - Test case ID 
     * @param {Object} caseData - Updated case data
     * @returns {Promise<Object>} Updated case data
     */
    async updateTestCase(caseId, caseData) {
        return await this.request(`/api/cases/${caseId}`, 'PUT', caseData);
    }

    /**
     * Delete a test case
     * @param {string} caseId - Test case ID
     * @returns {Promise<Object>} Deletion confirmation
     */
    async deleteTestCase(caseId) {
        return await this.request(`/api/cases/${caseId}`, 'DELETE');
    }

    // Chat API methods

    /**
     * Get chat messages for a test plan
     * @param {string} planId - Test plan ID
     * @returns {Promise<Object>} Chat messages
     */
    async getChatMessages(planId) {
        return await this.request(`/api/plans/${planId}/chat`);
    }

    /**
     * Send a chat message
     * @param {string} planId - Test plan ID
     * @param {string} message - Chat message
     * @returns {Promise<Object>} AI response
     */
    async sendChatMessage(planId, message) {
        return await this.request(`/api/plans/${planId}/chat`, 'POST', { message });
    }

    /**
     * Clear chat history
     * @param {string} planId - Test plan ID
     * @returns {Promise<Object>} Confirmation
     */
    async clearChatHistory(planId) {
        return await this.request(`/api/plans/${planId}/chat`, 'DELETE');
    }

    // AI Generation API methods

    /**
     * Generate a test plan using AI with async polling support
     * @param {Object} requirements - Requirements for AI generation
     * @param {Function} onProgress - Optional callback for progress updates
     * @returns {Promise<Object>} Generated test plan
     */
    async generateTestPlanWithAI(requirements, onProgress = null) {
        // Start async generation
        const startResponse = await this.request('/api/ai/async', 'POST', {
            action: 'generate-plan',
            ...requirements
        });
        
        // If we got a task_id, poll for completion
        if (startResponse.task_id) {
            return await this.pollTaskCompletion(startResponse.task_id, onProgress);
        }
        
        // Fallback: if response is immediate (shouldn't happen for 8-10 cases)
        return startResponse;
    }

    /**
     * Poll for async task completion
     * @param {string} taskId - Task ID to poll
     * @param {Function} onProgress - Optional callback for progress updates
     * @returns {Promise<Object>} Task result
     */
    async pollTaskCompletion(taskId, onProgress = null) {
        const maxAttempts = 90; // 90 attempts * 2 seconds = 3 minutes max
        const pollInterval = 2000; // 2 seconds
        
        for (let attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                // Call progress callback if provided
                if (onProgress) {
                    onProgress({
                        status: 'processing',
                        attempt: attempt,
                        maxAttempts: maxAttempts,
                        message: `Generando casos de prueba... (${attempt}/${maxAttempts})`
                    });
                }
                
                // Check task status
                const statusResponse = await this.request(`/api/ai/async/${taskId}`, 'GET');
                
                // Task completed successfully
                if (statusResponse.status === 'completed') {
                    if (onProgress) {
                        onProgress({
                            status: 'completed',
                            message: '✅ Casos de prueba generados exitosamente'
                        });
                    }
                    return statusResponse.result;
                }
                
                // Task failed
                if (statusResponse.status === 'failed') {
                    throw new APIError(
                        statusResponse.error || 'Task failed',
                        500,
                        statusResponse
                    );
                }
                
                // Task still processing, wait before next poll
                if (statusResponse.status === 'processing') {
                    await this.sleep(pollInterval);
                    continue;
                }
                
                // Unknown status
                throw new APIError(`Unknown task status: ${statusResponse.status}`, 500);
                
            } catch (error) {
                // If it's the last attempt, throw the error
                if (attempt === maxAttempts) {
                    throw new APIError(
                        'Timeout: La generación está tomando más tiempo del esperado. Por favor, intenta con menos casos.',
                        408
                    );
                }
                
                // For other errors, rethrow immediately
                if (error instanceof APIError && error.status !== 0) {
                    throw error;
                }
                
                // Network error, wait and retry
                await this.sleep(pollInterval);
            }
        }
        
        throw new APIError('Timeout: Task did not complete in time', 408);
    }

    /**
     * Sleep utility for polling
     * @param {number} ms - Milliseconds to sleep
     * @returns {Promise<void>}
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Generate test cases for a plan using AI
     * @param {string} planId - Test plan ID
     * @param {Object} requirements - Requirements for test case generation
     * @returns {Promise<Object>} Generated test cases
     */
    async generateTestCasesWithAI(planId, requirements) {
        return await this.request('/api/ai', 'POST', {
            action: 'generate_cases',
            plan_id: planId,
            ...requirements
        });
    }

    /**
     * Chat with AI about a test plan
     * @param {string} planId - Test plan ID
     * @param {string} message - User message
     * @returns {Promise<Object>} AI response
     */
    async chatWithAI(planId, message) {
        return await this.request('/api/ai', 'POST', {
            action: 'chat',
            plan_id: planId,
            message: message
        });
    }

    /**
     * Interactive chat with test cases context
     * @param {Object} context - Full context including test plan, cases, and history
     * @returns {Promise<Object>} Structured AI response with action and data
     */
    async chatWithTestCases(context) {
        return await this.request('/api/chat-agent', 'POST', context);
    }

    /**
     * Improve test cases using AI
     * @param {string} planId - Test plan ID
     * @param {Object} improvementRequest - Improvement requirements
     * @returns {Promise<Object>} Improved test cases
     */
    async improveTestCasesWithAI(planId, improvementRequest) {
        return await this.request('/api/ai', 'POST', {
            action: 'improve_cases',
            plan_id: planId,
            ...improvementRequest
        });
    }

    // Jira Integration API methods

    /**
     * Fetch real Jira issues for a team
     * @param {string} team - Team name (darwin, mulesoft, sap, saplcorp)
     * @param {number} maxResults - Maximum number of issues to fetch (default: 50)
     * @returns {Promise<Object>} Jira issues data
     */
    async fetchJiraIssues(team, maxResults = 50) {
        return await this.request('/api/jira', 'POST', {
            team: team,
            maxResults: maxResults
        });
    }

    // Utility methods

    /**
     * Test API connectivity
     * @returns {Promise<boolean>} Connection status
     */
    async testConnection() {
        try {
            await this.getTestPlans(1);
            return true;
        } catch (error) {
            console.error('API connection test failed:', error);
            return false;
        }
    }

    /**
     * Get API health status
     * @returns {Promise<Object>} Health status
     */
    async getHealthStatus() {
        try {
            return await this.request('/api/health');
        } catch (error) {
            return { status: 'error', message: error.message };
        }
    }
}

// Custom error class for API errors
class APIError extends Error {
    constructor(message, status = 0, response = null) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.response = response;
    }

    // Check if error is a specific type
    isNetworkError() {
        return this.status === 0;
    }

    isServerError() {
        return this.status >= 500;
    }

    isClientError() {
        return this.status >= 400 && this.status < 500;
    }

    isDatabaseError() {
        return this.response && this.response.type === 'DatabaseError';
    }

    isAuthError() {
        return this.status === 401 || this.status === 403;
    }
}

// Create global instance
window.apiService = new APIService();

// Export classes for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { APIService, APIError };
}
