# Authentication Patterns for Postman Collections

This reference guide covers comprehensive authentication patterns for API testing in Postman.

## Table of Contents

1. [API Key Authentication](#api-key-authentication)
2. [Bearer Token Authentication](#bearer-token-authentication)
3. [OAuth 2.0 Flow](#oauth-20-flow)
4. [JWT Authentication](#jwt-authentication)
5. [Basic Authentication](#basic-authentication)
6. [Session-Based Authentication](#session-based-authentication)
7. [Custom Authentication Headers](#custom-authentication-headers)

---

## API Key Authentication

### Collection-Level Configuration

Set API key at collection level:
1. Collection Settings → Authorization
2. Type: API Key
3. Key: `x-api-key` (or your header name)
4. Value: `{{api_key}}`
5. Add to: Header

### Dynamic API Key Rotation
```javascript
// Pre-request Script for API Key rotation
const currentKey = pm.environment.get("api_key");
const keyExpiry = pm.environment.get("key_expiry");

if (!currentKey || Date.now() > keyExpiry) {
    pm.sendRequest({
        url: pm.environment.get("base_url") + "/auth/new-key",
        method: "POST",
        header: {
            "Authorization": "Basic " + pm.environment.get("master_credentials")
        }
    }, function (err, res) {
        if (!err && res.code === 200) {
            const data = res.json();
            pm.environment.set("api_key", data.key);
            pm.environment.set("key_expiry", Date.now() + (data.ttl * 1000));
        }
    });
}
```

---

## Bearer Token Authentication

### Standard Bearer Token Setup
```javascript
// Pre-request Script: Set Bearer token
const token = pm.environment.get("access_token");

if (!token) {
    console.error("Access token not found. Please authenticate first.");
    throw new Error("Authentication required");
}

pm.request.headers.add({
    key: "Authorization",
    value: "Bearer " + token
});
```

### Token Refresh Pattern
```javascript
// Pre-request Script: Auto-refresh expired tokens
const token = pm.environment.get("access_token");
const tokenExpiry = pm.environment.get("token_expiry");
const refreshToken = pm.environment.get("refresh_token");

function refreshAccessToken() {
    pm.sendRequest({
        url: pm.environment.get("base_url") + "/auth/refresh",
        method: "POST",
        header: {
            "Content-Type": "application/json"
        },
        body: {
            mode: "raw",
            raw: JSON.stringify({
                refresh_token: refreshToken
            })
        }
    }, function (err, res) {
        if (!err && res.code === 200) {
            const data = res.json();
            pm.environment.set("access_token", data.access_token);
            pm.environment.set("token_expiry", Date.now() + (data.expires_in * 1000));
            
            // Update refresh token if provided
            if (data.refresh_token) {
                pm.environment.set("refresh_token", data.refresh_token);
            }
        } else {
            console.error("Token refresh failed:", err || res.json());
        }
    });
}

// Check if token needs refresh (refresh 5 minutes before expiry)
if (!token || !tokenExpiry || Date.now() > (tokenExpiry - 300000)) {
    refreshAccessToken();
}
```

---

## OAuth 2.0 Flow

### Authorization Code Flow

**Step 1: Get Authorization Code (Manual)**
1. Open browser to: `{{auth_url}}/authorize?response_type=code&client_id={{client_id}}&redirect_uri={{redirect_uri}}&scope={{scope}}`
2. Copy the authorization code from redirect URL

**Step 2: Exchange Code for Token (Automated)**
```javascript
// Pre-request Script: Exchange auth code for tokens
const authCode = pm.environment.get("auth_code");
const clientId = pm.environment.get("client_id");
const clientSecret = pm.environment.get("client_secret");
const redirectUri = pm.environment.get("redirect_uri");

if (authCode && !pm.environment.get("access_token")) {
    pm.sendRequest({
        url: pm.environment.get("token_url"),
        method: "POST",
        header: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: {
            mode: "urlencoded",
            urlencoded: [
                { key: "grant_type", value: "authorization_code" },
                { key: "code", value: authCode },
                { key: "client_id", value: clientId },
                { key: "client_secret", value: clientSecret },
                { key: "redirect_uri", value: redirectUri }
            ]
        }
    }, function (err, res) {
        if (!err && res.code === 200) {
            const data = res.json();
            pm.environment.set("access_token", data.access_token);
            pm.environment.set("refresh_token", data.refresh_token);
            pm.environment.set("token_expiry", Date.now() + (data.expires_in * 1000));
            
            // Clear auth code after use
            pm.environment.unset("auth_code");
        }
    });
}
```

### Client Credentials Flow
```javascript
// Pre-request Script: Client credentials grant
const clientId = pm.environment.get("client_id");
const clientSecret = pm.environment.get("client_secret");
const tokenExpiry = pm.environment.get("token_expiry");

if (!tokenExpiry || Date.now() > tokenExpiry) {
    const credentials = btoa(clientId + ":" + clientSecret);
    
    pm.sendRequest({
        url: pm.environment.get("token_url"),
        method: "POST",
        header: {
            "Authorization": "Basic " + credentials,
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: {
            mode: "urlencoded",
            urlencoded: [
                { key: "grant_type", value: "client_credentials" },
                { key: "scope", value: pm.environment.get("scope") }
            ]
        }
    }, function (err, res) {
        if (!err && res.code === 200) {
            const data = res.json();
            pm.environment.set("access_token", data.access_token);
            pm.environment.set("token_expiry", Date.now() + (data.expires_in * 1000));
        }
    });
}
```

---

## JWT Authentication

### Creating JWT Token
```javascript
// Pre-request Script: Generate JWT
const CryptoJS = require('crypto-js');

// JWT Header
const header = {
    "alg": "HS256",
    "typ": "JWT"
};

// JWT Payload
const payload = {
    "sub": pm.environment.get("user_id"),
    "iat": Math.floor(Date.now() / 1000),
    "exp": Math.floor(Date.now() / 1000) + 3600, // 1 hour
    "scope": "read write"
};

// Encode
const encodedHeader = btoa(JSON.stringify(header));
const encodedPayload = btoa(JSON.stringify(payload));

// Create signature
const secret = pm.environment.get("jwt_secret");
const signatureInput = encodedHeader + "." + encodedPayload;
const signature = CryptoJS.HmacSHA256(signatureInput, secret).toString(CryptoJS.enc.Base64);

// Construct JWT
const jwt = encodedHeader + "." + encodedPayload + "." + signature;

pm.environment.set("jwt_token", jwt);
pm.request.headers.add({
    key: "Authorization",
    value: "Bearer " + jwt
});
```

### Validating JWT Response
```javascript
// Test Script: Validate JWT in response
pm.test("JWT token received and valid", function () {
    const response = pm.response.json();
    pm.expect(response).to.have.property("token");
    
    const token = response.token;
    const parts = token.split(".");
    
    pm.expect(parts).to.have.lengthOf(3);
    
    // Decode payload
    const payload = JSON.parse(atob(parts[1]));
    
    // Validate expiration
    pm.expect(payload.exp).to.be.above(Math.floor(Date.now() / 1000));
    
    // Save token
    pm.environment.set("access_token", token);
});
```

---

## Basic Authentication

### Static Basic Auth
```javascript
// Pre-request Script: Basic Authentication
const username = pm.environment.get("username");
const password = pm.environment.get("password");

const credentials = btoa(username + ":" + password);