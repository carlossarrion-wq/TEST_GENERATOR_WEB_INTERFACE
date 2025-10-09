# How to Update the Jira Project Key

## Location to Modify

The project key is configured in the file: **`js/app.js`**

**Line number: 1027**

Current code:
```javascript
body: JSON.stringify({
    projectKey: 'PDDSE2',  // <-- CHANGE THIS LINE
    maxResults: 100
})
```

## How to Find Your Correct Project Key

### Option 1: From Jira URL
When you're viewing your Jira board, look at the URL:
```
https://csarrion.atlassian.net/jira/software/projects/XXXXX/board
                                                    ^^^^^
                                              This is your project key
```

### Option 2: From Issue Keys
Look at your issue keys in the screenshot you provided:
- If issues are named `PDDSE2-1`, `PDDSE2-2`, etc.
- The project key is usually the part before the dash: `PDDSE2`

However, sometimes the issue key prefix doesn't match the actual project key in Jira's API.

### Option 3: Check Jira Project Settings
1. Go to your Jira project
2. Click on "Project settings" (gear icon)
3. Look for "Project key" in the details section

## Steps to Update

1. **Find your correct project key** using one of the methods above

2. **Edit `js/app.js`** at line 1027:
   ```javascript
   body: JSON.stringify({
       projectKey: 'YOUR_ACTUAL_PROJECT_KEY',  // Replace with your key
       maxResults: 100
   })
   ```

3. **Save the file**

4. **Test the application**:
   - Open `index.html` in your browser
   - Login
   - Click "Import from Jira"
   - The modal should now load your real Jira issues

## Example

If your actual project key is `PDS2025`, change line 1027 to:
```javascript
body: JSON.stringify({
    projectKey: 'PDS2025',
    maxResults: 100
})
```

## Troubleshooting

If you still get "No issues found":

1. **Verify API token permissions**:
   - Go to https://id.atlassian.com/manage-profile/security/api-tokens
   - Make sure your token has access to the project

2. **Test with curl** (replace YOUR_KEY with your project key):
   ```bash
   curl -X POST https://2xlh113423.execute-api.eu-west-1.amazonaws.com/dev/jira/import \
     -H "Content-Type: application/json" \
     -d '{"projectKey": "YOUR_KEY", "maxResults": 5}'
   ```

3. **Check the response** - it should return your issues

## Need Help?

If you're still having issues, please provide:
- The URL of your Jira board
- An example issue key (e.g., PDDSE2-1)
- The project name from Jira

This will help identify the correct project key to use.
