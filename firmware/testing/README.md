# Firmware Testing and Validation Framework

A comprehensive testing framework for IoT firmware validation, supporting multiple platforms and test types including hardware-in-loop testing, network testing, and automated validation.

## Features

- **Multi-Platform Support**: ESP32, ESP8266, Arduino, STM32, Raspberry Pi Pico
- **Hardware-in-Loop Testing**: Direct device communication and testing
- **Network Testing**: WiFi, MQTT, HTTP, WebSocket validation
- **Automated Test Execution**: Parallel test execution with retry logic
- **Comprehensive Reporting**: JSON, HTML, and console reports
- **Test Suite Management**: YAML-based test suite definitions
- **Quality Gates**: Configurable pass/fail criteria
- **CI/CD Integration**: Easy integration with build pipelines

## Architecture

```
Testing Framework
├── test-framework.py         # Main testing framework
├── test-config.yaml          # Configuration file
├── run-tests.py             # Simple test runner
├── test_suites/             # Test suite definitions
│   ├── esp32_smoke_tests.yaml
│   ├── esp32_functional_tests.yaml
│   └── esp8266_smoke_tests.yaml
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Quick Start

### Prerequisites

1. **Python 3.8+**
2. **Hardware Setup**: Connect target devices to USB ports
3. **Required Tools**: esptool, platformio (for flashing)
4. **Network Setup**: Configure test network for network tests

### Installation

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure hardware**:
   - Connect devices to USB ports
   - Update `test-config.yaml` with correct port mappings
   - Ensure proper drivers are installed

3. **Configure network**:
   - Set up test WiFi network
   - Configure MQTT broker for testing
   - Update network settings in configuration

### Basic Usage

1. **Run smoke tests**:
   ```bash
   python run-tests.py --test-type smoke --platform esp32
   ```

2. **Run functional tests**:
   ```bash
   python run-tests.py --test-type functional --platform esp32
   ```

3. **Run all tests**:
   ```bash
   python run-tests.py --test-type all
   ```

4. **List available test suites**:
   ```bash
   python run-tests.py --list
   ```

5. **Run specific test suite**:
   ```bash
   python run-tests.py --suite esp32_smoke_tests
   ```

## Configuration

### Main Configuration (`test-config.yaml`)

```yaml
# Hardware interfaces
hardware_interfaces:
  esp32:
    port: "/dev/ttyUSB0"
    baudrate: 115200
    
# Network interfaces
network_interfaces:
  esp32:
    host: "192.168.1.100"
    port: 80
    
# Test execution settings
execution:
  parallel_execution: true
  max_parallel_tests: 4
  default_timeout: 30
```

### Test Suite Definition

Test suites are defined in YAML format:

```yaml
name: "esp32_smoke_tests"
description: "Quick smoke tests for ESP32"
platform: "esp32"

test_cases:
  - name: "boot_test"
    description: "Test device boot"
    test_type: "hardware"
    timeout: 15
    parameters:
      command: "info"
      expected_response: "ESP32"
```

## Test Types

### Hardware-in-Loop Tests

Direct communication with hardware devices:

```yaml
- name: "gpio_test"
  test_type: "hardware"
  parameters:
    command: "gpio_test"
    pin: 2
    mode: "output"
    value: 1
```

### Network Tests

Network-based testing:

```yaml
- name: "mqtt_test"
  test_type: "network"
  parameters:
    test_type: "mqtt"
    topic: "test/topic"
    message: "test message"
```

### Integration Tests

End-to-end system tests:

```yaml
- name: "ota_update_test"
  test_type: "integration"
  parameters:
    firmware_url: "http://server.com/firmware.bin"
    timeout: 120
```

## Test Categories

### Smoke Tests
- Quick validation (< 5 minutes)
- Basic functionality
- Boot and communication tests
- Must pass for basic operation

### Functional Tests
- Comprehensive feature testing
- All device capabilities
- Network connectivity
- Sensor/actuator validation

### Integration Tests
- End-to-end scenarios
- OTA updates
- Cloud connectivity
- Multi-device coordination

### Performance Tests
- Timing validation
- Memory usage
- Power consumption
- Stress testing

## Hardware Setup

### ESP32 Setup

1. **Connection**:
   - USB-to-serial adapter
   - GPIO connections for testing
   - Power supply

2. **Firmware Requirements**:
   - Test command interface
   - Serial communication
   - Response formatting

### Network Setup

1. **WiFi Network**:
   - Test SSID: "TestNetwork"
   - Password: "TestPassword"
   - Isolated from production

2. **MQTT Broker**:
   - Test broker setup
   - Topic permissions
   - Message retention

## Test Development

### Creating Test Suites

1. **Create YAML file** in `test_suites/` directory:
   ```yaml
   name: "my_test_suite"
   description: "Custom test suite"
   platform: "esp32"
   test_cases:
     - name: "custom_test"
       description: "My custom test"
       test_type: "hardware"
       timeout: 10
       parameters:
         command: "custom_command"
   ```

2. **Test Framework Integration**:
   - Framework automatically loads YAML files
   - Validates test suite structure
   - Executes tests in order

### Test Commands

Hardware tests use serial commands:

```
info                 # Device information
memory_info          # Memory status
gpio_test <pin>      # GPIO testing
wifi_scan           # WiFi scan
wifi_connect <ssid> <pass>  # WiFi connection
sensor_test         # Sensor reading
actuator_test       # Actuator control
```

## Reporting

### Console Output

Real-time test execution status:
```
Running test: boot_test
✓ boot_test passed (2.34s)
Running test: memory_test
✓ memory_test passed (1.12s)

TEST SUMMARY
============
Total Tests: 10
Passed: 9
Failed: 1
Success Rate: 90%
```

### JSON Reports

Detailed test results:
```json
{
  "timestamp": "2024-01-01T12:00:00",
  "total_tests": 10,
  "summary": {
    "passed": 9,
    "failed": 1,
    "skipped": 0,
    "errors": 0
  },
  "suites": {
    "esp32_smoke_tests": {
      "total_tests": 10,
      "passed": 9,
      "failed": 1,
      "tests": [...]
    }
  }
}
```

### HTML Reports

Visual test reports with:
- Test execution timeline
- Pass/fail statistics
- Error details
- Performance metrics

## CI/CD Integration

### GitHub Actions

```yaml
name: Firmware Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r firmware/testing/requirements.txt
      - name: Run smoke tests
        run: python firmware/testing/run-tests.py --test-type smoke
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    stages {
        stage('Test') {
            steps {
                sh 'pip install -r firmware/testing/requirements.txt'
                sh 'python firmware/testing/run-tests.py --test-type smoke'
            }
        }
    }
    post {
        always {
            archiveArtifacts artifacts: 'test_report_*.json'
        }
    }
}
```

## Quality Gates

### Pass Criteria

- Minimum 80% test pass rate
- All critical tests must pass
- Performance within thresholds
- No security vulnerabilities

### Configuration

```yaml
quality_gates:
  min_success_rate: 80
  critical_tests:
    - "boot_test"
    - "memory_test"
    - "safety_test"
  performance_thresholds:
    boot_time: 5.0
    min_free_heap: 50000
```

## Troubleshooting

### Common Issues

1. **Device Not Detected**:
   - Check USB connection
   - Verify port permissions
   - Ensure correct drivers

2. **Test Timeouts**:
   - Increase timeout values
   - Check device responsiveness
   - Verify command format

3. **Network Tests Fail**:
   - Check WiFi credentials
   - Verify network connectivity
   - Confirm MQTT broker status

### Debug Mode

Enable verbose logging:
```bash
python run-tests.py --verbose --test-type smoke
```

### Hardware Debug

Check device communication:
```bash
# Manual device communication
python -c "
import serial
ser = serial.Serial('/dev/ttyUSB0', 115200)
ser.write(b'info\\n')
print(ser.read(100))
"
```

## Performance Optimization

### Parallel Execution

Configure parallel test execution:
```yaml
execution:
  parallel_execution: true
  max_parallel_tests: 4
```

### Test Filtering

Run specific test categories:
```bash
python run-tests.py --platform esp32 --test-type smoke
```

### Hardware Optimization

- Use dedicated test hardware
- Optimize serial communication
- Implement hardware multiplexing

## Security Testing

### Vulnerability Scanning

Built-in security checks:
- Hardcoded credentials
- Insecure communications
- Buffer overflow tests
- Encryption validation

### Configuration

```yaml
security_validation:
  check_vulnerabilities: true
  scan_for_secrets: true
  validate_certificates: true
```

## Extending the Framework

### Custom Test Types

Add new test types:
```python
def run_custom_test(self, test_case):
    # Custom test logic
    return TestResult.PASS, "Custom test passed"
```

### New Platforms

Add platform support:
1. Update configuration templates
2. Add platform-specific commands
3. Create test suites
4. Update documentation

### Custom Interfaces

Implement new communication interfaces:
```python
class CustomInterface:
    def __init__(self, config):
        self.config = config
    
    def send_command(self, command):
        # Custom communication logic
        pass
```

## Best Practices

### Test Design

- Keep tests atomic and independent
- Use descriptive test names
- Include proper error handling
- Document expected behavior

### Test Maintenance

- Regular test review and updates
- Version control for test suites
- Test result archival
- Performance monitoring

### Hardware Management

- Dedicated test hardware
- Regular hardware validation
- Automated setup scripts
- Hardware health monitoring

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
- Check troubleshooting section
- Review test logs
- Contact development team