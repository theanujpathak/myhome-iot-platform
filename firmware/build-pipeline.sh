#!/bin/bash

# Home Automation Firmware Build Pipeline
# Supports ESP32, ESP8266, Arduino, STM32, and Raspberry Pi Pico

set -e

# Configuration
FIRMWARE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$FIRMWARE_DIR/builds"
DIST_DIR="$FIRMWARE_DIR/dist"
LOG_DIR="$FIRMWARE_DIR/logs"
CONFIG_FILE="$FIRMWARE_DIR/build-config.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        INFO)
            echo -e "${GREEN}[INFO]${NC} $timestamp - $message" | tee -a "$LOG_DIR/build.log"
            ;;
        WARN)
            echo -e "${YELLOW}[WARN]${NC} $timestamp - $message" | tee -a "$LOG_DIR/build.log"
            ;;
        ERROR)
            echo -e "${RED}[ERROR]${NC} $timestamp - $message" | tee -a "$LOG_DIR/build.log"
            ;;
        DEBUG)
            echo -e "${BLUE}[DEBUG]${NC} $timestamp - $message" | tee -a "$LOG_DIR/build.log"
            ;;
    esac
}

# Create directories
setup_directories() {
    log "INFO" "Setting up build directories"
    mkdir -p "$BUILD_DIR" "$DIST_DIR" "$LOG_DIR"
    
    # Create subdirectories for each platform
    mkdir -p "$BUILD_DIR/esp32" "$BUILD_DIR/esp8266" "$BUILD_DIR/arduino" "$BUILD_DIR/stm32" "$BUILD_DIR/pico"
    mkdir -p "$DIST_DIR/esp32" "$DIST_DIR/esp8266" "$DIST_DIR/arduino" "$DIST_DIR/stm32" "$DIST_DIR/pico"
}

# Check dependencies
check_dependencies() {
    log "INFO" "Checking build dependencies"
    
    # Check if PlatformIO is installed
    if ! command -v pio &> /dev/null; then
        log "ERROR" "PlatformIO is not installed. Please install it first."
        exit 1
    fi
    
    # Check if Python is installed
    if ! command -v python3 &> /dev/null; then
        log "ERROR" "Python 3 is not installed. Please install it first."
        exit 1
    fi
    
    # Check if jq is installed for JSON processing
    if ! command -v jq &> /dev/null; then
        log "WARN" "jq is not installed. Installing..."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew install jq
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            sudo apt-get update && sudo apt-get install -y jq
        fi
    fi
    
    log "INFO" "All dependencies are available"
}

# Load build configuration
load_config() {
    if [[ -f "$CONFIG_FILE" ]]; then
        log "INFO" "Loading build configuration from $CONFIG_FILE"
        # Export configuration variables
        export BUILD_CONFIG=$(cat "$CONFIG_FILE")
    else
        log "INFO" "No build configuration found, using defaults"
        export BUILD_CONFIG='{
            "version": "1.0.0",
            "build_number": 1,
            "environments": ["esp32", "esp8266", "arduino", "stm32", "pico"],
            "optimization": "release",
            "debug": false
        }'
    fi
}

# Generate firmware metadata
generate_metadata() {
    local platform=$1
    local firmware_path=$2
    local version=$3
    local build_number=$4
    
    log "INFO" "Generating metadata for $platform firmware"
    
    # Calculate file size and checksum
    local file_size=$(stat -c%s "$firmware_path" 2>/dev/null || stat -f%z "$firmware_path" 2>/dev/null || echo "0")
    local checksum=$(sha256sum "$firmware_path" 2>/dev/null | cut -d' ' -f1 || shasum -a 256 "$firmware_path" | cut -d' ' -f1)
    
    # Create metadata JSON
    cat > "${firmware_path}.metadata.json" << EOF
{
    "platform": "$platform",
    "version": "$version",
    "build_number": $build_number,
    "build_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "file_size": $file_size,
    "checksum": "$checksum",
    "compiler": "platformio",
    "optimization": "$(echo "$BUILD_CONFIG" | jq -r '.optimization')",
    "debug": $(echo "$BUILD_CONFIG" | jq -r '.debug'),
    "capabilities": $(get_platform_capabilities "$platform"),
    "hardware_requirements": $(get_hardware_requirements "$platform")
}
EOF
}

# Get platform capabilities
get_platform_capabilities() {
    local platform=$1
    
    case $platform in
        esp32)
            echo '["wifi", "bluetooth", "ota", "mqtt", "https", "pwm", "adc", "spi", "i2c", "uart"]'
            ;;
        esp8266)
            echo '["wifi", "ota", "mqtt", "https", "pwm", "adc", "spi", "i2c", "uart"]'
            ;;
        arduino)
            echo '["ethernet", "mqtt", "pwm", "adc", "spi", "i2c", "uart"]'
            ;;
        stm32)
            echo '["ethernet", "can", "usb", "pwm", "adc", "spi", "i2c", "uart"]'
            ;;
        pico)
            echo '["wifi", "bluetooth", "ota", "pwm", "adc", "spi", "i2c", "uart", "pio"]'
            ;;
        *)
            echo '["basic"]'
            ;;
    esac
}

# Get hardware requirements
get_hardware_requirements() {
    local platform=$1
    
    case $platform in
        esp32)
            echo '{"min_flash": 4194304, "min_ram": 520192, "min_cpu_freq": 160000000}'
            ;;
        esp8266)
            echo '{"min_flash": 1048576, "min_ram": 81920, "min_cpu_freq": 80000000}'
            ;;
        arduino)
            echo '{"min_flash": 32768, "min_ram": 2048, "min_cpu_freq": 16000000}'
            ;;
        stm32)
            echo '{"min_flash": 524288, "min_ram": 131072, "min_cpu_freq": 72000000}'
            ;;
        pico)
            echo '{"min_flash": 2097152, "min_ram": 264192, "min_cpu_freq": 133000000}'
            ;;
        *)
            echo '{"min_flash": 32768, "min_ram": 1024, "min_cpu_freq": 8000000}'
            ;;
    esac
}

# Build firmware for specific platform
build_firmware() {
    local platform=$1
    local project_path="$FIRMWARE_DIR/$platform"
    local version=$(echo "$BUILD_CONFIG" | jq -r '.version')
    local build_number=$(echo "$BUILD_CONFIG" | jq -r '.build_number')
    
    log "INFO" "Building firmware for $platform"
    
    if [[ ! -d "$project_path" ]]; then
        log "ERROR" "Project path $project_path does not exist"
        return 1
    fi
    
    # Change to project directory
    cd "$project_path"
    
    # Clean previous build
    pio run --target clean
    
    # Build firmware
    log "INFO" "Compiling $platform firmware..."
    if pio run; then
        log "INFO" "Build successful for $platform"
        
        # Find the built firmware file
        local firmware_file
        case $platform in
            esp32*|esp8266*)
                firmware_file=$(find .pio/build -name "*.bin" | head -1)
                ;;
            arduino*|stm32*)
                firmware_file=$(find .pio/build -name "*.hex" | head -1)
                ;;
            pico*)
                firmware_file=$(find .pio/build -name "*.uf2" | head -1)
                ;;
        esac
        
        if [[ -n "$firmware_file" && -f "$firmware_file" ]]; then
            # Copy to dist directory with version
            local dist_file="$DIST_DIR/$platform/firmware-$version-$build_number.$(basename "$firmware_file" | cut -d. -f2-)"
            cp "$firmware_file" "$dist_file"
            
            # Generate metadata
            generate_metadata "$platform" "$dist_file" "$version" "$build_number"
            
            log "INFO" "Firmware built and saved to $dist_file"
            
            # Create latest symlink
            local latest_file="$DIST_DIR/$platform/firmware-latest.$(basename "$firmware_file" | cut -d. -f2-)"
            ln -sf "$(basename "$dist_file")" "$latest_file"
            
            return 0
        else
            log "ERROR" "Built firmware file not found for $platform"
            return 1
        fi
    else
        log "ERROR" "Build failed for $platform"
        return 1
    fi
}

# Build all platforms
build_all() {
    local environments=$(echo "$BUILD_CONFIG" | jq -r '.environments[]')
    local total_builds=0
    local successful_builds=0
    
    log "INFO" "Starting build process for all platforms"
    
    for env in $environments; do
        total_builds=$((total_builds + 1))
        
        # Find matching project directory
        local project_dir=""
        case $env in
            esp32)
                project_dir="esp32-smart-light"
                ;;
            esp8266)
                project_dir="esp8266-switch"
                ;;
            arduino)
                project_dir="arduino-uno-gateway"
                ;;
            stm32)
                project_dir="stm32-sensor-hub"
                ;;
            pico)
                project_dir="raspberry-pi-pico"
                ;;
        esac
        
        if [[ -d "$FIRMWARE_DIR/$project_dir" ]]; then
            if build_firmware "$project_dir"; then
                successful_builds=$((successful_builds + 1))
            fi
        else
            log "WARN" "Project directory for $env not found, skipping"
        fi
    done
    
    log "INFO" "Build process completed: $successful_builds/$total_builds successful"
    
    # Generate build report
    generate_build_report "$successful_builds" "$total_builds"
}

# Generate build report
generate_build_report() {
    local successful=$1
    local total=$2
    local report_file="$DIST_DIR/build-report.json"
    
    log "INFO" "Generating build report"
    
    cat > "$report_file" << EOF
{
    "build_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "version": "$(echo "$BUILD_CONFIG" | jq -r '.version')",
    "build_number": $(echo "$BUILD_CONFIG" | jq -r '.build_number'),
    "total_builds": $total,
    "successful_builds": $successful,
    "failed_builds": $((total - successful)),
    "success_rate": $(echo "scale=2; $successful * 100 / $total" | bc -l 2>/dev/null || echo "0"),
    "artifacts": [
EOF

    # Add artifact information
    local first=true
    for platform_dir in "$DIST_DIR"/*; do
        if [[ -d "$platform_dir" ]]; then
            local platform=$(basename "$platform_dir")
            for firmware_file in "$platform_dir"/firmware-*.bin "$platform_dir"/firmware-*.hex "$platform_dir"/firmware-*.uf2; do
                if [[ -f "$firmware_file" && "$firmware_file" != *"latest"* ]]; then
                    if [[ "$first" == "true" ]]; then
                        first=false
                    else
                        echo "," >> "$report_file"
                    fi
                    
                    echo "        {" >> "$report_file"
                    echo "            \"platform\": \"$platform\"," >> "$report_file"
                    echo "            \"filename\": \"$(basename "$firmware_file")\"," >> "$report_file"
                    echo "            \"path\": \"$firmware_file\"," >> "$report_file"
                    echo "            \"metadata\": \"${firmware_file}.metadata.json\"" >> "$report_file"
                    echo -n "        }" >> "$report_file"
                fi
            done
        fi
    done
    
    echo "" >> "$report_file"
    echo "    ]" >> "$report_file"
    echo "}" >> "$report_file"
    
    log "INFO" "Build report generated: $report_file"
}

# Upload firmware to OTA service
upload_to_ota_service() {
    local ota_service_url="http://localhost:3004"
    local api_token=${OTA_API_TOKEN:-""}
    
    if [[ -z "$api_token" ]]; then
        log "WARN" "No OTA API token provided, skipping upload"
        return 0
    fi
    
    log "INFO" "Uploading firmware to OTA service"
    
    for platform_dir in "$DIST_DIR"/*; do
        if [[ -d "$platform_dir" ]]; then
            local platform=$(basename "$platform_dir")
            
            for firmware_file in "$platform_dir"/firmware-*.bin "$platform_dir"/firmware-*.hex "$platform_dir"/firmware-*.uf2; do
                if [[ -f "$firmware_file" && "$firmware_file" != *"latest"* ]]; then
                    local metadata_file="${firmware_file}.metadata.json"
                    
                    if [[ -f "$metadata_file" ]]; then
                        log "INFO" "Uploading $firmware_file to OTA service"
                        
                        # Extract metadata
                        local device_type=$(jq -r '.platform' "$metadata_file")
                        local version=$(jq -r '.version' "$metadata_file")
                        local build_number=$(jq -r '.build_number' "$metadata_file")
                        
                        # Upload via API
                        curl -X POST "$ota_service_url/api/firmware/upload" \
                            -H "Authorization: Bearer $api_token" \
                            -F "firmware_file=@$firmware_file" \
                            -F "device_type=$device_type" \
                            -F "board_model=generic" \
                            -F "version=$version.$build_number" \
                            -F "status=testing" \
                            -F "description=Automated build from pipeline" \
                            -F "changelog=Build $build_number for $device_type" \
                            --silent --show-error
                        
                        if [[ $? -eq 0 ]]; then
                            log "INFO" "Successfully uploaded $firmware_file"
                        else
                            log "ERROR" "Failed to upload $firmware_file"
                        fi
                    fi
                fi
            done
        fi
    done
}

# Clean build artifacts
clean() {
    log "INFO" "Cleaning build artifacts"
    rm -rf "$BUILD_DIR" "$DIST_DIR" "$LOG_DIR"
    
    # Clean PlatformIO build directories
    for project_dir in "$FIRMWARE_DIR"/*; do
        if [[ -d "$project_dir/.pio" ]]; then
            rm -rf "$project_dir/.pio"
        fi
    done
    
    log "INFO" "Clean completed"
}

# Increment build number
increment_build_number() {
    local current_build=$(echo "$BUILD_CONFIG" | jq -r '.build_number')
    local new_build=$((current_build + 1))
    
    # Update build configuration
    echo "$BUILD_CONFIG" | jq ".build_number = $new_build" > "$CONFIG_FILE"
    
    log "INFO" "Build number incremented to $new_build"
}

# Main function
main() {
    local command=${1:-"build"}
    
    log "INFO" "Starting firmware build pipeline"
    
    setup_directories
    check_dependencies
    load_config
    
    case $command in
        build)
            build_all
            increment_build_number
            ;;
        clean)
            clean
            ;;
        upload)
            upload_to_ota_service
            ;;
        build-and-upload)
            build_all
            increment_build_number
            upload_to_ota_service
            ;;
        *)
            echo "Usage: $0 {build|clean|upload|build-and-upload}"
            echo "  build           - Build firmware for all platforms"
            echo "  clean           - Clean build artifacts"
            echo "  upload          - Upload built firmware to OTA service"
            echo "  build-and-upload - Build and upload firmware"
            exit 1
            ;;
    esac
    
    log "INFO" "Firmware build pipeline completed"
}

# Run main function with all arguments
main "$@"