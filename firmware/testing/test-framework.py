#!/usr/bin/env python3
"""
Firmware Testing and Validation Framework
Comprehensive testing system for IoT firmware validation
"""

import os
import sys
import json
import yaml
import time
import serial
import socket
import subprocess
import threading
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import requests
import hashlib
import tempfile
import shutil

class TestResult(Enum):
    """Test result enumeration"""
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    ERROR = "ERROR"

@dataclass
class TestCase:
    """Individual test case"""
    name: str
    description: str
    test_type: str  # unit, integration, hardware, performance
    platform: str
    timeout: int = 30
    retry_count: int = 3
    dependencies: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    expected_result: Any = None
    
@dataclass
class TestExecution:
    """Test execution result"""
    test_case: TestCase
    result: TestResult
    execution_time: float
    output: str
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    
@dataclass
class TestSuite:
    """Collection of test cases"""
    name: str
    description: str
    platform: str
    test_cases: List[TestCase] = field(default_factory=list)
    setup_commands: List[str] = field(default_factory=list)
    teardown_commands: List[str] = field(default_factory=list)
    
class HardwareTestInterface:
    """Interface for hardware-in-loop testing"""
    
    def __init__(self, port: str, baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        self.connection = None
        self.logger = logging.getLogger(__name__)
        
    def connect(self) -> bool:
        """Connect to hardware device"""
        try:
            self.connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=10
            )
            time.sleep(2)  # Wait for device to initialize
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to {self.port}: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from hardware device"""
        if self.connection and self.connection.is_open:
            self.connection.close()
    
    def send_command(self, command: str, timeout: int = 5) -> str:
        """Send command to device and get response"""
        if not self.connection or not self.connection.is_open:
            raise RuntimeError("Not connected to device")
        
        try:
            # Send command
            self.connection.write(f"{command}\\n".encode())
            
            # Read response
            start_time = time.time()
            response = ""
            
            while time.time() - start_time < timeout:
                if self.connection.in_waiting > 0:
                    data = self.connection.read(self.connection.in_waiting)
                    response += data.decode('utf-8', errors='ignore')
                    
                    # Check for command completion
                    if "OK" in response or "ERROR" in response:
                        break
                
                time.sleep(0.1)
            
            return response.strip()
            
        except Exception as e:
            self.logger.error(f"Error sending command '{command}': {e}")
            raise
    
    def flash_firmware(self, firmware_path: str, platform: str) -> bool:
        """Flash firmware to device"""
        try:
            if platform == "esp32":
                cmd = [
                    "python", "-m", "esptool",
                    "--chip", "esp32",
                    "--port", self.port,
                    "--baud", "921600",
                    "--before", "default_reset",
                    "--after", "hard_reset",
                    "write_flash",
                    "--flash_mode", "dio",
                    "--flash_freq", "80m",
                    "--flash_size", "4MB",
                    "0x10000", firmware_path
                ]
            elif platform == "esp8266":
                cmd = [
                    "python", "-m", "esptool",
                    "--chip", "esp8266",
                    "--port", self.port,
                    "--baud", "460800",
                    "write_flash",
                    "--flash_size", "4MB",
                    "0x0", firmware_path
                ]
            else:
                raise ValueError(f"Unsupported platform: {platform}")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            self.logger.error(f"Error flashing firmware: {e}")
            return False

class NetworkTestInterface:
    """Interface for network-based testing"""
    
    def __init__(self, host: str, port: int = 80):
        self.host = host
        self.port = port
        self.logger = logging.getLogger(__name__)
    
    def test_connectivity(self, timeout: int = 5) -> bool:
        """Test basic network connectivity"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            return result == 0
        except Exception as e:
            self.logger.error(f"Network connectivity test failed: {e}")
            return False
    
    def test_http_endpoint(self, endpoint: str, method: str = "GET", 
                          timeout: int = 10) -> Tuple[bool, str]:
        """Test HTTP endpoint"""
        try:
            url = f"http://{self.host}:{self.port}{endpoint}"
            response = requests.request(method, url, timeout=timeout)
            return response.status_code == 200, response.text
        except Exception as e:
            self.logger.error(f"HTTP endpoint test failed: {e}")
            return False, str(e)
    
    def test_mqtt_connection(self, topic: str, message: str, 
                           timeout: int = 10) -> bool:
        """Test MQTT functionality"""
        try:
            import paho.mqtt.client as mqtt
            
            result = {"success": False}
            
            def on_connect(client, userdata, flags, rc):
                if rc == 0:
                    client.publish(topic, message)
                
            def on_publish(client, userdata, mid):
                result["success"] = True
                client.disconnect()
            
            client = mqtt.Client()
            client.on_connect = on_connect
            client.on_publish = on_publish
            
            client.connect(self.host, 1883, timeout)
            client.loop_start()
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                if result["success"]:
                    break
                time.sleep(0.1)
            
            client.loop_stop()
            client.disconnect()
            
            return result["success"]
            
        except Exception as e:
            self.logger.error(f"MQTT test failed: {e}")
            return False

class TestRunner:
    """Main test runner"""
    
    def __init__(self, config_file: str = "test-config.yaml"):
        self.config = self.load_config(config_file)
        self.test_suites: Dict[str, TestSuite] = {}
        self.hardware_interfaces: Dict[str, HardwareTestInterface] = {}
        self.network_interfaces: Dict[str, NetworkTestInterface] = {}
        self.results: List[TestExecution] = []
        
        # Setup logging
        self.setup_logging()
        
        # Load test suites
        self.load_test_suites()
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('test-framework.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_config(self, config_file: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
                self.logger.info(f"Configuration loaded from {config_file}")
                return config
        except FileNotFoundError:
            self.logger.warning(f"Config file {config_file} not found, using defaults")
            return self.get_default_config()
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            "platforms": ["esp32", "esp8266", "arduino", "stm32", "pico"],
            "test_suites_dir": "test_suites",
            "hardware_interfaces": {
                "esp32": {
                    "port": "/dev/ttyUSB0",
                    "baudrate": 115200
                }
            },
            "network_interfaces": {
                "esp32": {
                    "host": "192.168.1.100",
                    "port": 80
                }
            },
            "timeouts": {
                "default": 30,
                "flash": 120,
                "network": 10
            },
            "parallel_execution": True,
            "max_parallel_tests": 4
        }
    
    def load_test_suites(self):
        """Load test suites from configuration"""
        suites_dir = self.config.get("test_suites_dir", "test_suites")
        
        if not os.path.exists(suites_dir):
            self.logger.info(f"Test suites directory {suites_dir} not found, creating default suites")
            self.create_default_test_suites()
            return
        
        # Load test suites from files
        for filename in os.listdir(suites_dir):
            if filename.endswith('.yaml') or filename.endswith('.yml'):
                suite_path = os.path.join(suites_dir, filename)
                try:
                    with open(suite_path, 'r') as f:
                        suite_data = yaml.safe_load(f)
                        suite = self.create_test_suite_from_dict(suite_data)
                        self.test_suites[suite.name] = suite
                        self.logger.info(f"Loaded test suite: {suite.name}")
                except Exception as e:
                    self.logger.error(f"Error loading test suite {filename}: {e}")
    
    def create_test_suite_from_dict(self, data: Dict) -> TestSuite:
        """Create test suite from dictionary"""
        suite = TestSuite(
            name=data["name"],
            description=data.get("description", ""),
            platform=data["platform"],
            setup_commands=data.get("setup_commands", []),
            teardown_commands=data.get("teardown_commands", [])
        )
        
        for test_data in data.get("test_cases", []):
            test_case = TestCase(
                name=test_data["name"],
                description=test_data.get("description", ""),
                test_type=test_data.get("test_type", "unit"),
                platform=test_data["platform"],
                timeout=test_data.get("timeout", 30),
                retry_count=test_data.get("retry_count", 3),
                dependencies=test_data.get("dependencies", []),
                parameters=test_data.get("parameters", {}),
                expected_result=test_data.get("expected_result")
            )
            suite.test_cases.append(test_case)
        
        return suite
    
    def create_default_test_suites(self):
        """Create default test suites"""
        # ESP32 Test Suite
        esp32_suite = TestSuite(
            name="esp32_validation",
            description="ESP32 firmware validation tests",
            platform="esp32",
            setup_commands=["reset", "boot"]
        )
        
        # Basic functionality tests
        esp32_suite.test_cases.extend([
            TestCase(
                name="boot_test",
                description="Test device boot sequence",
                test_type="hardware",
                platform="esp32",
                timeout=15,
                parameters={"command": "info", "expected_response": "ESP32"}
            ),
            TestCase(
                name="memory_test",
                description="Test memory allocation",
                test_type="hardware",
                platform="esp32",
                timeout=10,
                parameters={"command": "memory_info", "min_free_heap": 100000}
            ),
            TestCase(
                name="wifi_scan_test",
                description="Test WiFi scanning capability",
                test_type="hardware",
                platform="esp32",
                timeout=15,
                parameters={"command": "wifi_scan", "min_networks": 1}
            ),
            TestCase(
                name="gpio_test",
                description="Test GPIO functionality",
                test_type="hardware",
                platform="esp32",
                timeout=10,
                parameters={"command": "gpio_test", "pin": 2}
            )
        ])
        
        self.test_suites["esp32_validation"] = esp32_suite
        
        # ESP8266 Test Suite
        esp8266_suite = TestSuite(
            name="esp8266_validation",
            description="ESP8266 firmware validation tests",
            platform="esp8266"
        )
        
        esp8266_suite.test_cases.extend([
            TestCase(
                name="boot_test",
                description="Test device boot sequence",
                test_type="hardware",
                platform="esp8266",
                timeout=15,
                parameters={"command": "info", "expected_response": "ESP8266"}
            ),
            TestCase(
                name="wifi_connection_test",
                description="Test WiFi connection",
                test_type="hardware",
                platform="esp8266",
                timeout=20,
                parameters={"command": "wifi_connect", "ssid": "test_network"}
            )
        ])
        
        self.test_suites["esp8266_validation"] = esp8266_suite
    
    def run_test_case(self, test_case: TestCase) -> TestExecution:
        """Run a single test case"""
        self.logger.info(f"Running test: {test_case.name}")
        
        start_time = time.time()
        result = TestResult.FAIL
        output = ""
        error_message = None
        retry_count = 0
        
        for attempt in range(test_case.retry_count + 1):
            try:
                if test_case.test_type == "hardware":
                    result, output = self.run_hardware_test(test_case)
                elif test_case.test_type == "network":
                    result, output = self.run_network_test(test_case)
                elif test_case.test_type == "integration":
                    result, output = self.run_integration_test(test_case)
                elif test_case.test_type == "performance":
                    result, output = self.run_performance_test(test_case)
                else:
                    result, output = self.run_unit_test(test_case)
                
                if result == TestResult.PASS:
                    break
                
                retry_count = attempt + 1
                if attempt < test_case.retry_count:
                    self.logger.info(f"Test {test_case.name} failed, retrying ({attempt + 1}/{test_case.retry_count})")
                    time.sleep(1)
                
            except Exception as e:
                error_message = str(e)
                result = TestResult.ERROR
                self.logger.error(f"Test {test_case.name} error: {e}")
                break
        
        execution_time = time.time() - start_time
        
        execution = TestExecution(
            test_case=test_case,
            result=result,
            execution_time=execution_time,
            output=output,
            error_message=error_message,
            retry_count=retry_count
        )
        
        self.results.append(execution)
        
        self.logger.info(f"Test {test_case.name} completed: {result.value} (took {execution_time:.2f}s)")
        
        return execution
    
    def run_hardware_test(self, test_case: TestCase) -> Tuple[TestResult, str]:
        """Run hardware-in-loop test"""
        platform = test_case.platform
        
        if platform not in self.hardware_interfaces:
            # Create hardware interface
            hw_config = self.config.get("hardware_interfaces", {}).get(platform, {})
            port = hw_config.get("port", "/dev/ttyUSB0")
            baudrate = hw_config.get("baudrate", 115200)
            
            hw_interface = HardwareTestInterface(port, baudrate)
            if not hw_interface.connect():
                return TestResult.ERROR, f"Failed to connect to {port}"
            
            self.hardware_interfaces[platform] = hw_interface
        
        hw_interface = self.hardware_interfaces[platform]
        
        try:
            command = test_case.parameters.get("command", "")
            expected_response = test_case.parameters.get("expected_response", "")
            
            if not command:
                return TestResult.ERROR, "No command specified"
            
            response = hw_interface.send_command(command, test_case.timeout)
            
            if expected_response and expected_response in response:
                return TestResult.PASS, response
            elif "OK" in response:
                return TestResult.PASS, response
            else:
                return TestResult.FAIL, f"Unexpected response: {response}"
                
        except Exception as e:
            return TestResult.ERROR, str(e)
    
    def run_network_test(self, test_case: TestCase) -> Tuple[TestResult, str]:
        """Run network-based test"""
        platform = test_case.platform
        
        if platform not in self.network_interfaces:
            # Create network interface
            net_config = self.config.get("network_interfaces", {}).get(platform, {})
            host = net_config.get("host", "192.168.1.100")
            port = net_config.get("port", 80)
            
            net_interface = NetworkTestInterface(host, port)
            self.network_interfaces[platform] = net_interface
        
        net_interface = self.network_interfaces[platform]
        
        try:
            test_type = test_case.parameters.get("test_type", "connectivity")
            
            if test_type == "connectivity":
                success = net_interface.test_connectivity(test_case.timeout)
                return TestResult.PASS if success else TestResult.FAIL, "Network connectivity test"
            
            elif test_type == "http":
                endpoint = test_case.parameters.get("endpoint", "/")
                method = test_case.parameters.get("method", "GET")
                success, response = net_interface.test_http_endpoint(endpoint, method, test_case.timeout)
                return TestResult.PASS if success else TestResult.FAIL, response
            
            elif test_type == "mqtt":
                topic = test_case.parameters.get("topic", "test/topic")
                message = test_case.parameters.get("message", "test message")
                success = net_interface.test_mqtt_connection(topic, message, test_case.timeout)
                return TestResult.PASS if success else TestResult.FAIL, "MQTT test"
            
            else:
                return TestResult.ERROR, f"Unknown network test type: {test_type}"
                
        except Exception as e:
            return TestResult.ERROR, str(e)
    
    def run_integration_test(self, test_case: TestCase) -> Tuple[TestResult, str]:
        """Run integration test"""
        # Placeholder for integration tests
        return TestResult.SKIP, "Integration tests not implemented"
    
    def run_performance_test(self, test_case: TestCase) -> Tuple[TestResult, str]:
        """Run performance test"""
        # Placeholder for performance tests
        return TestResult.SKIP, "Performance tests not implemented"
    
    def run_unit_test(self, test_case: TestCase) -> Tuple[TestResult, str]:
        """Run unit test"""
        # Placeholder for unit tests
        return TestResult.SKIP, "Unit tests not implemented"
    
    def run_test_suite(self, suite_name: str) -> List[TestExecution]:
        """Run all tests in a test suite"""
        if suite_name not in self.test_suites:
            raise ValueError(f"Test suite {suite_name} not found")
        
        suite = self.test_suites[suite_name]
        self.logger.info(f"Running test suite: {suite_name}")
        
        # Run setup commands
        for command in suite.setup_commands:
            self.logger.info(f"Running setup command: {command}")
            # Execute setup command
        
        # Run test cases
        suite_results = []
        for test_case in suite.test_cases:
            execution = self.run_test_case(test_case)
            suite_results.append(execution)
        
        # Run teardown commands
        for command in suite.teardown_commands:
            self.logger.info(f"Running teardown command: {command}")
            # Execute teardown command
        
        return suite_results
    
    def run_all_tests(self) -> Dict[str, List[TestExecution]]:
        """Run all test suites"""
        all_results = {}
        
        for suite_name in self.test_suites:
            try:
                results = self.run_test_suite(suite_name)
                all_results[suite_name] = results
            except Exception as e:
                self.logger.error(f"Error running test suite {suite_name}: {e}")
        
        return all_results
    
    def generate_report(self, results: Dict[str, List[TestExecution]]) -> Dict:
        """Generate test report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_suites": len(results),
            "total_tests": sum(len(executions) for executions in results.values()),
            "suites": {},
            "summary": {
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "errors": 0
            }
        }
        
        for suite_name, executions in results.items():
            suite_report = {
                "name": suite_name,
                "total_tests": len(executions),
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "errors": 0,
                "execution_time": 0,
                "tests": []
            }
            
            for execution in executions:
                test_report = {
                    "name": execution.test_case.name,
                    "description": execution.test_case.description,
                    "result": execution.result.value,
                    "execution_time": execution.execution_time,
                    "retry_count": execution.retry_count,
                    "output": execution.output[:1000] if execution.output else "",  # Truncate output
                    "error_message": execution.error_message
                }
                
                suite_report["tests"].append(test_report)
                suite_report["execution_time"] += execution.execution_time
                
                if execution.result == TestResult.PASS:
                    suite_report["passed"] += 1
                    report["summary"]["passed"] += 1
                elif execution.result == TestResult.FAIL:
                    suite_report["failed"] += 1
                    report["summary"]["failed"] += 1
                elif execution.result == TestResult.SKIP:
                    suite_report["skipped"] += 1
                    report["summary"]["skipped"] += 1
                elif execution.result == TestResult.ERROR:
                    suite_report["errors"] += 1
                    report["summary"]["errors"] += 1
            
            report["suites"][suite_name] = suite_report
        
        return report
    
    def save_report(self, report: Dict, filename: str = None):
        """Save test report to file"""
        if filename is None:
            filename = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Test report saved to {filename}")
    
    def cleanup(self):
        """Cleanup resources"""
        # Disconnect hardware interfaces
        for hw_interface in self.hardware_interfaces.values():
            hw_interface.disconnect()
        
        self.hardware_interfaces.clear()
        self.network_interfaces.clear()

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Firmware Test Framework')
    parser.add_argument('--config', '-c', default='test-config.yaml', help='Configuration file')
    parser.add_argument('--suite', '-s', help='Run specific test suite')
    parser.add_argument('--platform', '-p', help='Filter tests by platform')
    parser.add_argument('--output', '-o', help='Output report file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Create test runner
    runner = TestRunner(args.config)
    
    try:
        if args.suite:
            # Run specific test suite
            results = {args.suite: runner.run_test_suite(args.suite)}
        else:
            # Run all test suites
            results = runner.run_all_tests()
        
        # Generate and save report
        report = runner.generate_report(results)
        runner.save_report(report, args.output)
        
        # Print summary
        print(f"\\nTest Summary:")
        print(f"Total Tests: {report['total_tests']}")
        print(f"Passed: {report['summary']['passed']}")
        print(f"Failed: {report['summary']['failed']}")
        print(f"Skipped: {report['summary']['skipped']}")
        print(f"Errors: {report['summary']['errors']}")
        
        # Return appropriate exit code
        if report['summary']['failed'] > 0 or report['summary']['errors'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    finally:
        runner.cleanup()

if __name__ == "__main__":
    main()