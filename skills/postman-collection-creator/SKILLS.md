---
name: postman-collection-creator
description: Create, organize, and maintain comprehensive Postman collections for API testing and documentation. Use when building API test suites, documenting REST APIs, setting up automated tests with pre-request and test scripts, managing environments and variables, or creating collections for CI/CD integration. Includes expertise in request configuration, JavaScript test automation, data-driven testing, and collection best practices.
license: Apache-2.0
compatibility: Requires Postman Desktop or Web application. Newman CLI recommended for CI/CD integration.
metadata:
  author: korade-krushna
  version: "1.0"
  category: api-testing
---

# Postman Collection Creator Skill

This skill provides comprehensive guidance for creating, organizing, and maintaining high-quality Postman collections for API testing, documentation, and automation.

## When to Use This Skill

Use this skill when you need to:
- Create new Postman collections from scratch or API specifications
- Organize existing collections with proper folder structures
- Write pre-request and test scripts using JavaScript
- Set up environment and variable management
- Implement data-driven testing with CSV/JSON files
- Integrate collections into CI/CD pipelines using Newman
- Document API endpoints with examples and descriptions
- Create mock servers for API development

## Core Principles

### 1. Collection Organization
- Use hierarchical folder structures that mirror API resource organization
- Group related endpoints logically (by feature, resource type, or workflow)
- Name folders and requests clearly and consistently
- Keep collections focused on a single API or related set of endpoints

### 2. Naming Conventions
Follow consistent naming patterns:
- **Collections**: `[API Name] - [Purpose]` (e.g., "User Management API - V2")
- **Folders**: Use title case, group by resource (e.g., "User Management", "Authentication")
- **Requests**: `[HTTP Method] [Resource]` (e.g., "GET User by ID", "POST Create User")
- **Variables**: Use snake_case for environment variables (e.g., `base_url`, `auth_token`)

### 3. Progressive Disclosure
Structure collections for efficient navigation:
- Add collection-level descriptions with overview and prerequisites
- Document each folder's purpose
- Include detailed request descriptions with parameters and expected responses
- Provide example responses for success and error scenarios

## Creating Collections

### Basic Collection Structure

```
API Collection Name/
├── 📁 Authentication
│   ├── POST Login
│   ├── POST Refresh Token
│   └── POST Logout
├── 📁 Users
│   ├── GET List Users
│   ├── GET User by ID
│   ├── POST Create User
│   ├── PUT Update User
│   └── DELETE Delete User
└── 📁 Admin
    └── GET System Health
```

### Request Configuration Checklist

For each request, configure:
1. **Method and URL**: Correct HTTP method with parameterized URLs
2. **Headers**: Content-Type, Authorization, custom headers
3. **Query Parameters**: Document required vs optional parameters
4. **Request Body**: Provide example payloads in proper format
5. **Authorization**: Set up auth at collection or request level
6. **Pre-request Scripts**: Set up dynamic data or authentication
7. **Tests**: Add assertions for status codes, response structure, data validation

### Environment Management

Create environments for different deployment stages:

```javascript
// Development Environment
{
  "base_url": "https://dev-api.example.com",
  "api_key": "dev_key_123",
  "timeout": "5000"
}

// Production Environment
{
  "base_url": "https://api.example.com",
  "api_key": "prod_key_456",
  "timeout": "10000"
}
```

## Writing Test Scripts

### Essential Test Patterns

**1. Status Code Validation**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});
```

**2. Response Time Testing**
```javascript
pm.test("Response time is less than 500ms", function () {
    pm.expect(pm.response.responseTime).to.be.below(500);
});
```

**3. JSON Schema Validation**
```javascript
const schema = {
    type: "object",
    required: ["id", "name", "email"],
    properties: {
        id: { type: "number" },
        name: { type: "string" },
        email: { type: "string" }
    }
};

pm.test("Response matches schema", function () {
    pm.response.to.have.jsonSchema(schema);
});
```

**4. Extracting and Setting Variables**
```javascript
// Parse response
const response = pm.response.json();

// Save data for subsequent requests
pm.environment.set("user_id", response.id);
pm.environment.set("auth_token", response.token);
```

**5. Response Body Assertions**
```javascript
pm.test("User email is correct", function () {
    const data = pm.response.json();
    pm.expect(data.email).to.eql("user@example.com");
});

pm.test("Response has required fields", function () {
    const data = pm.response.json();
    pm.expect(data).to.have.property("id");
    pm.expect(data).to.have.property("created_at");
});
```

### Pre-request Script Patterns

**1. Generate Dynamic Values**
```javascript
// Set timestamp
pm.environment.set("timestamp", new Date().toISOString());

// Generate random data
pm.environment.set("random_email", `user${Math.random().toString(36).substring(7)}@test.com`);
pm.environment.set("uuid", pm.variables.replaceIn("{{$guid}}"));
```

**2. Set Up Authentication**
```javascript
// Check if token exists and is valid
const token = pm.environment.get("auth_token");
const tokenExpiry = pm.environment.get("token_expiry");

if (!token || Date.now() > tokenExpiry) {
    // Token missing or expired - refresh it
    pm.sendRequest({
        url: pm.environment.get("base_url") + "/auth/refresh",
        method: "POST",
        header: {
            "Content-Type": "application/json"
        },
        body: {
            mode: "raw",
            raw: JSON.stringify({
                refresh_token: pm.environment.get("refresh_token")
            })
        }
    }, function (err, res) {
        if (!err) {
            const data = res.json();
            pm.environment.set("auth_token", data.access_token);
            pm.environment.set("token_expiry", Date.now() + 3600000); // 1 hour
        }
    });
}
```

## Data-Driven Testing

### Using CSV Files

Create a CSV file with test data:
```csv
username,password,expected_status
valid_user,correct_pass,200
invalid_user,any_pass,401
valid_user,wrong_pass,401
```

In your request:
1. Use variables: `{{username}}` and `{{password}}`
2. Add test for expected outcome:
```javascript
pm.test("Status matches expected", function () {
    const expectedStatus = pm.iterationData.get("expected_status");
    pm.response.to.have.status(parseInt(expectedStatus));
});
```

3. Run with Collection Runner using the CSV file

## Documentation Best Practices

### Collection Description Template

```markdown
# [API Name] Collection

## Overview
Brief description of the API and this collection's purpose.

## Prerequisites
- Valid API key (obtain from: https://...)
- Base URL configured in environment
- Dependencies: [list any required setups]

## Quick Start
1. Import this collection
2. Set up environment variables
3. Run the Authentication folder first
4. Execute requests in order

## Authentication
Description of auth method and how it's handled in this collection.

## Rate Limits
- X requests per minute
- Y requests per day

## Support
Contact: support@example.com
Documentation: https://docs.example.com
```

### Request Description Template

```markdown
# [Request Name]

## Description
What this endpoint does and when to use it.

## Parameters
- `id` (path, required): User ID
- `include` (query, optional): Related resources to include
- `fields` (query, optional): Specific fields to return

## Request Body
```json
{
  "name": "string (required)",
  "email": "string (required, format: email)",
  "role": "string (optional, enum: [admin, user])"
}
```

## Success Response (200)
```json
{
  "id": 123,
  "name": "John Doe",
  "email": "john@example.com",
  "created_at": "2024-01-01T00:00:00Z"
}
```

## Error Responses
- 400: Invalid request body
- 401: Unauthorized
- 404: User not found
- 422: Validation error
```

## CI/CD Integration

### Newman Command Examples

**Run collection with environment:**
```bash
newman run collection.json -e environment.json
```

**Run with data file:**
```bash
newman run collection.json -d test-data.csv --iteration-count 10
```

**Generate HTML report:**
```bash
newman run collection.json -r html --reporter-html-export report.html
```

**With custom timeout and iterations:**
```bash
newman run collection.json \
  -e prod.json \
  --timeout-request 10000 \
  --iteration-count 5 \
  --bail
```

### Jenkins Pipeline Example

```groovy
stage('API Tests') {
    steps {
        sh 'newman run collection.json -e ${ENV}.json -r junit,cli --reporter-junit-export results.xml'
    }
    post {
        always {
            junit 'results.xml'
        }
    }
}
```

## Common Patterns & Solutions

### Request Chaining
```javascript
// Request 1: Create resource
pm.test("Resource created", function () {
    const response = pm.response.json();
    pm.environment.set("resource_id", response.id);
});

// Request 2: Use the resource_id
// URL: {{base_url}}/resources/{{resource_id}}
```

### Handling Pagination
```javascript
pm.test("Handle pagination", function () {
    const response = pm.response.json();
    
    // Save next page token
    if (response.next_page) {
        pm.environment.set("next_page_token", response.next_page);
    }
    
    // Test pagination metadata
    pm.expect(response).to.have.property("total_count");
    pm.expect(response).to.have.property("page_size");
});
```

### Error Handling in Scripts
```javascript
try {
    const response = pm.response.json();
    pm.test("Response parsed successfully", function () {
        pm.expect(response).to.be.an("object");
    });
    
    // Your test logic here
    
} catch (e) {
    pm.test("Failed to parse response: " + e.message, function () {
        pm.expect.fail();
    });
}
```

## Quality Checklist

Before sharing or deploying a collection, verify:

- [ ] All requests have clear, consistent names
- [ ] Environment variables are used instead of hardcoded values
- [ ] Sensitive data (API keys, passwords) are in environment variables, not in collection
- [ ] Each request has appropriate tests (minimum: status code)
- [ ] Collection and folders have descriptive documentation
- [ ] Request examples show both success and error scenarios
- [ ] Pre-request scripts handle authentication and dynamic data
- [ ] Variables are cleaned up (don't leave test data in environment)
- [ ] Collection can run in sequence successfully
- [ ] Authorization is configured at appropriate level (collection vs request)

## Troubleshooting

### Common Issues

**Problem**: Tests failing intermittently
- Check response times - API might be slow
- Verify test assertions aren't too strict
- Look for race conditions in chained requests

**Problem**: Variables not persisting
- Ensure you're using `pm.environment.set()` not `pm.variables.set()`
- Check variable scope (collection vs environment vs global)
- Verify environment is selected in Postman

**Problem**: Authentication failing
- Check token expiration and refresh logic
- Verify auth is set at correct level (collection/folder/request)
- Ensure environment variables are populated

**Problem**: Scripts not executing
- Check for JavaScript syntax errors in console
- Verify script is in correct section (Pre-request vs Tests)
- Check for console.log() output for debugging

## Advanced Topics

### Custom JavaScript Libraries

You can use these built-in libraries in scripts:
- `crypto-js`: For encryption and hashing
- `moment`: For date manipulation
- `lodash`: For utility functions
- `cheerio`: For HTML parsing (in Newman only)

Example:
```javascript
const CryptoJS = require('crypto-js');
const signature = CryptoJS.HmacSHA256(message, secret);
pm.environment.set('signature', signature.toString());
```

### Mock Servers

Create mock endpoints for development:
1. Set up examples with desired responses
2. Create mock server from collection
3. Use mock server URL in development environment
4. Switch to real API when ready

### Monitoring

Set up monitors for:
- Health check endpoints (run every 5 minutes)
- Critical user flows (run hourly)
- Data validation checks (run daily)

Configure alerts for failures and performance degradation.

## Resources and References

For additional information:
- See `references/AUTHENTICATION.md` for detailed auth patterns
- See `references/TESTING_PATTERNS.md` for advanced test scenarios
- See `scripts/` directory for utility scripts
- Check Postman Learning Center: https://learning.postman.com

## Version History

- 1.0: Initial skill creation with core collection management capabilities