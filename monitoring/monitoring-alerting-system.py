#!/usr/bin/env python3
"""
Monitoring and Alerting System
Comprehensive monitoring, metrics collection, and alerting for IoT device platform
"""

import os
import sys
import json
import yaml
import time
import logging
import threading
import subprocess
import requests
import smtplib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import tempfile
import shutil
from pathlib import Path
import concurrent.futures
import psutil
import sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import hashlib
import socket
import asyncio
import aiohttp
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
from prometheus_client.exposition import MetricsHandler
from http.server import HTTPServer
import schedule

class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertStatus(Enum):
    """Alert status"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SILENCED = "silenced"

class MetricType(Enum):
    """Metric types"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

class NotificationChannel(Enum):
    """Notification channels"""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"
    PAGERDUTY = "pagerduty"

@dataclass
class MetricDefinition:
    """Metric definition"""
    name: str
    type: MetricType
    description: str
    labels: List[str] = field(default_factory=list)
    unit: str = ""
    help_text: str = ""

@dataclass
class AlertRule:
    """Alert rule definition"""
    rule_id: str
    name: str
    description: str
    metric_query: str
    threshold: float
    comparison: str  # >, <, >=, <=, ==, !=
    severity: AlertSeverity
    duration: int  # seconds
    notification_channels: List[NotificationChannel]
    tags: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    silenced_until: Optional[datetime] = None

@dataclass
class Alert:
    """Active alert"""
    alert_id: str
    rule: AlertRule
    value: float
    status: AlertStatus
    triggered_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_by: Optional[str] = None
    message: str = ""
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MonitoringTarget:
    """Monitoring target definition"""
    target_id: str
    name: str
    type: str  # service, device, endpoint, process
    endpoint: str
    check_interval: int  # seconds
    timeout: int  # seconds
    enabled: bool = True
    tags: Dict[str, str] = field(default_factory=dict)
    auth_config: Dict[str, Any] = field(default_factory=dict)

@dataclass
class HealthCheck:
    """Health check definition"""
    check_id: str
    name: str
    target: MonitoringTarget
    check_type: str  # http, tcp, ping, custom
    config: Dict[str, Any]
    success_threshold: int = 1
    failure_threshold: int = 3
    enabled: bool = True

@dataclass
class MetricSample:
    """Metric sample"""
    metric_name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)

class MonitoringAlertingSystem:
    """Comprehensive monitoring and alerting system"""
    
    def __init__(self, config_file: str = "monitoring-config.yaml"):
        self.config_file = config_file
        self.config = self.load_config()
        
        # Initialize components
        self.metrics_registry = CollectorRegistry()
        self.metrics: Dict[str, Any] = {}
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.monitoring_targets: Dict[str, MonitoringTarget] = {}
        self.health_checks: Dict[str, HealthCheck] = {}
        
        # Initialize database
        self.db_path = self.config.get('database', {}).get('path', 'monitoring.db')
        self.init_database()
        
        # Initialize metrics
        self.init_metrics()
        
        # Initialize monitoring threads
        self.monitoring_threads: Dict[str, threading.Thread] = {}
        self.shutdown_event = threading.Event()
        
        # Load configuration
        self.load_alert_rules()
        self.load_monitoring_targets()
        self.load_health_checks()
        
        # Setup logging
        self.setup_logging()
        
        # Start monitoring services
        self.start_monitoring_services()
        
        self.logger.info("Monitoring and Alerting System initialized")
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            self.create_default_config()
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f)
    
    def create_default_config(self):
        """Create default configuration file"""
        default_config = {
            'global': {
                'organization': 'MyHome IoT',
                'project': 'Device Management Platform',
                'environment': 'production'
            },
            'database': {
                'path': 'monitoring.db',
                'retention_days': 30
            },
            'metrics': {
                'collection_interval': 60,
                'retention_days': 30,
                'prometheus_port': 8080
            },
            'alerting': {
                'evaluation_interval': 60,
                'notification_timeout': 300,
                'max_retries': 3
            },
            'notifications': {
                'email': {
                    'enabled': True,
                    'smtp_server': 'smtp.gmail.com',
                    'smtp_port': 587,
                    'use_tls': True,
                    'from_email': 'alerts@i4planet.com',
                    'recipients': ['admin@i4planet.com']
                },
                'slack': {
                    'enabled': False,
                    'webhook_url': '',
                    'channel': '#alerts'
                },
                'webhook': {
                    'enabled': False,
                    'url': '',
                    'method': 'POST'
                }
            },
            'monitoring_targets': {
                'device_service': {
                    'name': 'Device Service',
                    'type': 'service',
                    'endpoint': 'http://localhost:3002/health',
                    'check_interval': 30,
                    'timeout': 10
                },
                'ota_service': {
                    'name': 'OTA Service',
                    'type': 'service',
                    'endpoint': 'http://localhost:3003/health',
                    'check_interval': 30,
                    'timeout': 10
                },
                'auth_service': {
                    'name': 'Auth Service',
                    'type': 'service',
                    'endpoint': 'http://localhost:3001/health',
                    'check_interval': 30,
                    'timeout': 10
                }
            },
            'alert_rules': {
                'service_down': {
                    'name': 'Service Down',
                    'description': 'Service is not responding',
                    'metric_query': 'service_up',
                    'threshold': 1,
                    'comparison': '<',
                    'severity': 'critical',
                    'duration': 60,
                    'notification_channels': ['email', 'slack']
                },
                'high_cpu_usage': {
                    'name': 'High CPU Usage',
                    'description': 'CPU usage is above 80%',
                    'metric_query': 'cpu_usage_percent',
                    'threshold': 80,
                    'comparison': '>',
                    'severity': 'high',
                    'duration': 300,
                    'notification_channels': ['email']
                },
                'high_memory_usage': {
                    'name': 'High Memory Usage',
                    'description': 'Memory usage is above 85%',
                    'metric_query': 'memory_usage_percent',
                    'threshold': 85,
                    'comparison': '>',
                    'severity': 'high',
                    'duration': 300,
                    'notification_channels': ['email']
                },
                'disk_space_low': {
                    'name': 'Low Disk Space',
                    'description': 'Disk space is below 20%',
                    'metric_query': 'disk_free_percent',
                    'threshold': 20,
                    'comparison': '<',
                    'severity': 'medium',
                    'duration': 600,
                    'notification_channels': ['email']
                }
            }
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False, indent=2)
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_level = self.config.get('logging', {}).get('level', 'INFO')
        log_file = self.config.get('logging', {}).get('file', 'monitoring.log')
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                value REAL NOT NULL,
                timestamp DATETIME NOT NULL,
                labels TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT UNIQUE NOT NULL,
                rule_id TEXT NOT NULL,
                value REAL NOT NULL,
                status TEXT NOT NULL,
                triggered_at DATETIME NOT NULL,
                acknowledged_at DATETIME,
                resolved_at DATETIME,
                acknowledged_by TEXT,
                resolved_by TEXT,
                message TEXT,
                context TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS health_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                status TEXT NOT NULL,
                response_time REAL,
                error_message TEXT,
                timestamp DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT NOT NULL,
                channel TEXT NOT NULL,
                status TEXT NOT NULL,
                sent_at DATETIME,
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_name_timestamp ON metrics(metric_name, timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_health_checks_target_timestamp ON health_checks(target_id, timestamp)')
        
        conn.commit()
        conn.close()
    
    def init_metrics(self):
        """Initialize Prometheus metrics"""
        # System metrics
        self.metrics['cpu_usage_percent'] = Gauge('cpu_usage_percent', 'CPU usage percentage', registry=self.metrics_registry)
        self.metrics['memory_usage_percent'] = Gauge('memory_usage_percent', 'Memory usage percentage', registry=self.metrics_registry)
        self.metrics['disk_usage_percent'] = Gauge('disk_usage_percent', 'Disk usage percentage', ['path'], registry=self.metrics_registry)
        self.metrics['disk_free_percent'] = Gauge('disk_free_percent', 'Disk free percentage', ['path'], registry=self.metrics_registry)
        
        # Service metrics
        self.metrics['service_up'] = Gauge('service_up', 'Service availability', ['service'], registry=self.metrics_registry)
        self.metrics['service_response_time'] = Histogram('service_response_time_seconds', 'Service response time', ['service'], registry=self.metrics_registry)
        self.metrics['service_requests_total'] = Counter('service_requests_total', 'Total service requests', ['service', 'status'], registry=self.metrics_registry)
        
        # Device metrics
        self.metrics['device_count'] = Gauge('device_count', 'Number of devices', ['status'], registry=self.metrics_registry)
        self.metrics['device_connectivity'] = Gauge('device_connectivity', 'Device connectivity status', ['device_id'], registry=self.metrics_registry)
        self.metrics['firmware_version_distribution'] = Gauge('firmware_version_distribution', 'Firmware version distribution', ['version'], registry=self.metrics_registry)
        
        # Deployment metrics
        self.metrics['deployment_success_rate'] = Gauge('deployment_success_rate', 'Deployment success rate', registry=self.metrics_registry)
        self.metrics['deployment_duration'] = Histogram('deployment_duration_seconds', 'Deployment duration', ['strategy'], registry=self.metrics_registry)
        self.metrics['deployment_failures_total'] = Counter('deployment_failures_total', 'Total deployment failures', ['reason'], registry=self.metrics_registry)
        
        # Alert metrics
        self.metrics['active_alerts'] = Gauge('active_alerts', 'Number of active alerts', ['severity'], registry=self.metrics_registry)
        self.metrics['alert_notifications_total'] = Counter('alert_notifications_total', 'Total alert notifications', ['channel', 'status'], registry=self.metrics_registry)
        
        # Health check metrics
        self.metrics['health_check_success'] = Gauge('health_check_success', 'Health check success', ['target'], registry=self.metrics_registry)
        self.metrics['health_check_response_time'] = Histogram('health_check_response_time_seconds', 'Health check response time', ['target'], registry=self.metrics_registry)
    
    def load_alert_rules(self):
        """Load alert rules from configuration"""
        rules_config = self.config.get('alert_rules', {})
        
        for rule_id, rule_config in rules_config.items():
            alert_rule = AlertRule(
                rule_id=rule_id,
                name=rule_config['name'],
                description=rule_config['description'],
                metric_query=rule_config['metric_query'],
                threshold=rule_config['threshold'],
                comparison=rule_config['comparison'],
                severity=AlertSeverity(rule_config['severity']),
                duration=rule_config['duration'],
                notification_channels=[NotificationChannel(ch) for ch in rule_config['notification_channels']],
                tags=rule_config.get('tags', {}),
                enabled=rule_config.get('enabled', True)
            )
            
            self.alert_rules[rule_id] = alert_rule
        
        self.logger.info(f"Loaded {len(self.alert_rules)} alert rules")
    
    def load_monitoring_targets(self):
        """Load monitoring targets from configuration"""
        targets_config = self.config.get('monitoring_targets', {})
        
        for target_id, target_config in targets_config.items():
            monitoring_target = MonitoringTarget(
                target_id=target_id,
                name=target_config['name'],
                type=target_config['type'],
                endpoint=target_config['endpoint'],
                check_interval=target_config['check_interval'],
                timeout=target_config['timeout'],
                enabled=target_config.get('enabled', True),
                tags=target_config.get('tags', {}),
                auth_config=target_config.get('auth_config', {})
            )
            
            self.monitoring_targets[target_id] = monitoring_target
        
        self.logger.info(f"Loaded {len(self.monitoring_targets)} monitoring targets")
    
    def load_health_checks(self):
        """Load health checks from configuration"""
        # Create default health checks for monitoring targets
        for target_id, target in self.monitoring_targets.items():
            if target.type == 'service':
                health_check = HealthCheck(
                    check_id=f"{target_id}_health",
                    name=f"{target.name} Health Check",
                    target=target,
                    check_type='http',
                    config={
                        'method': 'GET',
                        'expected_status': 200,
                        'expected_content': None
                    }
                )
                
                self.health_checks[health_check.check_id] = health_check
        
        self.logger.info(f"Loaded {len(self.health_checks)} health checks")
    
    def start_monitoring_services(self):
        """Start monitoring services"""
        # Start metrics collection
        self.start_metrics_collection()
        
        # Start health checks
        self.start_health_checks()
        
        # Start alert evaluation
        self.start_alert_evaluation()
        
        # Start Prometheus metrics server
        self.start_prometheus_server()
        
        # Start cleanup scheduler
        self.start_cleanup_scheduler()
    
    def start_metrics_collection(self):
        """Start metrics collection thread"""
        def collect_metrics():
            while not self.shutdown_event.is_set():
                try:
                    self.collect_system_metrics()
                    self.collect_service_metrics()
                    self.collect_device_metrics()
                    self.collect_deployment_metrics()
                    self.collect_alert_metrics()
                    
                    time.sleep(self.config.get('metrics', {}).get('collection_interval', 60))
                except Exception as e:
                    self.logger.error(f"Error collecting metrics: {e}")
                    time.sleep(10)
        
        thread = threading.Thread(target=collect_metrics, daemon=True)
        thread.start()
        self.monitoring_threads['metrics_collection'] = thread
        self.logger.info("Started metrics collection thread")
    
    def start_health_checks(self):
        """Start health check threads"""
        for check_id, health_check in self.health_checks.items():
            def run_health_check(check):
                while not self.shutdown_event.is_set():
                    try:
                        self.perform_health_check(check)
                        time.sleep(check.target.check_interval)
                    except Exception as e:
                        self.logger.error(f"Error performing health check {check.check_id}: {e}")
                        time.sleep(10)
            
            thread = threading.Thread(target=run_health_check, args=(health_check,), daemon=True)
            thread.start()
            self.monitoring_threads[f"health_check_{check_id}"] = thread
        
        self.logger.info(f"Started {len(self.health_checks)} health check threads")
    
    def start_alert_evaluation(self):
        """Start alert evaluation thread"""
        def evaluate_alerts():
            while not self.shutdown_event.is_set():
                try:
                    self.evaluate_alert_rules()
                    time.sleep(self.config.get('alerting', {}).get('evaluation_interval', 60))
                except Exception as e:
                    self.logger.error(f"Error evaluating alerts: {e}")
                    time.sleep(10)
        
        thread = threading.Thread(target=evaluate_alerts, daemon=True)
        thread.start()
        self.monitoring_threads['alert_evaluation'] = thread
        self.logger.info("Started alert evaluation thread")
    
    def start_prometheus_server(self):
        """Start Prometheus metrics server"""
        def run_prometheus_server():
            try:
                port = self.config.get('metrics', {}).get('prometheus_port', 8080)
                
                class PrometheusHandler(MetricsHandler):
                    def __init__(self, registry):
                        super().__init__(registry)
                
                handler = PrometheusHandler(self.metrics_registry)
                httpd = HTTPServer(('', port), lambda *args: handler(*args))
                
                self.logger.info(f"Prometheus metrics server started on port {port}")
                httpd.serve_forever()
            except Exception as e:
                self.logger.error(f"Error starting Prometheus server: {e}")
        
        thread = threading.Thread(target=run_prometheus_server, daemon=True)
        thread.start()
        self.monitoring_threads['prometheus_server'] = thread
    
    def start_cleanup_scheduler(self):
        """Start cleanup scheduler"""
        def run_cleanup():
            schedule.every().day.at("02:00").do(self.cleanup_old_data)
            
            while not self.shutdown_event.is_set():
                schedule.run_pending()
                time.sleep(60)
        
        thread = threading.Thread(target=run_cleanup, daemon=True)
        thread.start()
        self.monitoring_threads['cleanup_scheduler'] = thread
        self.logger.info("Started cleanup scheduler")
    
    def collect_system_metrics(self):
        """Collect system metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics['cpu_usage_percent'].set(cpu_percent)
            self.store_metric('cpu_usage_percent', cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            self.metrics['memory_usage_percent'].set(memory_percent)
            self.store_metric('memory_usage_percent', memory_percent)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            disk_free_percent = (disk.free / disk.total) * 100
            
            self.metrics['disk_usage_percent'].labels(path='/').set(disk_percent)
            self.metrics['disk_free_percent'].labels(path='/').set(disk_free_percent)
            self.store_metric('disk_usage_percent', disk_percent, {'path': '/'})
            self.store_metric('disk_free_percent', disk_free_percent, {'path': '/'})
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
    
    def collect_service_metrics(self):
        """Collect service metrics"""
        try:
            for target_id, target in self.monitoring_targets.items():
                if target.type == 'service':
                    # Get service status from health checks
                    service_up = self.get_service_status(target_id)
                    self.metrics['service_up'].labels(service=target_id).set(1 if service_up else 0)
                    self.store_metric('service_up', 1 if service_up else 0, {'service': target_id})
                    
        except Exception as e:
            self.logger.error(f"Error collecting service metrics: {e}")
    
    def collect_device_metrics(self):
        """Collect device metrics"""
        try:
            # Get device count from device service
            device_counts = self.get_device_counts()
            
            for status, count in device_counts.items():
                self.metrics['device_count'].labels(status=status).set(count)
                self.store_metric('device_count', count, {'status': status})
            
            # Get firmware version distribution
            firmware_versions = self.get_firmware_version_distribution()
            
            for version, count in firmware_versions.items():
                self.metrics['firmware_version_distribution'].labels(version=version).set(count)
                self.store_metric('firmware_version_distribution', count, {'version': version})
                
        except Exception as e:
            self.logger.error(f"Error collecting device metrics: {e}")
    
    def collect_deployment_metrics(self):
        """Collect deployment metrics"""
        try:
            # Get deployment success rate
            success_rate = self.get_deployment_success_rate()
            self.metrics['deployment_success_rate'].set(success_rate)
            self.store_metric('deployment_success_rate', success_rate)
            
        except Exception as e:
            self.logger.error(f"Error collecting deployment metrics: {e}")
    
    def collect_alert_metrics(self):
        """Collect alert metrics"""
        try:
            # Count active alerts by severity
            severity_counts = {}
            for alert in self.active_alerts.values():
                if alert.status == AlertStatus.ACTIVE:
                    severity = alert.rule.severity.value
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            for severity in AlertSeverity:
                count = severity_counts.get(severity.value, 0)
                self.metrics['active_alerts'].labels(severity=severity.value).set(count)
                self.store_metric('active_alerts', count, {'severity': severity.value})
                
        except Exception as e:
            self.logger.error(f"Error collecting alert metrics: {e}")
    
    def perform_health_check(self, health_check: HealthCheck):
        """Perform health check"""
        try:
            start_time = time.time()
            status = 'success'
            error_message = None
            
            if health_check.check_type == 'http':
                response = requests.get(
                    health_check.target.endpoint,
                    timeout=health_check.target.timeout
                )
                
                expected_status = health_check.config.get('expected_status', 200)
                if response.status_code != expected_status:
                    status = 'failure'
                    error_message = f"Expected status {expected_status}, got {response.status_code}"
                
                expected_content = health_check.config.get('expected_content')
                if expected_content and expected_content not in response.text:
                    status = 'failure'
                    error_message = f"Expected content '{expected_content}' not found"
            
            elif health_check.check_type == 'tcp':
                host, port = health_check.target.endpoint.split(':')
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(health_check.target.timeout)
                result = sock.connect_ex((host, int(port)))
                sock.close()
                
                if result != 0:
                    status = 'failure'
                    error_message = f"TCP connection failed to {host}:{port}"
            
            elif health_check.check_type == 'ping':
                result = subprocess.run(['ping', '-c', '1', health_check.target.endpoint], 
                                      capture_output=True, timeout=health_check.target.timeout)
                if result.returncode != 0:
                    status = 'failure'
                    error_message = f"Ping failed to {health_check.target.endpoint}"
            
            response_time = time.time() - start_time
            
            # Update metrics
            self.metrics['health_check_success'].labels(target=health_check.target.target_id).set(1 if status == 'success' else 0)
            self.metrics['health_check_response_time'].labels(target=health_check.target.target_id).observe(response_time)
            
            # Store result
            self.store_health_check_result(health_check.check_id, health_check.target.target_id, 
                                         status, response_time, error_message)
            
        except Exception as e:
            self.logger.error(f"Error performing health check {health_check.check_id}: {e}")
            self.store_health_check_result(health_check.check_id, health_check.target.target_id, 
                                         'failure', 0, str(e))
    
    def evaluate_alert_rules(self):
        """Evaluate alert rules"""
        try:
            for rule_id, rule in self.alert_rules.items():
                if not rule.enabled or (rule.silenced_until and rule.silenced_until > datetime.utcnow()):
                    continue
                
                # Get metric value
                metric_value = self.get_metric_value(rule.metric_query)
                
                if metric_value is None:
                    continue
                
                # Evaluate condition
                condition_met = self.evaluate_condition(metric_value, rule.threshold, rule.comparison)
                
                # Check if alert should trigger
                if condition_met:
                    if rule_id not in self.active_alerts:
                        # Create new alert
                        alert = Alert(
                            alert_id=f"{rule_id}_{int(time.time())}",
                            rule=rule,
                            value=metric_value,
                            status=AlertStatus.ACTIVE,
                            triggered_at=datetime.utcnow(),
                            message=f"{rule.name}: {rule.description} (current value: {metric_value})"
                        )
                        
                        self.active_alerts[rule_id] = alert
                        self.store_alert(alert)
                        self.send_alert_notifications(alert)
                        
                        self.logger.warning(f"Alert triggered: {alert.message}")
                else:
                    # Resolve alert if it exists
                    if rule_id in self.active_alerts:
                        alert = self.active_alerts[rule_id]
                        if alert.status == AlertStatus.ACTIVE:
                            alert.status = AlertStatus.RESOLVED
                            alert.resolved_at = datetime.utcnow()
                            alert.resolved_by = "system"
                            
                            self.update_alert(alert)
                            self.send_alert_notifications(alert)
                            
                            self.logger.info(f"Alert resolved: {alert.message}")
                            
                        del self.active_alerts[rule_id]
                        
        except Exception as e:
            self.logger.error(f"Error evaluating alert rules: {e}")
    
    def evaluate_condition(self, value: float, threshold: float, comparison: str) -> bool:
        """Evaluate alert condition"""
        if comparison == '>':
            return value > threshold
        elif comparison == '<':
            return value < threshold
        elif comparison == '>=':
            return value >= threshold
        elif comparison == '<=':
            return value <= threshold
        elif comparison == '==':
            return value == threshold
        elif comparison == '!=':
            return value != threshold
        else:
            return False
    
    def get_metric_value(self, metric_query: str) -> Optional[float]:
        """Get current metric value"""
        try:
            # Get latest metric value from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT value FROM metrics 
                WHERE metric_name = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            ''', (metric_query,))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else None
            
        except Exception as e:
            self.logger.error(f"Error getting metric value for {metric_query}: {e}")
            return None
    
    def send_alert_notifications(self, alert: Alert):
        """Send alert notifications"""
        for channel in alert.rule.notification_channels:
            try:
                if channel == NotificationChannel.EMAIL:
                    self.send_email_notification(alert)
                elif channel == NotificationChannel.SLACK:
                    self.send_slack_notification(alert)
                elif channel == NotificationChannel.WEBHOOK:
                    self.send_webhook_notification(alert)
                
                # Record notification
                self.record_notification(alert.alert_id, channel.value, 'sent')
                
            except Exception as e:
                self.logger.error(f"Error sending {channel.value} notification for alert {alert.alert_id}: {e}")
                self.record_notification(alert.alert_id, channel.value, 'failed', str(e))
    
    def send_email_notification(self, alert: Alert):
        """Send email notification"""
        email_config = self.config.get('notifications', {}).get('email', {})
        
        if not email_config.get('enabled', False):
            return
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = email_config['from_email']
        msg['To'] = ', '.join(email_config['recipients'])
        msg['Subject'] = f"[{alert.rule.severity.value.upper()}] {alert.rule.name}"
        
        # Email body
        body = f"""
Alert: {alert.rule.name}
Severity: {alert.rule.severity.value.upper()}
Description: {alert.rule.description}
Current Value: {alert.value}
Threshold: {alert.rule.threshold}
Triggered At: {alert.triggered_at}
Status: {alert.status.value.upper()}

Message: {alert.message}
"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
        if email_config.get('use_tls', False):
            server.starttls()
        
        if 'username' in email_config and 'password' in email_config:
            server.login(email_config['username'], email_config['password'])
        
        server.send_message(msg)
        server.quit()
        
        self.logger.info(f"Email notification sent for alert {alert.alert_id}")
    
    def send_slack_notification(self, alert: Alert):
        """Send Slack notification"""
        slack_config = self.config.get('notifications', {}).get('slack', {})
        
        if not slack_config.get('enabled', False):
            return
        
        # Prepare message
        color = {
            AlertSeverity.LOW: '#36a64f',
            AlertSeverity.MEDIUM: '#ff9500',
            AlertSeverity.HIGH: '#ff5722',
            AlertSeverity.CRITICAL: '#f44336'
        }.get(alert.rule.severity, '#36a64f')
        
        payload = {
            'channel': slack_config['channel'],
            'username': 'Monitoring Bot',
            'attachments': [{
                'color': color,
                'title': f"{alert.rule.name} - {alert.rule.severity.value.upper()}",
                'text': alert.message,
                'fields': [
                    {'title': 'Current Value', 'value': str(alert.value), 'short': True},
                    {'title': 'Threshold', 'value': str(alert.rule.threshold), 'short': True},
                    {'title': 'Status', 'value': alert.status.value.upper(), 'short': True},
                    {'title': 'Triggered At', 'value': alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S'), 'short': True}
                ]
            }]
        }
        
        # Send to Slack
        response = requests.post(slack_config['webhook_url'], json=payload)
        response.raise_for_status()
        
        self.logger.info(f"Slack notification sent for alert {alert.alert_id}")
    
    def send_webhook_notification(self, alert: Alert):
        """Send webhook notification"""
        webhook_config = self.config.get('notifications', {}).get('webhook', {})
        
        if not webhook_config.get('enabled', False):
            return
        
        # Prepare payload
        payload = {
            'alert_id': alert.alert_id,
            'rule_name': alert.rule.name,
            'severity': alert.rule.severity.value,
            'description': alert.rule.description,
            'value': alert.value,
            'threshold': alert.rule.threshold,
            'status': alert.status.value,
            'triggered_at': alert.triggered_at.isoformat(),
            'message': alert.message
        }
        
        # Send webhook
        headers = webhook_config.get('headers', {})
        response = requests.request(
            webhook_config['method'],
            webhook_config['url'],
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        
        self.logger.info(f"Webhook notification sent for alert {alert.alert_id}")
    
    def store_metric(self, metric_name: str, value: float, labels: Dict[str, str] = None):
        """Store metric in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO metrics (metric_name, value, timestamp, labels)
                VALUES (?, ?, ?, ?)
            ''', (metric_name, value, datetime.utcnow(), json.dumps(labels) if labels else None))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error storing metric {metric_name}: {e}")
    
    def store_alert(self, alert: Alert):
        """Store alert in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO alerts (alert_id, rule_id, value, status, triggered_at, 
                                  acknowledged_at, resolved_at, acknowledged_by, resolved_by, 
                                  message, context)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert.alert_id, alert.rule.rule_id, alert.value, alert.status.value,
                alert.triggered_at, alert.acknowledged_at, alert.resolved_at,
                alert.acknowledged_by, alert.resolved_by, alert.message,
                json.dumps(alert.context)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error storing alert {alert.alert_id}: {e}")
    
    def update_alert(self, alert: Alert):
        """Update alert in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE alerts 
                SET status = ?, acknowledged_at = ?, resolved_at = ?, 
                    acknowledged_by = ?, resolved_by = ?, context = ?
                WHERE alert_id = ?
            ''', (
                alert.status.value, alert.acknowledged_at, alert.resolved_at,
                alert.acknowledged_by, alert.resolved_by, json.dumps(alert.context),
                alert.alert_id
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error updating alert {alert.alert_id}: {e}")
    
    def store_health_check_result(self, check_id: str, target_id: str, status: str, 
                                response_time: float, error_message: Optional[str]):
        """Store health check result"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO health_checks (check_id, target_id, status, response_time, 
                                         error_message, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (check_id, target_id, status, response_time, error_message, datetime.utcnow()))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error storing health check result: {e}")
    
    def record_notification(self, alert_id: str, channel: str, status: str, 
                          error_message: Optional[str] = None):
        """Record notification attempt"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO notifications (alert_id, channel, status, sent_at, error_message)
                VALUES (?, ?, ?, ?, ?)
            ''', (alert_id, channel, status, datetime.utcnow() if status == 'sent' else None, error_message))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error recording notification: {e}")
    
    def get_service_status(self, service_id: str) -> bool:
        """Get service status from recent health checks"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT status FROM health_checks 
                WHERE target_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            ''', (service_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] == 'success' if result else False
            
        except Exception as e:
            self.logger.error(f"Error getting service status for {service_id}: {e}")
            return False
    
    def get_device_counts(self) -> Dict[str, int]:
        """Get device counts by status"""
        try:
            # Mock data - replace with actual device service API call
            return {
                'online': 150,
                'offline': 25,
                'total': 175
            }
        except Exception as e:
            self.logger.error(f"Error getting device counts: {e}")
            return {}
    
    def get_firmware_version_distribution(self) -> Dict[str, int]:
        """Get firmware version distribution"""
        try:
            # Mock data - replace with actual device service API call
            return {
                '1.0.0': 50,
                '1.1.0': 75,
                '1.2.0': 50
            }
        except Exception as e:
            self.logger.error(f"Error getting firmware version distribution: {e}")
            return {}
    
    def get_deployment_success_rate(self) -> float:
        """Get deployment success rate"""
        try:
            # Mock data - replace with actual deployment service API call
            return 95.5
        except Exception as e:
            self.logger.error(f"Error getting deployment success rate: {e}")
            return 0.0
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str):
        """Acknowledge alert"""
        for rule_id, alert in self.active_alerts.items():
            if alert.alert_id == alert_id:
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_at = datetime.utcnow()
                alert.acknowledged_by = acknowledged_by
                
                self.update_alert(alert)
                self.logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
                break
    
    def resolve_alert(self, alert_id: str, resolved_by: str):
        """Resolve alert"""
        for rule_id, alert in list(self.active_alerts.items()):
            if alert.alert_id == alert_id:
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = datetime.utcnow()
                alert.resolved_by = resolved_by
                
                self.update_alert(alert)
                self.logger.info(f"Alert {alert_id} resolved by {resolved_by}")
                
                del self.active_alerts[rule_id]
                break
    
    def silence_alert_rule(self, rule_id: str, duration_hours: int):
        """Silence alert rule"""
        if rule_id in self.alert_rules:
            self.alert_rules[rule_id].silenced_until = datetime.utcnow() + timedelta(hours=duration_hours)
            self.logger.info(f"Alert rule {rule_id} silenced for {duration_hours} hours")
    
    def cleanup_old_data(self):
        """Clean up old data"""
        try:
            retention_days = self.config.get('database', {}).get('retention_days', 30)
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Clean up old metrics
            cursor.execute('DELETE FROM metrics WHERE timestamp < ?', (cutoff_date,))
            metrics_deleted = cursor.rowcount
            
            # Clean up old health checks
            cursor.execute('DELETE FROM health_checks WHERE timestamp < ?', (cutoff_date,))
            health_checks_deleted = cursor.rowcount
            
            # Clean up old resolved alerts
            cursor.execute('DELETE FROM alerts WHERE resolved_at < ?', (cutoff_date,))
            alerts_deleted = cursor.rowcount
            
            # Clean up old notifications
            cursor.execute('DELETE FROM notifications WHERE created_at < ?', (cutoff_date,))
            notifications_deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Cleaned up old data: {metrics_deleted} metrics, "
                           f"{health_checks_deleted} health checks, {alerts_deleted} alerts, "
                           f"{notifications_deleted} notifications")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {e}")
    
    def get_active_alerts(self) -> List[Alert]:
        """Get active alerts"""
        return [alert for alert in self.active_alerts.values() if alert.status == AlertStatus.ACTIVE]
    
    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """Get alert history"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT alert_id, rule_id, value, status, triggered_at, acknowledged_at, 
                       resolved_at, acknowledged_by, resolved_by, message, context
                FROM alerts 
                WHERE triggered_at >= ?
                ORDER BY triggered_at DESC
            ''', (start_time,))
            
            alerts = []
            for row in cursor.fetchall():
                # This is a simplified version - in production you'd reconstruct the full Alert object
                alert_data = {
                    'alert_id': row[0],
                    'rule_id': row[1],
                    'value': row[2],
                    'status': row[3],
                    'triggered_at': row[4],
                    'acknowledged_at': row[5],
                    'resolved_at': row[6],
                    'acknowledged_by': row[7],
                    'resolved_by': row[8],
                    'message': row[9],
                    'context': json.loads(row[10]) if row[10] else {}
                }
                alerts.append(alert_data)
            
            conn.close()
            return alerts
            
        except Exception as e:
            self.logger.error(f"Error getting alert history: {e}")
            return []
    
    def get_metrics_data(self, metric_name: str, hours: int = 24) -> List[Dict]:
        """Get metrics data for time range"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT value, timestamp, labels
                FROM metrics 
                WHERE metric_name = ? AND timestamp >= ?
                ORDER BY timestamp
            ''', (metric_name, start_time))
            
            data = []
            for row in cursor.fetchall():
                data.append({
                    'value': row[0],
                    'timestamp': row[1],
                    'labels': json.loads(row[2]) if row[2] else {}
                })
            
            conn.close()
            return data
            
        except Exception as e:
            self.logger.error(f"Error getting metrics data for {metric_name}: {e}")
            return []
    
    def get_health_check_history(self, target_id: str, hours: int = 24) -> List[Dict]:
        """Get health check history"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT check_id, status, response_time, error_message, timestamp
                FROM health_checks 
                WHERE target_id = ? AND timestamp >= ?
                ORDER BY timestamp
            ''', (target_id, start_time))
            
            data = []
            for row in cursor.fetchall():
                data.append({
                    'check_id': row[0],
                    'status': row[1],
                    'response_time': row[2],
                    'error_message': row[3],
                    'timestamp': row[4]
                })
            
            conn.close()
            return data
            
        except Exception as e:
            self.logger.error(f"Error getting health check history for {target_id}: {e}")
            return []
    
    def shutdown(self):
        """Shutdown monitoring system"""
        self.logger.info("Shutting down monitoring system...")
        self.shutdown_event.set()
        
        # Wait for threads to finish
        for thread_name, thread in self.monitoring_threads.items():
            if thread.is_alive():
                self.logger.info(f"Waiting for {thread_name} to finish...")
                thread.join(timeout=5)
        
        self.logger.info("Monitoring system shutdown complete")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitoring and Alerting System')
    parser.add_argument('--config', '-c', default='monitoring-config.yaml', 
                       help='Configuration file path')
    parser.add_argument('--daemon', '-d', action='store_true', 
                       help='Run as daemon')
    
    args = parser.parse_args()
    
    # Initialize monitoring system
    monitoring_system = MonitoringAlertingSystem(args.config)
    
    try:
        if args.daemon:
            # Run as daemon
            monitoring_system.logger.info("Running as daemon...")
            while True:
                time.sleep(60)
        else:
            # Interactive mode
            print("Monitoring and Alerting System started")
            print("Commands:")
            print("  status - Show system status")
            print("  alerts - Show active alerts")
            print("  metrics - Show metrics summary")
            print("  quit - Exit")
            
            while True:
                command = input("\nmonitoring> ").strip().lower()
                
                if command == 'quit':
                    break
                elif command == 'status':
                    print(f"Active alerts: {len(monitoring_system.get_active_alerts())}")
                    print(f"Monitoring targets: {len(monitoring_system.monitoring_targets)}")
                    print(f"Alert rules: {len(monitoring_system.alert_rules)}")
                elif command == 'alerts':
                    alerts = monitoring_system.get_active_alerts()
                    if alerts:
                        for alert in alerts:
                            print(f"- {alert.rule.name}: {alert.message}")
                    else:
                        print("No active alerts")
                elif command == 'metrics':
                    print("Metrics collection active")
                    print(f"Prometheus server: http://localhost:{monitoring_system.config.get('metrics', {}).get('prometheus_port', 8080)}")
                else:
                    print("Unknown command")
    
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        monitoring_system.shutdown()

if __name__ == "__main__":
    main()