#!/usr/bin/env python3
"""
Test Runner Script
Simplified interface for running firmware tests
"""

import sys
import os
import json
import argparse
from datetime import datetime
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_framework import TestRunner, TestResult

def print_test_summary(report):
    """Print test summary to console"""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total Test Suites: {report['total_suites']}")
    print(f"Total Tests: {report['total_tests']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Skipped: {report['summary']['skipped']}")
    print(f"Errors: {report['summary']['errors']}")
    
    if report['total_tests'] > 0:
        success_rate = (report['summary']['passed'] / report['total_tests']) * 100
        print(f"Success Rate: {success_rate:.1f}%")
    
    print("\nSuite Details:")
    for suite_name, suite_data in report['suites'].items():
        print(f"  {suite_name}:")
        print(f"    Total: {suite_data['total_tests']}")
        print(f"    Passed: {suite_data['passed']}")
        print(f"    Failed: {suite_data['failed']}")
        print(f"    Execution Time: {suite_data['execution_time']:.2f}s")
        
        if suite_data['failed'] > 0:
            print("    Failed Tests:")
            for test in suite_data['tests']:
                if test['result'] == 'FAIL':
                    print(f"      - {test['name']}: {test.get('error_message', 'No error message')}")

def run_smoke_tests(platform=None):
    """Run smoke tests for specified platform or all platforms"""
    print("Running smoke tests...")
    
    runner = TestRunner()
    
    # Find smoke test suites
    smoke_suites = []
    for suite_name, suite in runner.test_suites.items():
        if "smoke" in suite_name.lower():
            if platform is None or suite.platform == platform:
                smoke_suites.append(suite_name)
    
    if not smoke_suites:
        print(f"No smoke test suites found for platform: {platform}")
        return False
    
    # Run smoke test suites
    results = {}
    for suite_name in smoke_suites:
        print(f"Running suite: {suite_name}")
        try:
            suite_results = runner.run_test_suite(suite_name)
            results[suite_name] = suite_results
        except Exception as e:
            print(f"Error running suite {suite_name}: {e}")
    
    # Generate and print report
    report = runner.generate_report(results)
    print_test_summary(report)
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"smoke_test_report_{timestamp}.json"
    runner.save_report(report, report_file)
    print(f"\nDetailed report saved to: {report_file}")
    
    # Cleanup
    runner.cleanup()
    
    # Return success if all tests passed
    return report['summary']['failed'] == 0 and report['summary']['errors'] == 0

def run_functional_tests(platform=None):
    """Run functional tests for specified platform or all platforms"""
    print("Running functional tests...")
    
    runner = TestRunner()
    
    # Find functional test suites
    functional_suites = []
    for suite_name, suite in runner.test_suites.items():
        if "functional" in suite_name.lower():
            if platform is None or suite.platform == platform:
                functional_suites.append(suite_name)
    
    if not functional_suites:
        print(f"No functional test suites found for platform: {platform}")
        return False
    
    # Run functional test suites
    results = {}
    for suite_name in functional_suites:
        print(f"Running suite: {suite_name}")
        try:
            suite_results = runner.run_test_suite(suite_name)
            results[suite_name] = suite_results
        except Exception as e:
            print(f"Error running suite {suite_name}: {e}")
    
    # Generate and print report
    report = runner.generate_report(results)
    print_test_summary(report)
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"functional_test_report_{timestamp}.json"
    runner.save_report(report, report_file)
    print(f"\nDetailed report saved to: {report_file}")
    
    # Cleanup
    runner.cleanup()
    
    # Return success if all tests passed
    return report['summary']['failed'] == 0 and report['summary']['errors'] == 0

def run_all_tests(platform=None):
    """Run all tests for specified platform or all platforms"""
    print("Running all tests...")
    
    runner = TestRunner()
    
    # Filter by platform if specified
    if platform:
        filtered_suites = {}
        for suite_name, suite in runner.test_suites.items():
            if suite.platform == platform:
                filtered_suites[suite_name] = suite
        runner.test_suites = filtered_suites
    
    if not runner.test_suites:
        print(f"No test suites found for platform: {platform}")
        return False
    
    # Run all test suites
    results = runner.run_all_tests()
    
    # Generate and print report
    report = runner.generate_report(results)
    print_test_summary(report)
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"all_tests_report_{timestamp}.json"
    runner.save_report(report, report_file)
    print(f"\nDetailed report saved to: {report_file}")
    
    # Cleanup
    runner.cleanup()
    
    # Return success if all tests passed
    return report['summary']['failed'] == 0 and report['summary']['errors'] == 0

def list_test_suites():
    """List available test suites"""
    print("Available test suites:")
    
    runner = TestRunner()
    
    for suite_name, suite in runner.test_suites.items():
        print(f"  {suite_name}:")
        print(f"    Platform: {suite.platform}")
        print(f"    Description: {suite.description}")
        print(f"    Test Cases: {len(suite.test_cases)}")
        print()

def validate_firmware(firmware_path, platform):
    """Validate firmware before testing"""
    print(f"Validating firmware: {firmware_path}")
    
    if not os.path.exists(firmware_path):
        print(f"Error: Firmware file not found: {firmware_path}")
        return False
    
    # Check file size
    file_size = os.path.getsize(firmware_path)
    print(f"Firmware size: {file_size} bytes")
    
    # Platform-specific size limits
    size_limits = {
        "esp32": 3 * 1024 * 1024,      # 3MB
        "esp8266": 1 * 1024 * 1024,    # 1MB
        "arduino": 30 * 1024,          # 30KB
        "stm32": 512 * 1024,           # 512KB
        "pico": 2 * 1024 * 1024        # 2MB
    }
    
    if platform in size_limits:
        limit = size_limits[platform]
        if file_size > limit:
            print(f"Error: Firmware size ({file_size}) exceeds limit ({limit}) for {platform}")
            return False
        print(f"✓ Firmware size within limits for {platform}")
    
    # Check file extension
    valid_extensions = {
        "esp32": [".bin"],
        "esp8266": [".bin"],
        "arduino": [".hex"],
        "stm32": [".bin", ".hex"],
        "pico": [".uf2"]
    }
    
    if platform in valid_extensions:
        ext = os.path.splitext(firmware_path)[1].lower()
        if ext not in valid_extensions[platform]:
            print(f"Warning: Unexpected file extension '{ext}' for {platform}")
            print(f"Expected: {valid_extensions[platform]}")
    
    print("✓ Firmware validation passed")
    return True

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Firmware Test Runner')
    parser.add_argument('--platform', '-p', choices=['esp32', 'esp8266', 'arduino', 'stm32', 'pico'],
                       help='Target platform')
    parser.add_argument('--test-type', '-t', choices=['smoke', 'functional', 'all'],
                       default='smoke', help='Type of tests to run')
    parser.add_argument('--suite', '-s', help='Run specific test suite')
    parser.add_argument('--list', '-l', action='store_true', help='List available test suites')
    parser.add_argument('--validate', '-v', help='Validate firmware file')
    parser.add_argument('--config', '-c', default='test-config.yaml', help='Test configuration file')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Set up logging level
    if args.verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    
    try:
        # List test suites
        if args.list:
            list_test_suites()
            return 0
        
        # Validate firmware
        if args.validate:
            if not args.platform:
                print("Error: --platform required for firmware validation")
                return 1
            
            if validate_firmware(args.validate, args.platform):
                print("Firmware validation passed")
                return 0
            else:
                print("Firmware validation failed")
                return 1
        
        # Run specific test suite
        if args.suite:
            print(f"Running test suite: {args.suite}")
            runner = TestRunner(args.config)
            try:
                results = {args.suite: runner.run_test_suite(args.suite)}
                report = runner.generate_report(results)
                print_test_summary(report)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                report_file = f"test_report_{args.suite}_{timestamp}.json"
                runner.save_report(report, report_file)
                print(f"\nDetailed report saved to: {report_file}")
                
                runner.cleanup()
                
                return 0 if report['summary']['failed'] == 0 and report['summary']['errors'] == 0 else 1
                
            except Exception as e:
                print(f"Error running test suite: {e}")
                return 1
        
        # Run tests by type
        success = True
        
        if args.test_type == 'smoke':
            success = run_smoke_tests(args.platform)
        elif args.test_type == 'functional':
            success = run_functional_tests(args.platform)
        elif args.test_type == 'all':
            success = run_all_tests(args.platform)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())