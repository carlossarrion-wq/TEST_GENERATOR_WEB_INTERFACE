const JiraClient = require('../services/jiraClient');
const { parseIssues } = require('../utils/jiraParser');
const { validateIssueKeysRequest } = require('../utils/validators');
const fs = require('fs');
const path = require('path');

/**
 * Lambda handler for getting specific Jira issues by their keys
 * @param {Object} event - Lambda event
 * @returns {Promise<Object>} Lambda response
 */
async function handler(event) {
  console.log('Get Issues Handler invoked', {
    httpMethod: event.httpMethod,
    path: event.path
  });

  try {
    // Parse request body
    const body = JSON.parse(event.body || '{}');
    
    // Validate request
    const validation = validateIssueKeysRequest(body);
    if (!validation.valid) {
      return createResponse(400, {
        success: false,
        error: 'Validation failed',
        details: validation.errors
      });
    }

    // Load Jira credentials
    const credentials = loadJiraCredentials();
    
    // Create Jira client
    const jiraClient = new JiraClient(credentials);
    
    // Get issues
    const issueKeys = body.issueKeys;
    console.log('Fetching issues:', issueKeys);
    
    const rawIssues = await jiraClient.getIssues(issueKeys);
    
    // Parse and normalize issues
    const parsedIssues = parseIssues(rawIssues);
    
    // Check for missing issues
    const foundKeys = parsedIssues.map(issue => issue.key);
    const missingKeys = issueKeys.filter(key => !foundKeys.includes(key));

    // Build response
    const response = {
      success: true,
      issues: parsedIssues,
      summary: {
        requested: issueKeys.length,
        found: parsedIssues.length,
        missing: missingKeys.length,
        missingKeys: missingKeys
      },
      fetchedAt: new Date().toISOString()
    };

    console.log('Issues fetched successfully', {
      requested: issueKeys.length,
      found: parsedIssues.length,
      missing: missingKeys.length
    });

    return createResponse(200, response);

  } catch (error) {
    console.error('Error in get issues handler:', error);
    
    return createResponse(error.statusCode || 500, {
      success: false,
      error: error.message || 'Internal server error',
      details: error.details || {}
    });
  }
}

/**
 * Load Jira credentials from config file or environment variables
 * @returns {Object} Jira credentials
 */
function loadJiraCredentials() {
  // Try to load from config file first (for local development)
  const configPath = path.join(__dirname, '../config/jira-credentials.json');
  
  if (fs.existsSync(configPath)) {
    console.log('Loading Jira credentials from config file');
    const credentials = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    
    // Validate credentials
    if (!credentials.jiraUrl || !credentials.jiraEmail || !credentials.jiraApiToken) {
      throw new Error('Invalid credentials in config file. Missing required fields.');
    }
    
    return credentials;
  }
  
  // If config file doesn't exist, try environment variables
  if (process.env.JIRA_URL && process.env.JIRA_EMAIL && process.env.JIRA_API_TOKEN) {
    console.log('Loading Jira credentials from environment variables');
    return {
      jiraUrl: process.env.JIRA_URL,
      jiraEmail: process.env.JIRA_EMAIL,
      jiraApiToken: process.env.JIRA_API_TOKEN
    };
  }
  
  throw new Error('Jira credentials not found. Please provide credentials in config file or environment variables.');
}

/**
 * Create HTTP response
 * @param {number} statusCode - HTTP status code
 * @param {Object} body - Response body
 * @returns {Object} Lambda response
 */
function createResponse(statusCode, body) {
  return {
    statusCode,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Content-Type,Authorization',
      'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
    },
    body: JSON.stringify(body)
  };
}

module.exports = { handler };
