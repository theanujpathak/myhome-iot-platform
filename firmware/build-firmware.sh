#!/bin/bash

# ESP32 Firmware Build Script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 ESP32 Firmware Build Tool${NC}"
echo -e "${BLUE}============================${NC}"

# Check if PlatformIO is installed
check_platformio() {
    if ! command -v pio &> /dev/null; then
        echo -e "${RED}❌ PlatformIO is not installed${NC}"
        echo -e "${YELLOW}📦 Installing PlatformIO...${NC}"
        
        # Install PlatformIO
        if command -v pip &> /dev/null; then
            pip install platformio
        elif command -v pip3 &> /dev/null; then
            pip3 install platformio
        else
            echo -e "${RED}❌ Python/pip not found. Please install Python first.${NC}"
            exit 1
        fi
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ PlatformIO installed successfully${NC}"
        else
            echo -e "${RED}❌ Failed to install PlatformIO${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}✅ PlatformIO is installed${NC}"
    fi
}

# Build firmware for a specific project
build_firmware() {
    local project_dir=$1
    local project_name=$(basename "$project_dir")
    
    echo -e "${YELLOW}🔨 Building firmware: ${project_name}${NC}"
    
    if [ ! -d "$project_dir" ]; then
        echo -e "${RED}❌ Project directory not found: $project_dir${NC}"
        return 1
    fi
    
    cd "$project_dir"
    
    # Clean previous build
    echo -e "${YELLOW}🧹 Cleaning previous build...${NC}"
    pio run --target clean
    
    # Build firmware
    echo -e "${YELLOW}🔨 Building firmware...${NC}"
    pio run
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Build successful for ${project_name}${NC}"
        
        # Get firmware details
        local firmware_file=".pio/build/esp32dev/firmware.bin"
        if [ -f "$firmware_file" ]; then
            local file_size=$(stat -f%z "$firmware_file" 2>/dev/null || stat -c%s "$firmware_file" 2>/dev/null)
            local checksum=$(shasum -a 256 "$firmware_file" | cut -d' ' -f1)
            
            echo -e "${GREEN}📊 Firmware Details:${NC}"
            echo -e "   File: $firmware_file"
            echo -e "   Size: $file_size bytes"
            echo -e "   SHA256: $checksum"
            
            # Copy to output directory
            local output_dir="../build_output"
            mkdir -p "$output_dir"
            
            local version="1.0.0"  # Get from source code or environment
            local timestamp=$(date +%Y%m%d_%H%M%S)
            local output_file="${output_dir}/${project_name}_v${version}_${timestamp}.bin"
            
            cp "$firmware_file" "$output_file"
            
            # Create metadata file
            cat > "${output_file}.json" << EOF
{
  "filename": "$(basename "$output_file")",
  "version": "$version",
  "device_type": "Smart Light",
  "description": "Home automation smart light firmware",
  "checksum": "$checksum",
  "build_time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "file_size": $file_size,
  "project": "$project_name"
}
EOF
            
            echo -e "${GREEN}✅ Firmware saved to: $output_file${NC}"
        else
            echo -e "${RED}❌ Firmware file not found${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ Build failed for ${project_name}${NC}"
        return 1
    fi
    
    cd - > /dev/null
}

# Upload firmware to OTA service
upload_firmware() {
    local firmware_file=$1
    local metadata_file="${firmware_file}.json"
    
    if [ ! -f "$firmware_file" ] || [ ! -f "$metadata_file" ]; then
        echo -e "${RED}❌ Firmware or metadata file not found${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}📤 Uploading firmware to OTA service...${NC}"
    
    # Read metadata
    local version=$(jq -r '.version' "$metadata_file")
    local device_type=$(jq -r '.device_type' "$metadata_file")
    local description=$(jq -r '.description' "$metadata_file")
    
    # Get admin token (in real implementation, this would be automated)
    echo -e "${YELLOW}ℹ️ Manual upload required${NC}"
    echo -e "   1. Go to http://localhost:3000/admin"
    echo -e "   2. Navigate to Firmware tab"
    echo -e "   3. Upload the firmware file:"
    echo -e "      File: $firmware_file"
    echo -e "      Version: $version"
    echo -e "      Device Type: $device_type"
    echo -e "      Description: $description"
}

# Main function
main() {
    echo -e "${YELLOW}📋 Checking dependencies...${NC}"
    check_platformio
    
    case "${1:-build}" in
        "build")
            echo -e "${YELLOW}🏗️ Building all firmware projects...${NC}"
            
            # Build all projects
            for project_dir in esp32-*/; do
                if [ -d "$project_dir" ] && [ -f "$project_dir/platformio.ini" ]; then
                    build_firmware "$project_dir"
                    echo ""
                fi
            done
            
            echo -e "${GREEN}🎉 Build process complete!${NC}"
            
            # List built firmware
            if [ -d "build_output" ] && [ "$(ls -A build_output 2>/dev/null)" ]; then
                echo -e "${GREEN}📦 Built Firmware:${NC}"
                ls -la build_output/*.bin
            fi
            ;;
            
        "upload")
            if [ -z "$2" ]; then
                echo -e "${RED}❌ Usage: $0 upload <firmware_file>${NC}"
                exit 1
            fi
            upload_firmware "$2"
            ;;
            
        "clean")
            echo -e "${YELLOW}🧹 Cleaning build output...${NC}"
            rm -rf build_output
            
            for project_dir in esp32-*/; do
                if [ -d "$project_dir" ]; then
                    cd "$project_dir"
                    pio run --target clean 2>/dev/null
                    cd - > /dev/null
                fi
            done
            
            echo -e "${GREEN}✅ Clean complete${NC}"
            ;;
            
        "flash")
            project_dir=${2:-"esp32-smart-light"}
            if [ ! -d "$project_dir" ]; then
                echo -e "${RED}❌ Project directory not found: $project_dir${NC}"
                exit 1
            fi
            
            echo -e "${YELLOW}📱 Flashing firmware to device...${NC}"
            cd "$project_dir"
            pio run --target upload
            cd - > /dev/null
            ;;
            
        "monitor")
            project_dir=${2:-"esp32-smart-light"}
            if [ ! -d "$project_dir" ]; then
                echo -e "${RED}❌ Project directory not found: $project_dir${NC}"
                exit 1
            fi
            
            echo -e "${YELLOW}📺 Starting serial monitor...${NC}"
            cd "$project_dir"
            pio device monitor
            cd - > /dev/null
            ;;
            
        *)
            echo -e "${YELLOW}Usage: $0 [command] [options]${NC}"
            echo -e "${YELLOW}Commands:${NC}"
            echo -e "  build          - Build all firmware projects (default)"
            echo -e "  upload <file>  - Upload firmware to OTA service"
            echo -e "  clean          - Clean build output"
            echo -e "  flash [proj]   - Flash firmware to connected device"
            echo -e "  monitor [proj] - Start serial monitor"
            exit 1
            ;;
    esac
}

# Check for required tools
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}⚠️ jq is not installed. Installing...${NC}"
    if command -v brew &> /dev/null; then
        brew install jq
    elif command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y jq
    else
        echo -e "${RED}❌ Please install jq manually${NC}"
        exit 1
    fi
fi

# Run main function
main "$@"