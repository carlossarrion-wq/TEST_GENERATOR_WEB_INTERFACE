const JiraClient = require('../services/jiraClient');
const { parseIssues, calculateStatistics } = require('../utils/jiraParser');
const { validateJiraImportRequest } = require('../utils/validators');
const fs = require('fs');
const path = require('path');

/**
 * Lambda handler for importing Jira issues
 * @param {Object} event - Lambda event
 * @returns {Promise<Object>} Lambda response
 */
async function handler(event) {
  console.log('Jira Import Handler invoked', {
    httpMethod: event.httpMethod,
    path: event.path
  });

  try {
    // Parse request body
    const body = JSON.parse(event.body || '{}');
    
    // Validate request
    const validation = validateJiraImportRequest(body);
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
    
    // Build JQL query
    let jql;
    if (body.jql) {
      // Use custom JQL if provided
      jql = body.jql;
    } else if (body.projectKey) {
      // Simple project query
      jql = `project = ${body.projectKey}`;
      
      // Add filters if provided
      if (body.filters) {
        const additionalJql = jiraClient.buildJQL(body.filters);
        if (additionalJql) {
          jql += ` AND ${additionalJql}`;
        }
      }
    } else if (body.filters) {
      // Only filters provided
      jql = jiraClient.buildJQL(body.filters);
    }

    console.log('Executing JQL query:', jql);

    // Search issues
    const maxResults = body.maxResults || 50;
    const startAt = body.startAt || 0;
    
    // Define fields to retrieve
    const fields = [
      'key', 'summary', 'description', 'status', 'issuetype',
      'priority', 'assignee', 'reporter', 'created', 'updated',
      'resolutiondate', 'duedate', 'resolution', 'labels', 'components'
    ];
    
    const searchResult = await jiraClient.searchIssues({
      jql,
      maxResults,
      startAt,
      fields
    });

    // Parse and normalize issues
    const parsedIssues = parseIssues(searchResult.issues);
    
    // Calculate statistics
    const statistics = calculateStatistics(parsedIssues);

    // Build response
    const response = {
      success: true,
      issues: parsedIssues,
      pagination: {
        total: searchResult.total,
        startAt: searchResult.startAt,
        maxResults: searchResult.maxResults,
        returned: parsedIssues.length
      },
      statistics,
      query: {
        jql,
        executedAt: new Date().toISOString()
      }
    };

    console.log('Jira import successful', {
      issuesReturned: parsedIssues.length,
      total: searchResult.total
    });

    return createResponse(200, response);

  } catch (error) {
    console.error('Error in Jira import handler:', error);
    
    return createResponse(error.statusCode || 500, {
      success: false,
      error: error.message || 'Internal server error',
      details: error.details || {}
    });
  }
}

/**
 * Load Jira credentials from config file or Secrets Manager
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
