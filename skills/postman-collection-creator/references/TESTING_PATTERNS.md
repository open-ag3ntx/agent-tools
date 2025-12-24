# Advanced Testing Patterns

## Schema Validation
```javascript
const userSchema = {
    type: "object",
    required: ["id", "email", "created_at"],
    properties: {
        id: { type: "integer", minimum: 1 },
        email: { type: "string", format: "email" },
        name: { type: "string", minLength: 1, maxLength: 100 },
        roles: {
            type: "array",
            items: { type: "string", enum: ["admin", "user", "guest"] }
        }
    }
};

pm.test("Response matches schema", function () {
    pm.response.to.have.jsonSchema(userSchema);
});
```

## Array Validation
```javascript
pm.test("Array response valid", function () {
    const response = pm.response.json();
    
    pm.expect(response).to.be.an("array");
    pm.expect(response).to.have.length.above(0);
    
    response.forEach((item, i) => {
        pm.expect(item, `Item ${i} has id`).to.have.property("id");
        pm.expect(item.id, `Item ${i} id is number`).to.be.a("number");
    });
});
```

## Data-Driven Testing with CSV

**test-data.csv:**
```csv
test_case,username,password,expected_status,expected_message
valid_user,john@example.com,Pass123!,200,Success
invalid_email,notanemail,Pass123!,400,Invalid email
wrong_password,john@example.com,wrongpass,401,Invalid credentials
```

**Test Script:**
```javascript
const testCase = pm.iterationData.get("test_case");
const expectedStatus = parseInt(pm.iterationData.get("expected_status"));
const expectedMsg = pm.iterationData.get("expected_message");

pm.test(`${testCase}: Status ${expectedStatus}`, function () {
    pm.response.to.have.status(expectedStatus);
});

pm.test(`${testCase}: Message correct`, function () {
    const response = pm.response.json();
    pm.expect(response.message).to.include(expectedMsg);
});
```

## Multi-Step Workflow Testing
```javascript
// Step 1: Create Resource
pm.test("Resource created", function () {
    pm.response.to.have.status(201);
    const response = pm.response.json();
    pm.environment.set("resource_id", response.id);
});

// Step 2: Read Resource (next request uses {{resource_id}})
pm.test("Resource retrieved", function () {
    pm.response.to.have.status(200);
    const response = pm.response.json();
    pm.expect(response.id).to.eql(pm.environment.get("resource_id"));
});

// Step 3: Update Resource
pm.test("Resource updated", function () {
    pm.response.to.have.status(200);
});

// Step 4: Delete Resource
pm.test("Resource deleted", function () {
    pm.response.to.have.status(204);
});

// Step 5: Verify Deletion
pm.test("Deleted resource not found", function () {
    pm.response.to.have.status(404);
});
```

## Performance Testing
```javascript
pm.test("Response time acceptable", function () {
    pm.expect(pm.response.responseTime).to.be.below(500);
});

pm.test("No memory leaks", function () {
    const size = pm.response.headers.get("Content-Length");
    pm.expect(parseInt(size)).to.be.below(1048576); // 1MB
});
```

## Pagination Testing
```javascript
pm.test("Pagination works", function () {
    const response = pm.response.json();
    
    pm.expect(response).to.have.property("data");
    pm.expect(response).to.have.property("total_count");
    pm.expect(response).to.have.property("page_size");
    pm.expect(response).to.have.property("page");
    
    if (response.next_page) {
        pm.environment.set("next_page_url", response.next_page);
    }
});
```

## Error Handling
```javascript
try {
    const response = pm.response.json();
    
    pm.test("Response parsed", function () {
        pm.expect(response).to.be.an("object");
    });
    
    // Your assertions here
    
} catch (e) {
    pm.test("Parse error: " + e.message, function () {
        pm.expect.fail();
    });
}
```

## Conditional Testing
```javascript
if (pm.response.code === 200) {
    pm.test("Success response valid", function () {
        const response = pm.response.json();
        pm.expect(response).to.have.property("data");
    });
} else if (pm.response.code === 404) {
    pm.test("Not found response valid", function () {
        const response = pm.response.json();
        pm.expect(response).to.have.property("error");
    });
}
```