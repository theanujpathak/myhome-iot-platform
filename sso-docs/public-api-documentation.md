# SSO System API Documentation

## Overview

This documentation provides comprehensive information about the SSO system's public API endpoints. The API is built using Express.js and integrates with Keycloak for authentication and authorization.

**Base URL**: `http://localhost:3001`

## Authentication

### Token-Based Authentication

The API uses JWT tokens for authentication. Tokens are obtained through the Keycloak authentication flow and must be included in the Authorization header for protected endpoints.

**Header Format:**
```
Authorization: Bearer <your-jwt-token>
```

### Token Lifecycle

- **Expiration**: Tokens expire after 30 minutes of inactivity or 10 hours maximum
- **Refresh**: Tokens are automatically refreshed while active
- **Revocation**: Tokens are revoked upon logout

## Endpoints

### Health Check

#### GET /health

Check the API server health status.

**Authentication**: None required

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "keycloak": {
    "url": "http://localhost:8080",
    "realm": "i4planet-login"
  }
}
```

**Status Codes:**
- `200 OK`: Service is healthy
- `500 Internal Server Error`: Service is unhealthy

---

### Public Endpoints

#### GET /api/public

Access public information without authentication.

**Authentication**: None required

**Response:**
```json
{
  "message": "This is a public endpoint",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

**Status Codes:**
- `200 OK`: Success

---

### Protected Endpoints

#### GET /api/protected

Access protected information with valid authentication.

**Authentication**: Required (Bearer token)

**Response:**
```json
{
  "message": "This is a protected endpoint",
  "user": {
    "sub": "user-id",
    "email": "user@example.com",
    "name": "User Name",
    "preferred_username": "username",
    "given_name": "First",
    "family_name": "Last"
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Missing or invalid token

---

### Profile Management

#### GET /api/profile

Retrieve the current user's profile information.

**Authentication**: Required (Bearer token)

**Response:**
```json
{
  "message": "Profile data retrieved",
  "user": {
    "sub": "user-id",
    "email": "user@example.com",
    "name": "User Name",
    "preferred_username": "username",
    "given_name": "First",
    "family_name": "Last"
  },
  "profile": {
    "lastLogin": "2024-01-15T10:30:00.000Z",
    "preferences": {
      "theme": "light",
      "language": "en"
    }
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Missing or invalid token

#### PUT /api/profile

Update the current user's profile information.

**Authentication**: Required (Bearer token)

**Request Body:**
```json
{
  "preferences": {
    "theme": "dark",
    "language": "es"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

**Status Codes:**
- `200 OK`: Success
- `400 Bad Request`: Invalid request body
- `401 Unauthorized`: Missing or invalid token
- `500 Internal Server Error`: Update failed

---

### Token Management

#### POST /api/introspect

Introspect a token to verify its validity and get token information.

**Authentication**: None required for the endpoint, but token is required in request body

**Request Body:**
```json
{
  "token": "your-jwt-token-here"
}
```

**Response (Valid Token):**
```json
{
  "active": true,
  "sub": "user-id",
  "iss": "http://localhost:8080/realms/i4planet-login",
  "aud": "demo-app",
  "exp": 1642248600,
  "iat": 1642246800,
  "username": "user@example.com",
  "email": "user@example.com",
  "given_name": "First",
  "family_name": "Last"
}
```

**Response (Invalid Token):**
```json
{
  "active": false
}
```

**Status Codes:**
- `200 OK`: Success (check `active` field for validity)
- `400 Bad Request`: Missing token in request body
- `500 Internal Server Error`: Introspection failed

---

### Admin Endpoints

#### GET /api/admin

Access admin-only information.

**Authentication**: Required (Bearer token with admin role)

**Response:**
```json
{
  "message": "This is an admin-only endpoint",
  "user": {
    "sub": "admin-user-id",
    "email": "admin@example.com",
    "name": "Admin User",
    "realm_roles": ["admin"]
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: Insufficient permissions

#### GET /api/users

Retrieve list of all users (admin only).

**Authentication**: Required (Bearer token with admin role)

**Response:**
```json
[
  {
    "id": "user-id-1",
    "username": "user1@example.com",
    "email": "user1@example.com",
    "firstName": "First",
    "lastName": "Last",
    "enabled": true,
    "createdTimestamp": 1642246800000
  },
  {
    "id": "user-id-2",
    "username": "user2@example.com",
    "email": "user2@example.com",
    "firstName": "Second",
    "lastName": "User",
    "enabled": true,
    "createdTimestamp": 1642246900000
  }
]
```

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: Insufficient permissions
- `500 Internal Server Error`: Failed to fetch users

#### POST /api/admin/users

Create a new user (admin only).

**Authentication**: Required (Bearer token with admin role)

**Request Body:**
```json
{
  "username": "newuser@example.com",
  "email": "newuser@example.com",
  "firstName": "New",
  "lastName": "User",
  "enabled": true,
  "credentials": [
    {
      "type": "password",
      "value": "temporaryPassword123",
      "temporary": true
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "message": "User created successfully"
}
```

**Status Codes:**
- `200 OK`: Success
- `400 Bad Request`: Invalid request body
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: Insufficient permissions
- `409 Conflict`: User already exists
- `500 Internal Server Error`: Creation failed

#### PUT /api/admin/users/:userId

Update an existing user (admin only).

**Authentication**: Required (Bearer token with admin role)

**Path Parameters:**
- `userId`: The unique identifier of the user to update

**Request Body:**
```json
{
  "firstName": "Updated",
  "lastName": "Name",
  "email": "updated@example.com",
  "enabled": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "User updated successfully"
}
```

**Status Codes:**
- `200 OK`: Success
- `400 Bad Request`: Invalid request body
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: User not found
- `500 Internal Server Error`: Update failed

#### PUT /api/admin/users/:userId/reset-password

Reset a user's password (admin only).

**Authentication**: Required (Bearer token with admin role)

**Path Parameters:**
- `userId`: The unique identifier of the user

**Response:**
```json
{
  "success": true,
  "message": "Password reset successfully"
}
```

**Note**: This endpoint sets a temporary password "temp123" that the user must change on next login.

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: User not found
- `500 Internal Server Error`: Password reset failed

---

## Error Handling

### Error Response Format

All error responses follow a consistent format:

```json
{
  "error": "Error message description"
}
```

### Common Error Codes

| Status Code | Description |
|-------------|-------------|
| `400 Bad Request` | Invalid request format or missing required fields |
| `401 Unauthorized` | Missing, invalid, or expired authentication token |
| `403 Forbidden` | Insufficient permissions for the requested operation |
| `404 Not Found` | Requested resource not found |
| `409 Conflict` | Resource already exists or conflicts with existing data |
| `500 Internal Server Error` | Server error or external service failure |

### Error Examples

**Missing Authorization Header:**
```json
{
  "error": "Missing or invalid authorization header"
}
```

**Invalid Token:**
```json
{
  "error": "Invalid or expired token"
}
```

**Insufficient Permissions:**
```json
{
  "error": "Insufficient permissions for this operation"
}
```

---

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **General Endpoints**: 100 requests per minute per IP
- **Admin Endpoints**: 60 requests per minute per IP
- **Authentication Endpoints**: 10 requests per minute per IP

### Rate Limit Headers

Rate limit information is included in response headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248600
```

---

## Security Considerations

### HTTPS

In production environments, always use HTTPS to encrypt data in transit.

### Token Security

- Never expose tokens in URLs or logs
- Store tokens securely on the client side
- Implement proper token refresh mechanisms
- Use secure storage methods (not localStorage for sensitive data)

### Input Validation

- All input is validated on the server side
- SQL injection protection is implemented
- XSS protection is enabled via helmet middleware

### CORS

CORS is configured to allow requests from authorized origins only.

---

## SDKs and Libraries

### JavaScript/Node.js

```javascript
// Example using fetch API
const response = await fetch('http://localhost:3001/api/protected', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});

const data = await response.json();
```

### cURL Examples

**Get Profile:**
```bash
curl -X GET http://localhost:3001/api/profile \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Update Profile:**
```bash
curl -X PUT http://localhost:3001/api/profile \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"preferences": {"theme": "dark"}}'
```

**Create User (Admin):**
```bash
curl -X POST http://localhost:3001/api/admin/users \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser@example.com",
    "email": "newuser@example.com",
    "firstName": "New",
    "lastName": "User",
    "enabled": true
  }'
```

---

## Testing

### Postman Collection

A Postman collection is available with pre-configured requests for all endpoints. Import the collection and set up the following environment variables:

- `baseUrl`: `http://localhost:3001`
- `token`: Your JWT token
- `adminToken`: Admin JWT token

### Unit Tests

Run the test suite with:
```bash
npm test
```

### Integration Tests

Run integration tests with:
```bash
npm run test:integration
```

---

## Support

For API-related questions or issues:

- **Technical Documentation**: Refer to this document
- **Bug Reports**: Create an issue in the project repository
- **Feature Requests**: Contact the development team
- **Security Issues**: Report via secure channel to security@company.com

---

## Changelog

### Version 1.0.0
- Initial API release
- Basic authentication endpoints
- Profile management
- Admin user management
- Token introspection

---

*This documentation is regularly updated. Please check for the latest version and report any discrepancies or suggestions for improvement.*