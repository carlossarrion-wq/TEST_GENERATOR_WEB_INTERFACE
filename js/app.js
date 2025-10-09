// Test Plan Generator - Main Application Logic

// Global state
let currentTestPlan = null;
let testCases = [];

// Check authentication on page load
document.addEventListener('DOMContentLoaded', function() {
    if (sessionStorage.getItem('user_authenticated') !== 'true') {
        window.location.href = 'login.html';
        return;
    }
    
    initializeApp();
});

// Initialize application
function initializeApp() {
    // Set up slider event listeners
    setupSliders();
    
    // Set up Enter key for chat
    document.getElementById('chat-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendChatMessage();
        }
    });
    
    // Initialize button state
    updateGenerateButtonState();
}

// Update Generate Test Plan button state
function updateGenerateButtonState() {
    const generateBtn = document.querySelector('.btn-primary');
    if (generateBtn) {
        generateBtn.disabled = testCases.length > 0;
    }
}

// Setup slider value updates
function setupSliders() {
    // Coverage slider setup with segments
    const coverageSlider = document.getElementById('coverage');
    const coverageValue = document.getElementById('coverage-value');
    const coverageContainer = coverageSlider.closest('.slider-container');
    
    // Create segments container for coverage slider
    const coverageSegmentsContainer = document.createElement('div');
    coverageSegmentsContainer.className = 'slider-track-segments';
    
    // Create 10 segments for coverage (0-100% in steps of 10)
    for (let i = 0; i < 10; i++) {
        const segment = document.createElement('div');
        segment.className = 'slider-segment';
        segment.dataset.segmentIndex = i;
        coverageSegmentsContainer.appendChild(segment);
    }
    
    // Insert segments before the slider
    coverageSlider.parentNode.insertBefore(coverageSegmentsContainer, coverageSlider);
    
    // Update coverage slider segments
    function updateCoverageSegments() {
        const value = parseInt(coverageSlider.value);
        const activeSegments = Math.floor(value / 10);
        
        coverageValue.textContent = value + '%';
        
        // Update segment states
        const segments = coverageSegmentsContainer.querySelectorAll('.slider-segment');
        segments.forEach((segment, index) => {
            if (index < activeSegments) {
                segment.classList.add('active');
            } else {
                segment.classList.remove('active');
            }
        });
    }
    
    coverageSlider.addEventListener('input', updateCoverageSegments);
    updateCoverageSegments(); // Initialize
    
    // Dual slider setup - Number of Test Cases with segments
    const minCasesSlider = document.getElementById('min-cases');
    const maxCasesSlider = document.getElementById('max-cases');
    const minCasesValue = document.getElementById('min-cases-value');
    const maxCasesValue = document.getElementById('max-cases-value');
    const dualSliderContainer = minCasesSlider.closest('.dual-slider-container');
    
    // Create segments container for dual slider
    const dualSegmentsContainer = document.createElement('div');
    dualSegmentsContainer.className = 'dual-slider-track-segments';
    
    // Create 20 segments for test cases (1-20)
    for (let i = 0; i < 20; i++) {
        const segment = document.createElement('div');
        segment.className = 'dual-slider-segment';
        segment.dataset.segmentIndex = i;
        dualSegmentsContainer.appendChild(segment);
    }
    
    // Insert segments before the first slider
    minCasesSlider.parentNode.insertBefore(dualSegmentsContainer, minCasesSlider);
    
    function updateDualSlider() {
        const min = parseInt(minCasesSlider.value);
        const max = parseInt(maxCasesSlider.value);
        
        // Ensure min doesn't exceed max
        if (min > max) {
            minCasesSlider.value = max;
            minCasesValue.textContent = max;
            return;
        }
        
        // Update values
        minCasesValue.textContent = min;
        maxCasesValue.textContent = max;
        
        // Calculate percentages for value badges
        const minPercent = ((min - 1) / (20 - 1)) * 100;
        const maxPercent = ((max - 1) / (20 - 1)) * 100;
        
        // Update value positions
        minCasesValue.style.left = minPercent + '%';
        maxCasesValue.style.left = maxPercent + '%';
        
        // Update segment states (segments are 0-indexed, values are 1-indexed)
        const segments = dualSegmentsContainer.querySelectorAll('.dual-slider-segment');
        segments.forEach((segment, index) => {
            const segmentValue = index + 1; // Convert to 1-indexed
            if (segmentValue >= min && segmentValue <= max) {
                segment.classList.add('active');
            } else {
                segment.classList.remove('active');
            }
        });
    }
    
    minCasesSlider.addEventListener('input', updateDualSlider);
    maxCasesSlider.addEventListener('input', function() {
        const min = parseInt(minCasesSlider.value);
        const max = parseInt(this.value);
        
        // Ensure max doesn't go below min
        if (max < min) {
            this.value = min;
        }
        updateDualSlider();
    });
    
    // Initialize dual slider
    updateDualSlider();
}

// Update slider value position
function updateSliderPosition(valueElement, slider) {
    const percent = ((slider.value - slider.min) / (slider.max - slider.min)) * 100;
    valueElement.style.left = `calc(${percent}% + (${8 - percent * 0.16}px))`;
}

// Generate unique ID for test plan
function generateTestPlanId() {
    const timestamp = Date.now();
    const random = Math.floor(Math.random() * 10000).toString().padStart(4, '0');
    return `TP-${timestamp}-${random}`;
}

// Generate test plan
async function generateTestPlan() {
    const title = document.getElementById('plan-title').value.trim();
    const requirements = document.getElementById('requirements').value.trim();
    const coverage = document.getElementById('coverage').value;
    const minCases = parseInt(document.getElementById('min-cases').value);
    const maxCases = parseInt(document.getElementById('max-cases').value);
    
    // Validation
    if (!title) {
        alert('Please enter a test plan title');
        return;
    }
    
    if (!requirements) {
        alert('Please enter functional requirements');
        return;
    }
    
    // Generate unique ID for the test plan
    const planId = generateTestPlanId();
    document.getElementById('plan-id').value = planId;
    
    // Show loading state
    const btn = event.target;
    const originalHTML = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<div class="loading-spinner"></div> Generating test plan...';
    
    // Simulate AI generation (in real app, this would call Lambda function)
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Generate mock test cases
    testCases = generateMockTestCases(requirements, minCases, maxCases);
    
    // Get reference if it exists
    const reference = document.getElementById('plan-reference').value.trim();
    
    currentTestPlan = {
        id: planId,
        title: title,
        reference: reference || '',
        requirements: requirements,
        coverage: coverage,
        minCases: minCases,
        maxCases: maxCases,
        testCases: testCases,
        createdAt: new Date().toISOString()
    };
    
    // Display results
    displayTestCases();
    
    // Show results, chat, and actions sections
    document.getElementById('results-section').style.display = 'block';
    document.getElementById('chat-section').style.display = 'block';
    document.getElementById('actions-section').style.display = 'block';
    
    // Scroll to results
    document.getElementById('results-section').scrollIntoView({ behavior: 'smooth' });
    
    // Reset button
    btn.disabled = false;
    btn.innerHTML = originalHTML;
    
    // Update button state (disable since we now have test cases)
    updateGenerateButtonState();
}

// Generate mock test cases (simulates AI generation)
function generateMockTestCases(requirements, minCases, maxCases) {
    const numCases = Math.floor(Math.random() * (maxCases - minCases + 1)) + minCases;
    const cases = [];
    
    const priorities = ['High', 'Medium', 'Low'];
    const reqLines = requirements.split('\n').filter(line => line.trim());
    
    for (let i = 0; i < numCases; i++) {
        const priority = priorities[Math.floor(Math.random() * priorities.length)];
        const reqIndex = i % reqLines.length;
        const requirement = reqLines[reqIndex] || 'General functionality';
        
        cases.push({
            id: `TC-${String(i + 1).padStart(3, '0')}`,
            name: `Test Case ${i + 1}: ${requirement.substring(0, 50).replace(/^[-•*]\s*/, '')}`,
            description: `Verify that ${requirement.toLowerCase().replace(/^[-•*]\s*/, '')}`,
            priority: priority,
            preconditions: 'System is accessible and user has valid credentials',
            expectedResult: 'The functionality works as expected without errors',
            testData: 'Valid test data as per requirements',
            steps: generateTestSteps(i + 1)
        });
    }
    
    return cases;
}

// Generate test steps for a test case
function generateTestSteps(caseNumber) {
    const numSteps = Math.floor(Math.random() * 4) + 3; // 3-6 steps
    const steps = [];
    
    const stepTemplates = [
        'Navigate to the application',
        'Enter valid credentials',
        'Click on the submit button',
        'Verify the response message',
        'Check that data is saved correctly',
        'Validate the UI elements are displayed',
        'Confirm the expected behavior occurs'
    ];
    
    for (let i = 0; i < numSteps && i < stepTemplates.length; i++) {
        steps.push({
            number: i + 1,
            description: stepTemplates[i]
        });
    }
    
    return steps;
}

// Display test cases in table
function displayTestCases() {
    const tbody = document.getElementById('test-cases-tbody');
    tbody.innerHTML = '';
    
    testCases.forEach(testCase => {
        const row = document.createElement('tr');
        row.style.cursor = 'pointer';
        row.onclick = function(e) {
            // Don't trigger row click if clicking on action buttons
            if (!e.target.closest('.btn-icon')) {
                editTestCase(testCase.id);
            }
        };
        row.innerHTML = `
            <td><strong>${testCase.id}</strong></td>
            <td>${testCase.name}</td>
            <td>${testCase.description}</td>
            <td><span class="priority-badge priority-${testCase.priority.toLowerCase()}">${testCase.priority}</span></td>
            <td>${testCase.preconditions}</td>
            <td>${testCase.expectedResult}</td>
            <td>
                <div style="display: flex; gap: 0.5rem; justify-content: center;">
                    <button class="btn-icon btn-icon-view" onclick="event.stopPropagation(); viewTestSteps('${testCase.id}')" title="View Steps">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" style="width: 18px; height: 18px;">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                            <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                    </button>
                    <button class="btn-icon btn-icon-edit" onclick="event.stopPropagation(); editTestCase('${testCase.id}')" title="Edit Test Case">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" style="width: 18px; height: 18px;">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
                        </svg>
                    </button>
                    <button class="btn-icon btn-icon-delete" onclick="event.stopPropagation(); deleteTestCase('${testCase.id}')" title="Delete Test Case">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" style="width: 18px; height: 18px;">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                        </svg>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// View test steps in modal
function viewTestSteps(testCaseId) {
    const testCase = testCases.find(tc => tc.id === testCaseId);
    if (!testCase) return;
    
    const modal = document.getElementById('test-case-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');
    
    modalTitle.textContent = `${testCase.id}: ${testCase.name}`;
    
    let stepsHTML = `
        <div style="margin-bottom: 1.5rem;">
            <h4 style="color: #2d3748; margin-bottom: 0.5rem;">Description</h4>
            <p style="color: #4a5568;">${testCase.description}</p>
        </div>
        
        <div style="margin-bottom: 1.5rem;">
            <h4 style="color: #2d3748; margin-bottom: 0.5rem;">Preconditions</h4>
            <p style="color: #4a5568;">${testCase.preconditions}</p>
        </div>
        
        <div style="margin-bottom: 1.5rem;">
            <h4 style="color: #2d3748; margin-bottom: 0.5rem;">Test Data</h4>
            <p style="color: #4a5568;">${testCase.testData}</p>
        </div>
        
        <div style="margin-bottom: 1.5rem;">
            <h4 style="color: #2d3748; margin-bottom: 1rem;">Test Steps</h4>
    `;
    
    testCase.steps.forEach(step => {
        stepsHTML += `
            <div class="test-step">
                <div class="test-step-number">Step ${step.number}</div>
                <div class="test-step-description">${step.description}</div>
            </div>
        `;
    });
    
    stepsHTML += `
        </div>
        
        <div>
            <h4 style="color: #2d3748; margin-bottom: 0.5rem;">Expected Result</h4>
            <p style="color: #4a5568;">${testCase.expectedResult}</p>
        </div>
    `;
    
    modalBody.innerHTML = stepsHTML;
    modal.classList.add('show');
}

// Close modal
function closeModal() {
    const modal = document.getElementById('test-case-modal');
    modal.classList.remove('show');
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('test-case-modal');
    if (event.target === modal) {
        closeModal();
    }
}

// Send chat message
async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addChatMessage(message, 'user');
    
    // Clear input
    input.value = '';
    
    // Show loading
    const chatMessages = document.getElementById('chat-messages');
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'chat-message assistant';
    loadingDiv.id = 'loading-message';
    loadingDiv.innerHTML = `
        <div class="message-avatar">AI</div>
        <div class="message-content">
            <div class="loading-spinner"></div> Processing your request...
        </div>
    `;
    chatMessages.appendChild(loadingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Simulate AI response (in real app, this would call Lambda function)
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // Remove loading message
    loadingDiv.remove();
    
    // Generate response based on message
    let response = generateChatResponse(message);
    
    // Add AI response
    addChatMessage(response, 'assistant');
}

// Generate chat response (simulates AI)
function generateChatResponse(userMessage) {
    const lowerMessage = userMessage.toLowerCase();
    
    if (lowerMessage.includes('add') || lowerMessage.includes('include')) {
        return 'I can help you add more test cases. Based on your request, I would suggest adding test cases for edge cases and boundary conditions. Would you like me to generate specific test cases for error handling and validation scenarios?';
    } else if (lowerMessage.includes('remove') || lowerMessage.includes('delete')) {
        return 'I can help you remove redundant test cases. Please specify which test cases you\'d like to remove, or I can analyze the current plan and suggest which ones might be redundant.';
    } else if (lowerMessage.includes('modify') || lowerMessage.includes('change')) {
        return 'I can help you modify existing test cases. Please specify which test case you\'d like to modify and what changes you\'d like to make.';
    } else if (lowerMessage.includes('security') || lowerMessage.includes('performance')) {
        return 'Great idea! I can add specialized test cases for security and performance testing. These would include tests for authentication, authorization, data validation, load testing, and response time verification. Would you like me to generate these?';
    } else {
        return 'I understand you want to refine the test plan. I can help you with:\n\n• Adding new test cases for specific scenarios\n• Removing redundant or unnecessary test cases\n• Modifying existing test cases\n• Adding security or performance test cases\n• Reorganizing test cases by priority\n\nPlease let me know what specific changes you\'d like to make.';
    }
}

// Add message to chat
function addChatMessage(message, type) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${type}`;
    
    const avatar = type === 'user' ? sessionStorage.getItem('username').charAt(0).toUpperCase() : 'AI';
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            <p>${message.replace(/\n/g, '<br>')}</p>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Save test plan
function saveTestPlan() {
    if (!currentTestPlan) {
        alert('No test plan to save');
        return;
    }
    
    // Get chat history
    const chatMessages = document.getElementById('chat-messages');
    const chatHistory = [];
    chatMessages.querySelectorAll('.chat-message').forEach(msg => {
        const isAssistant = msg.classList.contains('assistant');
        const content = msg.querySelector('.message-content p').innerHTML.replace(/<br>/g, '\n');
        chatHistory.push({
            type: isAssistant ? 'assistant' : 'user',
            content: content
        });
    });
    
    // Add chat history to current test plan
    currentTestPlan.chatHistory = chatHistory;
    currentTestPlan.lastModified = new Date().toISOString();
    
    // Save to localStorage
    const savedPlans = JSON.parse(localStorage.getItem('savedTestPlans') || '[]');
    savedPlans.push(currentTestPlan);
    localStorage.setItem('savedTestPlans', JSON.stringify(savedPlans));
    
    alert('Test plan saved successfully!');
}

// Export to CSV
function exportToCSV() {
    if (!testCases.length) {
        alert('No test cases to export');
        return;
    }
    
    let csv = 'ID,Name,Description,Priority,Preconditions,Expected Result,Test Data,Steps\n';
    
    testCases.forEach(tc => {
        const steps = tc.steps.map(s => `Step ${s.number}: ${s.description}`).join('; ');
        csv += `"${tc.id}","${tc.name}","${tc.description}","${tc.priority}","${tc.preconditions}","${tc.expectedResult}","${tc.testData}","${steps}"\n`;
    });
    
    downloadFile(csv, `test-plan-${currentTestPlan.title.replace(/\s+/g, '-')}.csv`, 'text/csv');
}

// Export to JSON
function exportToJSON() {
    if (!currentTestPlan) {
        alert('No test plan to export');
        return;
    }
    
    const json = JSON.stringify(currentTestPlan, null, 2);
    downloadFile(json, `test-plan-${currentTestPlan.title.replace(/\s+/g, '-')}.json`, 'application/json');
}

// Export to Gherkin (BDD)
function exportToGherkin() {
    if (!testCases.length) {
        alert('No test cases to export');
        return;
    }
    
    let gherkin = `Feature: ${currentTestPlan.title}\n\n`;
    gherkin += `  Background:\n`;
    gherkin += `    Given the system is accessible\n`;
    gherkin += `    And the user has valid credentials\n\n`;
    
    testCases.forEach(tc => {
        gherkin += `  Scenario: ${tc.name}\n`;
        gherkin += `    # Priority: ${tc.priority}\n`;
        gherkin += `    # ${tc.description}\n`;
        
        tc.steps.forEach(step => {
            const keyword = step.number === 1 ? 'Given' : 
                           step.number === tc.steps.length ? 'Then' : 'And';
            gherkin += `    ${keyword} ${step.description.toLowerCase()}\n`;
        });
        
        gherkin += `\n`;
    });
    
    downloadFile(gherkin, `test-plan-${currentTestPlan.title.replace(/\s+/g, '-')}.feature`, 'text/plain');
}

// Download file helper
function downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

// Discard test plan
function discardTestPlan() {
    if (!confirm('Are you sure you want to discard this test plan? This action cannot be undone.')) {
        return;
    }
    
    newTestPlan();
}

// Start new test plan
function newTestPlan() {
    // Reset form
    document.getElementById('plan-title').value = '';
    document.getElementById('plan-id').value = '';
    document.getElementById('plan-reference').value = '';
    document.getElementById('requirements').value = '';
    document.getElementById('coverage').value = 80;
    document.getElementById('coverage-value').textContent = '80%';
    document.getElementById('min-cases').value = 5;
    document.getElementById('min-cases-value').textContent = '5';
    document.getElementById('max-cases').value = 20;
    document.getElementById('max-cases-value').textContent = '20';
    
    // Hide results sections
    document.getElementById('results-section').style.display = 'none';
    document.getElementById('chat-section').style.display = 'none';
    document.getElementById('actions-section').style.display = 'none';
    
    // Reset state
    currentTestPlan = null;
    testCases = [];
    
    // Reset chat
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML = `
        <div class="chat-message assistant">
            <div class="message-avatar">AI</div>
            <div class="message-content">
                <p>Test plan generated successfully! You can now refine it by asking me to:</p>
                <ul>
                    <li>Add specific test cases for edge cases</li>
                    <li>Include negative testing scenarios</li>
                    <li>Add performance or security test cases</li>
                    <li>Modify existing test cases</li>
                    <li>Remove redundant test cases</li>
                </ul>
                <p>What would you like to adjust?</p>
            </div>
        </div>
    `;
    
    // Update button state (enable since testCases is now empty)
    updateGenerateButtonState();
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Edit test case
function editTestCase(testCaseId) {
    const testCase = testCases.find(tc => tc.id === testCaseId);
    if (!testCase) return;
    
    const modal = document.getElementById('edit-test-case-modal');
    const modalTitle = document.getElementById('edit-modal-title');
    const modalBody = document.getElementById('edit-modal-body');
    
    modalTitle.textContent = `Edit ${testCase.id}`;
    
    // Build steps HTML for editing
    let stepsHTML = '';
    testCase.steps.forEach((step, index) => {
        stepsHTML += `
            <div class="edit-step-row" style="display: flex; gap: 0.5rem; margin-bottom: 0.5rem;">
                <input type="text" class="form-control" value="Step ${step.number}" readonly style="width: 100px;">
                <input type="text" class="form-control step-description" data-step-index="${index}" value="${step.description}" style="flex: 1;">
            </div>
        `;
    });
    
    modalBody.innerHTML = `
        <div class="form-group" style="margin-bottom: 1rem;">
            <label for="edit-name">Test Case Name</label>
            <input type="text" id="edit-name" class="form-control" value="${testCase.name}">
        </div>
        
        <div class="form-group" style="margin-bottom: 1rem;">
            <label for="edit-description">Description</label>
            <textarea id="edit-description" class="form-control" rows="2">${testCase.description}</textarea>
        </div>
        
        <div class="form-group" style="margin-bottom: 1rem;">
            <label for="edit-priority">Priority</label>
            <select id="edit-priority" class="form-control">
                <option value="High" ${testCase.priority === 'High' ? 'selected' : ''}>High</option>
                <option value="Medium" ${testCase.priority === 'Medium' ? 'selected' : ''}>Medium</option>
                <option value="Low" ${testCase.priority === 'Low' ? 'selected' : ''}>Low</option>
            </select>
        </div>
        
        <div class="form-group" style="margin-bottom: 1rem;">
            <label for="edit-preconditions">Preconditions</label>
            <textarea id="edit-preconditions" class="form-control" rows="2">${testCase.preconditions}</textarea>
        </div>
        
        <div class="form-group" style="margin-bottom: 1rem;">
            <label for="edit-test-data">Test Data</label>
            <textarea id="edit-test-data" class="form-control" rows="2">${testCase.testData}</textarea>
        </div>
        
        <div class="form-group" style="margin-bottom: 1rem;">
            <label>Test Steps</label>
            <div id="edit-steps-container">
                ${stepsHTML}
            </div>
        </div>
        
        <div class="form-group" style="margin-bottom: 1rem;">
            <label for="edit-expected-result">Expected Result</label>
            <textarea id="edit-expected-result" class="form-control" rows="2">${testCase.expectedResult}</textarea>
        </div>
        
        <div style="display: flex; gap: 1rem; justify-content: flex-end; margin-top: 1.5rem;">
            <button class="btn-cancel" onclick="closeEditModal()">Cancel</button>
            <button class="btn-save" onclick="saveTestCaseEdit('${testCaseId}')">Save Changes</button>
        </div>
    `;
    
    modal.classList.add('show');
}

// Save test case edits
function saveTestCaseEdit(testCaseId) {
    const testCase = testCases.find(tc => tc.id === testCaseId);
    if (!testCase) return;
    
    // Get updated values
    testCase.name = document.getElementById('edit-name').value;
    testCase.description = document.getElementById('edit-description').value;
    testCase.priority = document.getElementById('edit-priority').value;
    testCase.preconditions = document.getElementById('edit-preconditions').value;
    testCase.testData = document.getElementById('edit-test-data').value;
    testCase.expectedResult = document.getElementById('edit-expected-result').value;
    
    // Update steps
    const stepDescriptions = document.querySelectorAll('.step-description');
    stepDescriptions.forEach((input, index) => {
        if (testCase.steps[index]) {
            testCase.steps[index].description = input.value;
        }
    });
    
    // Update the display
    displayTestCases();
    
    // Close modal
    closeEditModal();
    
    // Show success message
    alert('Test case updated successfully!');
}

// Close edit modal
function closeEditModal() {
    const modal = document.getElementById('edit-test-case-modal');
    modal.classList.remove('show');
}

// Delete test case
function deleteTestCase(testCaseId) {
    const testCase = testCases.find(tc => tc.id === testCaseId);
    if (!testCase) return;
    
    if (!confirm(`Are you sure you want to delete ${testCase.id}?\n\nThis action cannot be undone.`)) {
        return;
    }
    
    // Remove from array
    const index = testCases.findIndex(tc => tc.id === testCaseId);
    if (index > -1) {
        testCases.splice(index, 1);
    }
    
    // Update display
    displayTestCases();
}

// Delete all test cases
function deleteAllTestCases() {
    if (testCases.length === 0) {
        alert('No test cases to delete');
        return;
    }
    
    const numCases = testCases.length;
    
    if (!confirm(`Are you sure you want to delete ALL ${numCases} test cases?\n\nThis action cannot be undone.`)) {
        return;
    }
    
    // Clear the test cases array
    testCases = [];
    
    // Update the display
    displayTestCases();
    
    // Update Generate button state (enable it since testCases is now empty)
    updateGenerateButtonState();
}

// Jira Import functionality
let selectedJiraIssue = null;
let allJiraIssues = [];
let filteredJiraIssues = [];
let displayedJiraIssues = [];
let currentJiraPage = 0;
const ISSUES_PER_PAGE = 20;

// Open Jira Import Modal
async function openJiraImportModal() {
    const modal = document.getElementById('jira-import-modal');
    const issuesList = document.getElementById('jira-issues-list');
    
    // Reset filters
    document.getElementById('jira-search').value = '';
    document.getElementById('jira-type-filter').value = '';
    document.getElementById('jira-status-filter').value = '';
    document.getElementById('jira-priority-filter').value = '';
    document.getElementById('jira-assignee-filter').value = '';
    
    // Reset pagination
    currentJiraPage = 0;
    displayedJiraIssues = [];
    
    // Show loading
    issuesList.innerHTML = '<div class="jira-loading"><div class="loading-spinner"></div><p style="margin-top: 1rem;">Loading Jira issues...</p></div>';
    
    modal.classList.add('show');
    
    // Simulate fetching Jira issues (in real app, this would call Lambda/Jira API)
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Generate mock Jira issues
    allJiraIssues = generateMockJiraIssues();
    filteredJiraIssues = [...allJiraIssues];
    
    // Populate assignee filter
    populateAssigneeFilter();
    
    // Display first page of issues
    loadMoreJiraIssues();
}

// Generate comprehensive mock Jira issues
function generateMockJiraIssues() {
    const assignees = ['John Doe', 'Jane Smith', 'Mike Johnson', 'Sarah Williams', 'Unassigned'];
    const statuses = ['To Do', 'In Progress', 'Done', 'Blocked'];
    const priorities = ['High', 'Medium', 'Low'];
    
    return [
        {
            key: 'PROJ-1234',
            type: 'story',
            summary: 'Implement user authentication system',
            description: 'As a user, I want to be able to log in securely so that I can access my account.\n\nAcceptance Criteria:\n- Users can log in with email and password\n- System validates email format\n- Password must be at least 8 characters\n- Failed login attempts are tracked\n- Account locks after 5 failed attempts',
            status: 'In Progress',
            priority: 'High',
            assignee: 'John Doe'
        },
        {
            key: 'PROJ-1235',
            type: 'bug',
            summary: 'Login form validation not working correctly',
            description: 'The login form is not properly validating email addresses. Users can submit invalid email formats.\n\nSteps to reproduce:\n1. Navigate to login page\n2. Enter invalid email (e.g., "test@")\n3. Click submit\n4. Form submits without validation error\n\nExpected: Validation error should be displayed\nActual: Form submits successfully',
            status: 'To Do',
            priority: 'High',
            assignee: 'Jane Smith'
        },
        {
            key: 'PROJ-1236',
            type: 'task',
            summary: 'Add password reset functionality',
            description: 'Implement password reset feature that allows users to reset their password via email.\n\nRequirements:\n- User can request password reset\n- System sends reset link via email\n- Reset link expires after 24 hours\n- User can set new password using the link\n- Old password is invalidated after reset',
            status: 'To Do',
            priority: 'Medium',
            assignee: 'Mike Johnson'
        },
        {
            key: 'PROJ-1237',
            type: 'story',
            summary: 'Implement two-factor authentication',
            description: 'As a security-conscious user, I want to enable two-factor authentication so that my account is more secure.\n\nAcceptance Criteria:\n- Users can enable 2FA in settings\n- Support for authenticator apps (Google Authenticator, Authy)\n- Backup codes provided during setup\n- Option to disable 2FA\n- 2FA required for sensitive operations',
            status: 'In Progress',
            priority: 'High',
            assignee: 'Sarah Williams'
        },
        {
            key: 'PROJ-1238',
            type: 'task',
            summary: 'Update user profile management',
            description: 'Allow users to update their profile information including name, email, and profile picture.\n\nRequirements:\n- Form to edit profile information\n- Email change requires verification\n- Profile picture upload with size limits (max 5MB)\n- Changes are saved immediately\n- Audit log for profile changes',
            status: 'Done',
            priority: 'Low',
            assignee: 'John Doe'
        },
        {
            key: 'PROJ-1239',
            type: 'epic',
            summary: 'User Management System Overhaul',
            description: 'Complete redesign of the user management system to improve security, usability, and scalability.\n\nScope:\n- Authentication improvements\n- Profile management\n- Role-based access control\n- Audit logging\n- User activity tracking',
            status: 'In Progress',
            priority: 'High',
            assignee: 'Unassigned'
        },
        {
            key: 'PROJ-1240',
            type: 'bug',
            summary: 'Session timeout not working properly',
            description: 'Users are not being logged out after the configured session timeout period.\n\nSteps to reproduce:\n1. Log in to the application\n2. Wait for session timeout period (30 minutes)\n3. Try to perform an action\n\nExpected: User should be logged out\nActual: User session remains active',
            status: 'Blocked',
            priority: 'High',
            assignee: 'Jane Smith'
        },
        {
            key: 'PROJ-1241',
            type: 'story',
            summary: 'Add social media login options',
            description: 'As a user, I want to log in using my social media accounts so that I don\'t have to remember another password.\n\nAcceptance Criteria:\n- Support Google OAuth\n- Support Facebook login\n- Support GitHub login\n- Link social accounts to existing accounts\n- Unlink social accounts option',
            status: 'To Do',
            priority: 'Medium',
            assignee: 'Mike Johnson'
        },
        {
            key: 'PROJ-1242',
            type: 'task',
            summary: 'Implement email verification for new users',
            description: 'Add email verification step during user registration.\n\nRequirements:\n- Send verification email upon registration\n- Verification link expires after 48 hours\n- Resend verification email option\n- Account activation upon verification\n- Clear error messages for expired links',
            status: 'In Progress',
            priority: 'Medium',
            assignee: 'Sarah Williams'
        },
        {
            key: 'PROJ-1243',
            type: 'bug',
            summary: 'Password strength indicator not displaying',
            description: 'The password strength indicator on the registration form is not showing up.\n\nSteps to reproduce:\n1. Navigate to registration page\n2. Start typing in password field\n3. Observe password strength indicator\n\nExpected: Indicator should show password strength\nActual: No indicator is displayed',
            status: 'To Do',
            priority: 'Low',
            assignee: 'Unassigned'
        },
        {
            key: 'PROJ-1244',
            type: 'story',
            summary: 'Implement role-based access control',
            description: 'As an administrator, I want to assign different roles to users so that I can control access to features.\n\nAcceptance Criteria:\n- Define user roles (Admin, Manager, User)\n- Assign permissions to roles\n- Users can have multiple roles\n- Role changes take effect immediately\n- Audit log for role changes',
            status: 'To Do',
            priority: 'High',
            assignee: 'John Doe'
        },
        {
            key: 'PROJ-1245',
            type: 'task',
            summary: 'Add user activity logging',
            description: 'Implement comprehensive logging of user activities for security and audit purposes.\n\nRequirements:\n- Log all login attempts\n- Log profile changes\n- Log permission changes\n- Log data access\n- Retention policy for logs (90 days)',
            status: 'Done',
            priority: 'Medium',
            assignee: 'Jane Smith'
        },
        {
            key: 'PROJ-1246',
            type: 'bug',
            summary: 'Remember me checkbox not persisting',
            description: 'The "Remember me" checkbox on login form is not keeping users logged in.\n\nSteps to reproduce:\n1. Check "Remember me" checkbox\n2. Log in successfully\n3. Close browser\n4. Reopen browser and navigate to site\n\nExpected: User should still be logged in\nActual: User has to log in again',
            status: 'In Progress',
            priority: 'Medium',
            assignee: 'Mike Johnson'
        },
        {
            key: 'PROJ-1247',
            type: 'story',
            summary: 'Add account deletion functionality',
            description: 'As a user, I want to be able to delete my account so that my data is removed from the system.\n\nAcceptance Criteria:\n- User can request account deletion\n- Confirmation email sent before deletion\n- Grace period of 30 days before permanent deletion\n- All user data is removed\n- Compliance with GDPR requirements',
            status: 'To Do',
            priority: 'Low',
            assignee: 'Sarah Williams'
        },
        {
            key: 'PROJ-1248',
            type: 'task',
            summary: 'Implement password complexity requirements',
            description: 'Add configurable password complexity requirements.\n\nRequirements:\n- Minimum length (8-20 characters)\n- Require uppercase letters\n- Require lowercase letters\n- Require numbers\n- Require special characters\n- Password history (prevent reuse of last 5 passwords)',
            status: 'Done',
            priority: 'High',
            assignee: 'John Doe'
        }
    ];
}

// Populate assignee filter dropdown
function populateAssigneeFilter() {
    const assigneeFilter = document.getElementById('jira-assignee-filter');
    const uniqueAssignees = [...new Set(allJiraIssues.map(issue => issue.assignee))].sort();
    
    // Clear existing options except "All Assignees"
    assigneeFilter.innerHTML = '<option value="">All Assignees</option>';
    
    // Add unique assignees
    uniqueAssignees.forEach(assignee => {
        const option = document.createElement('option');
        option.value = assignee;
        option.textContent = assignee;
        assigneeFilter.appendChild(option);
    });
}

// Filter Jira issues based on all filters
function filterJiraIssues() {
    const searchText = document.getElementById('jira-search').value.toLowerCase();
    const typeFilter = document.getElementById('jira-type-filter').value.toLowerCase();
    const statusFilter = document.getElementById('jira-status-filter').value;
    const priorityFilter = document.getElementById('jira-priority-filter').value;
    const assigneeFilter = document.getElementById('jira-assignee-filter').value;
    
    filteredJiraIssues = allJiraIssues.filter(issue => {
        // Filter by type
        if (typeFilter && issue.type !== typeFilter) return false;
        
        // Filter by status
        if (statusFilter && issue.status !== statusFilter) return false;
        
        // Filter by priority
        if (priorityFilter && issue.priority !== priorityFilter) return false;
        
        // Filter by assignee
        if (assigneeFilter && issue.assignee !== assigneeFilter) return false;
        
        // Filter by search text (ID, title, or description)
        if (searchText) {
            const matchesSearch = 
                issue.key.toLowerCase().includes(searchText) ||
                issue.summary.toLowerCase().includes(searchText) ||
                issue.description.toLowerCase().includes(searchText);
            if (!matchesSearch) return false;
        }
        
        return true;
    });
    
    // Reset pagination and display
    currentJiraPage = 0;
    displayedJiraIssues = [];
    loadMoreJiraIssues();
}

// Clear all Jira filters
function clearJiraFilters() {
    document.getElementById('jira-search').value = '';
    document.getElementById('jira-type-filter').value = '';
    document.getElementById('jira-status-filter').value = '';
    document.getElementById('jira-priority-filter').value = '';
    document.getElementById('jira-assignee-filter').value = '';
    
    filterJiraIssues();
}

// Load more Jira issues (pagination)
function loadMoreJiraIssues() {
    const startIndex = currentJiraPage * ISSUES_PER_PAGE;
    const endIndex = startIndex + ISSUES_PER_PAGE;
    const newIssues = filteredJiraIssues.slice(startIndex, endIndex);
    
    displayedJiraIssues = displayedJiraIssues.concat(newIssues);
    currentJiraPage++;
    
    // Display issues
    displayJiraIssues();
    
    // Update results info
    updateJiraResultsInfo();
    
    // Show/hide Load More button
    const loadMoreContainer = document.getElementById('jira-load-more-container');
    if (endIndex >= filteredJiraIssues.length) {
        loadMoreContainer.style.display = 'none';
    } else {
        loadMoreContainer.style.display = 'flex';
    }
}

// Update results info
function updateJiraResultsInfo() {
    document.getElementById('jira-showing-count').textContent = displayedJiraIssues.length;
    document.getElementById('jira-total-count').textContent = filteredJiraIssues.length;
}

// Display Jira issues in modal
function displayJiraIssues() {
    const issuesList = document.getElementById('jira-issues-list');
    
    if (filteredJiraIssues.length === 0) {
        issuesList.innerHTML = `
            <div class="jira-empty-state">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
                </svg>
                <h4>No issues found</h4>
                <p>Try adjusting your filters or search criteria</p>
            </div>
        `;
        return;
    }
    
    issuesList.innerHTML = displayedJiraIssues.map(issue => {
        const statusClass = issue.status.toLowerCase().replace(/\s+/g, '-');
        const priorityClass = issue.priority.toLowerCase();
        const assigneeInitials = issue.assignee === 'Unassigned' ? 'U' : issue.assignee.split(' ').map(n => n[0]).join('');
        
        return `
            <div class="jira-issue-item" onclick="selectJiraIssue('${issue.key}')">
                <div class="jira-issue-tooltip">
                    <div class="jira-issue-tooltip-title">${issue.key}: ${issue.summary}</div>
                    <div class="jira-issue-tooltip-description">${issue.description}</div>
                </div>
                <div class="jira-issue-header">
                    <span class="jira-issue-key">${issue.key}</span>
                    <span class="jira-issue-type ${issue.type}">${issue.type}</span>
                </div>
                <div class="jira-issue-summary">${issue.summary}</div>
                <div class="jira-issue-description">${issue.description}</div>
                <div class="jira-issue-meta">
                    <span class="jira-issue-status ${statusClass}">${issue.status}</span>
                    <span class="jira-issue-priority ${priorityClass}">${issue.priority}</span>
                    <div class="jira-issue-assignee">
                        <div class="jira-issue-avatar">${assigneeInitials}</div>
                        <span>${issue.assignee}</span>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    // Add event listeners for tooltip positioning
    setTimeout(() => {
        const issueItems = issuesList.querySelectorAll('.jira-issue-item');
        issueItems.forEach(item => {
            const tooltip = item.querySelector('.jira-issue-tooltip');
            
            item.addEventListener('mouseenter', function() {
                positionTooltip(item, tooltip);
            });
            
            item.addEventListener('mousemove', function() {
                positionTooltip(item, tooltip);
            });
        });
    }, 0);
}

// Position tooltip using fixed positioning
function positionTooltip(item, tooltip) {
    const rect = item.getBoundingClientRect();
    const tooltipRect = tooltip.getBoundingClientRect();
    
    // Calculate position above the item
    const left = rect.left + (rect.width / 2);
    const top = rect.top - 16; // 16px above the item
    
    // Set position
    tooltip.style.left = left + 'px';
    tooltip.style.top = top + 'px';
    tooltip.style.transform = 'translateX(-50%) translateY(-100%)';
    
    // Check if tooltip goes off screen and adjust if needed
    const tooltipWidth = tooltipRect.width || 400; // Use actual width or max-width
    const viewportWidth = window.innerWidth;
    
    // Adjust horizontal position if tooltip goes off screen
    if (left - tooltipWidth / 2 < 10) {
        // Too far left
        tooltip.style.left = '10px';
        tooltip.style.transform = 'translateY(-100%)';
    } else if (left + tooltipWidth / 2 > viewportWidth - 10) {
        // Too far right
        tooltip.style.left = (viewportWidth - 10) + 'px';
        tooltip.style.transform = 'translateX(-100%) translateY(-100%)';
    }
    
    // Adjust vertical position if tooltip goes off top of screen
    if (top - tooltipRect.height < 10) {
        // Show below instead
        tooltip.style.top = (rect.bottom + 16) + 'px';
        tooltip.style.transform = tooltip.style.transform.replace('translateY(-100%)', 'translateY(0)');
        
        // Flip arrow direction (would need CSS adjustment)
        tooltip.classList.add('tooltip-below');
    } else {
        tooltip.classList.remove('tooltip-below');
    }
}

// Select a Jira issue
function selectJiraIssue(issueKey) {
    // Remove previous selection
    document.querySelectorAll('.jira-issue-item').forEach(item => {
        item.classList.remove('selected');
    });
    
    // Add selection to clicked item
    event.target.closest('.jira-issue-item').classList.add('selected');
    
    // Store selected issue
    selectedJiraIssue = allJiraIssues.find(issue => issue.key === issueKey);
    
    // Enable import button
    document.getElementById('import-jira-btn').disabled = false;
}

// Import selected Jira issue
function importSelectedJiraIssue() {
    if (!selectedJiraIssue) {
        alert('Please select a Jira issue first');
        return;
    }
    
    // Populate form fields
    document.getElementById('plan-title').value = `Test Plan: ${selectedJiraIssue.summary}`;
    document.getElementById('plan-reference').value = selectedJiraIssue.key;
    document.getElementById('requirements').value = selectedJiraIssue.description;
    
    // Close modal
    closeJiraImportModal();
    
    // Show success message
    alert(`Successfully imported Jira issue ${selectedJiraIssue.key}`);
    
    // Reset selection
    selectedJiraIssue = null;
}

// Close Jira Import Modal
function closeJiraImportModal() {
    const modal = document.getElementById('jira-import-modal');
    modal.classList.remove('show');
    
    // Reset selection
    selectedJiraIssue = null;
    document.getElementById('import-jira-btn').disabled = true;
}

// Test Type Selection
function selectTestType(type) {
    // Remove active class from all cards
    document.querySelectorAll('.test-type-card').forEach(card => {
        card.classList.remove('active');
    });
    
    // Add active class to selected card
    const selectedCard = document.querySelector(`.test-type-card[data-type="${type}"]`);
    if (selectedCard) {
        selectedCard.classList.add('active');
    }
    
    // Update hidden input value
    document.getElementById('selected-test-type').value = type;
}

// Load Plan functionality
let selectedSavedPlan = null;

// Open Load Plan Modal
function openLoadPlanModal() {
    const modal = document.getElementById('load-plan-modal');
    const plansList = document.getElementById('saved-plans-list');
    
    // Get saved plans from localStorage
    const savedPlans = JSON.parse(localStorage.getItem('savedTestPlans') || '[]');
    
    if (savedPlans.length === 0) {
        plansList.innerHTML = '<div style="text-align: center; padding: 2rem; color: #718096;">No saved test plans found.</div>';
    } else {
        // Display saved plans
        plansList.innerHTML = savedPlans.map((plan, index) => {
            const date = new Date(plan.createdAt);
            const formattedDate = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
            const numTestCases = plan.testCases ? plan.testCases.length : 0;
            
            // Build ID and Reference display
            let idReferenceText = '';
            if (plan.id) {
                idReferenceText = `ID: ${plan.id}`;
                if (plan.reference) {
                    idReferenceText += ` | Reference: ${plan.reference}`;
                }
            }
            
            return `
                <div class="jira-issue-item" onclick="selectSavedPlan(${index})" style="position: relative;">
                    <button class="btn-icon btn-icon-delete" onclick="event.stopPropagation(); deleteSavedPlan(${index})" title="Delete Plan" style="position: absolute; top: 0.75rem; right: 0.75rem; z-index: 10;">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" style="width: 18px; height: 18px;">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                        </svg>
                    </button>
                    <div class="jira-issue-header">
                        <span class="jira-issue-key">${plan.title}</span>
                        <span class="jira-issue-type story">${numTestCases} test cases</span>
                    </div>
                    ${idReferenceText ? `<div class="jira-issue-summary" style="font-weight: 500; color: #319795; margin-bottom: 0.25rem;">${idReferenceText}</div>` : ''}
                    <div class="jira-issue-summary">Coverage: ${plan.coverage}% | Test Cases: ${plan.minCases}-${plan.maxCases}</div>
                    <div class="jira-issue-description" style="font-size: 0.75rem; color: #a0aec0;">Saved: ${formattedDate}</div>
                </div>
            `;
        }).join('');
    }
    
    modal.classList.add('show');
}

// Select a saved plan
function selectSavedPlan(planIndex) {
    // Remove previous selection
    document.querySelectorAll('#saved-plans-list .jira-issue-item').forEach(item => {
        item.classList.remove('selected');
    });
    
    // Add selection to clicked item
    event.target.closest('.jira-issue-item').classList.add('selected');
    
    // Store selected plan index
    selectedSavedPlan = planIndex;
    
    // Enable load button
    document.getElementById('load-plan-btn').disabled = false;
}

// Load selected plan
function loadSelectedPlan() {
    if (selectedSavedPlan === null) {
        alert('Please select a test plan first');
        return;
    }
    
    // Get saved plans
    const savedPlans = JSON.parse(localStorage.getItem('savedTestPlans') || '[]');
    const plan = savedPlans[selectedSavedPlan];
    
    if (!plan) {
        alert('Error loading test plan');
        return;
    }
    
    // Populate form fields
    document.getElementById('plan-title').value = plan.title;
    document.getElementById('plan-id').value = plan.id || '';
    document.getElementById('plan-reference').value = plan.reference || '';
    document.getElementById('requirements').value = plan.requirements;
    document.getElementById('coverage').value = plan.coverage;
    document.getElementById('coverage-value').textContent = plan.coverage + '%';
    document.getElementById('min-cases').value = plan.minCases;
    document.getElementById('min-cases-value').textContent = plan.minCases;
    document.getElementById('max-cases').value = plan.maxCases;
    document.getElementById('max-cases-value').textContent = plan.maxCases;
    
    // Update dual slider display
    const minPercent = ((plan.minCases - 1) / (20 - 1)) * 100;
    const maxPercent = ((plan.maxCases - 1) / (20 - 1)) * 100;
    const sliderRange = document.getElementById('slider-range');
    sliderRange.style.left = minPercent + '%';
    sliderRange.style.width = (maxPercent - minPercent) + '%';
    document.getElementById('min-cases-value').style.left = minPercent + '%';
    document.getElementById('max-cases-value').style.left = maxPercent + '%';
    
    // Load test cases
    testCases = plan.testCases || [];
    currentTestPlan = plan;
    
    // Display test cases if they exist
    if (testCases.length > 0) {
        displayTestCases();
        
        // Show results, chat, and actions sections
        document.getElementById('results-section').style.display = 'block';
        document.getElementById('chat-section').style.display = 'block';
        document.getElementById('actions-section').style.display = 'block';
        
        // Restore chat history if it exists
        if (plan.chatHistory && plan.chatHistory.length > 0) {
            const chatMessages = document.getElementById('chat-messages');
            chatMessages.innerHTML = ''; // Clear existing messages
            
            plan.chatHistory.forEach(msg => {
                const messageDiv = document.createElement('div');
                messageDiv.className = `chat-message ${msg.type}`;
                
                const avatar = msg.type === 'user' ? sessionStorage.getItem('username').charAt(0).toUpperCase() : 'AI';
                
                messageDiv.innerHTML = `
                    <div class="message-avatar">${avatar}</div>
                    <div class="message-content">
                        <p>${msg.content.replace(/\n/g, '<br>')}</p>
                    </div>
                `;
                
                chatMessages.appendChild(messageDiv);
            });
            
            // Scroll to bottom of chat
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }
    
    // Close modal
    closeLoadPlanModal();
    
    // Update button state (disable if test cases exist, enable if empty)
    updateGenerateButtonState();
    
    // Show success message
    alert(`Successfully loaded test plan: ${plan.title}`);
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Delete saved plan
function deleteSavedPlan(planIndex) {
    // Get saved plans
    const savedPlans = JSON.parse(localStorage.getItem('savedTestPlans') || '[]');
    
    if (planIndex < 0 || planIndex >= savedPlans.length) {
        alert('Error: Invalid plan index');
        return;
    }
    
    const plan = savedPlans[planIndex];
    
    // Confirm deletion
    if (!confirm(`Are you sure you want to delete "${plan.title}"?\n\nThis action cannot be undone.`)) {
        return;
    }
    
    // Remove plan from array
    savedPlans.splice(planIndex, 1);
    
    // Save updated array back to localStorage
    localStorage.setItem('savedTestPlans', JSON.stringify(savedPlans));
    
    // Refresh the modal display
    openLoadPlanModal();
}

// Close Load Plan Modal
function closeLoadPlanModal() {
    const modal = document.getElementById('load-plan-modal');
    modal.classList.remove('show');
    
    // Reset selection
    selectedSavedPlan = null;
    document.getElementById('load-plan-btn').disabled = true;
}

// Clear chat conversation
function clearChatConversation() {
    if (!confirm('Are you sure you want to clear the chat conversation?\n\nThis will reset the conversation to its initial state.')) {
        return;
    }
    
    // Reset chat to initial message
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML = `
        <div class="chat-message assistant">
            <div class="message-avatar">AI</div>
            <div class="message-content">
                <p>Test plan generated successfully! You can now refine it by asking me to:</p>
                <ul>
                    <li>Add specific test cases for edge cases</li>
                    <li>Include negative testing scenarios</li>
                    <li>Add performance or security test cases</li>
                    <li>Modify existing test cases</li>
                    <li>Remove redundant test cases</li>
                </ul>
                <p>What would you like to adjust?</p>
            </div>
        </div>
    `;
    
    // Clear the input field
    document.getElementById('chat-input').value = '';
}

// Logout
function logout() {
    sessionStorage.clear();
    window.location.href = 'login.html';
}
