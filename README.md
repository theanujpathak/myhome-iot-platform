# Home Automation System with SSO Integration

A comprehensive home automation system built with FastAPI backend microservices and React frontend, featuring enterprise-grade SSO authentication using Keycloak.

## 🏠 Features

### Core Functionality
- **Device Control**: Manage smart home devices (lights, switches, sensors)
- **Smart Scheduling**: Automated device scheduling and rules
- **Real-time Monitoring**: Live device status updates via MQTT
- **User Management**: Role-based access control with SSO
- **Mobile Responsive**: Works on desktop and mobile devices

### Security & Authentication
- **Single Sign-On (SSO)**: Keycloak integration for centralized authentication
- **Role-based Access**: Admin, Manager, and User roles
- **Session Management**: Secure token-based authentication
- **Brute Force Protection**: Account lockout after failed attempts

### Architecture
- **Microservices**: Separate services for users, devices, and scheduling
- **Event-Driven**: MQTT for real-time device communication
- **Scalable**: Docker containerization for easy deployment
- **Database**: PostgreSQL for persistent storage, Redis for caching

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for development)
- Python 3.11+ (for development)
- curl and jq (for setup scripts)

### 1. Start the System

```bash
# Clone the repository
git clone <repository-url>
cd home-automation-system

# Start all services
docker-compose up -d

# Wait for services to be ready (2-3 minutes)
docker-compose logs -f keycloak
```

### 2. Configure Keycloak

```bash
# Run the automated setup script
cd keycloak-setup
chmod +x setup-home-automation-realm.sh
./setup-home-automation-realm.sh
```

### 3. Access the Application

- **Home Automation Frontend**: http://localhost:3000
- **Keycloak Admin Console**: http://localhost:8080/admin
- **User Service API**: http://localhost:3001
- **Device Service API**: http://localhost:3002
- **Scheduler Service API**: http://localhost:3003

### 4. Login with Test Accounts

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Manager | manager | manager123 |
| User | user | user123 |

## 📁 Project Structure

```
home-automation-system/
├── docker-compose.yml              # Docker services configuration
├── keycloak-setup/                 # Keycloak configuration scripts
│   └── setup-home-automation-realm.sh
├── backend/                        # Backend microservices
│   ├── user-service/              # User management service
│   ├── device-service/            # Device control service
│   └── scheduler-service/         # Scheduling service
├── frontend/                       # React frontend application
│   ├── src/
│   │   ├── components/           # React components
│   │   ├── contexts/             # React contexts
│   │   └── keycloak.js          # Keycloak configuration
│   └── public/
└── docs/                          # Documentation
```

## 🔧 Development

### Backend Development

Each backend service follows the same structure:

```bash
cd backend/user-service
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 3001
```

### Frontend Development

```bash
cd frontend
npm install
npm start
```

### Environment Variables

Backend services use these environment variables:

```bash
DATABASE_URL=postgresql://homeuser:homepass@localhost:5432/home_automation
REDIS_URL=redis://localhost:6379
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=home-automation
KEYCLOAK_CLIENT_ID=home-automation-backend
MQTT_URL=mqtt://localhost:1883
```

Frontend environment variables:

```bash
REACT_APP_KEYCLOAK_URL=http://localhost:8080
REACT_APP_KEYCLOAK_REALM=home-automation
REACT_APP_KEYCLOAK_CLIENT_ID=home-automation-frontend
REACT_APP_API_URL=http://localhost:3001
```

## 🏗️ Sprint Implementation Status

Based on the development plan, here's the current implementation status:

### ✅ Sprint 1 (Foundation) - COMPLETED
- [x] Docker Compose setup
- [x] FastAPI boilerplate with microservices
- [x] PostgreSQL and Redis setup
- [x] MQTT broker (EMQX) setup
- [x] Keycloak SSO integration

### 🔄 Sprint 2 (Authentication) - IN PROGRESS
- [x] User management with JWT tokens
- [x] SSO integration with Keycloak
- [x] Role-based access control
- [ ] OAuth providers (Google, Apple)

### 📅 Sprint 3 (Device Management) - PLANNED
- [ ] Device database schema
- [ ] Device registration APIs
- [ ] MQTT device communication
- [ ] Device-to-user assignment

### 📅 Sprint 4-9 (Remaining Features) - PLANNED
- Location management
- Scheduling system
- AI/ML automation rules
- Mobile app (Flutter/React Native)
- Firmware development
- Admin dashboard

## 🔒 Security Features

### Authentication
- JWT tokens with RS256 signing
- Token refresh mechanism
- Session timeout (30 minutes idle, 10 hours max)
- Secure logout with token invalidation

### Authorization
- Role-based access control (RBAC)
- Endpoint protection by role
- Resource-level permissions

### Security Hardening
- Brute force protection (30 attempts, 15-minute lockout)
- CORS configuration
- Secure headers
- Input validation and sanitization

## 📡 API Documentation

### User Service (Port 3001)
- `GET /health` - Health check
- `GET /api/user/profile` - Get user profile
- `PUT /api/user/profile` - Update user profile
- `GET /api/users` - List users (admin only)
- `POST /api/user/logout` - Logout user

### Device Service (Port 3002)
- `GET /health` - Health check
- `GET /api/devices` - List user devices
- `POST /api/devices` - Add new device
- `PUT /api/devices/{id}` - Update device
- `DELETE /api/devices/{id}` - Remove device

### Scheduler Service (Port 3003)
- `GET /health` - Health check
- `GET /api/schedules` - List user schedules
- `POST /api/schedules` - Create schedule
- `PUT /api/schedules/{id}` - Update schedule
- `DELETE /api/schedules/{id}` - Delete schedule

## 🐛 Troubleshooting

### Common Issues

1. **Keycloak not starting**
   ```bash
   # Check logs
   docker-compose logs keycloak
   
   # Ensure ports are available
   netstat -tlnp | grep :8080
   ```

2. **Database connection failed**
   ```bash
   # Check database container
   docker-compose logs home-automation-db
   
   # Test connection
   psql -h localhost -U homeuser -d home_automation
   ```

3. **Frontend login redirect issues**
   - Verify Keycloak client configuration
   - Check redirect URLs in client settings
   - Ensure CORS is properly configured

### Logs and Monitoring

```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f keycloak
docker-compose logs -f user-service
docker-compose logs -f frontend
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Keycloak for SSO implementation
- FastAPI for backend framework
- React for frontend framework
- Material-UI for UI components
- EMQX for MQTT broker