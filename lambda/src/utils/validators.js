/**
 * Input validation utilities
 */

/**
 * Validate Jira import request
 * @param {Object} body - Request body
 * @returns {Object} Validation result
 */
function validateJiraImportRequest(body) {
  const errors = [];

  if (!body) {
    return { valid: false, errors: ['Request body is required'] };
  }

  // Validate projectKey or filters
  if (!body.projectKey && !body.filters) {
    errors.push('Either projectKey or filters must be provided');
  }

  // Validate maxResults if provided
  if (body.maxResults !== undefined) {
    if (typeof body.maxResults !== 'number' || body.maxResults < 1 || body.maxResults > 100) {
      errors.push('maxResults must be a number between 1 and 100');
    }
  }

  // Validate filters if provided
  if (body.filters) {
    if (body.filters.issueTypes && !Array.isArray(body.filters.issueTypes)) {
      errors.push('filters.issueTypes must be an array');
    }
    if (body.filters.status && !Array.isArray(body.filters.status)) {
      errors.push('filters.status must be an array');
    }
    if (body.filters.labels && !Array.isArray(body.filters.labels)) {
      errors.push('filters.labels must be an array');
    }
  }

  return {
    valid: errors.length === 0,
    errors
  };
}

/**
 * Validate issue keys request
 * @param {Object} body - Request body
 * @returns {Object} Validation result
 */
function validateIssueKeysRequest(body) {
  const errors = [];

  if (!body) {
    return { valid: false, errors: ['Request body is required'] };
  }

  if (!body.issueKeys) {
    errors.push('issueKeys is required');
  } else if (!Array.isArray(body.issueKeys)) {
    errors.push('issueKeys must be an array');
  } else if (body.issueKeys.length === 0) {
    errors.push('issueKeys array cannot be empty');
  } else if (body.issueKeys.length > 50) {
    errors.push('issueKeys array cannot contain more than 50 items');
  }

  return {
    valid: errors.length === 0,
    errors
  };
}

/**
 * Sanitize JQL query
 * @param {string} jql - JQL query
 * @returns {string} Sanitized JQL
 */
function sanitizeJQL(jql) {
  if (!jql || typeof jql !== 'string') {
    return '';
  }
  
  // Remove potentially dangerous characters
  return jql.trim();
}

module.exports = {
  validateJiraImportRequest,
  validateIssueKeysRequest,
  sanitizeJQL
};
