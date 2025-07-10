# Home Automation Firmware System

A comprehensive firmware management system for IoT devices supporting ESP32, ESP8266, Arduino, STM32, and Raspberry Pi Pico platforms with advanced OTA (Over-The-Air) update capabilities.

## Features

### 🔧 Multi-Platform Support
- **ESP32**: Smart lights, sensors, and actuators
- **ESP8266**: Smart switches and basic IoT devices
- **Arduino Uno**: Gateway and sensor hub devices
- **STM32**: Advanced sensor hubs and CAN gateways
- **Raspberry Pi Pico**: Multi-sensor nodes and PIO-based devices

### 🚀 Advanced OTA System
- **Single Device Updates**: Target specific devices for updates
- **Bulk Updates**: Update multiple devices simultaneously
- **Gradual Rollouts**: Staged deployment with percentage-based rollouts
- **Scheduled Updates**: Time-based deployment scheduling
- **Rollback Support**: Automatic and manual rollback capabilities

### 🛡️ Security & Safety
- **Firmware Signing**: Cryptographic verification of firmware integrity
- **Version Compatibility**: Automatic compatibility checking
- **Secure Boot**: Hardware-level security for supported platforms
- **Encrypted Updates**: End-to-end encryption during OTA updates
- **Backward Compatibility**: Seamless upgrades with compatibility checks

### 📊 Management & Monitoring
- **Web Dashboard**: Comprehensive firmware management interface
- **Build Pipeline**: Automated building and testing
- **Deployment Tracking**: Real-time update progress monitoring
- **Statistics**: Detailed analytics and reporting
- **Quality Gates**: Automated quality checks and validations

## Architecture

```
├── firmware/
│   ├── esp32-smart-light/          # ESP32 smart light firmware
│   ├── esp8266-switch/             # ESP8266 smart switch firmware
│   ├── arduino-uno-gateway/        # Arduino Uno gateway firmware
│   ├── stm32-sensor-hub/          # STM32 sensor hub firmware
│   ├── raspberry-pi-pico/         # Raspberry Pi Pico firmware
│   ├── build-pipeline.sh          # Automated build system
│   ├── build-config.json          # Build configuration
│   └── README.md                  # This file
├── backend/
│   └── ota-service/               # OTA service backend
│       ├── main_enhanced.py       # Enhanced OTA service
│       ├── firmware_manager.py    # Firmware management logic
│       ├── models.py              # Data models
│       └── schemas.py             # API schemas
└── frontend/
    └── src/components/
        └── FirmwareManagement.js  # Web interface
```

## Quick Start

### Prerequisites

1. **PlatformIO**: Install PlatformIO Core
   ```bash
   pip install platformio
   ```

2. **Dependencies**: Install required tools
   ```bash
   # macOS
   brew install jq
   
   # Ubuntu/Debian
   sudo apt-get install jq
   ```

3. **Python 3.8+**: Required for the build pipeline

### Building Firmware

1. **Build All Platforms**:
   ```bash
   ./build-pipeline.sh build
   ```

2. **Build Specific Platform**:
   ```bash
   cd esp32-smart-light
   pio run
   ```

3. **Clean Build Artifacts**:
   ```bash
   ./build-pipeline.sh clean
   ```

### Deploying Firmware

1. **Upload to OTA Service**:
   ```bash
   export OTA_API_TOKEN="your-api-token"
   ./build-pipeline.sh upload
   ```

2. **Build and Deploy**:
   ```bash
   ./build-pipeline.sh build-and-upload
   ```

## Platform-Specific Information

### ESP32 (Smart Light)
- **Features**: WiFi, Bluetooth, PWM control, color management
- **Hardware**: LED control, relay, button input
- **Capabilities**: OTA updates, MQTT communication, web interface
- **Memory**: 4MB flash, 520KB RAM minimum

### ESP8266 (Smart Switch)
- **Features**: WiFi, relay control, button input
- **Hardware**: Relay, status LED, physical button
- **Capabilities**: OTA updates, MQTT communication, web interface
- **Memory**: 1MB flash, 80KB RAM minimum

### Arduino Uno (Gateway)
- **Features**: Ethernet connectivity, sensor integration
- **Hardware**: Ethernet shield, DHT sensor, relay control
- **Capabilities**: MQTT gateway, sensor data collection
- **Memory**: 32KB flash, 2KB RAM

### STM32 (Sensor Hub)
- **Features**: Multiple sensor interfaces, CAN bus
- **Hardware**: I2C/SPI sensors, CAN transceiver, USB
- **Capabilities**: High-performance sensor processing
- **Memory**: 512KB flash, 128KB RAM minimum

### Raspberry Pi Pico (Multi-Sensor)
- **Features**: WiFi, Bluetooth, PIO programming
- **Hardware**: Multiple sensors, actuators, custom protocols
- **Capabilities**: Advanced sensor fusion, custom interfaces
- **Memory**: 2MB flash, 264KB RAM

## Firmware Versioning

### Version Format
- **Standard**: `MAJOR.MINOR.PATCH` (e.g., `1.2.3`)
- **With Build**: `MAJOR.MINOR.PATCH.BUILD` (e.g., `1.2.3.456`)

### Version Compatibility
- **Backward Compatible**: Minor and patch updates
- **Breaking Changes**: Major version updates
- **Build Updates**: Bug fixes and optimizations

### Update Policies
- **Automatic**: Patch updates (e.g., `1.2.3` → `1.2.4`)
- **Manual**: Minor updates (e.g., `1.2.x` → `1.3.0`)
- **Supervised**: Major updates (e.g., `1.x.x` → `2.0.0`)

## OTA Update Process

### 1. Compatibility Check
```javascript
// Check device compatibility
const compatibility = await checkCompatibility(deviceId, firmwareId);
if (!compatibility.compatible) {
    console.log('Incompatible firmware:', compatibility.issues);
    return;
}
```

### 2. Update Initiation
```javascript
// Start single device update
await updateDevice(deviceId, firmwareId);

// Start bulk update
await bulkUpdateDevices({
    device_ids: deviceIds,
    firmware_id: firmwareId,
    strategy: 'gradual',
    max_concurrent_updates: 5
});
```

### 3. Progress Monitoring
```javascript
// Monitor update progress
const status = await getUpdateStatus(deviceId);
console.log(`Progress: ${status.progress}%`);
console.log(`Status: ${status.status}`);
```

## Security Features

### Firmware Signing
- **Digital Signatures**: RSA-2048 or ECDSA-256
- **Certificate Chain**: Hierarchical trust model
- **Verification**: Device-level signature checking

### Secure Boot
- **Hardware Root of Trust**: Immutable bootloader
- **Verified Boot**: Cryptographic chain of trust
- **Rollback Protection**: Anti-rollback version checking

### Encrypted Updates
- **TLS/SSL**: End-to-end encryption during download
- **AES Encryption**: Firmware payload encryption
- **Key Management**: Secure key distribution

## Quality Assurance

### Build Quality Gates
- **Size Limits**: Maximum firmware size per platform
- **Memory Requirements**: Minimum free heap validation
- **Code Coverage**: Unit test coverage threshold
- **Static Analysis**: Code quality checks

### Testing Pipeline
- **Unit Tests**: Component-level testing
- **Integration Tests**: System-level validation
- **Hardware-in-Loop**: Real device testing
- **Regression Tests**: Backward compatibility validation

## Configuration

### Build Configuration (`build-config.json`)
```json
{
    "version": "1.0.0",
    "build_number": 1,
    "environments": ["esp32", "esp8266", "arduino", "stm32", "pico"],
    "optimization": "release",
    "debug": false,
    "security": {
        "enable_secure_boot": true,
        "enable_encryption": true,
        "code_signing": true
    }
}
```

### Platform Configuration
Each platform has specific configuration in `build-config.json`:
- **Device Type**: Hardware platform identifier
- **Board Model**: Specific board variant
- **Capabilities**: Supported features
- **Memory Requirements**: Flash and RAM minimums

## API Reference

### Firmware Management API

#### Upload Firmware
```http
POST /api/firmware/upload
Content-Type: multipart/form-data

{
    "firmware_file": <binary>,
    "device_type": "ESP32",
    "board_model": "ESP32-WROOM-32",
    "version": "1.0.0",
    "status": "development",
    "description": "Smart light firmware",
    "changelog": "Initial release"
}
```

#### Create Rollout
```http
POST /api/rollouts
Content-Type: application/json

{
    "firmware_id": "fw-12345",
    "name": "ESP32 Smart Light v1.1",
    "strategy": "gradual",
    "target_device_types": ["ESP32"],
    "gradual_percentage": 10,
    "max_concurrent_updates": 5
}
```

#### Update Single Device
```http
POST /api/devices/{device_id}/update
Content-Type: application/json

{
    "firmware_id": "fw-12345",
    "force_update": false
}
```

### Device API (MQTT)

#### OTA Command Topic
```
homeautomation/devices/{device_id}/ota
```

#### OTA Command Message
```json
{
    "action": "update",
    "firmware_id": "fw-12345",
    "url": "https://ota.example.com/firmware/fw-12345.bin",
    "version": "1.1.0",
    "checksum": "sha256:abc123...",
    "size": 1048576
}
```

#### Status Response Topic
```
homeautomation/devices/{device_id}/status
```

#### Status Response Message
```json
{
    "device_id": "device-001",
    "status": "updating",
    "progress": 45,
    "current_version": "1.0.0",
    "target_version": "1.1.0",
    "error_message": null
}
```

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check PlatformIO installation
   - Verify platform tools are installed
   - Review build logs in `logs/build.log`

2. **OTA Update Failures**
   - Verify device connectivity
   - Check firmware compatibility
   - Validate firmware checksums

3. **Device Not Responding**
   - Check MQTT connection
   - Verify device is online
   - Review device logs

### Debug Mode
Enable debug mode in `build-config.json`:
```json
{
    "debug": true,
    "optimization": "debug"
}
```

### Log Analysis
```bash
# Build logs
tail -f logs/build.log

# OTA service logs
tail -f ../backend/ota-service/ota-service.log

# Device logs (via serial)
pio device monitor
```

## Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/new-platform`
3. **Add firmware template** in new directory
4. **Update build configuration**
5. **Test thoroughly**
6. **Submit pull request**

### Adding New Platform

1. Create platform directory: `mkdir new-platform`
2. Add `platformio.ini` configuration
3. Implement `main.cpp` with OTA support
4. Update `build-config.json`
5. Add platform to build pipeline
6. Create documentation

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Support

For support and questions:
- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: Comprehensive guides and API reference
- **Community**: Join our developer community

## Changelog

### v1.0.0
- Initial release with multi-platform support
- OTA update system with rollout management
- Security features and quality gates
- Web-based firmware management interface

### v1.1.0 (Planned)
- Hardware-in-loop testing
- Advanced rollback strategies
- Performance optimizations
- Extended platform support