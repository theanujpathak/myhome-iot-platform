# SSO Setup Guide

This guide walks you through setting up the complete SSO solution with Keycloak.

## Prerequisites

- Docker and Docker Compose installed
- Node.js 18+ and npm installed
- jq (JSON processor) for the setup scripts

## Step 1: Start Keycloak and PostgreSQL

```bash
# Start the containers
docker compose up -d

# Check if containers are running
docker compose ps
```

Wait for Keycloak to be fully started (about 2-3 minutes). You can check the logs:

```bash
docker compose logs -f keycloak
```

## Step 2: Set Up Keycloak Realm

```bash
# Run the automated setup script
cd keycloak-setup
./setup-realm.sh
```

This script will:
- Wait for Keycloak to be ready
- Create the SSO realm
- Set up OIDC clients for React and Node.js
- Create user roles (admin, user, manager)
- Create test users

## Step 3: Configure Google SSO (Optional)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google+ API
4. Create OAuth 2.0 credentials:
   - Application type: Web application
   - Authorized redirect URIs: `http://localhost:8080/realms/sso-realm/broker/google/endpoint`

5. Update the Google Identity Provider in Keycloak:
   - Go to: http://localhost:8080/admin/master/console/#/sso-realm/identity-providers
   - Click on "google"
   - Add your Google Client ID and Secret
   - Save the configuration

## Step 4: Start the Applications

### React App
```bash
cd react-app
npm install
npm start
```

The React app will be available at http://localhost:3000

### Node.js API
```bash
cd node-api
npm install
npm start
```

The API will be available at http://localhost:3001

## Step 5: Test the Integration

1. Open http://localhost:3000 in your browser
2. Click "Login with Keycloak"
3. Use test credentials:
   - Username: `testuser`
   - Password: `test123`
4. After login, try calling the protected API
5. Test logout functionality

## Keycloak Admin Console

Access the Keycloak Admin Console at http://localhost:8080

- Username: `admin`
- Password: `admin`

## API Endpoints

### Public Endpoints
- `GET /health` - Health check
- `GET /api/public` - Public endpoint

### Protected Endpoints
- `GET /api/protected` - Requires valid JWT token
- `GET /api/admin` - Requires admin role
- `GET /api/users` - Requires admin role
- `POST /api/introspect` - Token introspection

## Testing with curl

```bash
# Get token
TOKEN=$(curl -s -X POST "http://localhost:8080/realms/sso-realm/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser" \
  -d "password=test123" \
  -d "grant_type=password" \
  -d "client_id=react-app" | jq -r '.access_token')

# Call protected endpoint
curl -H "Authorization: Bearer $TOKEN" http://localhost:3001/api/protected
```

## Troubleshooting

### Common Issues

1. **Keycloak not starting**: Check Docker logs and ensure ports 8080 and 5432 are available
2. **Token validation failing**: Verify the realm and client configurations
3. **CORS errors**: Ensure the React app origin is added to the client's web origins

### Checking Logs

```bash
# Keycloak logs
docker compose logs keycloak

# API logs
cd node-api && npm start

# React app logs
cd react-app && npm start
```

## Security Considerations

1. Change default passwords in production
2. Use HTTPS for all communications
3. Configure proper CORS settings
4. Set up proper session management
5. Enable brute force protection
6. Configure email verification

## Next Steps

1. Integrate additional applications
2. Set up email configuration
3. Configure user self-registration
4. Set up monitoring and logging
5. Deploy to production environment