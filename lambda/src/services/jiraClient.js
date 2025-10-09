const axios = require('axios');
const axiosRetry = require('axios-retry').default;

/**
 * Jira API Client
 * Handles all HTTP communication with Jira REST API
 */
class JiraClient {
  constructor(credentials) {
    this.jiraUrl = credentials.jiraUrl;
    this.jiraEmail = credentials.jiraEmail;
    this.jiraApiToken = credentials.jiraApiToken;
    
    // Create axios instance with base configuration
    this.client = axios.create({
      baseURL: `${this.jiraUrl}/rest/api/3`,
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      auth: {
        username: this.jiraEmail,
        password: this.jiraApiToken
      },
      timeout: 30000 // 30 seconds
    });

    // Configure retry strategy
    axiosRetry(this.client, {
      retries: 3,
      retryDelay: axiosRetry.exponentialDelay,
      retryCondition: (error) => {
        // Retry on network errors or 5xx errors or 429 (rate limit)
        return axiosRetry.isNetworkOrIdempotentRequestError(error) ||
               error.response?.status === 429 ||
               (error.response?.status >= 500 && error.response?.status < 600);
      },
      onRetry: (retryCount, error, requestConfig) => {
        console.log(`Retry attempt ${retryCount} for ${requestConfig.url}`, {
          status: error.response?.status,
          message: error.message
        });
      }
    });
  }

  /**
   * Search for issues using JQL (Jira Query Language)
   * @param {Object} params - Search parameters
   * @param {string} params.jql - JQL query string
   * @param {number} params.maxResults - Maximum number of results (default: 50)
   * @param {number} params.startAt - Starting index for pagination (default: 0)
   * @param {string[]} params.fields - Fields to return (default: all)
   * @returns {Promise<Object>} Search results
   */
  async searchIssues({ jql, maxResults = 50, startAt = 0, fields = [] }) {
    try {
      const params = {
        jql,
        maxResults,
        startAt
      };

      if (fields.length > 0) {
        params.fields = fields.join(',');
      }

      console.log('Searching Jira issues', { jql, maxResults, startAt, fields: params.fields });

      const response = await this.client.get('/search/jql', { params });

      console.log('Jira API response:', {
        issuesCount: response.data.issues?.length || 0,
        hasNextPage: !response.data.isLast,
        nextPageToken: response.data.nextPageToken
      });

      return {
        issues: response.data.issues || [],
        total: response.data.issues?.length || 0,
        startAt: startAt,
        maxResults: maxResults,
        isLast: response.data.isLast,
        nextPageToken: response.data.nextPageToken
      };
    } catch (error) {
      this._handleError(error, 'searchIssues');
    }
  }

  /**
   * Get a single issue by key or ID
   * @param {string} issueIdOrKey - Issue key (e.g., 'PROJ-123') or ID
   * @param {string[]} fields - Fields to return (default: all)
   * @returns {Promise<Object>} Issue details
   */
  async getIssue(issueIdOrKey, fields = []) {
    try {
      const params = {};
      if (fields.length > 0) {
        params.fields = fields.join(',');
      }

      console.log('Fetching Jira issue', { issueIdOrKey });

      const response = await this.client.get(`/issue/${issueIdOrKey}`, { params });
      return response.data;
    } catch (error) {
      this._handleError(error, 'getIssue');
    }
  }

  /**
   * Get multiple issues by their keys
   * @param {string[]} issueKeys - Array of issue keys
   * @returns {Promise<Object[]>} Array of issue details
   */
  async getIssues(issueKeys) {
    try {
      if (!issueKeys || issueKeys.length === 0) {
        return [];
      }

      // Build JQL query to fetch multiple issues
      const jql = `key in (${issueKeys.join(',')})`;
      
      const result = await this.searchIssues({
        jql,
        maxResults: issueKeys.length
      });

      return result.issues;
    } catch (error) {
      this._handleError(error, 'getIssues');
    }
  }

  /**
   * Get all custom fields available in Jira
   * @returns {Promise<Object[]>} Array of field definitions
   */
  async getFields() {
    try {
      console.log('Fetching Jira fields');
      const response = await this.client.get('/field');
      return response.data;
    } catch (error) {
      this._handleError(error, 'getFields');
    }
  }

  /**
   * Get projects accessible to the user
   * @returns {Promise<Object[]>} Array of projects
   */
  async getProjects() {
    try {
      console.log('Fetching Jira projects');
      const response = await this.client.get('/project');
      return response.data;
    } catch (error) {
      this._handleError(error, 'getProjects');
    }
  }

  /**
   * Build JQL query from filters
   * @param {Object} filters - Filter object
   * @param {string} filters.projectKey - Project key
   * @param {string[]} filters.issueTypes - Issue types to filter
   * @param {string[]} filters.status - Status values to filter
   * @param {string[]} filters.labels - Labels to filter
   * @param {string} filters.sprint - Sprint name
   * @returns {string} JQL query string
   */
  buildJQL(filters) {
    const conditions = [];

    if (filters.projectKey) {
      conditions.push(`project = ${filters.projectKey}`);
    }

    if (filters.issueTypes && filters.issueTypes.length > 0) {
      const types = filters.issueTypes.map(t => `"${t}"`).join(',');
      conditions.push(`type in (${types})`);
    }

    if (filters.status && filters.status.length > 0) {
      const statuses = filters.status.map(s => `"${s}"`).join(',');
      conditions.push(`status in (${statuses})`);
    }

    if (filters.labels && filters.labels.length > 0) {
      const labels = filters.labels.map(l => `"${l}"`).join(',');
      conditions.push(`labels in (${labels})`);
    }

    if (filters.sprint) {
      conditions.push(`sprint = "${filters.sprint}"`);
    }

    return conditions.join(' AND ');
  }

  /**
   * Handle API errors
   * @private
   */
  _handleError(error, operation) {
    const errorInfo = {
      operation,
      message: error.message,
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data
    };

    console.error('Jira API Error:', errorInfo);

    // Create user-friendly error message
    let userMessage = 'Error communicating with Jira';
    
    if (error.response) {
      switch (error.response.status) {
        case 401:
          userMessage = 'Authentication failed. Please check your Jira credentials.';
          break;
        case 403:
          userMessage = 'Access denied. You do not have permission to access this resource.';
          break;
        case 404:
          userMessage = 'Resource not found in Jira.';
          break;
        case 429:
          userMessage = 'Rate limit exceeded. Please try again later.';
          break;
        case 500:
        case 502:
        case 503:
        case 504:
          userMessage = 'Jira server error. Please try again later.';
          break;
        default:
          userMessage = error.response.data?.errorMessages?.[0] || 
                       error.response.data?.message || 
                       'Unknown error occurred';
      }
    } else if (error.code === 'ECONNABORTED') {
      userMessage = 'Request timeout. Jira is taking too long to respond.';
    } else if (error.code === 'ENOTFOUND' || error.code === 'ECONNREFUSED') {
      userMessage = 'Cannot connect to Jira. Please check the URL.';
    }

    const customError = new Error(userMessage);
    customError.originalError = error;
    customError.statusCode = error.response?.status || 500;
    customError.details = errorInfo;

    throw customError;
  }
}

module.exports = JiraClient;
