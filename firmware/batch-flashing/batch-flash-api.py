#!/usr/bin/env python3
"""
Batch Flash API Service
REST API for managing batch firmware flashing operations
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import tempfile
import threading
import time

# Import the batch flash manager
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from batch_flash_manager import BatchFlashManager, FlashTarget, DeviceType, FlashStatus

class BatchFlashAPI:
    """REST API for batch firmware flashing"""
    
    def __init__(self, config_file: str = "batch-flash-config.yaml"):
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Initialize manager
        self.manager = BatchFlashManager(config_file)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Setup routes
        self.setup_routes()
        
        # Background cleanup thread
        self.cleanup_thread = threading.Thread(target=self.cleanup_worker, daemon=True)
        self.cleanup_thread.start()
    
    def setup_routes(self):
        """Setup API routes"""
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0'
            })
        
        @self.app.route('/api/batches', methods=['GET'])
        def list_batches():
            """List all batches"""
            try:
                batches = self.manager.list_batches()
                return jsonify({
                    'success': True,
                    'batches': batches,
                    'count': len(batches)
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/batches', methods=['POST'])
        def create_batch():
            """Create new batch"""
            try:
                data = request.get_json()
                
                # Validate required fields
                required_fields = ['name', 'firmware_file', 'device_type', 'version', 'targets']
                for field in required_fields:
                    if field not in data:
                        return jsonify({
                            'success': False,
                            'error': f'Missing required field: {field}'
                        }), 400
                
                # Create firmware package
                firmware_package = self.manager.create_firmware_package(
                    firmware_path=data['firmware_file'],
                    device_type=data['device_type'],
                    version=data['version'],
                    metadata=data.get('metadata', {})
                )
                
                # Create targets
                targets = []
                for target_data in data['targets']:
                    target = FlashTarget(
                        device_id=target_data['device_id'],
                        device_type=DeviceType(target_data['device_type']),
                        connection_info=target_data['connection_info'],
                        priority=target_data.get('priority', 1),
                        max_retries=target_data.get('max_retries', 3)
                    )
                    targets.append(target)
                
                # Create batch
                batch = self.manager.create_flash_batch(
                    name=data['name'],
                    firmware_package=firmware_package,
                    targets=targets,
                    description=data.get('description', ''),
                    strategy=data.get('strategy', 'parallel'),
                    max_concurrent=data.get('max_concurrent', 10),
                    timeout=data.get('timeout', 300),
                    rollback_on_failure=data.get('rollback_on_failure', False)
                )
                
                return jsonify({
                    'success': True,
                    'batch_id': batch.batch_id,
                    'message': 'Batch created successfully'
                }), 201
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/batches/<batch_id>', methods=['GET'])
        def get_batch_status(batch_id):
            """Get batch status"""
            try:
                status = self.manager.get_batch_status(batch_id)
                if status:
                    return jsonify({
                        'success': True,
                        'batch': status
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Batch not found'
                    }), 404
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/batches/<batch_id>/start', methods=['POST'])
        def start_batch(batch_id):
            """Start batch flashing"""
            try:
                success = self.manager.start_batch_flash(batch_id)
                if success:
                    return jsonify({
                        'success': True,
                        'message': 'Batch started successfully'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Failed to start batch'
                    }), 400
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/batches/<batch_id>/cancel', methods=['POST'])
        def cancel_batch(batch_id):
            """Cancel batch operation"""
            try:
                success = self.manager.cancel_batch(batch_id)
                if success:
                    return jsonify({
                        'success': True,
                        'message': 'Batch cancelled successfully'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Failed to cancel batch'
                    }), 400
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/batches/<batch_id>/rollback', methods=['POST'])
        def rollback_batch(batch_id):
            """Rollback batch operation"""
            try:
                if batch_id not in self.manager.batches:
                    return jsonify({
                        'success': False,
                        'error': 'Batch not found'
                    }), 404
                
                batch = self.manager.batches[batch_id]
                self.manager.rollback_batch(batch)
                
                return jsonify({
                    'success': True,
                    'message': 'Batch rollback initiated'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/batches/<batch_id>/report', methods=['GET'])
        def get_batch_report(batch_id):
            """Get batch report"""
            try:
                if batch_id not in self.manager.batches:
                    return jsonify({
                        'success': False,
                        'error': 'Batch not found'
                    }), 404
                
                batch = self.manager.batches[batch_id]
                report = self.manager.generate_batch_report(batch)
                
                return jsonify({
                    'success': True,
                    'report': report
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/batches/<batch_id>/report/download', methods=['GET'])
        def download_batch_report(batch_id):
            """Download batch report as file"""
            try:
                report_file = f"batch_report_{batch_id}.json"
                if os.path.exists(report_file):
                    return send_file(report_file, as_attachment=True)
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Report file not found'
                    }), 404
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/firmware/upload', methods=['POST'])
        def upload_firmware():
            """Upload firmware file"""
            try:
                if 'firmware' not in request.files:
                    return jsonify({
                        'success': False,
                        'error': 'No firmware file provided'
                    }), 400
                
                file = request.files['firmware']
                if file.filename == '':
                    return jsonify({
                        'success': False,
                        'error': 'No file selected'
                    }), 400
                
                # Validate file extension
                allowed_extensions = {'.bin', '.hex', '.uf2'}
                if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
                    return jsonify({
                        'success': False,
                        'error': 'Invalid file type. Allowed: .bin, .hex, .uf2'
                    }), 400
                
                # Save file
                filename = secure_filename(file.filename)
                upload_dir = os.path.join(os.getcwd(), 'uploads')
                os.makedirs(upload_dir, exist_ok=True)
                
                file_path = os.path.join(upload_dir, filename)
                file.save(file_path)
                
                # Get file info
                file_size = os.path.getsize(file_path)
                
                return jsonify({
                    'success': True,
                    'file_path': file_path,
                    'file_size': file_size,
                    'filename': filename
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/firmware/validate', methods=['POST'])
        def validate_firmware():
            """Validate firmware file"""
            try:
                data = request.get_json()
                
                if 'file_path' not in data or 'device_type' not in data:
                    return jsonify({
                        'success': False,
                        'error': 'Missing required fields: file_path, device_type'
                    }), 400
                
                file_path = data['file_path']
                device_type = data['device_type']
                
                # Check if file exists
                if not os.path.exists(file_path):
                    return jsonify({
                        'success': False,
                        'error': 'File not found'
                    }), 404
                
                # Validate file size
                file_size = os.path.getsize(file_path)
                max_sizes = {
                    'esp32': 3 * 1024 * 1024,      # 3MB
                    'esp8266': 1 * 1024 * 1024,    # 1MB
                    'arduino': 30 * 1024,          # 30KB
                    'stm32': 512 * 1024,           # 512KB
                    'pico': 2 * 1024 * 1024        # 2MB
                }
                
                validation_result = {
                    'file_size': file_size,
                    'max_size': max_sizes.get(device_type, 0),
                    'size_valid': file_size <= max_sizes.get(device_type, 0),
                    'device_type': device_type
                }
                
                return jsonify({
                    'success': True,
                    'validation': validation_result
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/devices/discover', methods=['GET'])
        def discover_devices():
            """Discover available devices"""
            try:
                # Get device type filter
                device_type = request.args.get('device_type', None)
                
                # Mock discovery for now - in real implementation, this would scan ports
                discovered_devices = []
                
                # ESP32/ESP8266 devices on serial ports
                if not device_type or device_type in ['esp32', 'esp8266']:
                    for i in range(8):  # Check USB0-7
                        port = f"/dev/ttyUSB{i}"
                        if os.path.exists(port):
                            discovered_devices.append({
                                'device_id': f'ESP32_{i:03d}',
                                'device_type': 'esp32',
                                'connection_info': {
                                    'port': port,
                                    'baudrate': 115200
                                },
                                'status': 'available'
                            })
                
                # Network devices
                if not device_type or device_type == 'network':
                    # This would scan network for devices
                    pass
                
                return jsonify({
                    'success': True,
                    'devices': discovered_devices,
                    'count': len(discovered_devices)
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/config', methods=['GET'])
        def get_config():
            """Get current configuration"""
            try:
                return jsonify({
                    'success': True,
                    'config': self.manager.config
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/stats', methods=['GET'])
        def get_stats():
            """Get system statistics"""
            try:
                stats = {
                    'total_batches': len(self.manager.batches),
                    'active_batches': len([b for b in self.manager.batches.values() if b.status == 'running']),
                    'completed_batches': len([b for b in self.manager.batches.values() if b.status == 'completed']),
                    'failed_batches': len([b for b in self.manager.batches.values() if b.status == 'failed']),
                    'total_devices_flashed': sum(b.success_count for b in self.manager.batches.values()),
                    'total_devices_failed': sum(b.failure_count for b in self.manager.batches.values()),
                    'active_operations': len(self.manager.active_operations),
                    'available_interfaces': list(self.manager.interfaces.keys())
                }
                
                return jsonify({
                    'success': True,
                    'stats': stats
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/logs', methods=['GET'])
        def get_logs():
            """Get recent logs"""
            try:
                log_file = 'batch-flash.log'
                lines = int(request.args.get('lines', 100))
                
                if os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        log_lines = f.readlines()
                    
                    # Get last N lines
                    recent_logs = log_lines[-lines:] if len(log_lines) > lines else log_lines
                    
                    return jsonify({
                        'success': True,
                        'logs': recent_logs,
                        'total_lines': len(log_lines)
                    })
                else:
                    return jsonify({
                        'success': True,
                        'logs': [],
                        'total_lines': 0
                    })
                    
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/templates', methods=['GET'])
        def get_templates():
            """Get batch templates"""
            try:
                templates = {
                    'esp32_basic': {
                        'name': 'ESP32 Basic Flash',
                        'description': 'Basic ESP32 firmware flashing',
                        'device_type': 'esp32',
                        'strategy': 'parallel',
                        'max_concurrent': 5,
                        'timeout': 120,
                        'rollback_on_failure': True
                    },
                    'esp8266_basic': {
                        'name': 'ESP8266 Basic Flash',
                        'description': 'Basic ESP8266 firmware flashing',
                        'device_type': 'esp8266',
                        'strategy': 'parallel',
                        'max_concurrent': 5,
                        'timeout': 90,
                        'rollback_on_failure': True
                    },
                    'production_rollout': {
                        'name': 'Production Rollout',
                        'description': 'Safe production firmware rollout',
                        'strategy': 'gradual',
                        'max_concurrent': 3,
                        'timeout': 300,
                        'rollback_on_failure': True
                    }
                }
                
                return jsonify({
                    'success': True,
                    'templates': templates
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({
                'success': False,
                'error': 'Endpoint not found'
            }), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({
                'success': False,
                'error': 'Internal server error'
            }), 500
    
    def cleanup_worker(self):
        """Background cleanup worker"""
        while True:
            try:
                # Clean up old batches every hour
                self.manager.cleanup_old_batches(days=7)
                time.sleep(3600)  # 1 hour
            except Exception as e:
                self.logger.error(f"Cleanup worker error: {e}")
                time.sleep(300)  # 5 minutes on error
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the API server"""
        self.logger.info(f"Starting Batch Flash API on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug, threaded=True)
    
    def shutdown(self):
        """Shutdown the API service"""
        self.logger.info("Shutting down Batch Flash API")
        self.manager.shutdown()

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Batch Flash API Service')
    parser.add_argument('--config', '-c', default='batch-flash-config.yaml', help='Configuration file')
    parser.add_argument('--host', default='0.0.0.0', help='Host address')
    parser.add_argument('--port', '-p', type=int, default=5000, help='Port number')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Create API service
    api = BatchFlashAPI(args.config)
    
    try:
        api.run(host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        api.shutdown()

if __name__ == "__main__":
    main()