/**
 * Main entry point for Lambda functions
 * Routes requests to appropriate handlers
 */

const jiraImportHandler = require('./handlers/jiraImport');
const getIssuesHandler = require('./handlers/getIssues');

/**
 * Main Lambda handler
 * Routes requests based on path and method
 */
exports.handler = async (event, context) => {
  console.log('Lambda invoked', {
    path: event.path,
    httpMethod: event.httpMethod,
    requestId: context.requestId
  });

  try {
    // Handle OPTIONS requests for CORS
    if (event.httpMethod === 'OPTIONS') {
      return {
        statusCode: 200,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Headers': 'Content-Type,Authorization',
          'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        },
        body: ''
      };
    }

    // Route to appropriate handler based on path
    const path = event.path || event.rawPath || '';
    
    if (path.includes('/jira/import') || path.includes('/import')) {
      return await jiraImportHandler.handler(event, context);
    }
    
    if (path.includes('/jira/issues') || path.includes('/issues')) {
      return await getIssuesHandler.handler(event, context);
    }

    // Default: return 404
    return {
      statusCode: 404,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify({
        success: false,
        error: 'Not Found',
        message: `Path ${path} not found`,
        availableEndpoints: [
          'POST /jira/import - Import Jira issues',
          'POST /jira/issues - Get specific issues by keys'
        ]
      })
    };

  } catch (error) {
    console.error('Unhandled error in main handler:', error);
    
    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify({
        success: false,
        error: 'Internal Server Error',
        message: error.message
      })
    };
  }
};

// Export individual handlers for direct invocation
exports.jiraImport = jiraImportHandler.handler;
exports.getIssues = getIssuesHandler.handler;
