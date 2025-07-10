#!/bin/bash

# Home Automation System Stop Script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🏠 Home Automation System Stop${NC}"
echo -e "${BLUE}==============================${NC}"

# Function to stop services
stop_services() {
    echo -e "${YELLOW}🛑 Stopping services...${NC}"
    
    if command -v docker-compose &> /dev/null; then
        docker-compose down
    else
        docker compose down
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Services stopped successfully${NC}"
    else
        echo -e "${RED}❌ Failed to stop some services${NC}"
        exit 1
    fi
}

# Function to stop and remove volumes
stop_and_clean() {
    echo -e "${YELLOW}🧹 Stopping services and removing volumes...${NC}"
    
    if command -v docker-compose &> /dev/null; then
        docker-compose down -v
    else
        docker compose down -v
    fi
    
    echo -e "${YELLOW}🧹 Removing unused Docker resources...${NC}"
    docker system prune -f
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Services stopped and cleaned${NC}"
    else
        echo -e "${RED}❌ Failed to clean some resources${NC}"
        exit 1
    fi
}

# Function to show service status
show_status() {
    echo -e "${BLUE}📊 Service Status${NC}"
    echo -e "${BLUE}===============${NC}"
    
    if command -v docker-compose &> /dev/null; then
        docker-compose ps
    else
        docker compose ps
    fi
}

# Handle script arguments
case "${1:-stop}" in
    stop)
        stop_services
        show_status
        ;;
    clean)
        stop_and_clean
        show_status
        ;;
    status)
        show_status
        ;;
    *)
        echo -e "${YELLOW}Usage: $0 [stop|clean|status]${NC}"
        echo -e "${YELLOW}  stop   - Stop all services (default)${NC}"
        echo -e "${YELLOW}  clean  - Stop services and remove volumes${NC}"
        echo -e "${YELLOW}  status - Show service status${NC}"
        exit 1
        ;;
esac

echo -e "${GREEN}✅ Done!${NC}"