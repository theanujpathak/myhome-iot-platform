#!/bin/bash

# Setup home-automation realm in existing Keycloak
KEYCLOAK_URL="http://localhost:8080"
ADMIN_USER="admin"
ADMIN_PASS="admin"

echo "Configuring home-automation realm in existing Keycloak..."

# Get admin token
echo "Getting admin token..."
ADMIN_TOKEN=$(curl -s -X POST "$KEYCLOAK_URL/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$ADMIN_USER" \
  -d "password=$ADMIN_PASS" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" | jq -r .access_token)

if [ "$ADMIN_TOKEN" = "null" ] || [ -z "$ADMIN_TOKEN" ]; then
  echo "Failed to get admin token. Please check Keycloak admin credentials."
  echo "Current assumption: admin/admin"
  echo "You may need to adjust ADMIN_USER and ADMIN_PASS variables in this script."
  exit 1
fi

echo "Creating home-automation realm..."
curl -s -X POST "$KEYCLOAK_URL/admin/realms" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "realm": "home-automation",
    "displayName": "Home Automation",
    "enabled": true,
    "registrationAllowed": false,
    "passwordPolicy": "length(8)",
    "accessTokenLifespan": 3600,
    "refreshTokenMaxReuse": 0,
    "ssoSessionMaxLifespan": 86400
  }'

echo "Creating backend client..."
curl -s -X POST "$KEYCLOAK_URL/admin/realms/home-automation/clients" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "home-automation-backend",
    "name": "Home Automation Backend",
    "enabled": true,
    "bearerOnly": true,
    "serviceAccountsEnabled": true,
    "authorizationServicesEnabled": true
  }'

echo "Creating frontend client..."
curl -s -X POST "$KEYCLOAK_URL/admin/realms/home-automation/clients" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "home-automation-frontend",
    "name": "Home Automation Frontend",
    "enabled": true,
    "publicClient": true,
    "redirectUris": ["http://localhost:3000/*"],
    "webOrigins": ["http://localhost:3000"],
    "attributes": {
      "post.logout.redirect.uris": "http://localhost:3000/*"
    }
  }'

echo "Creating admin role..."
curl -s -X POST "$KEYCLOAK_URL/admin/realms/home-automation/roles" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "admin",
    "description": "Administrator role with full access"
  }'

echo "Creating manager role..."
curl -s -X POST "$KEYCLOAK_URL/admin/realms/home-automation/roles" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "manager",
    "description": "Manager role with limited admin access"
  }'

echo "Creating admin user..."
curl -s -X POST "$KEYCLOAK_URL/admin/realms/home-automation/users" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@homeautomation.local",
    "firstName": "Admin",
    "lastName": "User",
    "enabled": true,
    "credentials": [{
      "type": "password",
      "value": "admin123",
      "temporary": false
    }]
  }'

# Get admin user ID and assign role
ADMIN_USER_ID=$(curl -s -G "$KEYCLOAK_URL/admin/realms/home-automation/users" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d "username=admin" | jq -r '.[0].id')

ADMIN_ROLE_ID=$(curl -s "$KEYCLOAK_URL/admin/realms/home-automation/roles/admin" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.id')

echo "Assigning admin role to admin user..."
curl -s -X POST "$KEYCLOAK_URL/admin/realms/home-automation/users/$ADMIN_USER_ID/role-mappings/realm" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "[{\"id\":\"$ADMIN_ROLE_ID\",\"name\":\"admin\"}]"

echo "Creating regular user..."
curl -s -X POST "$KEYCLOAK_URL/admin/realms/home-automation/users" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user",
    "email": "user@homeautomation.local",
    "firstName": "Regular",
    "lastName": "User",
    "enabled": true,
    "credentials": [{
      "type": "password",
      "value": "user123",
      "temporary": false
    }]
  }'

echo ""
echo "✅ Home automation realm configured successfully!"
echo "You can now use the following test credentials:"
echo "Admin: admin / admin123"
echo "User: user / user123"
echo ""
echo "Keycloak Admin Console: http://localhost:8080"
echo "Home Automation Realm: http://localhost:8080/realms/home-automation"