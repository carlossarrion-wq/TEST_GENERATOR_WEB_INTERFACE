// Login functionality for Test Plan Generator

document.addEventListener('DOMContentLoaded', function() {
    // Initialize login page
    initializeLoginPage();
});

function initializeLoginPage() {
    // Check if already authenticated
    if (apiService.isAuthenticated()) {
        window.location.href = 'index.html';
        return;
    }
    
    // Set up form submission
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    // Set up Enter key handling
    const accessKeyInput = document.getElementById('access-key');
    const secretKeyInput = document.getElementById('secret-key');
    
    if (accessKeyInput) {
        accessKeyInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                secretKeyInput.focus();
            }
        });
    }
    
    if (secretKeyInput) {
        secretKeyInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                handleLogin(e);
            }
        });
    }
}

async function handleLogin(event) {
    event.preventDefault();
    
    const accessKey = document.getElementById('access-key').value.trim();
    const secretKey = document.getElementById('secret-key').value.trim();
    const loginButton = document.getElementById('login-button');
    const errorContainer = document.getElementById('error-message');
    
    // Clear previous errors
    hideError();
    
    // Validate inputs
    if (!accessKey || !secretKey) {
        showError('Please enter both Access Key and Secret Key');
        return;
    }
    
    // Validate Access Key format (basic AWS format check)
    if (!accessKey.match(/^AKIA[0-9A-Z]{16}$/i) && !accessKey.startsWith('ASIA')) {
        showError('Access Key format appears invalid. AWS Access Keys typically start with AKIA or ASIA.');
        return;
    }
    
    // Show loading state
    const originalButtonText = loginButton.innerHTML;
    loginButton.disabled = true;
    loginButton.innerHTML = '<div class="loading-spinner"></div> Authenticating...';
    
    try {
        console.log('🔐 Attempting login with AWS credentials...');
        
        // Call authentication API
        const response = await fetch(`${apiService.baseURL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                access_key: accessKey,
                secret_key: secretKey
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || data.error || `HTTP ${response.status}`);
        }
        
        console.log('✅ Authentication successful:', data);
        
        // Store authentication data
        sessionStorage.setItem('session_token', data.session_token);
        sessionStorage.setItem('expires_at', data.expires_at.toString());
        sessionStorage.setItem('access_key', accessKey);
        
        // Store user information
        if (data.user) {
            sessionStorage.setItem('user_id', data.user.id.toString());
            sessionStorage.setItem('username', data.user.access_key);
            
            if (data.user.aws_user_info) {
                sessionStorage.setItem('aws_user_info', JSON.stringify(data.user.aws_user_info));
            }
            
            if (data.user.permissions) {
                sessionStorage.setItem('user_permissions', JSON.stringify(data.user.permissions));
            }
        }
        
        console.log('💾 Authentication data stored in sessionStorage');
        
        // Show success message briefly before redirect
        loginButton.innerHTML = '✅ Authentication Successful!';
        loginButton.style.backgroundColor = '#48bb78';
        
        // Redirect to main application
        setTimeout(() => {
            window.location.href = 'index.html';
        }, 1000);
        
    } catch (error) {
        console.error('❌ Login failed:', error);
        
        // Reset button
        loginButton.disabled = false;
        loginButton.innerHTML = originalButtonText;
        loginButton.style.backgroundColor = '';
        
        // Show error message
        let errorMessage = 'Authentication failed. Please check your credentials.';
        
        if (error.message) {
            if (error.message.includes('Invalid AWS Access Key') || error.message.includes('Invalid Access Key')) {
                errorMessage = 'Invalid AWS Access Key or Secret Key. Please verify your credentials.';
            } else if (error.message.includes('Network error') || error.message.includes('fetch')) {
                errorMessage = 'Network error. Please check your internet connection and try again.';
            } else if (error.message.includes('Account is deactivated')) {
                errorMessage = 'Your account has been deactivated. Please contact support.';
            } else {
                errorMessage = error.message;
            }
        }
        
        showError(errorMessage);
    }
}

function showError(message) {
    const errorContainer = document.getElementById('error-message');
    if (errorContainer) {
        errorContainer.textContent = message;
        errorContainer.style.display = 'block';
        errorContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

function hideError() {
    const errorContainer = document.getElementById('error-message');
    if (errorContainer) {
        errorContainer.style.display = 'none';
        errorContainer.textContent = '';
    }
}

// Test credentials function (for demo purposes)
function testCredentials() {
    document.getElementById('access-key').value = 'DEMO123456789EXAMPLE';
    document.getElementById('secret-key').value = 'demo-secret-key-for-testing-only';
    showError('Demo credentials filled. Note: These are test credentials and may not work with real AWS services.');
}
