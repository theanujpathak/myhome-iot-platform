#!/bin/bash

# i4iot Platform - Clone All Repositories Script
# This script clones all microservice repositories for local development

set -e

echo "🏠 Cloning i4iot Platform Repositories..."
echo "========================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[CLONE]${NC} $1"
}

# Create directories
mkdir -p services platforms frontend infrastructure

# Core Services
print_header "Cloning Core Services..."

clone_repo() {
    local repo_name=$1
    local target_dir=$2
    
    if [ -d "$target_dir" ]; then
        print_status "$repo_name already exists, pulling latest..."
        cd "$target_dir"
        git pull origin main
        cd - > /dev/null
    else
        print_status "Cloning $repo_name..."
        git clone "https://github.com/i4planet/$repo_name.git" "$target_dir"
    fi
}

# Core Services
clone_repo "i4iot-device-service" "services/device-service"
clone_repo "i4iot-ota-service" "services/ota-service"
clone_repo "i4iot-user-service" "services/user-service"
clone_repo "i4iot-scheduler-service" "services/scheduler-service"
clone_repo "i4iot-discovery-service" "services/discovery-service"

# Platform Systems
print_header "Cloning Platform Systems..."
clone_repo "i4iot-monitoring-system" "services/monitoring-system"
clone_repo "i4iot-deployment-system" "services/deployment-system"
clone_repo "i4iot-batch-flashing" "services/batch-flashing"
clone_repo "i4iot-factory-provisioning" "services/factory-provisioning"
clone_repo "i4iot-testing-framework" "services/testing-framework"

# Frontend & Interfaces
print_header "Cloning Frontend Applications..."
clone_repo "i4iot-admin-portal" "frontend/admin-portal"
clone_repo "i4iot-web-app" "frontend/web-app"

# Firmware Platforms
print_header "Cloning Firmware Repositories..."
clone_repo "i4iot-esp32-firmware" "platforms/esp32-firmware"
clone_repo "i4iot-esp8266-firmware" "platforms/esp8266-firmware"
clone_repo "i4iot-arduino-firmware" "platforms/arduino-firmware"
clone_repo "i4iot-stm32-firmware" "platforms/stm32-firmware"
clone_repo "i4iot-pico-firmware" "platforms/pico-firmware"

# Infrastructure
print_header "Cloning Infrastructure Repositories..."
clone_repo "i4iot-infrastructure" "infrastructure/infrastructure"
clone_repo "i4iot-ci-cd" "infrastructure/ci-cd"
clone_repo "i4iot-configs" "infrastructure/configs"

# Documentation & Tools
print_header "Cloning Documentation & Tools..."
clone_repo "i4iot-docs" "docs"
clone_repo "i4iot-tools" "tools"
clone_repo "i4iot-examples" "examples"

print_status "✅ All repositories cloned successfully!"
echo ""
echo "📁 Repository Structure:"
echo "========================"
tree -d -L 2 . 2>/dev/null || find . -type d -maxdepth 2 | sort

echo ""
print_status "🚀 Next steps:"
echo "  1. Install dependencies: ./scripts/install-dependencies.sh"
echo "  2. Start development environment: ./scripts/start-dev.sh"
echo "  3. Open admin portal: open frontend/admin-portal/index.html"
echo ""
print_status "Happy coding! 🎉"