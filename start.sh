#!/bin/bash

# Home Automation System Startup Script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🏠 Home Automation System Startup${NC}"
echo -e "${BLUE}=================================${NC}"

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Docker is running${NC}"
}

# Function to check if required tools are installed
check_dependencies() {
    echo -e "${YELLOW}📋 Checking dependencies...${NC}"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed${NC}"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${RED}❌ Docker Compose is not installed${NC}"
        exit 1
    fi
    
    # Check curl
    if ! command -v curl &> /dev/null; then
        echo -e "${RED}❌ curl is not installed${NC}"
        exit 1
    fi
    
    # Check jq
    if ! command -v jq &> /dev/null; then
        echo -e "${YELLOW}⚠️ jq is not installed. Installing jq...${NC}"
        if command -v brew &> /dev/null; then
            brew install jq
        elif command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y jq
        elif command -v yum &> /dev/null; then
            sudo yum install -y jq
        else
            echo -e "${RED}❌ Please install jq manually${NC}"
            exit 1
        fi
    fi
    
    echo -e "${GREEN}✅ All dependencies are installed${NC}"
}

# Function to start services
start_services() {
    echo -e "${YELLOW}🚀 Starting services...${NC}"
    
    # Create necessary directories
    mkdir -p keycloak-data
    
    # Start services with Docker Compose
    if command -v docker-compose &> /dev/null; then
        docker-compose up -d
    else
        docker compose up -d
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Services started successfully${NC}"
    else
        echo -e "${RED}❌ Failed to start services${NC}"
        exit 1
    fi
}

# Function to wait for services to be ready
wait_for_services() {
    echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
    
    # Wait for Keycloak
    echo -e "${YELLOW}⏳ Waiting for Keycloak (this may take 2-3 minutes)...${NC}"
    max_attempts=60
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f "http://localhost:8080/health/ready" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Keycloak is ready${NC}"
            break
        fi
        
        echo -n "."
        sleep 5
        attempt=$((attempt + 1))
    done
    
    if [ $attempt -eq $max_attempts ]; then
        echo -e "${RED}❌ Keycloak failed to start${NC}"
        exit 1
    fi
    
    # Wait a bit more for other services
    echo -e "${YELLOW}⏳ Waiting for other services...${NC}"
    sleep 10
    
    echo -e "${GREEN}✅ All services are ready${NC}"
}

# Function to setup Keycloak
setup_keycloak() {
    echo -e "${YELLOW}🔐 Setting up Keycloak realm...${NC}"
    
    if [ -f "keycloak-setup/setup-home-automation-realm.sh" ]; then
        cd keycloak-setup
        chmod +x setup-home-automation-realm.sh
        ./setup-home-automation-realm.sh
        cd ..
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Keycloak setup completed${NC}"
        else
            echo -e "${RED}❌ Keycloak setup failed${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ Keycloak setup script not found${NC}"
        exit 1
    fi
}

# Function to display service status
show_status() {
    echo -e "${BLUE}📊 Service Status${NC}"
    echo -e "${BLUE}===============${NC}"
    
    if command -v docker-compose &> /dev/null; then
        docker-compose ps
    else
        docker compose ps
    fi
}

# Function to display access information
show_access_info() {
    echo -e "${GREEN}🎉 Home Automation System is Ready!${NC}"
    echo -e "${GREEN}======================================${NC}"
    echo ""
    echo -e "${GREEN}📱 Frontend Application:${NC}"
    echo -e "   URL: ${BLUE}http://localhost:3000${NC}"
    echo ""
    echo -e "${GREEN}🔐 Keycloak Admin Console:${NC}"
    echo -e "   URL: ${BLUE}http://localhost:8080/admin${NC}"
    echo -e "   Username: ${YELLOW}admin${NC}"
    echo -e "   Password: ${YELLOW}admin${NC}"
    echo ""
    echo -e "${GREEN}🔧 API Services:${NC}"
    echo -e "   User Service: ${BLUE}http://localhost:3001${NC}"
    echo -e "   Device Service: ${BLUE}http://localhost:3002${NC}"
    echo -e "   Scheduler Service: ${BLUE}http://localhost:3003${NC}"
    echo ""
    echo -e "${GREEN}🗄️ Databases:${NC}"
    echo -e "   PostgreSQL: ${BLUE}localhost:5432${NC}"
    echo -e "   Redis: ${BLUE}localhost:6379${NC}"
    echo ""
    echo -e "${GREEN}📡 MQTT Broker:${NC}"
    echo -e "   MQTT: ${BLUE}localhost:1883${NC}"
    echo -e "   WebSocket: ${BLUE}localhost:8083${NC}"
    echo -e "   Dashboard: ${BLUE}http://localhost:18083${NC}"
    echo ""
    echo -e "${GREEN}👥 Test Accounts:${NC}"
    echo -e "   Admin: ${YELLOW}admin / admin123${NC}"
    echo -e "   Manager: ${YELLOW}manager / manager123${NC}"
    echo -e "   User: ${YELLOW}user / user123${NC}"
    echo ""
    echo -e "${GREEN}📖 Documentation:${NC}"
    echo -e "   README: ${BLUE}./README.md${NC}"
    echo -e "   Sprint Plan: ${BLUE}./home_automation_sprint_plan.csv${NC}"
    echo ""
    echo -e "${YELLOW}💡 Next Steps:${NC}"
    echo -e "   1. Open ${BLUE}http://localhost:3000${NC} in your browser"
    echo -e "   2. Click 'Sign In with SSO'"
    echo -e "   3. Use test credentials to log in"
    echo -e "   4. Start adding devices and creating schedules!"
    echo ""
    echo -e "${YELLOW}🛑 To Stop Services:${NC}"
    echo -e "   Run: ${BLUE}./stop.sh${NC} or ${BLUE}docker-compose down${NC}"
}

# Main execution
main() {
    check_dependencies
    check_docker
    start_services
    wait_for_services
    setup_keycloak
    show_status
    show_access_info
}

# Handle script arguments
case "${1:-start}" in
    start)
        main
        ;;
    status)
        show_status
        ;;
    info)
        show_access_info
        ;;
    *)
        echo -e "${YELLOW}Usage: $0 [start|status|info]${NC}"
        echo -e "${YELLOW}  start  - Start all services (default)${NC}"
        echo -e "${YELLOW}  status - Show service status${NC}"
        echo -e "${YELLOW}  info   - Show access information${NC}"
        exit 1
        ;;
esac