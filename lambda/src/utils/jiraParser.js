/**
 * Jira response parsing utilities
 */

/**
 * Convert Atlassian Document Format (ADF) to plain text
 * @param {Object|string} adfContent - ADF content or plain string
 * @returns {string} Plain text representation
 */
function adfToPlainText(adfContent) {
  // If it's already a string, return it
  if (typeof adfContent === 'string') {
    return adfContent;
  }

  // If it's null or undefined, return empty string
  if (!adfContent) {
    return '';
  }

  // If it's not an object, convert to string
  if (typeof adfContent !== 'object') {
    return String(adfContent);
  }

  // Handle ADF format
  let text = '';

  function extractText(node) {
    if (!node) return;

    // If node has text property, add it
    if (node.text) {
      text += node.text;
    }

    // Process content array recursively
    if (Array.isArray(node.content)) {
      node.content.forEach(childNode => {
        extractText(childNode);
        
        // Add line breaks for paragraphs and other block elements
        if (childNode.type === 'paragraph' || 
            childNode.type === 'heading' || 
            childNode.type === 'codeBlock') {
          text += '\n';
        }
      });
    }

    // Handle list items
    if (node.type === 'listItem') {
      text += '\n• ';
    }

    // Handle hard breaks
    if (node.type === 'hardBreak') {
      text += '\n';
    }
  }

  extractText(adfContent);

  // Clean up extra whitespace and newlines
  return text.trim().replace(/\n{3,}/g, '\n\n');
}

/**
 * Parse and normalize a Jira issue
 * @param {Object} issue - Raw Jira issue
 * @returns {Object} Normalized issue
 */
function parseIssue(issue) {
  if (!issue || !issue.fields) {
    return null;
  }

  return {
    id: issue.id,
    key: issue.key,
    summary: issue.fields.summary || '',
    description: adfToPlainText(issue.fields.description),
    issueType: issue.fields.issuetype?.name || 'Unknown',
    priority: issue.fields.priority?.name || 'Medium',
    status: issue.fields.status?.name || 'Unknown',
    assignee: issue.fields.assignee ? {
      displayName: issue.fields.assignee.displayName,
      emailAddress: issue.fields.assignee.emailAddress,
      accountId: issue.fields.assignee.accountId
    } : null,
    reporter: issue.fields.reporter ? {
      displayName: issue.fields.reporter.displayName,
      emailAddress: issue.fields.reporter.emailAddress,
      accountId: issue.fields.reporter.accountId
    } : null,
    labels: issue.fields.labels || [],
    components: issue.fields.components?.map(c => c.name) || [],
    created: issue.fields.created,
    updated: issue.fields.updated,
    customFields: extractCustomFields(issue.fields)
  };
}

/**
 * Parse multiple Jira issues
 * @param {Object[]} issues - Array of raw Jira issues
 * @returns {Object[]} Array of normalized issues
 */
function parseIssues(issues) {
  if (!Array.isArray(issues)) {
    return [];
  }

  return issues
    .map(issue => parseIssue(issue))
    .filter(issue => issue !== null);
}

/**
 * Extract custom fields from issue
 * @param {Object} fields - Issue fields
 * @returns {Object} Custom fields
 */
function extractCustomFields(fields) {
  const customFields = {};
  
  // Common custom fields
  const customFieldMappings = {
    'customfield_10000': 'acceptanceCriteria',
    'customfield_10001': 'storyPoints',
    'customfield_10002': 'epic',
    'customfield_10003': 'sprint'
  };

  Object.keys(fields).forEach(key => {
    if (key.startsWith('customfield_')) {
      const mappedName = customFieldMappings[key] || key;
      const value = fields[key];
      
      if (value !== null && value !== undefined) {
        customFields[mappedName] = value;
      }
    }
  });

  return customFields;
}

/**
 * Format issue for display
 * @param {Object} issue - Normalized issue
 * @returns {Object} Formatted issue for frontend
 */
function formatIssueForDisplay(issue) {
  return {
    id: issue.key,
    key: issue.key,
    summary: issue.summary,
    description: truncateText(issue.description, 200),
    issueType: issue.issueType,
    priority: issue.priority,
    status: issue.status,
    assignee: issue.assignee?.displayName || 'Unassigned',
    labels: issue.labels,
    created: formatDate(issue.created),
    updated: formatDate(issue.updated)
  };
}

/**
 * Truncate text to specified length
 * @param {string} text - Text to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} Truncated text
 */
function truncateText(text, maxLength) {
  if (!text || text.length <= maxLength) {
    return text;
  }
  
  return text.substring(0, maxLength) + '...';
}

/**
 * Format date for display
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date
 */
function formatDate(dateString) {
  if (!dateString) {
    return '';
  }
  
  const date = new Date(dateString);
  return date.toLocaleDateString('es-ES', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

/**
 * Group issues by status
 * @param {Object[]} issues - Array of issues
 * @returns {Object} Issues grouped by status
 */
function groupByStatus(issues) {
  return issues.reduce((groups, issue) => {
    const status = issue.status || 'Unknown';
    if (!groups[status]) {
      groups[status] = [];
    }
    groups[status].push(issue);
    return groups;
  }, {});
}

/**
 * Group issues by priority
 * @param {Object[]} issues - Array of issues
 * @returns {Object} Issues grouped by priority
 */
function groupByPriority(issues) {
  return issues.reduce((groups, issue) => {
    const priority = issue.priority || 'Medium';
    if (!groups[priority]) {
      groups[priority] = [];
    }
    groups[priority].push(issue);
    return groups;
  }, {});
}

/**
 * Calculate statistics for issues
 * @param {Object[]} issues - Array of issues
 * @returns {Object} Statistics
 */
function calculateStatistics(issues) {
  const stats = {
    total: issues.length,
    byStatus: {},
    byPriority: {},
    byIssueType: {}
  };

  issues.forEach(issue => {
    // Count by status
    const status = issue.status || 'Unknown';
    stats.byStatus[status] = (stats.byStatus[status] || 0) + 1;

    // Count by priority
    const priority = issue.priority || 'Medium';
    stats.byPriority[priority] = (stats.byPriority[priority] || 0) + 1;

    // Count by issue type
    const issueType = issue.issueType || 'Unknown';
    stats.byIssueType[issueType] = (stats.byIssueType[issueType] || 0) + 1;
  });

  return stats;
}

module.exports = {
  parseIssue,
  parseIssues,
  extractCustomFields,
  formatIssueForDisplay,
  truncateText,
  formatDate,
  groupByStatus,
  groupByPriority,
  calculateStatistics
};
