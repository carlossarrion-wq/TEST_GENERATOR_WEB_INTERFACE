const {
  validateJiraImportRequest,
  validateIssueKeysRequest,
  sanitizeJQL
} = require('../../../src/utils/validators');

describe('Validators', () => {
  describe('validateJiraImportRequest', () => {
    test('TC-006: should validate valid request with projectKey', () => {
      const body = {
        projectKey: 'PDDSE2',
        maxResults: 50
      };

      const result = validateJiraImportRequest(body);

      expect(result.valid).toBe(true);
      expect(result.errors).toEqual([]);
    });

    test('TC-007: should reject request without projectKey or filters', () => {
      const body = {};

      const result = validateJiraImportRequest(body);

      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Either projectKey or filters must be provided');
    });

    test('TC-008: should reject maxResults out of range', () => {
      const body = {
        projectKey: 'PDDSE2',
        maxResults: 150
      };

      const result = validateJiraImportRequest(body);

      expect(result.valid).toBe(false);
      expect(result.errors).toContain('maxResults must be a number between 1 and 100');
    });

    test('should validate request with filters only', () => {
      const body = {
        filters: {
          issueTypes: ['Story', 'Bug'],
          status: ['To Do']
        }
      };

      const result = validateJiraImportRequest(body);

      expect(result.valid).toBe(true);
      expect(result.errors).toEqual([]);
    });

    test('should reject invalid filters.issueTypes', () => {
      const body = {
        projectKey: 'PDDSE2',
        filters: {
          issueTypes: 'Story' // Should be array
        }
      };

      const result = validateJiraImportRequest(body);

      expect(result.valid).toBe(false);
      expect(result.errors).toContain('filters.issueTypes must be an array');
    });
  });

  describe('validateIssueKeysRequest', () => {
    test('TC-009: should validate valid issueKeys array', () => {
      const body = {
        issueKeys: ['PDDSE2-1', 'PDDSE2-2', 'PDDSE2-3']
      };

      const result = validateIssueKeysRequest(body);

      expect(result.valid).toBe(true);
      expect(result.errors).toEqual([]);
    });

    test('TC-010: should reject empty issueKeys array', () => {
      const body = {
        issueKeys: []
      };

      const result = validateIssueKeysRequest(body);

      expect(result.valid).toBe(false);
      expect(result.errors).toContain('issueKeys array cannot be empty');
    });

    test('should reject missing issueKeys', () => {
      const body = {};

      const result = validateIssueKeysRequest(body);

      expect(result.valid).toBe(false);
      expect(result.errors).toContain('issueKeys is required');
    });

    test('should reject non-array issueKeys', () => {
      const body = {
        issueKeys: 'PDDSE2-1'
      };

      const result = validateIssueKeysRequest(body);

      expect(result.valid).toBe(false);
      expect(result.errors).toContain('issueKeys must be an array');
    });

    test('should reject issueKeys array with more than 50 items', () => {
      const body = {
        issueKeys: Array(51).fill('PDDSE2-1')
      };

      const result = validateIssueKeysRequest(body);

      expect(result.valid).toBe(false);
      expect(result.errors).toContain('issueKeys array cannot contain more than 50 items');
    });
  });

  describe('sanitizeJQL', () => {
    test('should trim JQL string', () => {
      const jql = '  project = PDDSE2  ';
      const result = sanitizeJQL(jql);
      expect(result).toBe('project = PDDSE2');
    });

    test('should return empty string for null', () => {
      const result = sanitizeJQL(null);
      expect(result).toBe('');
    });

    test('should return empty string for non-string', () => {
      const result = sanitizeJQL(123);
      expect(result).toBe('');
    });
  });
});
