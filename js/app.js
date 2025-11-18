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
    
    // Monitor for team changes to refresh Jira filters
    monitorTeamChanges();
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

// Monitor for team changes in sessionStorage
function monitorTeamChanges() {
    let currentTeam = sessionStorage.getItem('user_team');
    
    // Check for team changes every second
    setInterval(() => {
        const newTeam = sessionStorage.getItem('user_team');
        
        // If team has changed
        if (newTeam !== currentTeam) {
            currentTeam = newTeam;
            
            // If Jira modal is open, refresh it with new team's data
            const jiraModal = document.getElementById('jira-import-modal');
            if (jiraModal && jiraModal.classList.contains('show')) {
                refreshJiraModalForNewTeam();
            }
        }
    }, 1000);
}

// Refresh Jira modal when team changes
async function refreshJiraModalForNewTeam() {
    const issuesList = document.getElementById('jira-issues-list');
    const modalHeader = document.querySelector('#jira-import-modal .modal-header h3');
    
    // Get new user team
    const userTeam = sessionStorage.getItem('user_team');
    
    // Check if user has a valid team
    if (!userTeam || !JIRA_PROJECTS_BY_TEAM[userTeam]) {
        issuesList.innerHTML = `
            <div class="jira-empty-state">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                </svg>
                <h4>Sin acceso a Jira</h4>
                <p>Tu usuario no tiene un equipo asignado o el equipo no tiene un proyecto de Jira configurado.</p>
            </div>
        `;
        return;
    }
    
    // Get project info for the team
    const projectInfo = JIRA_PROJECTS_BY_TEAM[userTeam];
    
    // Update modal header with new project badge
    modalHeader.innerHTML = `
        Importar desde Jira
        <span style="
            display: inline-block;
            margin-left: 1rem;
            padding: 0.25rem 0.75rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 600;
            letter-spacing: 0.5px;
        ">${projectInfo.key}</span>
    `;
    
    // Clear all filters
    document.getElementById('jira-search').value = '';
    document.getElementById('jira-type-filter').value = '';
    document.getElementById('jira-status-filter').value = '';
    document.getElementById('jira-priority-filter').value = '';
    document.getElementById('jira-assignee-filter').value = '';
    
    // Reset pagination
    currentJiraPage = 0;
    displayedJiraIssues = [];
    
    // Show loading
    issuesList.innerHTML = '<div class="jira-loading"><div class="loading-spinner"></div><p style="margin-top: 1rem;">Cargando incidencias del nuevo proyecto...</p></div>';
    
    try {
        // Fetch REAL Jira issues from Lambda for new team
        const response = await window.apiService.fetchJiraIssues(userTeam, 50);
        
        // Store new issues
        allJiraIssues = response.issues || [];
        filteredJiraIssues = [...allJiraIssues];
        
        // Repopulate filters with NEW project's data
        populateAssigneeFilter();
        populateStatusFilter();
        populateTypeFilter();
        populatePriorityFilter();
        
        // Display first page of issues
        loadMoreJiraIssues();
        
    } catch (error) {
        console.error('❌ Error fetching Jira issues for new team:', error);
        
        // Show error message
        issuesList.innerHTML = `
            <div class="jira-empty-state">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" style="color: #e53e3e;">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                </svg>
                <h4>Error al cargar incidencias</h4>
                <p>${error.message || 'No se pudieron cargar las incidencias del nuevo proyecto. Por favor, intenta de nuevo.'}</p>
                <button class="btn-secondary" onclick="refreshJiraModalForNewTeam()" style="margin-top: 1rem;">
                    Reintentar
                </button>
            </div>
        `;
    }
}

// Update Generate Test Plan button state
function updateGenerateButtonState() {
    const generateBtn = document.querySelector('.btn-primary');
    if (generateBtn) {
        // Keep button enabled always
        generateBtn.disabled = false;
        
        // Change button text after first generation
        if (testCases.length > 0) {
            generateBtn.textContent = 'Generar nuevo plan';
        } else {
            generateBtn.textContent = 'Generar Plan de Pruebas';
        }
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

// Collapse config section
function collapseConfigSection() {
    const configSection = document.getElementById('config-section');
    configSection.classList.add('collapsed');
    
    // Scroll to results section smoothly
    setTimeout(() => {
        document.getElementById('results-section').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 300);
}

// Expand config section
function expandConfigSection() {
    const configSection = document.getElementById('config-section');
    configSection.classList.remove('collapsed');
    
    // Scroll to config section smoothly
    setTimeout(() => {
        configSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
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
        alert('Por favor, introduce un título para el plan de pruebas');
        return;
    }
    
    if (!requirements) {
        alert('Por favor, introduce los requisitos funcionales');
        return;
    }
    
    // Generate unique ID for the test plan
    const planId = generateTestPlanId();
    document.getElementById('plan-id').value = planId;
    
    // Show loading overlay
    showLoadingOverlay();
    
    // Show loading state on button
    const btn = event.target;
    const originalHTML = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<div class="loading-spinner"></div> Generando plan de pruebas...';
    
    try {
        // Get user team from session storage
        const userTeam = sessionStorage.getItem('user_team');
        
        const requestData = {
            title: title,
            requirements: requirements,
            coverage_percentage: parseInt(coverage),
            min_test_cases: minCases,
            max_test_cases: maxCases,
            user_team: userTeam || null  // Always include user_team (null if not available)
        };
        
        const response = await window.apiService.generateTestPlanWithAI(requestData);
        
        // Process response
        testCases = response.test_cases || [];
        
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
        
        // Update button text to "Generar nuevo plan" after first generation
        updateGenerateButtonState();
        
    } catch (error) {
        console.error("Error generating test plan:", error);
        
        // Determine appropriate error message
        let errorTitle = 'Error al generar el plan de pruebas';
        let errorMessage = '';
        
        if (error.message.includes('504') || error.message.includes('Gateway Timeout')) {
            errorMessage = 'El servidor tardó demasiado en responder. Por favor, intenta de nuevo.';
        } else if (error.message.includes('CORS')) {
            errorMessage = 'Error de configuración CORS. Asegúrate de servir la aplicación desde un servidor web.';
        } else if (error.message.includes('Network') || error.message.includes('fetch')) {
            errorMessage = 'Error de conexión. Verifica tu conexión a internet e intenta de nuevo.';
        } else if (error.message.includes('500')) {
            errorMessage = 'Error interno del servidor. Por favor, intenta de nuevo más tarde.';
        } else {
            errorMessage = error.message || 'Error desconocido. Por favor, intenta de nuevo.';
        }
        
        // Show elegant error notification
        showErrorNotification(errorTitle, errorMessage);
    } finally {
        // Hide loading overlay
        hideLoadingOverlay();
        
        // Reset button
        btn.disabled = false;
        btn.innerHTML = originalHTML;
        
        // Update button state (disable since we now have test cases)
        updateGenerateButtonState();
    }
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
    
    // Priority translations
    const priorityTranslations = {
        'High': 'Alta',
        'Medium': 'Media',
        'Low': 'Baja'
    };
    
    testCases.forEach(testCase => {
        const row = document.createElement('tr');
        row.style.cursor = 'pointer';
        row.onclick = function(e) {
            // Don't trigger row click if clicking on action buttons
            if (!e.target.closest('.btn-icon')) {
                editTestCase(testCase.id);
            }
        };
        
        const translatedPriority = priorityTranslations[testCase.priority] || testCase.priority;
        
        row.innerHTML = `
            <td><strong>${testCase.id}</strong></td>
            <td>${testCase.name}</td>
            <td>${testCase.description}</td>
            <td><span class="priority-badge priority-${testCase.priority.toLowerCase()}">${translatedPriority}</span></td>
            <td>${testCase.preconditions}</td>
            <td>${testCase.expectedResult}</td>
            <td>
                <div style="display: flex; gap: 0.5rem; justify-content: center;">
                    <button class="btn-icon btn-icon-view" onclick="event.stopPropagation(); viewTestSteps('${testCase.id}')" title="Ver Pasos">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" style="width: 18px; height: 18px;">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                            <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                    </button>
                    <button class="btn-icon btn-icon-edit" onclick="event.stopPropagation(); editTestCase('${testCase.id}')" title="Editar Caso de Prueba">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" style="width: 18px; height: 18px;">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
                        </svg>
                    </button>
                    <button class="btn-icon btn-icon-delete" onclick="event.stopPropagation(); deleteTestCase('${testCase.id}')" title="Eliminar Caso de Prueba">
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
    
    // Build steps HTML
    let stepsListHTML = '';
    if (testCase.steps && testCase.steps.length > 0) {
        stepsListHTML = '<ol style="margin: 0; padding-left: 1.5rem;">';
        testCase.steps.forEach(step => {
            const stepText = typeof step === 'object' ? step.description : step;
            stepsListHTML += `<li style="margin-bottom: 0.5rem; color: #4a5568;">${stepText}</li>`;
        });
        stepsListHTML += '</ol>';
    } else {
        stepsListHTML = '<p style="color: #a0aec0; font-style: italic;">No steps defined</p>';
    }
    
    // Translate priority
    const priorityTranslations = {
        'High': 'Alta',
        'Medium': 'Media',
        'Low': 'Baja'
    };
    const translatedPriority = priorityTranslations[testCase.priority] || testCase.priority;
    
    let stepsHTML = `
        <div style="margin-bottom: 1.5rem;">
            <h4 style="color: #2d3748; margin-bottom: 0.5rem;">Descripción</h4>
            <p style="color: #4a5568;">${testCase.description}</p>
        </div>
        
        <div style="margin-bottom: 1.5rem;">
            <h4 style="color: #2d3748; margin-bottom: 0.5rem;">Prioridad</h4>
            <span class="priority-badge priority-${testCase.priority.toLowerCase()}">${translatedPriority}</span>
        </div>
        
        <div style="margin-bottom: 1.5rem;">
            <h4 style="color: #2d3748; margin-bottom: 0.5rem;">Precondiciones</h4>
            <p style="color: #4a5568;">${testCase.preconditions}</p>
        </div>
        
        <div style="margin-bottom: 1.5rem;">
            <h4 style="color: #2d3748; margin-bottom: 0.5rem;">Pasos de Prueba</h4>
            ${stepsListHTML}
        </div>
        
        <div style="margin-bottom: 1.5rem;">
            <h4 style="color: #2d3748; margin-bottom: 0.5rem;">Datos de Prueba</h4>
            <p style="color: #4a5568;">${testCase.testData}</p>
        </div>
        
        <div>
            <h4 style="color: #2d3748; margin-bottom: 0.5rem;">Resultado Esperado</h4>
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
    
    // Validate that we have test cases
    if (!testCases || testCases.length === 0) {
        alert('No hay casos de prueba para modificar. Genera un plan primero.');
        return;
    }
    
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
            <div class="loading-spinner"></div> Procesando tu solicitud...
        </div>
    `;
    chatMessages.appendChild(loadingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    try {
        // Build context for chat agent
        const context = {
            user_message: message,
            test_plan: currentTestPlan || {
                id: document.getElementById('plan-id').value,
                title: document.getElementById('plan-title').value,
                requirements: document.getElementById('requirements').value
            },
            test_cases: testCases,
            conversation_history: getChatHistory()
        };
        
        // Call chat agent API
        const response = await window.apiService.chatWithTestCases(context);
        
        // Remove loading message
        loadingDiv.remove();
        
        // Process response
        if (response.requires_confirmation) {
            // Show confirmation dialog
            showConfirmationDialog(response);
        } else {
            // Apply changes directly
            applyChanges(response);
            addChatMessage(response.message, 'assistant');
        }
        
    } catch (error) {
        console.error('Error in chat:', error);
        loadingDiv.remove();
        addChatMessage('Lo siento, hubo un error al procesar tu solicitud. Por favor, intenta de nuevo.', 'assistant');
    }
}

// Get chat history from DOM
function getChatHistory() {
    const chatMessages = document.getElementById('chat-messages');
    const messages = chatMessages.querySelectorAll('.chat-message');
    const history = [];
    
    messages.forEach(msg => {
        const isAssistant = msg.classList.contains('assistant');
        const content = msg.querySelector('.message-content p');
        if (content) {
            history.push({
                type: isAssistant ? 'assistant' : 'user',
                content: content.textContent
            });
        }
    });
    
    return history;
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
        alert('No hay plan de pruebas para guardar');
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
    
    alert('¡Plan de pruebas guardado exitosamente!');
}

// Export to CSV
function exportToCSV() {
    if (!testCases.length) {
        alert('No hay casos de prueba para exportar');
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
        alert('No hay plan de pruebas para exportar');
        return;
    }
    
    const json = JSON.stringify(currentTestPlan, null, 2);
    downloadFile(json, `test-plan-${currentTestPlan.title.replace(/\s+/g, '-')}.json`, 'application/json');
}

// Export to Gherkin (BDD)
function exportToGherkin() {
    if (!testCases.length) {
        alert('No hay casos de prueba para exportar');
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
    if (!confirm('¿Estás seguro de que quieres descartar este plan de pruebas? Esta acción no se puede deshacer.')) {
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
    
    // Expand the config section
    expandConfigSection();
    
    // Update button state (enable since testCases is now empty)
    updateGenerateButtonState();
}

// Edit test case
function editTestCase(testCaseId) {
    const testCase = testCases.find(tc => tc.id === testCaseId);
    if (!testCase) return;
    
    const modal = document.getElementById('edit-test-case-modal');
    const modalTitle = document.getElementById('edit-modal-title');
    const modalBody = document.getElementById('edit-modal-body');
    
    modalTitle.textContent = `Editar ${testCase.id}`;
    
    // Build steps HTML for editing
    let stepsHTML = '';
    if (testCase.steps && testCase.steps.length > 0) {
        testCase.steps.forEach((step, index) => {
            const stepText = typeof step === 'object' ? step.description : step;
            stepsHTML += `
                <div style="display: flex; gap: 0.5rem; margin-bottom: 0.5rem; align-items: center;">
                    <span style="min-width: 30px; color: #718096; font-weight: 500;">${index + 1}.</span>
                    <input type="text" class="form-control edit-step-input" data-step-index="${index}" value="${stepText}" style="flex: 1;">
                    <button class="btn-icon btn-icon-delete" onclick="removeStep(${index})" title="Remove step" style="flex-shrink: 0;">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" style="width: 16px; height: 16px;">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>
            `;
        });
    }
    
    modalBody.innerHTML = `
        <div class="form-group" style="margin-bottom: 1rem;">
            <label for="edit-name">Nombre del Caso de Prueba</label>
            <input type="text" id="edit-name" class="form-control" value="${testCase.name}">
        </div>
        
        <div class="form-group" style="margin-bottom: 1rem;">
            <label for="edit-description">Descripción</label>
            <textarea id="edit-description" class="form-control" rows="2">${testCase.description}</textarea>
        </div>
        
        <div class="form-group" style="margin-bottom: 1rem;">
            <label for="edit-priority">Prioridad</label>
            <select id="edit-priority" class="form-control">
                <option value="High" ${testCase.priority === 'High' ? 'selected' : ''}>Alta</option>
                <option value="Medium" ${testCase.priority === 'Medium' ? 'selected' : ''}>Media</option>
                <option value="Low" ${testCase.priority === 'Low' ? 'selected' : ''}>Baja</option>
            </select>
        </div>
        
        <div class="form-group" style="margin-bottom: 1rem;">
            <label for="edit-preconditions">Precondiciones</label>
            <textarea id="edit-preconditions" class="form-control" rows="2">${testCase.preconditions}</textarea>
        </div>
        
        <div class="form-group" style="margin-bottom: 1rem;">
            <label>Pasos de Prueba</label>
            <div id="edit-steps-container" style="margin-top: 0.5rem;">
                ${stepsHTML || '<p style="color: #a0aec0; font-style: italic; margin: 0;">No hay pasos definidos</p>'}
            </div>
            <button class="btn-secondary" onclick="addNewStep()" style="margin-top: 0.5rem; font-size: 0.875rem; padding: 0.5rem 1rem;">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" style="width: 16px; height: 16px;">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
                Agregar Paso
            </button>
        </div>
        
        <div class="form-group" style="margin-bottom: 1rem;">
            <label for="edit-test-data">Datos de Prueba</label>
            <textarea id="edit-test-data" class="form-control" rows="2">${testCase.testData}</textarea>
        </div>
        
        <div class="form-group" style="margin-bottom: 1rem;">
            <label for="edit-expected-result">Resultado Esperado</label>
            <textarea id="edit-expected-result" class="form-control" rows="2">${testCase.expectedResult}</textarea>
        </div>
        
        <div style="display: flex; gap: 1rem; justify-content: flex-end; margin-top: 1.5rem;">
            <button class="btn-cancel" onclick="closeEditModal()">Cancelar</button>
            <button class="btn-save" onclick="saveTestCaseEdit('${testCaseId}')">Guardar Cambios</button>
        </div>
    `;
    
    modal.classList.add('show');
}

// Add new step to test case being edited
function addNewStep() {
    const container = document.getElementById('edit-steps-container');
    const currentSteps = container.querySelectorAll('.edit-step-input');
    const newIndex = currentSteps.length;
    
            const newStepHTML = `
        <div style="display: flex; gap: 0.5rem; margin-bottom: 0.5rem; align-items: center;">
            <span style="min-width: 30px; color: #718096; font-weight: 500;">${newIndex + 1}.</span>
            <input type="text" class="form-control edit-step-input" data-step-index="${newIndex}" value="" placeholder="Introduce la descripción del paso..." style="flex: 1;">
            <button class="btn-icon btn-icon-delete" onclick="removeStep(${newIndex})" title="Eliminar paso" style="flex-shrink: 0;">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" style="width: 16px; height: 16px;">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
            </button>
        </div>
    `;
    
    // Remove "No steps defined" message if it exists
    const noStepsMsg = container.querySelector('p');
    if (noStepsMsg) {
        noStepsMsg.remove();
    }
    
    container.insertAdjacentHTML('beforeend', newStepHTML);
}

// Remove step from test case being edited
function removeStep(stepIndex) {
    const container = document.getElementById('edit-steps-container');
    const allSteps = container.querySelectorAll('.edit-step-input');
    
    if (allSteps.length <= 1) {
        alert('Un caso de prueba debe tener al menos un paso');
        return;
    }
    
    // Remove the step
    allSteps[stepIndex].closest('div').remove();
    
    // Renumber remaining steps
    const remainingSteps = container.querySelectorAll('.edit-step-input');
    remainingSteps.forEach((input, index) => {
        input.dataset.stepIndex = index;
        const numberSpan = input.previousElementSibling;
        if (numberSpan) {
            numberSpan.textContent = `${index + 1}.`;
        }
        // Update remove button onclick
        const removeBtn = input.nextElementSibling;
        if (removeBtn) {
            removeBtn.setAttribute('onclick', `removeStep(${index})`);
        }
    });
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
    
    // Get updated steps
    const stepInputs = document.querySelectorAll('.edit-step-input');
    const updatedSteps = [];
    stepInputs.forEach((input, index) => {
        const stepText = input.value.trim();
        if (stepText) {
            updatedSteps.push({
                number: index + 1,
                description: stepText
            });
        }
    });
    
    // Update steps (ensure at least one step)
    if (updatedSteps.length > 0) {
        testCase.steps = updatedSteps;
    } else {
        alert('Por favor, agrega al menos un paso de prueba');
        return;
    }
    
    // Update the display
    displayTestCases();
    
    // Close modal
    closeEditModal();
    
    // Show success message
    alert('¡Caso de prueba actualizado exitosamente!');
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
    
    if (!confirm(`¿Estás seguro de que quieres eliminar ${testCase.id}?\n\nEsta acción no se puede deshacer.`)) {
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
        alert('No hay casos de prueba para eliminar');
        return;
    }
    
    const numCases = testCases.length;
    
    if (!confirm(`¿Estás seguro de que quieres eliminar TODOS los ${numCases} casos de prueba?\n\nEsta acción no se puede deshacer.`)) {
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

// Jira Projects by Team Configuration
const JIRA_PROJECTS_BY_TEAM = {
    darwin: {
        key: 'GAESTG',
        name: 'Gestión de Aplicaciones y Servicios TG',
        url: 'https://csarrion.atlassian.net/jira/core/projects/GAESTG'
    },
    mulesoft: {
        key: 'ICACEP',
        name: 'Integración y Conectividad de Aplicaciones CEP',
        url: 'https://csarrion.atlassian.net/jira/core/projects/ICACEP'
    },
    sap: {
        key: 'RE',
        name: 'Reingeniería',
        url: 'https://csarrion.atlassian.net/jira/core/projects/RE'
    },
    saplcorp: {
        key: 'PDDSE2',
        name: 'Plataforma de Desarrollo y Despliegue SE2',
        url: 'https://csarrion.atlassian.net/jira/core/projects/PDDSE2'
    }
};

// Open Jira Import Modal
async function openJiraImportModal() {
    const modal = document.getElementById('jira-import-modal');
    const issuesList = document.getElementById('jira-issues-list');
    const modalHeader = modal.querySelector('.modal-header h3');
    
    // Get user team
    const userTeam = sessionStorage.getItem('user_team');
    
    // Check if user has a valid team
    if (!userTeam || !JIRA_PROJECTS_BY_TEAM[userTeam]) {
        issuesList.innerHTML = `
            <div class="jira-empty-state">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                </svg>
                <h4>Sin acceso a Jira</h4>
                <p>Tu usuario no tiene un equipo asignado o el equipo no tiene un proyecto de Jira configurado.</p>
            </div>
        `;
        modal.classList.add('show');
        return;
    }
    
    // Get project info for the team
    const projectInfo = JIRA_PROJECTS_BY_TEAM[userTeam];
    
    // Update modal header with project badge
    modalHeader.innerHTML = `
        Importar desde Jira
        <span style="
            display: inline-block;
            margin-left: 1rem;
            padding: 0.25rem 0.75rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 600;
            letter-spacing: 0.5px;
        ">${projectInfo.key}</span>
    `;
    
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
    issuesList.innerHTML = '<div class="jira-loading"><div class="loading-spinner"></div><p style="margin-top: 1rem;">Cargando incidencias reales de Jira...</p></div>';
    
    modal.classList.add('show');
    
    try {
        // Fetch REAL Jira issues from Lambda
        const response = await window.apiService.fetchJiraIssues(userTeam, 50);
        
        // Store issues with defensive checks
        allJiraIssues = response.issues || [];
        filteredJiraIssues = [...allJiraIssues];
        
        // Populate filters AFTER data is loaded
        try {
            populateAssigneeFilter();
            populateStatusFilter();
            populateTypeFilter();
            populatePriorityFilter();
        } catch (filterError) {
            console.error('Error during filter population:', filterError);
        }
        
        // Display first page of issues
        loadMoreJiraIssues();
        
    } catch (error) {
        console.error('❌ Error fetching Jira issues:', error);
        
        // Show error message
        issuesList.innerHTML = `
            <div class="jira-empty-state">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" style="color: #e53e3e;">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                </svg>
                <h4>Error al cargar incidencias</h4>
                <p>${error.message || 'No se pudieron cargar las incidencias de Jira. Por favor, intenta de nuevo.'}</p>
                <button class="btn-secondary" onclick="openJiraImportModal()" style="margin-top: 1rem;">
                    Reintentar
                </button>
            </div>
        `;
    }
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
    assigneeFilter.innerHTML = '<option value="">Todos los Asignados</option>';
    
    // Add unique assignees
    uniqueAssignees.forEach(assignee => {
        const option = document.createElement('option');
        option.value = assignee;
        option.textContent = assignee;
        assigneeFilter.appendChild(option);
    });
}

// Populate priority filter dropdown dynamically
function populatePriorityFilter() {
    const priorityFilter = document.getElementById('jira-priority-filter');
    
    if (!priorityFilter) {
        console.error('Priority filter element not found');
        return;
    }
    
    // Extract unique priorities, filtering out undefined/null values
    const uniquePriorities = [...new Set(
        allJiraIssues
            .map(issue => issue.priority)
            .filter(priority => priority !== undefined && priority !== null && priority !== '')
    )].sort();
    
    // Clear existing options except "All Priorities"
    priorityFilter.innerHTML = '<option value="">Todas las Prioridades</option>';
    
    // Priority translations for display
    const priorityTranslations = {
        'Highest': 'Muy Alta',
        'High': 'Alta',
        'Medium': 'Media',
        'Low': 'Baja',
        'Lowest': 'Muy Baja'
    };
    
    // Add unique priorities from actual data
    uniquePriorities.forEach(priority => {
        const option = document.createElement('option');
        option.value = priority;
        option.textContent = priorityTranslations[priority] || priority;
        priorityFilter.appendChild(option);
    });
}

// Populate status filter dropdown dynamically
function populateStatusFilter() {
    const statusFilter = document.getElementById('jira-status-filter');
    
    if (!statusFilter) {
        console.error('Status filter element not found');
        return;
    }
    
    // Extract unique statuses, filtering out undefined/null values
    const uniqueStatuses = [...new Set(
        allJiraIssues
            .map(issue => issue.status)
            .filter(status => status !== undefined && status !== null && status !== '')
    )].sort();
    
    // Clear existing options except "All Statuses"
    statusFilter.innerHTML = '<option value="">Todos los Estados</option>';
    
    // Add unique statuses from actual data
    uniqueStatuses.forEach(status => {
        const option = document.createElement('option');
        option.value = status;
        option.textContent = status;
        statusFilter.appendChild(option);
    });
}

// Populate type filter dropdown dynamically
function populateTypeFilter() {
    const typeFilter = document.getElementById('jira-type-filter');
    
    if (!typeFilter) {
        console.error('Type filter element not found');
        return;
    }
    
    // Extract unique types, filtering out undefined/null values
    const uniqueTypes = [...new Set(
        allJiraIssues
            .map(issue => issue.type)
            .filter(type => type !== undefined && type !== null && type !== '')
    )].sort();
    
    // Clear existing options except "All Types"
    typeFilter.innerHTML = '<option value="">Todos los Tipos</option>';
    
    // Type translations for display
    const typeTranslations = {
        'story': 'Historia',
        'bug': 'Error',
        'task': 'Tarea',
        'epic': 'Épica',
        'subtask': 'Subtarea',
        'improvement': 'Mejora'
    };
    
    // Add unique types from actual data
    uniqueTypes.forEach(type => {
        const option = document.createElement('option');
        option.value = type;
        option.textContent = typeTranslations[type.toLowerCase()] || type;
        typeFilter.appendChild(option);
    });
}

// Filter Jira issues based on all filters
function filterJiraIssues() {
    const searchText = document.getElementById('jira-search').value.toLowerCase().trim();
    const typeFilter = document.getElementById('jira-type-filter').value.trim();
    const statusFilter = document.getElementById('jira-status-filter').value.trim();
    const priorityFilter = document.getElementById('jira-priority-filter').value.trim();
    const assigneeFilter = document.getElementById('jira-assignee-filter').value.trim();

    filteredJiraIssues = allJiraIssues.filter(issue => {
        // Filter by type (exact match - case sensitive since API returns lowercase)
        if (typeFilter && issue.type !== typeFilter) {
            return false;
        }

        // Filter by status (exact match - case sensitive since statuses vary by project)
        if (statusFilter && issue.status !== statusFilter) {
            return false;
        }

        // Filter by priority (exact match - case sensitive)
        if (priorityFilter && issue.priority !== priorityFilter) {
            return false;
        }

        // Filter by assignee (exact match)
        if (assigneeFilter && issue.assignee !== assigneeFilter) {
            return false;
        }

        // Filter by search text (ID, title, or description)
        if (searchText) {
            const matchesSearch =
                issue.key.toLowerCase().includes(searchText) ||
                issue.summary.toLowerCase().includes(searchText) ||
                (issue.description && issue.description.toLowerCase().includes(searchText));
            if (!matchesSearch) {
                return false;
            }
        }

        return true;
    });

    // Reset pagination and display
    currentJiraPage = 0;
    displayedJiraIssues = [];
    loadMoreJiraIssues();
}

// Helper function to normalize Jira status values
function normalizeJiraStatus(status) {
    if (!status) return '';
    
    // Convert to lowercase and normalize common status variations
    const normalized = status.toLowerCase().trim();
    
    // Map common Jira status variations to standard values
    const statusMap = {
        'to do': 'todo',
        'todo': 'todo',
        'in progress': 'in-progress',
        'in-progress': 'in-progress',
        'done': 'done',
        'blocked': 'blocked',
        'backlog': 'backlog',
        'selected for development': 'todo',
        'in review': 'in-progress',
        'ready for testing': 'in-progress',
        'testing': 'in-progress',
        'closed': 'done',
        'resolved': 'done'
    };
    
    return statusMap[normalized] || normalized.replace(/\s+/g, '-');
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
                <h4>No se encontraron incidencias</h4>
                <p>Intenta ajustar tus filtros o criterios de búsqueda</p>
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
        alert('Por favor, selecciona primero una incidencia de Jira');
        return;
    }
    
    // Populate form fields
    document.getElementById('plan-title').value = `Test Plan: ${selectedJiraIssue.summary}`;
    document.getElementById('plan-reference').value = selectedJiraIssue.key;
    document.getElementById('requirements').value = selectedJiraIssue.description;
    
    // Close modal
    closeJiraImportModal();
    
    // Show success message
    alert(`Incidencia de Jira ${selectedJiraIssue.key} importada exitosamente`);
    
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
        plansList.innerHTML = '<div style="text-align: center; padding: 2rem; color: #718096;">No se encontraron planes de prueba guardados.</div>';
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
        alert('Por favor, selecciona primero un plan de pruebas');
        return;
    }
    
    // Get saved plans
    const savedPlans = JSON.parse(localStorage.getItem('savedTestPlans') || '[]');
    const plan = savedPlans[selectedSavedPlan];
    
    if (!plan) {
        alert('Error al cargar el plan de pruebas');
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
    
    // Show success notification
    showSuccessNotification(`Plan de pruebas cargado exitosamente`, plan.title);
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Show success notification (elegant modal)
function showSuccessNotification(title, subtitle) {
    // Create modal overlay
    const overlay = document.createElement('div');
    overlay.id = 'success-notification-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        animation: fadeIn 0.2s ease-out;
    `;
    
    // Create modal content
    const modal = document.createElement('div');
    modal.style.cssText = `
        background: white;
        border-radius: 12px;
        padding: 2rem;
        max-width: 450px;
        width: 90%;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        animation: slideIn 0.3s ease-out;
        text-align: center;
    `;
    
    modal.innerHTML = `
        <div style="margin-bottom: 1.5rem;">
            <div style="
                width: 64px;
                height: 64px;
                background: #d4f4dd;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 1rem auto;
            ">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="#38a169" style="width: 32px; height: 32px;">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                </svg>
            </div>
            <h3 style="margin: 0 0 0.5rem 0; color: #2d3748; font-size: 1.5rem; font-weight: 600;">${title}</h3>
            ${subtitle ? `<p style="color: #4a5568; margin: 0; font-size: 1rem;">${subtitle}</p>` : ''}
        </div>
        <button id="success-ok-btn" style="
            padding: 0.75rem 2rem;
            border: none;
            background: #319795;
            color: white;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            width: 100%;
        ">Aceptar</button>
    `;
    
    overlay.appendChild(modal);
    document.body.appendChild(overlay);
    
    // Add CSS animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        #success-ok-btn:hover {
            background: #2c7a7b !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }
    `;
    document.head.appendChild(style);
    
    // OK button handler
    const okBtn = document.getElementById('success-ok-btn');
    okBtn.onclick = function() {
        overlay.style.animation = 'fadeOut 0.2s ease-out';
        modal.style.animation = 'slideOut 0.2s ease-out';
        
        // Add fadeOut animation
        const fadeOutStyle = document.createElement('style');
        fadeOutStyle.textContent = `
            @keyframes fadeOut {
                from { opacity: 1; }
                to { opacity: 0; }
            }
            @keyframes slideOut {
                from {
                    opacity: 1;
                    transform: translateY(0);
                }
                to {
                    opacity: 0;
                    transform: translateY(-20px);
                }
            }
        `;
        document.head.appendChild(fadeOutStyle);
        
        setTimeout(() => {
            document.body.removeChild(overlay);
            document.head.removeChild(style);
            document.head.removeChild(fadeOutStyle);
        }, 200);
    };
    
    // Close on overlay click
    overlay.onclick = function(e) {
        if (e.target === overlay) {
            okBtn.click();
        }
    };
}

// Show error notification (elegant modal)
function showErrorNotification(title, message) {
    // Create modal overlay
    const overlay = document.createElement('div');
    overlay.id = 'error-notification-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        animation: fadeIn 0.2s ease-out;
    `;
    
    // Create modal content
    const modal = document.createElement('div');
    modal.style.cssText = `
        background: white;
        border-radius: 12px;
        padding: 2rem;
        max-width: 450px;
        width: 90%;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        animation: slideIn 0.3s ease-out;
        text-align: center;
    `;
    
    modal.innerHTML = `
        <div style="margin-bottom: 1.5rem;">
            <div style="
                width: 64px;
                height: 64px;
                background: #fed7d7;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 1rem auto;
            ">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="#e53e3e" style="width: 32px; height: 32px;">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
            </div>
            <h3 style="margin: 0 0 0.5rem 0; color: #2d3748; font-size: 1.5rem; font-weight: 600;">${title}</h3>
            ${message ? `<p style="color: #4a5568; margin: 0; font-size: 1rem; line-height: 1.5;">${message}</p>` : ''}
        </div>
        <button id="error-ok-btn" style="
            padding: 0.75rem 2rem;
            border: none;
            background: #e53e3e;
            color: white;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            width: 100%;
        ">Aceptar</button>
    `;
    
    overlay.appendChild(modal);
    document.body.appendChild(overlay);
    
    // Add CSS animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        #error-ok-btn:hover {
            background: #c53030 !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }
    `;
    document.head.appendChild(style);
    
    // OK button handler
    const okBtn = document.getElementById('error-ok-btn');
    okBtn.onclick = function() {
        overlay.style.animation = 'fadeOut 0.2s ease-out';
        modal.style.animation = 'slideOut 0.2s ease-out';
        
        // Add fadeOut animation
        const fadeOutStyle = document.createElement('style');
        fadeOutStyle.textContent = `
            @keyframes fadeOut {
                from { opacity: 1; }
                to { opacity: 0; }
            }
            @keyframes slideOut {
                from {
                    opacity: 1;
                    transform: translateY(0);
                }
                to {
                    opacity: 0;
                    transform: translateY(-20px);
                }
            }
        `;
        document.head.appendChild(fadeOutStyle);
        
        setTimeout(() => {
            document.body.removeChild(overlay);
            document.head.removeChild(style);
            document.head.removeChild(fadeOutStyle);
        }, 200);
    };
    
    // Close on overlay click
    overlay.onclick = function(e) {
        if (e.target === overlay) {
            okBtn.click();
        }
    };
}

// Delete saved plan
function deleteSavedPlan(planIndex) {
    // Get saved plans
    const savedPlans = JSON.parse(localStorage.getItem('savedTestPlans') || '[]');
    
    if (planIndex < 0 || planIndex >= savedPlans.length) {
        alert('Error: Índice de plan inválido');
        return;
    }
    
    const plan = savedPlans[planIndex];
    
    // Confirm deletion
    if (!confirm(`¿Estás seguro de que quieres eliminar "${plan.title}"?\n\nEsta acción no se puede deshacer.`)) {
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
    if (!confirm('¿Estás seguro de que quieres limpiar la conversación del chat?\n\nEsto restablecerá la conversación a su estado inicial.')) {
        return;
    }
    
    // Reset chat to initial message
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML = `
        <div class="chat-message assistant">
            <div class="message-avatar">AI</div>
            <div class="message-content">
                <p>¡Plan de pruebas generado exitosamente! Ahora puedes refinarlo pidiéndome que:</p>
                <ul>
                    <li>Agregue casos de prueba específicos para casos límite</li>
                    <li>Incluya escenarios de pruebas negativas</li>
                    <li>Agregue casos de prueba de rendimiento o seguridad</li>
                    <li>Modifique casos de prueba existentes</li>
                    <li>Elimine casos de prueba redundantes</li>
                </ul>
                <p>¿Qué te gustaría ajustar?</p>
            </div>
        </div>
    `;
    
    // Clear the input field
    document.getElementById('chat-input').value = '';
}

// Show confirmation dialog
function showConfirmationDialog(response) {
    // Create modal overlay
    const overlay = document.createElement('div');
    overlay.id = 'confirmation-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
    `;
    
    // Create modal content
    const modal = document.createElement('div');
    modal.style.cssText = `
        background: white;
        border-radius: 12px;
        padding: 2rem;
        max-width: 500px;
        width: 90%;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
    `;
    
    // Build affected cases list
    let affectedCasesList = '';
    if (response.affected_cases && response.affected_cases.length > 0) {
        affectedCasesList = '<div style="margin: 1rem 0; padding: 1rem; background: #f7fafc; border-radius: 8px;">';
        affectedCasesList += '<strong style="color: #2d3748;">Casos afectados:</strong><ul style="margin: 0.5rem 0; padding-left: 1.5rem;">';
        response.affected_cases.forEach(caseId => {
            const testCase = testCases.find(tc => tc.id === caseId);
            const caseName = testCase ? testCase.name : caseId;
            affectedCasesList += `<li style="color: #4a5568; margin: 0.25rem 0;">${caseId}: ${caseName}</li>`;
        });
        affectedCasesList += '</ul></div>';
    }
    
    modal.innerHTML = `
        <h3 style="margin: 0 0 1rem 0; color: #2d3748; font-size: 1.25rem;">Confirmar Acción</h3>
        <p style="color: #4a5568; margin-bottom: 1rem;">${response.message}</p>
        ${affectedCasesList}
        <div style="display: flex; gap: 1rem; justify-content: flex-end; margin-top: 1.5rem;">
            <button id="confirm-cancel-btn" style="
                padding: 0.75rem 1.5rem;
                border: 1px solid #e2e8f0;
                background: white;
                color: #4a5568;
                border-radius: 8px;
                font-size: 1rem;
                cursor: pointer;
                transition: all 0.2s;
            ">Cancelar</button>
            <button id="confirm-accept-btn" style="
                padding: 0.75rem 1.5rem;
                border: none;
                background: #319795;
                color: white;
                border-radius: 8px;
                font-size: 1rem;
                cursor: pointer;
                transition: all 0.2s;
            ">Aceptar</button>
        </div>
    `;
    
    overlay.appendChild(modal);
    document.body.appendChild(overlay);
    
    // Button references
    const acceptBtn = document.getElementById('confirm-accept-btn');
    const cancelBtn = document.getElementById('confirm-cancel-btn');
    
    // Accept handler
    acceptBtn.onclick = function() {
        // Visual feedback
        acceptBtn.style.background = '#2c7a7b';
        acceptBtn.style.cursor = 'not-allowed';
        cancelBtn.disabled = true;
        cancelBtn.style.opacity = '0.5';
        cancelBtn.style.cursor = 'not-allowed';
        
        // Apply changes
        applyChanges(response);
        
        // Add confirmation message based on action type
        let confirmationMessage = '';
        switch(response.action) {
            case 'DELETE':
                confirmationMessage = `✓ Casos de prueba eliminados exitosamente: ${response.affected_cases.join(', ')}`;
                break;
            case 'MODIFY':
                confirmationMessage = `✓ Casos de prueba modificados exitosamente: ${response.affected_cases.join(', ')}`;
                break;
            case 'UPDATE_STEP':
                confirmationMessage = `✓ Paso actualizado exitosamente en ${response.affected_cases.join(', ')}`;
                break;
            case 'ADD':
                confirmationMessage = `✓ Nuevos casos de prueba agregados exitosamente`;
                break;
            case 'GENERATE':
                confirmationMessage = `✓ Casos de prueba generados exitosamente: ${response.affected_cases.join(', ')}`;
                break;
            case 'MULTIPLE':
                confirmationMessage = `✓ Múltiples acciones ejecutadas exitosamente`;
                break;
            default:
                confirmationMessage = `✓ Acción ejecutada exitosamente`;
        }
        
        addChatMessage(confirmationMessage, 'assistant');
        
        // Close dialog
        setTimeout(() => {
            document.body.removeChild(overlay);
        }, 300);
    };
    
    // Cancel handler
    cancelBtn.onclick = function() {
        // Visual feedback
        cancelBtn.style.background = '#e2e8f0';
        cancelBtn.style.cursor = 'not-allowed';
        acceptBtn.disabled = true;
        acceptBtn.style.opacity = '0.5';
        acceptBtn.style.cursor = 'not-allowed';
        
        // Add cancellation message
        addChatMessage('Operación cancelada.', 'assistant');
        
        // Close dialog
        setTimeout(() => {
            document.body.removeChild(overlay);
        }, 300);
    };
}

// Apply changes from chat response
function applyChanges(response) {
    const action = response.action;
    const data = response.data;
    
    switch(action) {
        case 'DELETE':
            // Delete specified test cases
            if (data.case_ids && Array.isArray(data.case_ids)) {
                data.case_ids.forEach(caseId => {
                    const index = testCases.findIndex(tc => tc.id === caseId);
                    if (index > -1) {
                        testCases.splice(index, 1);
                    }
                });
            }
            break;
            
        case 'MODIFY':
            // Modify test case fields
            if (data.modifications && Array.isArray(data.modifications)) {
                data.modifications.forEach(mod => {
                    const testCase = testCases.find(tc => tc.id === mod.case_id);
                    if (testCase && mod.changes) {
                        Object.assign(testCase, mod.changes);
                    }
                });
            }
            break;
            
        case 'UPDATE_STEP':
            // Update specific step in a test case
            const testCase = testCases.find(tc => tc.id === data.case_id);
            if (!testCase) break;
            
            // Handle simple update (single step modification)
            if (data.step_number && data.new_description) {
                if (testCase.steps && testCase.steps[data.step_number - 1]) {
                    testCase.steps[data.step_number - 1].description = data.new_description;
                }
            }
            // Handle complex operations (INSERT, APPEND, DELETE, etc.)
            else if (data.operations && Array.isArray(data.operations)) {
                if (!testCase.steps) testCase.steps = [];
                
                data.operations.forEach(op => {
                    // Normalize operation name to lowercase for comparison
                    const operation = op.operation.toLowerCase();
                    
                    switch(operation) {
                        case 'insert':
                            // Insert step at specific position
                            const insertPos = op.position - 1; // Convert to 0-based index
                            const insertDescription = op.step ? op.step.description : op.description;
                            testCase.steps.splice(insertPos, 0, {
                                number: op.position,
                                description: insertDescription
                            });
                            // Renumber all steps after insertion
                            testCase.steps.forEach((step, idx) => {
                                step.number = idx + 1;
                            });
                            break;
                            
                        case 'append':
                            // Add step at the end
                            const appendDescription = op.step ? op.step.description : op.description;
                            testCase.steps.push({
                                number: testCase.steps.length + 1,
                                description: appendDescription
                            });
                            break;
                            
                        case 'delete':
                            // Delete step at specific position
                            const deletePos = op.position - 1;
                            if (deletePos >= 0 && deletePos < testCase.steps.length) {
                                testCase.steps.splice(deletePos, 1);
                                // Renumber remaining steps
                                testCase.steps.forEach((step, idx) => {
                                    step.number = idx + 1;
                                });
                            }
                            break;
                            
                        case 'update':
                            // Update step at specific position
                            const updatePos = op.position - 1;
                            const updateDescription = op.step ? op.step.description : op.description;
                            if (testCase.steps[updatePos]) {
                                testCase.steps[updatePos].description = updateDescription;
                            }
                            break;
                    }
                });
            }
            break;
            
        case 'ADD':
            // Add new test cases manually
            if (data.new_cases && Array.isArray(data.new_cases)) {
                // Generate IDs for new cases
                const maxId = testCases.reduce((max, tc) => {
                    const num = parseInt(tc.id.replace('TC-', ''));
                    return num > max ? num : max;
                }, 0);
                
                data.new_cases.forEach((newCase, index) => {
                    const caseId = `TC-${String(maxId + index + 1).padStart(3, '0')}`;
                    testCases.push({
                        id: caseId,
                        name: newCase.name || 'New Test Case',
                        description: newCase.description || '',
                        priority: newCase.priority || 'Medium',
                        preconditions: newCase.preconditions || '',
                        expectedResult: newCase.expectedResult || newCase.expected_result || '',
                        testData: newCase.testData || newCase.test_data || '',
                        steps: newCase.steps || []
                    });
                });
            }
            break;
            
        case 'GENERATE':
            // Generate new test cases from AI
            if (data.new_cases && Array.isArray(data.new_cases)) {
                // Generate IDs for new cases
                const maxId = testCases.reduce((max, tc) => {
                    const num = parseInt(tc.id.replace('TC-', ''));
                    return num > max ? num : max;
                }, 0);
                
                data.new_cases.forEach((newCase, index) => {
                    const caseId = `TC-${String(maxId + index + 1).padStart(3, '0')}`;
                    testCases.push({
                        id: caseId,
                        name: newCase.name || 'Generated Test Case',
                        description: newCase.description || '',
                        priority: newCase.priority || 'Medium',
                        preconditions: newCase.preconditions || '',
                        expectedResult: newCase.expectedResult || newCase.expected_result || '',
                        testData: newCase.testData || newCase.test_data || '',
                        steps: newCase.steps || []
                    });
                });
            }
            break;
            
        case 'MULTIPLE':
            // Handle multiple actions
            if (data.actions && Array.isArray(data.actions)) {
                data.actions.forEach(subAction => {
                    applyChanges({ action: subAction.type, data: subAction });
                });
            }
            break;
            
        case 'QUERY':
            // No changes to apply, just informational
            break;
            
        default:
            console.warn('Unknown action type:', action);
    }
    
    // Update the display
    displayTestCases();
    
    // Update current test plan
    if (currentTestPlan) {
        currentTestPlan.testCases = testCases;
        currentTestPlan.lastModified = new Date().toISOString();
    }
}

// Logout
function logout() {
    sessionStorage.clear();
    window.location.href = 'login.html';
}

// Show loading overlay
function showLoadingOverlay() {
    const overlay = document.getElementById('loading-overlay');
    overlay.style.display = 'flex';
}

// Hide loading overlay
function hideLoadingOverlay() {
    const overlay = document.getElementById('loading-overlay');
    overlay.style.display = 'none';
}
