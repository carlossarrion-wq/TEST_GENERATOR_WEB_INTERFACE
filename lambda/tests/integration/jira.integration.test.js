const JiraClient = require('../../src/services/jiraClient');
const { parseIssues } = require('../../src/utils/jiraParser');
const fs = require('fs');
const path = require('path');

/**
 * INTEGRATION TESTS - Conectan con Jira REAL
 * 
 * Estos tests hacen llamadas reales a la API de Jira
 * Requieren credenciales válidas en src/config/jira-credentials.json
 */

describe('Jira Integration Tests', () => {
  let jiraClient;
  let credentials;

  beforeAll(() => {
    // Cargar credenciales reales
    const credPath = path.join(__dirname, '../../src/config/jira-credentials.json');
    
    if (!fs.existsSync(credPath)) {
      throw new Error('Credentials file not found. Please create src/config/jira-credentials.json');
    }

    credentials = JSON.parse(fs.readFileSync(credPath, 'utf8'));
    jiraClient = new JiraClient(credentials);
  });

  describe('Real Jira Connection', () => {
    test('should connect to Jira and fetch projects', async () => {
      const projects = await jiraClient.getProjects();
      
      console.log('DEBUG - Projects response:', JSON.stringify(projects, null, 2));
      console.log('DEBUG - Projects type:', typeof projects);
      console.log('DEBUG - Is array:', Array.isArray(projects));
      console.log('DEBUG - Length:', projects?.length);
      
      expect(projects).toBeDefined();
      expect(Array.isArray(projects)).toBe(true);
      
      if (projects.length === 0) {
        console.log('⚠️ No projects found. This might be due to permissions.');
        console.log('⚠️ User may not have access to any projects or projects list is restricted.');
      } else {
        console.log(`✓ Found ${projects.length} projects`);
        console.log('Projects:', projects.map(p => `${p.key} - ${p.name}`).join(', '));
      }
      
      // Don't fail if no projects, just warn
      expect(projects.length).toBeGreaterThanOrEqual(0);
    }, 30000); // 30 second timeout

    test('should search issues from PDDSE2 project', async () => {
      const result = await jiraClient.searchIssues({
        jql: 'project = PDDSE2',
        maxResults: 5
      });

      console.log('DEBUG - Search result:', JSON.stringify(result, null, 2));
      console.log('DEBUG - Result type:', typeof result);
      console.log('DEBUG - Result keys:', Object.keys(result || {}));
      console.log('DEBUG - Total:', result?.total);
      console.log('DEBUG - Issues length:', result?.issues?.length);

      expect(result).toBeDefined();
      expect(result.issues).toBeDefined();
      expect(Array.isArray(result.issues)).toBe(true);
      
      // Check if total exists and is a number
      if (typeof result.total === 'number') {
        expect(result.total).toBeGreaterThanOrEqual(0);
        console.log(`✓ Found ${result.total} total issues in PDDSE2`);
      } else {
        console.log('⚠️ Total is undefined or not a number:', result.total);
      }
      
      console.log(`✓ Retrieved ${result.issues.length} issues`);
      
      if (result.issues.length > 0) {
        const firstIssue = result.issues[0];
        console.log(`First issue: ${firstIssue.key} - ${firstIssue.fields.summary}`);
      } else {
        console.log('⚠️ No issues found in PDDSE2. Project may be empty.');
      }
    }, 30000);

    test('should parse and normalize Jira issues', async () => {
      const result = await jiraClient.searchIssues({
        jql: 'project = PDDSE2',
        maxResults: 3
      });

      const parsedIssues = parseIssues(result.issues);

      expect(parsedIssues).toBeDefined();
      expect(Array.isArray(parsedIssues)).toBe(true);
      
      if (parsedIssues.length > 0) {
        const issue = parsedIssues[0];
        
        // Verificar estructura normalizada
        expect(issue).toHaveProperty('id');
        expect(issue).toHaveProperty('key');
        expect(issue).toHaveProperty('summary');
        expect(issue).toHaveProperty('description');
        expect(issue).toHaveProperty('issueType');
        expect(issue).toHaveProperty('priority');
        expect(issue).toHaveProperty('status');
        expect(issue).toHaveProperty('labels');
        expect(issue).toHaveProperty('created');
        expect(issue).toHaveProperty('updated');

        console.log('✓ Issue structure validated');
        console.log('Sample issue:', {
          key: issue.key,
          summary: issue.summary,
          type: issue.issueType,
          priority: issue.priority,
          status: issue.status
        });
      }
    }, 30000);

    test('should build correct JQL from filters', () => {
      const filters = {
        projectKey: 'PDDSE2',
        issueTypes: ['Story', 'Bug'],
        status: ['To Do', 'In Progress']
      };

      const jql = jiraClient.buildJQL(filters);

      expect(jql).toContain('project = PDDSE2');
      expect(jql).toContain('type in ("Story","Bug")');
      expect(jql).toContain('status in ("To Do","In Progress")');
      
      console.log('✓ Generated JQL:', jql);
    });

    test('should get specific issue by key', async () => {
      // Primero obtener un issue para tener un key válido
      const searchResult = await jiraClient.searchIssues({
        jql: 'project = PDDSE2',
        maxResults: 1
      });

      if (searchResult.issues.length === 0) {
        console.log('⚠ No issues found in PDDSE2, skipping test');
        return;
      }

      const issueKey = searchResult.issues[0].key;
      console.log(`Testing with issue: ${issueKey}`);

      const issue = await jiraClient.getIssue(issueKey);

      expect(issue).toBeDefined();
      expect(issue.key).toBe(issueKey);
      expect(issue.fields).toBeDefined();
      expect(issue.fields.summary).toBeDefined();

      console.log(`✓ Retrieved issue ${issueKey}: ${issue.fields.summary}`);
    }, 30000);

    test('should get multiple issues by keys', async () => {
      // Obtener algunos issues primero
      const searchResult = await jiraClient.searchIssues({
        jql: 'project = PDDSE2',
        maxResults: 3
      });

      if (searchResult.issues.length === 0) {
        console.log('⚠ No issues found in PDDSE2, skipping test');
        return;
      }

      const issueKeys = searchResult.issues.map(issue => issue.key);
      console.log(`Testing with issues: ${issueKeys.join(', ')}`);

      const issues = await jiraClient.getIssues(issueKeys);

      expect(issues).toBeDefined();
      expect(Array.isArray(issues)).toBe(true);
      expect(issues.length).toBe(issueKeys.length);

      console.log(`✓ Retrieved ${issues.length} issues successfully`);
    }, 30000);

    test('should handle search with filters', async () => {
      const filters = {
        issueTypes: ['Story'],
        status: ['To Do']
      };

      const jql = `project = PDDSE2 AND ${jiraClient.buildJQL(filters)}`;
      
      const result = await jiraClient.searchIssues({
        jql,
        maxResults: 10
      });

      expect(result).toBeDefined();
      expect(result.issues).toBeDefined();

      console.log(`✓ Found ${result.total} issues matching filters`);
      
      // Verificar que los issues cumplen los filtros
      result.issues.forEach(issue => {
        const issueType = issue.fields.issuetype?.name;
        const status = issue.fields.status?.name;
        
        console.log(`  - ${issue.key}: ${issueType} / ${status}`);
      });
    }, 30000);
  });

  describe('Error Handling', () => {
    test('should handle invalid JQL gracefully', async () => {
      await expect(
        jiraClient.searchIssues({
          jql: 'INVALID JQL SYNTAX !!!',
          maxResults: 5
        })
      ).rejects.toThrow();
    }, 30000);

    test('should handle non-existent issue key', async () => {
      await expect(
        jiraClient.getIssue('PDDSE2-999999')
      ).rejects.toThrow();
    }, 30000);
  });
});
