# Factory Provisioning System

A comprehensive system for mass provisioning and flashing of IoT devices in factory environments. This system automates the process of firmware flashing, device testing, registration, and quality control for multiple device types.

## Features

- **Multi-Platform Support**: ESP32, ESP8266, Arduino, STM32, Raspberry Pi Pico
- **Parallel Processing**: Multiple flashing stations working simultaneously
- **Automated Testing**: Built-in device testing after flashing
- **Quality Gates**: Automated quality control and validation
- **Device Registration**: Automatic device registration with backend services
- **QR Code Generation**: Automatic QR code generation for device provisioning
- **Batch Management**: Batch tracking and reporting
- **Error Handling**: Comprehensive error handling and retry logic

## Architecture

```
Factory Provisioning System
├── factory-flash.py          # Main provisioning system
├── factory-config.yaml       # Configuration file
├── test-flash.py             # Test suite
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Quick Start

### Prerequisites

1. **Python 3.8+**
2. **PlatformIO** (for esptool)
3. **Required Python packages**:
   ```bash
   pip install -r requirements.txt
   ```

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd firmware/factory-provisioning
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the system**:
   - Edit `factory-config.yaml` to match your setup
   - Update USB port mappings
   - Configure firmware paths
   - Set service URLs

### Basic Usage

1. **Test Mode** (detect devices without flashing):
   ```bash
   python factory-flash.py --test-mode
   ```

2. **Flash Single Station**:
   ```bash
   python factory-flash.py --station station_1 --batch-size 10
   ```

3. **Flash All Stations**:
   ```bash
   python factory-flash.py --batch-size 50
   ```

4. **Custom Configuration**:
   ```bash
   python factory-flash.py --config custom-config.yaml
   ```

## Configuration

### Main Configuration (`factory-config.yaml`)

```yaml
# Service URLs
provisioning_service_url: "http://localhost:3002"
ota_service_url: "http://localhost:3004"

# Flashing Stations
stations:
  - station_id: "station_1"
    ports:
      - "/dev/ttyUSB0"
      - "/dev/ttyUSB1"
    board_type: "esp32"

# Board Configurations
board_configs:
  esp32:
    platform: "esp32"
    board_model: "ESP32-WROOM-32"
    flash_size: "4MB"
    firmware_path: "../dist/esp32/firmware-latest.bin"
    bootloader_path: "../dist/esp32/bootloader.bin"
    partition_table_path: "../dist/esp32/partitions.bin"
```

### Station Setup

Each station represents a physical workstation with multiple USB ports:

1. **Connect devices** to USB ports
2. **Configure port mapping** in `factory-config.yaml`
3. **Set board type** for each station
4. **Update firmware paths** to match your build output

### Quality Gates

Configure quality gates to ensure device quality:

```yaml
quality_gates:
  max_firmware_size:
    esp32: 3145728      # 3MB
    esp8266: 1048576    # 1MB
  max_flash_time: 120   # seconds
  max_retry_attempts: 3
```

## Workflow

### 1. Device Detection
- System scans all configured ports
- Detects connected devices
- Extracts MAC addresses
- Validates device compatibility

### 2. Firmware Flashing
- Flashes bootloader (if required)
- Flashes partition table (if required)
- Flashes main firmware
- Verifies flash success

### 3. Device Testing
- Boots the device
- Runs automated tests
- Validates functionality
- Records test results

### 4. Device Registration
- Generates unique device IDs
- Registers with provisioning service
- Creates QR codes for pairing
- Updates device database

### 5. Quality Control
- Validates firmware size
- Checks test results
- Marks devices as pass/fail
- Generates batch reports

## Testing

### Built-in Tests

The system includes automated tests for:
- **Boot Test**: Verifies device boots correctly
- **WiFi Test**: Tests WiFi functionality
- **Memory Test**: Validates memory allocation
- **Sensor Test**: Tests sensor connectivity

### Running Tests

```bash
# Run all tests
python test-flash.py

# Run specific test
python test-flash.py --test detection

# Verbose output
python test-flash.py --verbose
```

### Test Configuration

Configure tests in `factory-config.yaml`:

```yaml
testing:
  enabled: true
  tests:
    - name: "boot_test"
      command: "info"
      expected_response: "OK"
      timeout: 5
```

## Output and Logging

### Log Files
- `factory-provisioning.log`: Main log file
- `factory_records_YYYYMMDD.csv`: Device records
- `batch_report_YYYYMMDD_HHMMSS.json`: Batch reports

### CSV Records
Each device record includes:
- Device ID and MAC address
- Board type and firmware version
- Flash time and station ID
- Test results and QR code

### Batch Reports
JSON reports containing:
- Total devices processed
- Success/failure counts
- Station statistics
- Performance metrics

## Advanced Features

### Parallel Processing
Multiple stations can operate simultaneously:
```python
# Automatic load balancing
factory.run_batch_processing(batch_size=100)
```

### Error Handling
Comprehensive error handling with retry logic:
```python
# Automatic retries on flash failures
max_retry_attempts: 3
```

### QR Code Generation
Automatic QR code generation for device pairing:
```python
# QR code includes device credentials
qr_code = factory.generate_qr_code(device_record)
```

## Integration

### Backend Services
The system integrates with:
- **Device Service**: Device registration and management
- **OTA Service**: Firmware management and updates
- **Provisioning Service**: Device provisioning and pairing

### API Endpoints
- `POST /api/admin/device-registrations`: Register new devices
- `GET /api/admin/provisioning/batches`: Get batch information
- `POST /api/admin/provisioning/bulk`: Bulk device provisioning

## Troubleshooting

### Common Issues

1. **Device Not Detected**
   - Check USB connections
   - Verify port permissions
   - Ensure correct drivers installed

2. **Flash Failures**
   - Check firmware file paths
   - Verify board type configuration
   - Ensure sufficient power supply

3. **Test Failures**
   - Check test configuration
   - Verify device boot sequence
   - Review test timeouts

### Debug Mode
Enable debug logging:
```yaml
logging:
  level: "DEBUG"
  console_output: true
```

### Port Permissions
On Linux, ensure port permissions:
```bash
sudo usermod -a -G dialout $USER
sudo chmod 666 /dev/ttyUSB*
```

## Performance Optimization

### Batch Size Optimization
- Adjust batch size based on station capacity
- Consider firmware size and flash time
- Monitor system resources

### Concurrent Processing
- Configure max concurrent stations
- Balance load across stations
- Monitor USB bandwidth

### Quality Gates
- Set appropriate firmware size limits
- Configure realistic test timeouts
- Optimize retry strategies

## Security Considerations

- **Device Secrets**: Securely generated per device
- **Provisioning Tokens**: One-time use tokens
- **QR Code Security**: Cryptographic device credentials
- **Network Security**: Secure communication with backend

## Maintenance

### Log Rotation
Configure log rotation to prevent disk space issues:
```yaml
logging:
  max_file_size: 10485760  # 10MB
  backup_count: 5
```

### Database Cleanup
Regular cleanup of old records:
- Archive old batch reports
- Clean up device records
- Monitor disk usage

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions:
- Check the troubleshooting section
- Review log files
- Contact the development team