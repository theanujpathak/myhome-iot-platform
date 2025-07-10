#!/usr/bin/env python3
"""
Monitoring API Service
REST API for monitoring and alerting system
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

# Import the monitoring system
from monitoring_alerting_system import MonitoringAlertingSystem, AlertSeverity, AlertStatus, NotificationChannel

app = Flask(__name__)
CORS(app)

# Global monitoring system instance
monitoring_system = None

# Configuration
API_CONFIG = {
    'host': '0.0.0.0',
    'port': 5002,
    'debug': False,
    'jwt_secret': 'your-jwt-secret-key',
    'api_key': 'monitoring-api-key-1'
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitoring-api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def init_monitoring_system():
    """Initialize the monitoring system"""
    global monitoring_system
    if monitoring_system is None:
        monitoring_system = MonitoringAlertingSystem()
    return monitoring_system

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

# System Status
@app.route('/api/status', methods=['GET'])
@require_auth
def get_system_status():
    """Get system status"""
    try:
        system = init_monitoring_system()
        
        active_alerts = system.get_active_alerts()
        
        status = {
            'system_health': 'healthy' if len(active_alerts) == 0 else 'warning',
            'active_alerts': len(active_alerts),
            'monitoring_targets': len(system.monitoring_targets),
            'alert_rules': len(system.alert_rules),
            'health_checks': len(system.health_checks),
            'uptime': time.time() - system.start_time if hasattr(system, 'start_time') else 0,
            'last_updated': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'success': True,
            'status': status
        })
    
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({'error': str(e)}), 500

# Metrics
@app.route('/api/metrics', methods=['GET'])
@require_auth
def get_metrics():
    """Get system metrics"""
    try:
        system = init_monitoring_system()
        
        # Get query parameters
        metric_name = request.args.get('metric')
        hours = request.args.get('hours', 24, type=int)
        
        if metric_name:
            # Get specific metric data
            data = system.get_metrics_data(metric_name, hours)
            return jsonify({
                'success': True,
                'metric': metric_name,
                'data': data
            })
        else:
            # Get all metrics summary
            metrics_summary = {
                'cpu_usage': system.get_metric_value('cpu_usage_percent'),
                'memory_usage': system.get_metric_value('memory_usage_percent'),
                'disk_free': system.get_metric_value('disk_free_percent'),
                'service_up_count': len([t for t in system.monitoring_targets.values() if system.get_service_status(t.target_id)]),
                'total_services': len(system.monitoring_targets),
                'active_alerts': len(system.get_active_alerts())
            }
            
            return jsonify({
                'success': True,
                'metrics': metrics_summary
            })
    
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/list', methods=['GET'])
@require_auth
def list_metrics():
    """List available metrics"""
    try:
        system = init_monitoring_system()
        
        # Get all available metrics from the registry
        metrics = list(system.metrics.keys())
        
        return jsonify({
            'success': True,
            'metrics': metrics
        })
    
    except Exception as e:
        logger.error(f"Error listing metrics: {e}")
        return jsonify({'error': str(e)}), 500

# Alerts
@app.route('/api/alerts', methods=['GET'])
@require_auth
def get_alerts():
    """Get alerts"""
    try:
        system = init_monitoring_system()
        
        # Get query parameters
        status = request.args.get('status')
        severity = request.args.get('severity')
        hours = request.args.get('hours', 24, type=int)
        
        if status == 'active':
            alerts = system.get_active_alerts()
            alerts_data = []
            for alert in alerts:
                alerts_data.append({
                    'alert_id': alert.alert_id,
                    'rule_id': alert.rule.rule_id,
                    'name': alert.rule.name,
                    'description': alert.rule.description,
                    'severity': alert.rule.severity.value,
                    'value': alert.value,
                    'threshold': alert.rule.threshold,
                    'status': alert.status.value,
                    'triggered_at': alert.triggered_at.isoformat(),
                    'message': alert.message
                })
        else:
            # Get alert history
            alerts_data = system.get_alert_history(hours)
        
        # Filter by severity if specified
        if severity:
            alerts_data = [a for a in alerts_data if a.get('severity') == severity]
        
        return jsonify({
            'success': True,
            'alerts': alerts_data
        })
    
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts/<alert_id>/acknowledge', methods=['POST'])
@require_auth
def acknowledge_alert(alert_id):
    """Acknowledge alert"""
    try:
        data = request.get_json()
        acknowledged_by = data.get('acknowledged_by', 'api_user')
        
        system = init_monitoring_system()
        system.acknowledge_alert(alert_id, acknowledged_by)
        
        return jsonify({
            'success': True,
            'message': 'Alert acknowledged successfully'
        })
    
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts/<alert_id>/resolve', methods=['POST'])
@require_auth
def resolve_alert(alert_id):
    """Resolve alert"""
    try:
        data = request.get_json()
        resolved_by = data.get('resolved_by', 'api_user')
        
        system = init_monitoring_system()
        system.resolve_alert(alert_id, resolved_by)
        
        return jsonify({
            'success': True,
            'message': 'Alert resolved successfully'
        })
    
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        return jsonify({'error': str(e)}), 500

# Alert Rules
@app.route('/api/alert-rules', methods=['GET'])
@require_auth
def get_alert_rules():
    """Get alert rules"""
    try:
        system = init_monitoring_system()
        
        rules = []
        for rule_id, rule in system.alert_rules.items():
            rules.append({
                'rule_id': rule.rule_id,
                'name': rule.name,
                'description': rule.description,
                'metric_query': rule.metric_query,
                'threshold': rule.threshold,
                'comparison': rule.comparison,
                'severity': rule.severity.value,
                'duration': rule.duration,
                'notification_channels': [ch.value for ch in rule.notification_channels],
                'enabled': rule.enabled,
                'silenced_until': rule.silenced_until.isoformat() if rule.silenced_until else None,
                'tags': rule.tags
            })
        
        return jsonify({
            'success': True,
            'rules': rules
        })
    
    except Exception as e:
        logger.error(f"Error getting alert rules: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/alert-rules/<rule_id>/silence', methods=['POST'])
@require_auth
def silence_alert_rule(rule_id):
    """Silence alert rule"""
    try:
        data = request.get_json()
        duration_hours = data.get('duration_hours', 1)
        
        system = init_monitoring_system()
        system.silence_alert_rule(rule_id, duration_hours)
        
        return jsonify({
            'success': True,
            'message': f'Alert rule silenced for {duration_hours} hours'
        })
    
    except Exception as e:
        logger.error(f"Error silencing alert rule: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/alert-rules/<rule_id>/enable', methods=['POST'])
@require_auth
def enable_alert_rule(rule_id):
    """Enable alert rule"""
    try:
        system = init_monitoring_system()
        
        if rule_id in system.alert_rules:
            system.alert_rules[rule_id].enabled = True
            return jsonify({
                'success': True,
                'message': 'Alert rule enabled'
            })
        else:
            return jsonify({'error': 'Alert rule not found'}), 404
    
    except Exception as e:
        logger.error(f"Error enabling alert rule: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/alert-rules/<rule_id>/disable', methods=['POST'])
@require_auth
def disable_alert_rule(rule_id):
    """Disable alert rule"""
    try:
        system = init_monitoring_system()
        
        if rule_id in system.alert_rules:
            system.alert_rules[rule_id].enabled = False
            return jsonify({
                'success': True,
                'message': 'Alert rule disabled'
            })
        else:
            return jsonify({'error': 'Alert rule not found'}), 404
    
    except Exception as e:
        logger.error(f"Error disabling alert rule: {e}")
        return jsonify({'error': str(e)}), 500

# Monitoring Targets
@app.route('/api/targets', methods=['GET'])
@require_auth
def get_monitoring_targets():
    """Get monitoring targets"""
    try:
        system = init_monitoring_system()
        
        targets = []
        for target_id, target in system.monitoring_targets.items():
            targets.append({
                'target_id': target.target_id,
                'name': target.name,
                'type': target.type,
                'endpoint': target.endpoint,
                'check_interval': target.check_interval,
                'timeout': target.timeout,
                'enabled': target.enabled,
                'tags': target.tags,
                'status': 'up' if system.get_service_status(target_id) else 'down'
            })
        
        return jsonify({
            'success': True,
            'targets': targets
        })
    
    except Exception as e:
        logger.error(f"Error getting monitoring targets: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/targets/<target_id>/health', methods=['GET'])
@require_auth
def get_target_health(target_id):
    """Get target health history"""
    try:
        system = init_monitoring_system()
        
        hours = request.args.get('hours', 24, type=int)
        health_data = system.get_health_check_history(target_id, hours)
        
        return jsonify({
            'success': True,
            'target_id': target_id,
            'health_data': health_data
        })
    
    except Exception as e:
        logger.error(f"Error getting target health: {e}")
        return jsonify({'error': str(e)}), 500

# Health Checks
@app.route('/api/health-checks', methods=['GET'])
@require_auth
def get_health_checks():
    """Get health check status"""
    try:
        system = init_monitoring_system()
        
        health_checks = []
        for check_id, check in system.health_checks.items():
            # Get latest health check result
            health_data = system.get_health_check_history(check.target.target_id, 1)
            latest_result = health_data[-1] if health_data else None
            
            health_checks.append({
                'check_id': check.check_id,
                'name': check.name,
                'target_id': check.target.target_id,
                'target_name': check.target.name,
                'check_type': check.check_type,
                'enabled': check.enabled,
                'last_check': latest_result['timestamp'] if latest_result else None,
                'status': latest_result['status'] if latest_result else 'unknown',
                'response_time': latest_result['response_time'] if latest_result else None,
                'error_message': latest_result['error_message'] if latest_result else None
            })
        
        return jsonify({
            'success': True,
            'health_checks': health_checks
        })
    
    except Exception as e:
        logger.error(f"Error getting health checks: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health-checks/run', methods=['POST'])
@require_auth
def run_health_checks():
    """Run health checks manually"""
    try:
        system = init_monitoring_system()
        
        # Run all health checks
        results = {}
        for check_id, check in system.health_checks.items():
            system.perform_health_check(check)
            results[check_id] = 'executed'
        
        return jsonify({
            'success': True,
            'message': 'Health checks executed',
            'results': results
        })
    
    except Exception as e:
        logger.error(f"Error running health checks: {e}")
        return jsonify({'error': str(e)}), 500

# Notifications
@app.route('/api/notifications', methods=['GET'])
@require_auth
def get_notifications():
    """Get notification history"""
    try:
        system = init_monitoring_system()
        
        # Get from database
        import sqlite3
        conn = sqlite3.connect(system.db_path)
        cursor = conn.cursor()
        
        hours = request.args.get('hours', 24, type=int)
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        cursor.execute('''
            SELECT alert_id, channel, status, sent_at, error_message, created_at
            FROM notifications 
            WHERE created_at >= ?
            ORDER BY created_at DESC
        ''', (start_time,))
        
        notifications = []
        for row in cursor.fetchall():
            notifications.append({
                'alert_id': row[0],
                'channel': row[1],
                'status': row[2],
                'sent_at': row[3],
                'error_message': row[4],
                'created_at': row[5]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'notifications': notifications
        })
    
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications/test', methods=['POST'])
@require_auth
def test_notifications():
    """Test notification channels"""
    try:
        data = request.get_json()
        channels = data.get('channels', ['email'])
        
        system = init_monitoring_system()
        
        # Create test alert
        from monitoring_alerting_system import Alert, AlertRule, AlertSeverity, AlertStatus
        
        test_rule = AlertRule(
            rule_id='test_rule',
            name='Test Alert',
            description='This is a test alert',
            metric_query='test_metric',
            threshold=0,
            comparison='>',
            severity=AlertSeverity.LOW,
            duration=0,
            notification_channels=[NotificationChannel(ch) for ch in channels]
        )
        
        test_alert = Alert(
            alert_id='test_alert',
            rule=test_rule,
            value=1,
            status=AlertStatus.ACTIVE,
            triggered_at=datetime.utcnow(),
            message='This is a test alert message'
        )
        
        # Send test notifications
        system.send_alert_notifications(test_alert)
        
        return jsonify({
            'success': True,
            'message': 'Test notifications sent',
            'channels': channels
        })
    
    except Exception as e:
        logger.error(f"Error testing notifications: {e}")
        return jsonify({'error': str(e)}), 500

# Dashboard Data
@app.route('/api/dashboard', methods=['GET'])
@require_auth
def get_dashboard_data():
    """Get dashboard data"""
    try:
        system = init_monitoring_system()
        
        # Get active alerts by severity
        active_alerts = system.get_active_alerts()
        alerts_by_severity = {}
        for severity in AlertSeverity:
            count = len([a for a in active_alerts if a.rule.severity == severity])
            alerts_by_severity[severity.value] = count
        
        # Get service status
        service_status = {}
        for target_id, target in system.monitoring_targets.items():
            if target.type == 'service':
                service_status[target_id] = {
                    'name': target.name,
                    'status': 'up' if system.get_service_status(target_id) else 'down'
                }
        
        # Get system metrics
        system_metrics = {
            'cpu_usage': system.get_metric_value('cpu_usage_percent'),
            'memory_usage': system.get_metric_value('memory_usage_percent'),
            'disk_free': system.get_metric_value('disk_free_percent')
        }
        
        dashboard_data = {
            'summary': {
                'total_alerts': len(active_alerts),
                'critical_alerts': alerts_by_severity.get('critical', 0),
                'services_down': len([s for s in service_status.values() if s['status'] == 'down']),
                'total_services': len(service_status)
            },
            'alerts_by_severity': alerts_by_severity,
            'service_status': service_status,
            'system_metrics': system_metrics,
            'last_updated': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'success': True,
            'dashboard': dashboard_data
        })
    
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return jsonify({'error': str(e)}), 500

# Reports
@app.route('/api/reports/alerts', methods=['GET'])
@require_auth
def get_alerts_report():
    """Get alerts report"""
    try:
        system = init_monitoring_system()
        
        days = request.args.get('days', 7, type=int)
        alerts_data = system.get_alert_history(days * 24)
        
        # Generate report
        report = {
            'period': f'Last {days} days',
            'total_alerts': len(alerts_data),
            'by_severity': {},
            'by_status': {},
            'by_rule': {},
            'timeline': []
        }
        
        # Count by severity
        for severity in AlertSeverity:
            count = len([a for a in alerts_data if a.get('severity') == severity.value])
            report['by_severity'][severity.value] = count
        
        # Count by status
        for status in AlertStatus:
            count = len([a for a in alerts_data if a.get('status') == status.value])
            report['by_status'][status.value] = count
        
        # Count by rule
        rule_counts = {}
        for alert in alerts_data:
            rule_id = alert.get('rule_id')
            rule_counts[rule_id] = rule_counts.get(rule_id, 0) + 1
        report['by_rule'] = rule_counts
        
        return jsonify({
            'success': True,
            'report': report
        })
    
    except Exception as e:
        logger.error(f"Error generating alerts report: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/performance', methods=['GET'])
@require_auth
def get_performance_report():
    """Get performance report"""
    try:
        system = init_monitoring_system()
        
        hours = request.args.get('hours', 24, type=int)
        
        # Get performance metrics
        cpu_data = system.get_metrics_data('cpu_usage_percent', hours)
        memory_data = system.get_metrics_data('memory_usage_percent', hours)
        disk_data = system.get_metrics_data('disk_free_percent', hours)
        
        # Calculate averages
        cpu_avg = sum(d['value'] for d in cpu_data) / len(cpu_data) if cpu_data else 0
        memory_avg = sum(d['value'] for d in memory_data) / len(memory_data) if memory_data else 0
        disk_avg = sum(d['value'] for d in disk_data) / len(disk_data) if disk_data else 0
        
        # Calculate peaks
        cpu_peak = max((d['value'] for d in cpu_data), default=0)
        memory_peak = max((d['value'] for d in memory_data), default=0)
        disk_min = min((d['value'] for d in disk_data), default=100)
        
        report = {
            'period': f'Last {hours} hours',
            'cpu': {
                'average': round(cpu_avg, 2),
                'peak': round(cpu_peak, 2),
                'data_points': len(cpu_data)
            },
            'memory': {
                'average': round(memory_avg, 2),
                'peak': round(memory_peak, 2),
                'data_points': len(memory_data)
            },
            'disk': {
                'average_free': round(disk_avg, 2),
                'minimum_free': round(disk_min, 2),
                'data_points': len(disk_data)
            }
        }
        
        return jsonify({
            'success': True,
            'report': report
        })
    
    except Exception as e:
        logger.error(f"Error generating performance report: {e}")
        return jsonify({'error': str(e)}), 500

# Configuration
@app.route('/api/config', methods=['GET'])
@require_auth
def get_config():
    """Get system configuration"""
    try:
        system = init_monitoring_system()
        
        config = {
            'monitoring_targets': len(system.monitoring_targets),
            'alert_rules': len(system.alert_rules),
            'health_checks': len(system.health_checks),
            'notification_channels': list(system.config.get('notifications', {}).keys()),
            'metrics_retention_days': system.config.get('database', {}).get('retention_days', 30),
            'collection_interval': system.config.get('metrics', {}).get('collection_interval', 60),
            'evaluation_interval': system.config.get('alerting', {}).get('evaluation_interval', 60)
        }
        
        return jsonify({
            'success': True,
            'config': config
        })
    
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        return jsonify({'error': str(e)}), 500

def start_background_tasks():
    """Start background tasks"""
    def cleanup_task():
        """Cleanup old data"""
        while True:
            try:
                system = init_monitoring_system()
                system.cleanup_old_data()
                time.sleep(86400)  # Run daily
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                time.sleep(3600)  # Retry in 1 hour
    
    # Start cleanup task
    cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()

if __name__ == '__main__':
    try:
        # Initialize monitoring system
        init_monitoring_system()
        
        # Start background tasks
        start_background_tasks()
        
        # Start the Flask app
        logger.info(f"Starting Monitoring API on {API_CONFIG['host']}:{API_CONFIG['port']}")
        app.run(
            host=API_CONFIG['host'],
            port=API_CONFIG['port'],
            debug=API_CONFIG['debug'],
            threaded=True
        )
    
    except KeyboardInterrupt:
        logger.info("Shutting down Monitoring API...")
        if monitoring_system:
            monitoring_system.shutdown()
    except Exception as e:
        logger.error(f"Error starting Monitoring API: {e}")
        raise