# SSO Implementation with Keycloak

This project implements a complete Single Sign-On (SSO) solution using Keycloak as the identity provider.

## Quick Start

1. **Start Keycloak and PostgreSQL**:
   ```bash
   docker-compose up -d
   ```

2. **Access Keycloak Admin Console**:
   - URL: http://localhost:8080
   - Username: admin
   - Password: admin

3. **Run Sample Applications**:
   ```bash
   # React App
   cd react-app
   npm install
   npm start

   # Node.js API
   cd node-api
   npm install
   npm start
   ```

## Architecture

- **Keycloak**: Identity Provider and Authentication Server
- **PostgreSQL**: Database for Keycloak
- **React App**: Sample frontend application with OIDC login
- **Node.js API**: Sample backend API with token validation
- **Google SSO**: External identity provider integration

## Project Structure

```
├── docker-compose.yml          # Docker setup for Keycloak + PostgreSQL
├── keycloak-setup/            # Keycloak configuration files
├── react-app/                 # Sample React application
├── node-api/                  # Sample Node.js API
└── docs/                      # Documentation
```

## Development Tasks

### Sprint 1 (Foundation)
- [x] Docker Compose setup
- [x] Keycloak container setup
- [x] Realm and client configuration
- [x] Sample React application
- [x] Sample Node.js API
- [x] OIDC integration
- [ ] Google SSO integration
- [ ] Email support setup
- [ ] Manual testing and QA

### Sprint 2 (Enhancement)
- [x] Additional app integration (Admin Dashboard, Employee Portal)
- [x] User management with departmental test users
- [x] Security hardening (brute force protection, session management)
- [x] Documentation (app team guide, user guide, demo materials)

### Sprint 3 (Production)
- [ ] Kubernetes deployment
- [ ] Monitoring and logging
- [ ] Backup strategy
- [ ] Developer portal

## Sprint 2 Progress

✅ **Completed:**
- **Multi-Application SSO**: 3 applications with seamless session sharing
- **Admin Dashboard**: Complete user management interface (port 3002)
- **Employee Portal**: Self-service employee interface (port 3003)
- **Enhanced Security**: Brute force protection and session controls
- **User Management**: 15+ departmental test users with proper roles
- **Documentation**: Comprehensive guides for developers, users, and stakeholders
- **Demo Materials**: Complete walkthrough and presentation materials

## Sprint 1 Progress

✅ **Completed:**
- Docker Compose configuration with Keycloak 23.0 and PostgreSQL 15
- Automated realm setup script with roles and test users
- React application with Keycloak-js integration
- Node.js API with JWT token validation
- OIDC clients configuration for both applications
- Comprehensive setup documentation

🔄 **In Progress:**
- Google SSO integration (requires Google OAuth credentials)
- Email configuration (requires SMTP setup)

## Current Status

**Sprint 2 is complete!** The SSO system now includes:

🎯 **Multi-Application Integration**
- Main React App (http://localhost:3000)
- Admin Dashboard (http://localhost:3002) - Admin role required
- Employee Portal (http://localhost:3003) - All users
- **Demo Application (http://localhost:3004) - SSO Integration Showcase**
- Seamless session sharing across all applications

🔐 **Enterprise Security**
- Brute force protection with account lockout
- Session management with automatic timeouts
- Strong password policies
- Complete audit logging

👥 **User Management**
- 15+ test users across departments
- Role-based access control (Admin, Manager, User)
- Self-service profile management
- Administrative user creation and management

📚 **Complete Documentation**
- Developer integration guides
- User usage instructions
- Demo walkthrough scripts
- Stakeholder presentation materials

Ready for Sprint 3 production deployment!