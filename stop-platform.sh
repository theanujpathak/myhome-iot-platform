#!/bin/bash

# i4iot Platform Stop Script
# This script stops all the IoT platform services

echo "🛑 Stopping i4iot Platform..."
echo "================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Function to stop a service
stop_service() {
    local service_name=$1
    local port=$2
    
    print_status "Stopping $service_name..."
    
    # Stop by PID file if exists
    if [ -f "logs/${service_name}.pid" ]; then
        local pid=$(cat "logs/${service_name}.pid")
        if kill -0 $pid 2>/dev/null; then
            kill $pid
            print_status "$service_name (PID $pid) stopped"
        fi
        rm -f "logs/${service_name}.pid"
    fi
    
    # Stop by port if still running
    if [ -n "$port" ]; then
        local pid=$(lsof -ti:$port 2>/dev/null)
        if [ -n "$pid" ]; then
            kill $pid 2>/dev/null
            print_status "Process on port $port stopped"
        fi
    fi
}

# Create logs directory if it doesn't exist
mkdir -p logs

# Stop all services
stop_service "monitoring-system" ""
stop_service "monitoring-api" "5002"
stop_service "deployment-api" "5001"
stop_service "batch-flashing-api" "5000"

# Kill any remaining Python processes related to our platform
pkill -f "monitoring-alerting-system.py" 2>/dev/null || true
pkill -f "monitoring-api.py" 2>/dev/null || true
pkill -f "deployment-api.py" 2>/dev/null || true
pkill -f "batch-flash-api.py" 2>/dev/null || true

# Wait a moment for processes to terminate
sleep 2

# Check if any services are still running
echo ""
echo "🔍 Checking for remaining processes..."

check_port() {
    local port=$1
    local service=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "$service is still running on port $port"
        return 1
    else
        print_status "Port $port is free"
        return 0
    fi
}

all_stopped=true

check_port 5002 "Monitoring API" || all_stopped=false
check_port 5001 "Deployment API" || all_stopped=false
check_port 5000 "Batch Flashing API" || all_stopped=false

if [ "$all_stopped" = true ]; then
    print_status "✅ All platform services stopped successfully"
else
    print_warning "⚠️  Some services may still be running"
    echo ""
    echo "To force stop remaining processes:"
    echo "sudo lsof -ti:5000,5001,5002 | xargs kill -9"
fi

echo ""
print_status "Platform shutdown complete! 🛑"