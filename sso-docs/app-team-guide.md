# Quick Start Guide for App Teams

This guide helps development teams integrate their applications with our SSO solution using Keycloak.

## Overview

Our SSO system provides:
- **Single Sign-On**: Users login once, access all applications
- **Role-based Access Control**: Admin, Manager, User roles
- **Secure Token Management**: JWT tokens with automatic refresh
- **Session Sharing**: Seamless navigation between applications

## Getting Started

### 1. Register Your Application

Contact the SSO team to register your application. Provide:
- Application name and description
- Callback URLs (where users return after login)
- Application type (public/confidential)
- Required user roles/permissions

### 2. Get Your Client Configuration

You'll receive:
```json
{
  "keycloakUrl": "http://localhost:8080",
  "realm": "sso-realm",
  "clientId": "your-app-client-id",
  "clientSecret": "your-secret-if-confidential"
}
```

## Frontend Integration (React/JavaScript)

### Installation
```bash
npm install keycloak-js
```

### Basic Setup
```javascript
import Keycloak from 'keycloak-js';

const keycloak = new Keycloak({
  url: 'http://localhost:8080',
  realm: 'sso-realm',
  clientId: 'your-app-client-id'
});

// Initialize Keycloak
const authenticated = await keycloak.init({
  onLoad: 'check-sso', // or 'login-required'
  silentCheckSsoRedirectUri: window.location.origin + '/silent-check-sso.html'
});

if (authenticated) {
  // User is logged in
  console.log('User:', keycloak.tokenParsed);
} else {
  // Redirect to login
  keycloak.login();
}
```

### Protected Routes
```javascript
// Check authentication before rendering
if (!keycloak.authenticated) {
  return <LoginRequired onLogin={() => keycloak.login()} />;
}

// Check roles
const hasAdminRole = keycloak.hasRealmRole('admin');
const hasManagerRole = keycloak.hasRealmRole('manager');
```

### API Calls with Token
```javascript
// Set token in headers
axios.defaults.headers.common['Authorization'] = `Bearer ${keycloak.token}`;

// Auto-refresh token
setInterval(() => {
  keycloak.updateToken(70).then((refreshed) => {
    if (refreshed) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${keycloak.token}`;
    }
  });
}, 60000);
```

## Backend Integration (Node.js)

### Installation
```bash
npm install keycloak-connect express-session
```

### Basic Setup
```javascript
const Keycloak = require('keycloak-connect');
const session = require('express-session');

// Session store
const memoryStore = new session.MemoryStore();
app.use(session({
  secret: 'your-secret',
  resave: false,
  saveUninitialized: true,
  store: memoryStore
}));

// Keycloak configuration
const keycloak = new Keycloak({
  store: memoryStore
}, {
  'auth-server-url': 'http://localhost:8080',
  'realm': 'sso-realm',
  'resource': 'your-app-client-id',
  'credentials': {
    'secret': 'your-client-secret'
  }
});

app.use(keycloak.middleware());
```

### Protecting Routes
```javascript
// Require authentication
app.get('/protected', keycloak.protect(), (req, res) => {
  res.json({ message: 'Protected content', user: req.kauth.grant.access_token.content });
});

// Require specific role
app.get('/admin', keycloak.protect('realm:admin'), (req, res) => {
  res.json({ message: 'Admin only content' });
});

// Multiple roles (OR)
app.get('/managers', keycloak.protect(['realm:admin', 'realm:manager']), (req, res) => {
  res.json({ message: 'Manager or admin content' });
});
```

### Token Validation (Stateless)
```javascript
const jwt = require('jsonwebtoken');
const axios = require('axios');

const verifyToken = async (req, res, next) => {
  try {
    const token = req.headers.authorization?.split(' ')[1];
    
    // Verify with Keycloak
    const response = await axios.get(
      'http://localhost:8080/realms/sso-realm/protocol/openid-connect/userinfo',
      { headers: { 'Authorization': `Bearer ${token}` } }
    );
    
    req.user = response.data;
    next();
  } catch (error) {
    res.status(401).json({ error: 'Invalid token' });
  }
};

app.get('/api/protected', verifyToken, (req, res) => {
  res.json({ user: req.user });
});
```

## Backend Integration (Other Languages)

### Python (Flask)
```python
from flask import Flask, request, jsonify
import requests

def verify_token():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    try:
        response = requests.get(
            'http://localhost:8080/realms/sso-realm/protocol/openid-connect/userinfo',
            headers={'Authorization': f'Bearer {token}'}
        )
        return response.json() if response.status_code == 200 else None
    except:
        return None

@app.route('/protected')
def protected():
    user = verify_token()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'user': user})
```

### Java (Spring Boot)
```java
@RestController
public class ProtectedController {
    
    @GetMapping("/protected")
    public ResponseEntity<?> getProtectedData(
        @RequestHeader("Authorization") String authHeader) {
        
        String token = authHeader.replace("Bearer ", "");
        
        // Verify token with Keycloak userinfo endpoint
        // Implementation depends on your HTTP client
        
        return ResponseEntity.ok(userData);
    }
}
```

## Configuration Files

### Silent Check SSO (public/silent-check-sso.html)
```html
<!DOCTYPE html>
<html>
<head><title>Silent Check SSO</title></head>
<body>
    <script>
        parent.postMessage(location.href, location.origin);
    </script>
</body>
</html>
```

### Environment Variables
```bash
# .env file
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=sso-realm
KEYCLOAK_CLIENT_ID=your-app-client-id
KEYCLOAK_CLIENT_SECRET=your-client-secret
```

## Common Integration Patterns

### 1. Check SSO (Recommended for SPAs)
- User might already be logged in from another app
- Silently checks authentication status
- Redirects to login only if needed

### 2. Login Required (For Admin Apps)
- Forces authentication before app loads
- Good for admin dashboards and sensitive applications

### 3. Mixed Mode
- Some pages public, others protected
- Check authentication per route/component

## User Information Available

```javascript
// From Keycloak token
const userInfo = {
  username: token.preferred_username,
  email: token.email,
  firstName: token.given_name,
  lastName: token.family_name,
  roles: token.realm_access.roles,
  groups: token.groups || []
};
```

## Logout Handling

### Frontend Logout
```javascript
// Logout from current app only
keycloak.logout();

// Logout from all applications
keycloak.logout({
  redirectUri: 'http://your-app.com/logged-out'
});
```

### Backend Logout
```javascript
app.post('/logout', (req, res) => {
  req.kauth.logout();
  res.redirect('/');
});
```

## Troubleshooting

### Common Issues

1. **CORS Errors**
   - Ensure your domain is added to client's Web Origins
   - Add both dev and production URLs

2. **Token Expired**
   - Implement automatic token refresh
   - Handle 401 responses by redirecting to login

3. **Role Check Failures**
   - Verify user has required roles assigned
   - Check role names match exactly (case-sensitive)

4. **Session Issues**
   - Ensure session configuration is consistent
   - Check session timeout settings

### Debug Mode
```javascript
// Enable Keycloak debugging
keycloak.enableLogging = true;

// Log token contents
console.log('Token:', keycloak.tokenParsed);
console.log('Roles:', keycloak.realmAccess?.roles);
```

## Testing Your Integration

### Manual Testing
1. Test login flow from your app
2. Verify user information is displayed correctly
3. Test role-based access to different pages
4. Test logout functionality
5. Test session sharing with other apps

### Automated Testing
```javascript
// Jest test example
test('protected route requires authentication', async () => {
  const response = await request(app)
    .get('/protected')
    .expect(401);
});

test('admin route requires admin role', async () => {
  const token = await getAdminToken();
  const response = await request(app)
    .get('/admin')
    .set('Authorization', `Bearer ${token}`)
    .expect(200);
});
```

## Support and Resources

- **Documentation**: `/docs/`
- **Sample Apps**: Check `react-app/`, `admin-dashboard/`, `employee-portal/`
- **API Documentation**: `http://localhost:3001/health`
- **Keycloak Admin**: `http://localhost:8080` (admin/admin)

### Getting Help

1. Check the logs: `docker compose logs keycloak`
2. Verify your client configuration in Keycloak Admin Console
3. Test with our sample applications first
4. Contact the SSO team with specific error messages

## Security Best Practices

1. **Never expose client secrets** in frontend code
2. **Always validate tokens** on the backend
3. **Use HTTPS** in production
4. **Implement proper CORS** policies
5. **Handle token refresh** gracefully
6. **Log security events** for monitoring
7. **Regular security reviews** of role assignments

---

*This guide covers the most common integration scenarios. For advanced use cases or custom requirements, please contact the SSO team.*