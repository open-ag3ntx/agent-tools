# Advanced Testing Patterns for Postman Collections

Comprehensive guide to advanced testing scenarios and patterns in Postman.

## Table of Contents

1. [Response Validation](#response-validation)
2. [Data-Driven Testing](#data-driven-testing)
3. [Workflow Testing](#workflow-testing)
4. [Performance Testing](#performance-testing)
5. [Error Handling](#error-handling)
6. [Dynamic Test Generation](#dynamic-test-generation)

---

## Response Validation

### Schema Validation with JSON Schema
```javascript
// Define comprehensive schema
const userSchema = {
    type: "object",
    required: ["id", "email", "created_at"],
    properties: {
        id: {
            type: "integer",
            minimum: 1
        },
        email: {
            type: "string",
            format: "email"
        },
        name: {
            type: "string",
            minLength: 1,
            maxLength: 100
        },
        age: {
            type: "integer",
            minimum: 0,
            maximum: 150
        },
        created_at: {
            type: "string",
            format: "date-time"
        },
        roles: {
            type: "array",
            items: {
                type: "string",
                enum: ["admin", "user", "guest"]
            }
        }
    }
};

pm.test("Response matches user schema", function () {
    pm.response.to.have.jsonSchema(userSchema);
});
```

### Array Response Validation
```javascript
pm.test("Response is array with valid items", function () {
    const response = pm.response.json();
    
    // Check it's an array
    pm.expect(response).to.be.an("array");
    pm.expect(response).to.have.length.above(0);
    
    // Validate each item
    response.forEach((item, index) => {
        pm.expect(item, `Item ${index} has id`).to.have.property("id");
        pm.expect(item.id, `Item ${index} id is number`).to.be.a("number");
        pm.expect(item, `Item ${index} has name`).to.have.property("name");
    });
});
```

### Nested Object Validation
```javascript
pm.test("Nested object structure valid", function () {
    const response = pm.response.json();
    
    // Check nested properties
    pm.expect(response).to.have.nested.property("user.profile.address.city");
    pm.expect(response.user.profile.address.city).to.be.a("string");
    
    // Validate nested array
    pm.expect(response).to.have.nested.property("user.orders");
    pm.expect(response.user.orders).to.be.an("array");
    pm.expect(response.user.orders[0]).to.have.property("order_id");
});
```

### Response Header Validation
```javascript
pm.test("Response headers are correct", function () {
    pm.response.to.have.header("Content-Type");
    pm.expect(pm.response.headers.get("Content-Type")).to.include("application/json");
    
    pm.response.to.have.header("X-RateLimit-Remaining");
    const remaining = parseInt(pm.response.headers.get("X-RateLimit-Remaining"));
    pm.expect(remaining).to.be.at.least(0);
    
    // Check caching headers
    pm.response.to.have.header("Cache-Control");
    pm.expect(pm.response.headers.get("Cache-Control")).to.not.include("no-store");
});
```

---

## Data-Driven Testing

### CSV Data File Structure

Create `test-data.csv`:
```csv
test_case,username,password,expected_status,expected_message
valid_user,john@example.com,Pass123!,200,Login successful
invalid_email,notanemail,Pass123!,400,Invalid email format
missing_password,john@example.com,,400,Password required
wrong_password,john@example.com,wrongpass,401,Invalid credentials
sql_injection,admin' OR '1'='1,anything,401,Invalid credentials
```

### Dynamic Test with CSV Data
```javascript
// Use iteration data
const testCase = pm.iterationData.get("test_case");
const expectedStatus = parseInt(pm.iterationData.get("expected_status"));
const expectedMessage = pm.iterationData.get("expected_message");

pm.test(`${testCase}: Status code is ${expectedStatus}`, function () {
    pm.response.to.have.status(expectedStatus);
});

pm.test(`${testCase}: Response message correct`, function () {
    const response = pm.response.json();
    pm.expect(response.message).to.include(expectedMessage);
});

// Log test case for debugging
console.log(`Running test case: ${testCase}`);
```

### JSON Data File Testing

Create `test-users.json`:
```json
[
    {
        "name": "John Doe",
        "email": "john@example.com",
        "role": "admin",
        "expected_access": ["read", "write", "delete"]
    },
    {
        "name": "Jane Smith",
        "email": "jane@example.com",
        "role": "user",
        "expected_access": ["read", "write"]
    }
]
```

Test script:
```javascript
const userData = pm.iterationData.toObject();

pm.test(`Create user: ${userData.name}`, function () {
    pm.response.to.have.status(201);
    
    const response = pm.response.json();
    pm.expect(response.email).to.eql(userData.email);
    pm.expect(response.role).to.eql(userData.role);
});

pm.test(`User has correct permissions`, function () {
    const response = pm.response.json();
    pm.expect(response.permissions).to.have.members(userData.expected_access);
});
```

---

## Workflow Testing

### Multi-Step User Flow
```javascript
// Step 1: Register User
pm.test("User registration successful", function () {
    pm.response.to.have.status(201);
    const response = pm.response.json();
    pm.environment.set("user_id", response.id);
    pm.environment.set("email", response.email);
});

// Step 2: Verify Email (next request)
pm.test("Email verification successful", function () {
    pm.response.to.have.status(200);
    const response = pm.response.json();
    pm.expect(response.verified).to.be.true;
    pm.environment.set("verification_token", response.token);
});

// Step 3: Login (next request)
pm.test("Login successful", function () {
    pm.response.to.have.status(200);
    const response = pm.response.json();
    pm.environment.set("access_token", response.access_token);
});

// Step 4: Access Protected Resource (next request)
pm.test("Protected resource accessible", function () {
    pm.response.to.have.status(200);
    const response = pm.response.json();
    pm.expect(response.user_id).to.e