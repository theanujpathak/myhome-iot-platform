#!/bin/bash

# Home Automation Keycloak Setup Script

KEYCLOAK_URL="http://localhost:8080"
ADMIN_USER="admin"
ADMIN_PASSWORD="admin"
REALM_NAME="home-automation"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🏠 Setting up Home Automation Keycloak Realm${NC}"

# Function to wait for Keycloak to be ready
wait_for_keycloak() {
    echo -e "${YELLOW}⏳ Waiting for Keycloak to be ready...${NC}"
    
    max_attempts=30
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f "$KEYCLOAK_URL/health/ready" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Keycloak is ready!${NC}"
            return 0
        fi
        
        echo -e "${YELLOW}⏳ Attempt $((attempt + 1))/$max_attempts - Keycloak not ready yet...${NC}"
        sleep 10
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}❌ Keycloak failed to start after $max_attempts attempts${NC}"
    exit 1
}

# Function to get admin access token
get_admin_token() {
    echo -e "${YELLOW}🔐 Getting admin access token...${NC}"
    
    ADMIN_TOKEN=$(curl -s -X POST "$KEYCLOAK_URL/realms/master/protocol/openid-connect/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=$ADMIN_USER" \
        -d "password=$ADMIN_PASSWORD" \
        -d "grant_type=password" \
        -d "client_id=admin-cli" | jq -r '.access_token')
    
    if [ "$ADMIN_TOKEN" = "null" ] || [ -z "$ADMIN_TOKEN" ]; then
        echo -e "${RED}❌ Failed to get admin token${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Admin token obtained${NC}"
}

# Function to create realm
create_realm() {
    echo -e "${YELLOW}🌍 Creating realm: $REALM_NAME${NC}"
    
    curl -s -X POST "$KEYCLOAK_URL/admin/realms" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "realm": "'$REALM_NAME'",
            "enabled": true,
            "displayName": "Home Automation",
            "displayNameHtml": "<strong>Home Automation</strong>",
            "loginTheme": "keycloak",
            "accountTheme": "keycloak",
            "adminTheme": "keycloak",
            "emailTheme": "keycloak",
            "accessTokenLifespan": 300,
            "ssoSessionMaxLifespan": 36000,
            "ssoSessionIdleTimeout": 1800,
            "offlineSessionIdleTimeout": 2592000,
            "bruteForceProtected": true,
            "failureFactor": 30,
            "waitIncrementSeconds": 60,
            "quickLoginCheckMilliSeconds": 1000,
            "minimumQuickLoginWaitSeconds": 60,
            "maxFailureWaitSeconds": 900,
            "maxDeltaTimeSeconds": 43200,
            "registrationAllowed": true,
            "registrationEmailAsUsername": true,
            "rememberMe": true,
            "verifyEmail": false,
            "resetPasswordAllowed": true,
            "editUsernameAllowed": true,
            "loginWithEmailAllowed": true,
            "duplicateEmailsAllowed": false
        }' > /dev/null
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Realm created successfully${NC}"
    else
        echo -e "${YELLOW}⚠️ Realm might already exist${NC}"
    fi
}

# Function to create client roles
create_client_roles() {
    echo -e "${YELLOW}👥 Creating client roles...${NC}"
    
    # Create admin role
    curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM_NAME/roles" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "admin",
            "description": "Administrator role with full access",
            "composite": false,
            "clientRole": false
        }' > /dev/null
    
    # Create user role
    curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM_NAME/roles" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "user",
            "description": "Standard user role",
            "composite": false,
            "clientRole": false
        }' > /dev/null
    
    # Create manager role
    curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM_NAME/roles" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "manager",
            "description": "Manager role with elevated permissions",
            "composite": false,
            "clientRole": false
        }' > /dev/null
    
    echo -e "${GREEN}✅ Roles created successfully${NC}"
}

# Function to create frontend client
create_frontend_client() {
    echo -e "${YELLOW}🖥️ Creating frontend client...${NC}"
    
    curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM_NAME/clients" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "clientId": "home-automation-frontend",
            "name": "Home Automation Frontend",
            "description": "React frontend application",
            "enabled": true,
            "publicClient": true,
            "directAccessGrantsEnabled": true,
            "implicitFlowEnabled": true,
            "standardFlowEnabled": true,
            "serviceAccountsEnabled": false,
            "protocol": "openid-connect",
            "rootUrl": "http://localhost:3000",
            "baseUrl": "http://localhost:3000",
            "adminUrl": "http://localhost:3000",
            "redirectUris": [
                "http://localhost:3000/*"
            ],
            "webOrigins": [
                "http://localhost:3000"
            ],
            "attributes": {
                "post.logout.redirect.uris": "http://localhost:3000/*"
            }
        }' > /dev/null
    
    echo -e "${GREEN}✅ Frontend client created${NC}"
}

# Function to create backend client
create_backend_client() {
    echo -e "${YELLOW}🔧 Creating backend client...${NC}"
    
    curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM_NAME/clients" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "clientId": "home-automation-backend",
            "name": "Home Automation Backend",
            "description": "Backend API services",
            "enabled": true,
            "publicClient": false,
            "directAccessGrantsEnabled": true,
            "implicitFlowEnabled": false,
            "standardFlowEnabled": true,
            "serviceAccountsEnabled": true,
            "protocol": "openid-connect",
            "bearerOnly": true,
            "attributes": {
                "access.token.lifespan": "300"
            }
        }' > /dev/null
    
    echo -e "${GREEN}✅ Backend client created${NC}"
}

# Function to create test users
create_test_users() {
    echo -e "${YELLOW}👤 Creating test users...${NC}"
    
    # Create admin user
    curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM_NAME/users" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "username": "admin",
            "email": "admin@homeautomation.com",
            "firstName": "Admin",
            "lastName": "User",
            "enabled": true,
            "emailVerified": true,
            "credentials": [{
                "type": "password",
                "value": "admin123",
                "temporary": false
            }]
        }' > /dev/null
    
    # Create regular user
    curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM_NAME/users" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "username": "user",
            "email": "user@homeautomation.com",
            "firstName": "Regular",
            "lastName": "User",
            "enabled": true,
            "emailVerified": true,
            "credentials": [{
                "type": "password",
                "value": "user123",
                "temporary": false
            }]
        }' > /dev/null
    
    # Create manager user
    curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM_NAME/users" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "username": "manager",
            "email": "manager@homeautomation.com",
            "firstName": "Manager",
            "lastName": "User",
            "enabled": true,
            "emailVerified": true,
            "credentials": [{
                "type": "password",
                "value": "manager123",
                "temporary": false
            }]
        }' > /dev/null
    
    echo -e "${GREEN}✅ Test users created${NC}"
}

# Function to assign roles to users
assign_user_roles() {
    echo -e "${YELLOW}🔗 Assigning roles to users...${NC}"
    
    # Get user IDs
    ADMIN_USER_ID=$(curl -s -X GET "$KEYCLOAK_URL/admin/realms/$REALM_NAME/users?username=admin" \
        -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.[0].id')
    
    USER_USER_ID=$(curl -s -X GET "$KEYCLOAK_URL/admin/realms/$REALM_NAME/users?username=user" \
        -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.[0].id')
    
    MANAGER_USER_ID=$(curl -s -X GET "$KEYCLOAK_URL/admin/realms/$REALM_NAME/users?username=manager" \
        -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.[0].id')
    
    # Get role representations
    ADMIN_ROLE=$(curl -s -X GET "$KEYCLOAK_URL/admin/realms/$REALM_NAME/roles/admin" \
        -H "Authorization: Bearer $ADMIN_TOKEN")
    
    USER_ROLE=$(curl -s -X GET "$KEYCLOAK_URL/admin/realms/$REALM_NAME/roles/user" \
        -H "Authorization: Bearer $ADMIN_TOKEN")
    
    MANAGER_ROLE=$(curl -s -X GET "$KEYCLOAK_URL/admin/realms/$REALM_NAME/roles/manager" \
        -H "Authorization: Bearer $ADMIN_TOKEN")
    
    # Assign admin role to admin user
    curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM_NAME/users/$ADMIN_USER_ID/role-mappings/realm" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d "[$ADMIN_ROLE]" > /dev/null
    
    # Assign user role to regular user
    curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM_NAME/users/$USER_USER_ID/role-mappings/realm" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d "[$USER_ROLE]" > /dev/null
    
    # Assign manager role to manager user
    curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM_NAME/users/$MANAGER_USER_ID/role-mappings/realm" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d "[$MANAGER_ROLE]" > /dev/null
    
    echo -e "${GREEN}✅ Roles assigned successfully${NC}"
}

# Function to display completion message
display_completion() {
    echo -e "${GREEN}🎉 Home Automation Keycloak Setup Complete!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}🌐 Keycloak Admin Console: http://localhost:8080/admin${NC}"
    echo -e "${GREEN}🔐 Admin Username: admin${NC}"
    echo -e "${GREEN}🔐 Admin Password: admin${NC}"
    echo -e "${GREEN}🌍 Realm: $REALM_NAME${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}👥 Test Users:${NC}"
    echo -e "${GREEN}   • Admin: admin / admin123${NC}"
    echo -e "${GREEN}   • Manager: manager / manager123${NC}"
    echo -e "${GREEN}   • User: user / user123${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}🚀 You can now start the Home Automation services!${NC}"
}

# Main execution
main() {
    wait_for_keycloak
    get_admin_token
    create_realm
    create_client_roles
    create_frontend_client
    create_backend_client
    create_test_users
    assign_user_roles
    display_completion
}

# Run main function
main