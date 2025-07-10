#!/bin/bash

# MyHome IoT Platform Startup Script
# This script starts all the IoT platform services

set -e

echo "🏠 Starting MyHome IoT Platform..."
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[SYSTEM]${NC} $1"
}

# Check if running from correct directory
if [ ! -f "start-platform.sh" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Create logs directory
mkdir -p logs

# Function to start a service in background
start_service() {
    local service_name=$1
    local command=$2
    local port=$3
    local dir=$4
    
    print_status "Starting $service_name on port $port..."
    
    if [ -n "$dir" ]; then
        cd "$dir"
    fi
    
    # Check if port is already in use
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "$service_name is already running on port $port"
    else
        # Start the service in background
        nohup $command > "../logs/${service_name}.log" 2>&1 &
        local pid=$!
        echo $pid > "../logs/${service_name}.pid"
        print_status "$service_name started with PID $pid"
    fi
    
    # Return to root directory
    cd - > /dev/null
}

# Function to check if a service is healthy
check_service_health() {
    local service_name=$1
    local url=$2
    local max_attempts=30
    local attempt=1
    
    print_status "Checking $service_name health..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            print_status "$service_name is healthy ✅"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_warning "$service_name health check failed after $max_attempts attempts"
    return 1
}

# Stop existing services
print_header "Stopping existing services..."
./stop-platform.sh 2>/dev/null || true

# Install dependencies if needed
print_header "Checking dependencies..."

check_dependencies() {
    local dir=$1
    local service_name=$2
    
    if [ -f "$dir/requirements.txt" ]; then
        print_status "Checking $service_name dependencies..."
        cd "$dir"
        
        # Check if virtual environment exists
        if [ ! -d "venv" ]; then
            print_status "Creating virtual environment for $service_name..."
            python3 -m venv venv
        fi
        
        # Activate virtual environment and install dependencies
        source venv/bin/activate
        pip install -q -r requirements.txt
        deactivate
        
        cd - > /dev/null
    fi
}

# Check dependencies for each service
check_dependencies "monitoring" "Monitoring System"
check_dependencies "deployment" "Deployment System"
check_dependencies "firmware/batch-flashing" "Batch Flashing System"

# Start core services
print_header "Starting core services..."

# Start monitoring system
start_service "monitoring-system" "monitoring/venv/bin/python monitoring/monitoring-alerting-system.py --daemon" "" "monitoring"

# Wait a moment for monitoring to initialize
sleep 3

# Start monitoring API
start_service "monitoring-api" "monitoring/venv/bin/python monitoring/monitoring-api.py" "5002" "monitoring"

# Start deployment API
start_service "deployment-api" "deployment/venv/bin/python deployment/deployment-api.py" "5001" "deployment"

# Start batch flashing API
start_service "batch-flashing-api" "firmware/batch-flashing/venv/bin/python firmware/batch-flashing/batch-flash-api.py" "5000" "firmware/batch-flashing"

# Wait for services to start
sleep 5

# Health checks
print_header "Performing health checks..."

check_service_health "Device Service" "http://localhost:3002/health"
check_service_health "Monitoring API" "http://localhost:5002/health"
check_service_health "Deployment API" "http://localhost:5001/health"
check_service_health "Batch Flashing API" "http://localhost:5000/health"

# Display access information
print_header "🎉 MyHome IoT Platform Started Successfully!"
echo ""
echo "📋 Access Points:"
echo "=================="
echo ""
echo "🏠 Admin Portal:"
echo "   File: admin-portal/admin-portal.html"
echo "   Command: open admin-portal/admin-portal.html"
echo ""
echo "📊 Monitoring System:"
echo "   API: http://localhost:5002"
echo "   Dashboard: monitoring/monitoring-dashboard.html"
echo "   CLI: cd monitoring && python monitoring-cli.py status"
echo ""
echo "🚀 Deployment System:"
echo "   API: http://localhost:5001"
echo "   Dashboard: deployment/deployment-web.html"
echo "   CLI: cd deployment && python deployment-cli.py env list"
echo ""
echo "⚡ Batch Flashing System:"
echo "   API: http://localhost:5000"
echo "   Dashboard: firmware/batch-flashing/web-interface.html"
echo "   CLI: cd firmware/batch-flashing && python batch-flash-cli.py list"
echo ""
echo "📱 Device Service:"
echo "   API: http://localhost:3002"
echo "   Health: http://localhost:3002/health"
echo ""
echo "🔧 Factory Provisioning:"
echo "   Script: cd firmware/factory-provisioning && python factory-flash.py"
echo ""
echo "🧪 Testing Framework:"
echo "   Script: cd firmware/testing && python test-framework.py"
echo ""
echo "📜 Logs:"
echo "   Directory: logs/"
echo "   View: tail -f logs/*.log"
echo ""
echo "🛑 Stop Platform:"
echo "   Command: ./stop-platform.sh"
echo ""

# API Keys
print_header "🔑 API Keys & Authentication:"
echo "Monitoring API Key: monitoring-api-key-1"
echo "Deployment API Key: your-api-key"
echo ""

# Quick commands
print_header "⚡ Quick Commands:"
echo "View system status: cd monitoring && python monitoring-cli.py status"
echo "Open admin portal: open admin-portal/admin-portal.html"
echo "View all logs: tail -f logs/*.log"
echo "Stop platform: ./stop-platform.sh"
echo ""

print_status "Platform startup complete! 🚀"