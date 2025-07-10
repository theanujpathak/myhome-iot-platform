#!/usr/bin/env python3
"""
Production Deployment API Service
REST API for managing deployment automation
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.exceptions import BadRequest, NotFound, Unauthorized
import jwt
from functools import wraps
import threading
import time

# Import the deployment manager
from production_deployment_manager import ProductionDeploymentManager

app = Flask(__name__)
CORS(app)

# Global deployment manager instance
deployment_manager = None

# Configuration
API_CONFIG = {
    'host': '0.0.0.0',
    'port': 5001,
    'debug': False,
    'jwt_secret': 'your-jwt-secret-key',
    'api_key': 'your-api-key'
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deployment-api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def init_deployment_manager():
    """Initialize the deployment manager"""
    global deployment_manager
    if deployment_manager is None:
        deployment_manager = ProductionDeploymentManager()
    return deployment_manager

def require_auth(f):
    """Authentication decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        api_key = request.headers.get('X-API-Key')
        
        if api_key and api_key == API_CONFIG['api_key']:
            return f(*args, **kwargs)
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                jwt.decode(token, API_CONFIG['jwt_secret'], algorithms=['HS256'])
                return f(*args, **kwargs)
            except jwt.InvalidTokenError:
                return jsonify({'error': 'Invalid token'}), 401
        
        return jsonify({'error': 'Authentication required'}), 401
    
    return decorated_function

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login endpoint"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Simple authentication (replace with proper authentication)
    if username == 'admin' and password == 'password':
        token = jwt.encode({
            'user': username,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, API_CONFIG['jwt_secret'], algorithm='HS256')
        
        return jsonify({
            'token': token,
            'expires_in': 24 * 3600
        })
    
    return jsonify({'error': 'Invalid credentials'}), 401

# Environment Management
@app.route('/api/environments', methods=['GET'])
@require_auth
def list_environments():
    """List all environments"""
    try:
        manager = init_deployment_manager()
        environments = []
        
        for env_name, env in manager.environments.items():
            environments.append({
                'name': env.name,
                'stage': env.stage.value,
                'description': env.description,
                'approval_required': env.approval_required,
                'auto_rollback': env.auto_rollback,
                'device_groups': env.device_groups,
                'max_concurrent_deployments': env.max_concurrent_deployments
            })
        
        return jsonify({
            'success': True,
            'environments': environments
        })
    
    except Exception as e:
        logger.error(f"Error listing environments: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/environments/<environment_name>', methods=['GET'])
@require_auth
def get_environment(environment_name):
    """Get specific environment details"""
    try:
        manager = init_deployment_manager()
        
        if environment_name not in manager.environments:
            return jsonify({'error': 'Environment not found'}), 404
        
        env = manager.environments[environment_name]
        return jsonify({
            'success': True,
            'environment': {
                'name': env.name,
                'stage': env.stage.value,
                'description': env.description,
                'api_endpoints': env.api_endpoints,
                'device_groups': env.device_groups,
                'approval_required': env.approval_required,
                'auto_rollback': env.auto_rollback,
                'health_check_url': env.health_check_url,
                'notification_channels': env.notification_channels,
                'deployment_window': env.deployment_window,
                'max_concurrent_deployments': env.max_concurrent_deployments,
                'rollback_timeout': env.rollback_timeout
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting environment: {e}")
        return jsonify({'error': str(e)}), 500

# Deployment Plan Management
@app.route('/api/deployment-plans', methods=['GET'])
@require_auth
def list_deployment_plans():
    """List all deployment plans"""
    try:
        manager = init_deployment_manager()
        plans = []
        
        for plan_id, plan in manager.deployment_plans.items():
            plans.append({
                'plan_id': plan.plan_id,
                'name': plan.name,
                'description': plan.description,
                'firmware_version': plan.firmware_version,
                'source_environment': plan.source_environment,
                'target_environment': plan.target_environment,
                'strategy': plan.strategy.value,
                'created_by': plan.created_by,
                'created_at': plan.created_at.isoformat(),
                'scheduled_at': plan.scheduled_at.isoformat() if plan.scheduled_at else None,
                'approved_by': plan.approved_by,
                'approved_at': plan.approved_at.isoformat() if plan.approved_at else None,
                'rollout_percentage': plan.rollout_percentage
            })
        
        return jsonify({
            'success': True,
            'plans': plans
        })
    
    except Exception as e:
        logger.error(f"Error listing deployment plans: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/deployment-plans', methods=['POST'])
@require_auth
def create_deployment_plan():
    """Create new deployment plan"""
    try:
        data = request.get_json()
        required_fields = ['name', 'firmware_version', 'source_environment', 'target_environment', 'strategy']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        manager = init_deployment_manager()
        plan = manager.create_deployment_plan(
            name=data['name'],
            description=data.get('description', ''),
            firmware_version=data['firmware_version'],
            source_environment=data['source_environment'],
            target_environment=data['target_environment'],
            strategy=data['strategy'],
            created_by=data.get('created_by', 'api_user'),
            scheduled_at=datetime.fromisoformat(data['scheduled_at']) if data.get('scheduled_at') else None,
            device_filters=data.get('device_filters', {}),
            rollout_percentage=data.get('rollout_percentage', 100),
            canary_percentage=data.get('canary_percentage', 10),
            validation_tests=data.get('validation_tests', []),
            pre_deployment_checks=data.get('pre_deployment_checks', []),
            post_deployment_checks=data.get('post_deployment_checks', []),
            rollback_criteria=data.get('rollback_criteria', {})
        )
        
        return jsonify({
            'success': True,
            'plan_id': plan.plan_id,
            'message': 'Deployment plan created successfully'
        })
    
    except Exception as e:
        logger.error(f"Error creating deployment plan: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/deployment-plans/<plan_id>', methods=['GET'])
@require_auth
def get_deployment_plan(plan_id):
    """Get specific deployment plan"""
    try:
        manager = init_deployment_manager()
        
        if plan_id not in manager.deployment_plans:
            return jsonify({'error': 'Deployment plan not found'}), 404
        
        plan = manager.deployment_plans[plan_id]
        return jsonify({
            'success': True,
            'plan': {
                'plan_id': plan.plan_id,
                'name': plan.name,
                'description': plan.description,
                'firmware_version': plan.firmware_version,
                'source_environment': plan.source_environment,
                'target_environment': plan.target_environment,
                'strategy': plan.strategy.value,
                'created_by': plan.created_by,
                'created_at': plan.created_at.isoformat(),
                'scheduled_at': plan.scheduled_at.isoformat() if plan.scheduled_at else None,
                'approved_by': plan.approved_by,
                'approved_at': plan.approved_at.isoformat() if plan.approved_at else None,
                'device_filters': plan.device_filters,
                'rollout_percentage': plan.rollout_percentage,
                'canary_percentage': plan.canary_percentage,
                'validation_tests': plan.validation_tests,
                'pre_deployment_checks': plan.pre_deployment_checks,
                'post_deployment_checks': plan.post_deployment_checks,
                'rollback_criteria': plan.rollback_criteria
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting deployment plan: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/deployment-plans/<plan_id>/approve', methods=['POST'])
@require_auth
def approve_deployment_plan(plan_id):
    """Approve deployment plan"""
    try:
        data = request.get_json()
        approved_by = data.get('approved_by', 'api_user')
        
        manager = init_deployment_manager()
        success = manager.approve_deployment_plan(plan_id, approved_by)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Deployment plan approved successfully'
            })
        else:
            return jsonify({'error': 'Failed to approve deployment plan'}), 500
    
    except Exception as e:
        logger.error(f"Error approving deployment plan: {e}")
        return jsonify({'error': str(e)}), 500

# Deployment Execution
@app.route('/api/deployments', methods=['GET'])
@require_auth
def list_deployments():
    """List all deployments"""
    try:
        manager = init_deployment_manager()
        deployments = []
        
        for execution_id, execution in manager.active_deployments.items():
            deployments.append({
                'execution_id': execution.execution_id,
                'plan_id': execution.plan.plan_id,
                'plan_name': execution.plan.name,
                'status': execution.status.value,
                'started_at': execution.started_at.isoformat() if execution.started_at else None,
                'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
                'progress': execution.progress,
                'success_count': execution.success_count,
                'failure_count': execution.failure_count,
                'total_devices': execution.total_devices,
                'current_phase': execution.current_phase
            })
        
        return jsonify({
            'success': True,
            'deployments': deployments
        })
    
    except Exception as e:
        logger.error(f"Error listing deployments: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/deployments/execute', methods=['POST'])
@require_auth
def execute_deployment():
    """Execute deployment plan"""
    try:
        data = request.get_json()
        plan_id = data.get('plan_id')
        
        if not plan_id:
            return jsonify({'error': 'Missing plan_id'}), 400
        
        manager = init_deployment_manager()
        execution = manager.execute_deployment(plan_id)
        
        if execution:
            return jsonify({
                'success': True,
                'execution_id': execution.execution_id,
                'message': 'Deployment started successfully'
            })
        else:
            return jsonify({'error': 'Failed to start deployment'}), 500
    
    except Exception as e:
        logger.error(f"Error executing deployment: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/deployments/<execution_id>', methods=['GET'])
@require_auth
def get_deployment_status(execution_id):
    """Get deployment status"""
    try:
        manager = init_deployment_manager()
        
        if execution_id not in manager.active_deployments:
            return jsonify({'error': 'Deployment not found'}), 404
        
        execution = manager.active_deployments[execution_id]
        return jsonify({
            'success': True,
            'deployment': {
                'execution_id': execution.execution_id,
                'plan_id': execution.plan.plan_id,
                'plan_name': execution.plan.name,
                'status': execution.status.value,
                'started_at': execution.started_at.isoformat() if execution.started_at else None,
                'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
                'progress': execution.progress,
                'success_count': execution.success_count,
                'failure_count': execution.failure_count,
                'total_devices': execution.total_devices,
                'current_phase': execution.current_phase,
                'health_status': execution.health_status,
                'rollback_available': execution.rollback_available,
                'logs': execution.logs[-50:] if execution.logs else []  # Last 50 logs
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting deployment status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/deployments/<execution_id>/cancel', methods=['POST'])
@require_auth
def cancel_deployment(execution_id):
    """Cancel deployment"""
    try:
        manager = init_deployment_manager()
        success = manager.cancel_deployment(execution_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Deployment cancelled successfully'
            })
        else:
            return jsonify({'error': 'Failed to cancel deployment'}), 500
    
    except Exception as e:
        logger.error(f"Error cancelling deployment: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/deployments/<execution_id>/rollback', methods=['POST'])
@require_auth
def rollback_deployment(execution_id):
    """Rollback deployment"""
    try:
        manager = init_deployment_manager()
        success = manager.rollback_deployment(execution_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Deployment rollback initiated'
            })
        else:
            return jsonify({'error': 'Failed to rollback deployment'}), 500
    
    except Exception as e:
        logger.error(f"Error rolling back deployment: {e}")
        return jsonify({'error': str(e)}), 500

# Health and Monitoring
@app.route('/api/health-checks', methods=['GET'])
@require_auth
def run_health_checks():
    """Run health checks for all environments"""
    try:
        manager = init_deployment_manager()
        results = {}
        
        for env_name, env in manager.environments.items():
            if env.health_check_url:
                health_status = manager.perform_health_check(env_name)
                results[env_name] = {
                    'status': health_status['status'],
                    'response_time': health_status['response_time'],
                    'timestamp': health_status['timestamp'],
                    'details': health_status.get('details', {})
                }
        
        return jsonify({
            'success': True,
            'health_checks': results
        })
    
    except Exception as e:
        logger.error(f"Error running health checks: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics', methods=['GET'])
@require_auth
def get_metrics():
    """Get system metrics"""
    try:
        manager = init_deployment_manager()
        
        # Calculate metrics
        total_deployments = len(manager.active_deployments)
        completed_deployments = len([d for d in manager.active_deployments.values() 
                                   if d.status.value == 'completed'])
        failed_deployments = len([d for d in manager.active_deployments.values() 
                                if d.status.value == 'failed'])
        
        success_rate = (completed_deployments / total_deployments * 100) if total_deployments > 0 else 0
        
        return jsonify({
            'success': True,
            'metrics': {
                'total_deployments': total_deployments,
                'completed_deployments': completed_deployments,
                'failed_deployments': failed_deployments,
                'success_rate': round(success_rate, 2),
                'active_deployments': len([d for d in manager.active_deployments.values() 
                                         if d.status.value in ['pending', 'running', 'validating']]),
                'total_environments': len(manager.environments),
                'total_plans': len(manager.deployment_plans)
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return jsonify({'error': str(e)}), 500

# Reporting
@app.route('/api/reports/deployment/<execution_id>', methods=['GET'])
@require_auth
def get_deployment_report(execution_id):
    """Get deployment report"""
    try:
        manager = init_deployment_manager()
        
        if execution_id not in manager.active_deployments:
            return jsonify({'error': 'Deployment not found'}), 404
        
        execution = manager.active_deployments[execution_id]
        
        report = {
            'execution_id': execution.execution_id,
            'plan_name': execution.plan.name,
            'firmware_version': execution.plan.firmware_version,
            'source_environment': execution.plan.source_environment,
            'target_environment': execution.plan.target_environment,
            'strategy': execution.plan.strategy.value,
            'status': execution.status.value,
            'started_at': execution.started_at.isoformat() if execution.started_at else None,
            'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
            'duration': (execution.completed_at - execution.started_at).total_seconds() 
                       if execution.completed_at and execution.started_at else None,
            'progress': execution.progress,
            'total_devices': execution.total_devices,
            'success_count': execution.success_count,
            'failure_count': execution.failure_count,
            'success_rate': (execution.success_count / execution.total_devices * 100) 
                          if execution.total_devices > 0 else 0,
            'phases': execution.phases,
            'health_status': execution.health_status,
            'logs': execution.logs
        }
        
        return jsonify({
            'success': True,
            'report': report
        })
    
    except Exception as e:
        logger.error(f"Error generating deployment report: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/summary', methods=['GET'])
@require_auth
def get_summary_report():
    """Get summary report"""
    try:
        manager = init_deployment_manager()
        
        # Get date range
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Filter deployments by date
        filtered_deployments = []
        for execution in manager.active_deployments.values():
            if execution.started_at and execution.started_at >= start_date:
                filtered_deployments.append(execution)
        
        # Calculate summary statistics
        total_deployments = len(filtered_deployments)
        completed = len([d for d in filtered_deployments if d.status.value == 'completed'])
        failed = len([d for d in filtered_deployments if d.status.value == 'failed'])
        
        total_devices = sum(d.total_devices for d in filtered_deployments)
        successful_devices = sum(d.success_count for d in filtered_deployments)
        failed_devices = sum(d.failure_count for d in filtered_deployments)
        
        report = {
            'period': f'Last {days} days',
            'start_date': start_date.isoformat(),
            'end_date': datetime.utcnow().isoformat(),
            'deployment_summary': {
                'total_deployments': total_deployments,
                'completed_deployments': completed,
                'failed_deployments': failed,
                'success_rate': (completed / total_deployments * 100) if total_deployments > 0 else 0
            },
            'device_summary': {
                'total_devices': total_devices,
                'successful_devices': successful_devices,
                'failed_devices': failed_devices,
                'device_success_rate': (successful_devices / total_devices * 100) if total_devices > 0 else 0
            },
            'strategy_breakdown': {},
            'environment_breakdown': {}
        }
        
        # Strategy breakdown
        for strategy in ['blue_green', 'canary', 'rolling', 'immediate']:
            count = len([d for d in filtered_deployments if d.plan.strategy.value == strategy])
            report['strategy_breakdown'][strategy] = count
        
        # Environment breakdown
        for env_name in manager.environments.keys():
            count = len([d for d in filtered_deployments if d.plan.target_environment == env_name])
            report['environment_breakdown'][env_name] = count
        
        return jsonify({
            'success': True,
            'report': report
        })
    
    except Exception as e:
        logger.error(f"Error generating summary report: {e}")
        return jsonify({'error': str(e)}), 500

# Utility endpoints
@app.route('/api/config', methods=['GET'])
@require_auth
def get_config():
    """Get system configuration"""
    try:
        manager = init_deployment_manager()
        
        return jsonify({
            'success': True,
            'config': {
                'deployment_strategies': [s.value for s in manager.config.get('deployment_strategies', {}).keys()],
                'environments': list(manager.environments.keys()),
                'notification_channels': manager.config.get('notifications', {}).keys(),
                'health_check_types': list(manager.config.get('health_checks', {}).keys())
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        return jsonify({'error': str(e)}), 500

def start_background_tasks():
    """Start background tasks"""
    def cleanup_task():
        """Cleanup old deployments"""
        while True:
            try:
                manager = init_deployment_manager()
                manager.cleanup_old_deployments()
                time.sleep(3600)  # Run every hour
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                time.sleep(60)
    
    # Start cleanup task
    cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()

if __name__ == '__main__':
    try:
        # Initialize deployment manager
        init_deployment_manager()
        
        # Start background tasks
        start_background_tasks()
        
        # Start the Flask app
        logger.info(f"Starting Deployment API on {API_CONFIG['host']}:{API_CONFIG['port']}")
        app.run(
            host=API_CONFIG['host'],
            port=API_CONFIG['port'],
            debug=API_CONFIG['debug'],
            threaded=True
        )
    
    except KeyboardInterrupt:
        logger.info("Shutting down Deployment API...")
    except Exception as e:
        logger.error(f"Error starting Deployment API: {e}")
        raise