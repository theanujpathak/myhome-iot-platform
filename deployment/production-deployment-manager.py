#!/usr/bin/env python3
"""
Production Deployment Manager
Comprehensive system for automating firmware deployment from development to production
"""

import os
import sys
import json
import yaml
import time
import logging
import hashlib
import threading
import subprocess
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import tempfile
import shutil
from pathlib import Path
import concurrent.futures
import psutil
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class DeploymentStage(Enum):
    """Deployment stages"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

class DeploymentStatus(Enum):
    """Deployment status"""
    PENDING = "pending"
    BUILDING = "building"
    TESTING = "testing"
    VALIDATING = "validating"
    DEPLOYING = "deploying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLED_BACK = "rolled_back"

class DeploymentStrategy(Enum):
    """Deployment strategies"""
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    ROLLING = "rolling"
    IMMEDIATE = "immediate"

@dataclass
class Environment:
    """Deployment environment configuration"""
    name: str
    stage: DeploymentStage
    description: str
    api_endpoints: Dict[str, str]
    device_groups: List[str]
    approval_required: bool = True
    auto_rollback: bool = True
    health_check_url: Optional[str] = None
    notification_channels: List[str] = field(default_factory=list)
    deployment_window: Optional[Dict[str, str]] = None
    max_concurrent_deployments: int = 10
    rollback_timeout: int = 300
    
@dataclass
class DeploymentPlan:
    """Deployment execution plan"""
    plan_id: str
    name: str
    description: str
    firmware_version: str
    source_environment: str
    target_environment: str
    strategy: DeploymentStrategy
    created_by: str
    created_at: datetime
    scheduled_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    device_filters: Dict[str, Any] = field(default_factory=dict)
    rollout_percentage: int = 100
    canary_percentage: int = 10
    validation_tests: List[str] = field(default_factory=list)
    pre_deployment_checks: List[str] = field(default_factory=list)
    post_deployment_checks: List[str] = field(default_factory=list)
    rollback_criteria: Dict[str, Any] = field(default_factory=dict)
    
@dataclass
class DeploymentExecution:
    """Active deployment execution"""
    execution_id: str
    plan: DeploymentPlan
    status: DeploymentStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    current_stage: str = "initializing"
    devices_targeted: int = 0
    devices_successful: int = 0
    devices_failed: int = 0
    error_message: Optional[str] = None
    rollback_execution_id: Optional[str] = None
    health_check_results: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)

class HealthChecker:
    """Health check system for deployment validation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def check_system_health(self, environment: Environment) -> Dict[str, Any]:
        """Check overall system health"""
        health_results = {
            "environment": environment.name,
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "checks": {}
        }
        
        # API health checks
        if environment.health_check_url:
            health_results["checks"]["api"] = self._check_api_health(environment.health_check_url)
        
        # Service health checks
        for service_name, endpoint in environment.api_endpoints.items():
            health_results["checks"][f"service_{service_name}"] = self._check_service_health(endpoint)
        
        # Database health checks
        health_results["checks"]["database"] = self._check_database_health(environment)
        
        # System resource checks
        health_results["checks"]["resources"] = self._check_system_resources()
        
        # Device connectivity checks
        health_results["checks"]["devices"] = self._check_device_connectivity(environment)
        
        # Determine overall status
        failed_checks = [name for name, result in health_results["checks"].items() 
                        if result.get("status") != "healthy"]
        
        if failed_checks:
            health_results["overall_status"] = "unhealthy"
            health_results["failed_checks"] = failed_checks
        
        return health_results
    
    def _check_api_health(self, url: str) -> Dict[str, Any]:
        """Check API health endpoint"""
        try:
            response = requests.get(f"{url}/health", timeout=10)
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time": response.elapsed.total_seconds(),
                "status_code": response.status_code
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def _check_service_health(self, endpoint: str) -> Dict[str, Any]:
        """Check individual service health"""
        try:
            response = requests.get(f"{endpoint}/health", timeout=5)
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time": response.elapsed.total_seconds(),
                "endpoint": endpoint
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "endpoint": endpoint
            }
    
    def _check_database_health(self, environment: Environment) -> Dict[str, Any]:
        """Check database connectivity and health"""
        try:
            # This would connect to actual database
            # For now, simulate database health check
            return {
                "status": "healthy",
                "connection_count": 10,
                "query_time": 0.05
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource utilization"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "status": "healthy" if cpu_percent < 80 and memory.percent < 85 else "warning",
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": (disk.used / disk.total) * 100,
                "available_memory": memory.available,
                "free_disk": disk.free
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def _check_device_connectivity(self, environment: Environment) -> Dict[str, Any]:
        """Check device connectivity and responsiveness"""
        try:
            # This would check actual device connectivity
            # For now, simulate device connectivity check
            return {
                "status": "healthy",
                "online_devices": 95,
                "total_devices": 100,
                "connectivity_rate": 95.0
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

class NotificationManager:
    """Notification system for deployment events"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def send_notification(self, channel: str, message: str, level: str = "info"):
        """Send notification to specified channel"""
        try:
            if channel == "email":
                self._send_email(message, level)
            elif channel == "slack":
                self._send_slack(message, level)
            elif channel == "webhook":
                self._send_webhook(message, level)
            else:
                self.logger.warning(f"Unknown notification channel: {channel}")
        except Exception as e:
            self.logger.error(f"Failed to send notification to {channel}: {e}")
    
    def _send_email(self, message: str, level: str):
        """Send email notification"""
        email_config = self.config.get("email", {})
        if not email_config.get("enabled", False):
            return
        
        msg = MIMEMultipart()
        msg['From'] = email_config.get("from_address", "deployment@company.com")
        msg['To'] = ", ".join(email_config.get("recipients", []))
        msg['Subject'] = f"Deployment Notification - {level.upper()}"
        
        msg.attach(MIMEText(message, 'plain'))
        
        try:
            server = smtplib.SMTP(email_config.get("smtp_server"), email_config.get("smtp_port", 587))
            server.starttls()
            server.login(email_config.get("username"), email_config.get("password"))
            server.send_message(msg)
            server.quit()
            self.logger.info("Email notification sent successfully")
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
    
    def _send_slack(self, message: str, level: str):
        """Send Slack notification"""
        slack_config = self.config.get("slack", {})
        if not slack_config.get("enabled", False):
            return
        
        webhook_url = slack_config.get("webhook_url")
        if not webhook_url:
            return
        
        color_map = {
            "info": "#36a64f",
            "warning": "#ff9500",
            "error": "#ff0000",
            "success": "#36a64f"
        }
        
        payload = {
            "text": "Deployment Notification",
            "attachments": [{
                "color": color_map.get(level, "#36a64f"),
                "text": message,
                "ts": int(time.time())
            }]
        }
        
        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            if response.status_code == 200:
                self.logger.info("Slack notification sent successfully")
            else:
                self.logger.error(f"Slack notification failed: {response.status_code}")
        except Exception as e:
            self.logger.error(f"Failed to send Slack notification: {e}")
    
    def _send_webhook(self, message: str, level: str):
        """Send webhook notification"""
        webhook_config = self.config.get("webhook", {})
        if not webhook_config.get("enabled", False):
            return
        
        webhook_url = webhook_config.get("url")
        if not webhook_url:
            return
        
        payload = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "source": "deployment_manager"
        }
        
        headers = webhook_config.get("headers", {})
        
        try:
            response = requests.post(webhook_url, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                self.logger.info("Webhook notification sent successfully")
            else:
                self.logger.error(f"Webhook notification failed: {response.status_code}")
        except Exception as e:
            self.logger.error(f"Failed to send webhook notification: {e}")

class DeploymentValidator:
    """Validation system for deployment safety"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def validate_deployment_plan(self, plan: DeploymentPlan) -> Dict[str, Any]:
        """Validate deployment plan before execution"""
        validation_results = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "checks": {}
        }
        
        # Validate firmware version
        validation_results["checks"]["firmware_version"] = self._validate_firmware_version(plan.firmware_version)
        
        # Validate target environment
        validation_results["checks"]["target_environment"] = self._validate_target_environment(plan.target_environment)
        
        # Validate deployment window
        validation_results["checks"]["deployment_window"] = self._validate_deployment_window(plan)
        
        # Validate device filters
        validation_results["checks"]["device_filters"] = self._validate_device_filters(plan.device_filters)
        
        # Validate rollout percentage
        validation_results["checks"]["rollout_percentage"] = self._validate_rollout_percentage(plan.rollout_percentage)
        
        # Validate canary settings
        if plan.strategy == DeploymentStrategy.CANARY:
            validation_results["checks"]["canary_settings"] = self._validate_canary_settings(plan)
        
        # Collect errors and warnings
        for check_name, check_result in validation_results["checks"].items():
            if check_result.get("status") == "error":
                validation_results["errors"].append(f"{check_name}: {check_result.get('message', 'Unknown error')}")
            elif check_result.get("status") == "warning":
                validation_results["warnings"].append(f"{check_name}: {check_result.get('message', 'Unknown warning')}")
        
        # Determine overall validity
        validation_results["valid"] = len(validation_results["errors"]) == 0
        
        return validation_results
    
    def _validate_firmware_version(self, version: str) -> Dict[str, Any]:
        """Validate firmware version format and existence"""
        try:
            # Check version format (semantic versioning)
            parts = version.split('.')
            if len(parts) != 3 or not all(part.isdigit() for part in parts):
                return {
                    "status": "error",
                    "message": "Invalid version format. Expected: MAJOR.MINOR.PATCH"
                }
            
            # Check if firmware exists in repository
            # This would check actual firmware repository
            return {
                "status": "success",
                "message": "Firmware version is valid"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Firmware validation failed: {str(e)}"
            }
    
    def _validate_target_environment(self, environment: str) -> Dict[str, Any]:
        """Validate target environment availability"""
        try:
            # Check if environment exists and is accessible
            valid_environments = ["development", "testing", "staging", "production"]
            if environment not in valid_environments:
                return {
                    "status": "error",
                    "message": f"Invalid environment. Valid options: {valid_environments}"
                }
            
            return {
                "status": "success",
                "message": "Target environment is valid"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Environment validation failed: {str(e)}"
            }
    
    def _validate_deployment_window(self, plan: DeploymentPlan) -> Dict[str, Any]:
        """Validate deployment timing"""
        try:
            # Check if deployment is scheduled during maintenance window
            if plan.scheduled_at:
                # Check if scheduled time is in the future
                if plan.scheduled_at <= datetime.now():
                    return {
                        "status": "error",
                        "message": "Scheduled deployment time must be in the future"
                    }
                
                # Check if scheduled during allowed window
                # This would check actual deployment windows
                return {
                    "status": "success",
                    "message": "Deployment window is valid"
                }
            
            return {
                "status": "success",
                "message": "Immediate deployment allowed"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Deployment window validation failed: {str(e)}"
            }
    
    def _validate_device_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate device filter criteria"""
        try:
            # Validate filter syntax and criteria
            if not filters:
                return {
                    "status": "warning",
                    "message": "No device filters specified - all devices will be targeted"
                }
            
            # Check filter validity
            valid_filters = ["device_type", "location", "firmware_version", "tags"]
            invalid_filters = [f for f in filters.keys() if f not in valid_filters]
            
            if invalid_filters:
                return {
                    "status": "error",
                    "message": f"Invalid filter criteria: {invalid_filters}"
                }
            
            return {
                "status": "success",
                "message": "Device filters are valid"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Device filter validation failed: {str(e)}"
            }
    
    def _validate_rollout_percentage(self, percentage: int) -> Dict[str, Any]:
        """Validate rollout percentage"""
        try:
            if not 1 <= percentage <= 100:
                return {
                    "status": "error",
                    "message": "Rollout percentage must be between 1 and 100"
                }
            
            if percentage < 10:
                return {
                    "status": "warning",
                    "message": "Low rollout percentage may result in limited validation"
                }
            
            return {
                "status": "success",
                "message": "Rollout percentage is valid"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Rollout percentage validation failed: {str(e)}"
            }
    
    def _validate_canary_settings(self, plan: DeploymentPlan) -> Dict[str, Any]:
        """Validate canary deployment settings"""
        try:
            if plan.canary_percentage < 1 or plan.canary_percentage > 50:
                return {
                    "status": "error",
                    "message": "Canary percentage must be between 1 and 50"
                }
            
            if not plan.validation_tests:
                return {
                    "status": "warning",
                    "message": "No validation tests specified for canary deployment"
                }
            
            return {
                "status": "success",
                "message": "Canary settings are valid"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Canary validation failed: {str(e)}"
            }

class ProductionDeploymentManager:
    """Main production deployment manager"""
    
    def __init__(self, config_file: str = "deployment-config.yaml"):
        self.config = self.load_config(config_file)
        self.environments: Dict[str, Environment] = {}
        self.deployment_plans: Dict[str, DeploymentPlan] = {}
        self.active_deployments: Dict[str, DeploymentExecution] = {}
        self.deployment_history: List[DeploymentExecution] = []
        
        # Initialize components
        self.health_checker = HealthChecker(self.config.get("health_checks", {}))
        self.notification_manager = NotificationManager(self.config.get("notifications", {}))
        self.validator = DeploymentValidator(self.config.get("validation", {}))
        
        # Setup logging
        self.setup_logging()
        
        # Initialize environments
        self.initialize_environments()
        
        # Background monitoring
        self.monitoring_thread = threading.Thread(target=self._monitoring_worker, daemon=True)
        self.monitoring_thread.start()
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('deployment-manager.log'),
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
    
    def get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            "environments": {
                "development": {
                    "stage": "development",
                    "description": "Development environment",
                    "api_endpoints": {
                        "device_service": "http://localhost:3002",
                        "ota_service": "http://localhost:3004"
                    },
                    "device_groups": ["dev_devices"],
                    "approval_required": False,
                    "auto_rollback": True
                },
                "production": {
                    "stage": "production",
                    "description": "Production environment",
                    "api_endpoints": {
                        "device_service": "https://api.company.com:3002",
                        "ota_service": "https://api.company.com:3004"
                    },
                    "device_groups": ["prod_devices"],
                    "approval_required": True,
                    "auto_rollback": True,
                    "health_check_url": "https://api.company.com/health"
                }
            },
            "deployment_strategies": {
                "blue_green": {
                    "enabled": True,
                    "switch_threshold": 95
                },
                "canary": {
                    "enabled": True,
                    "default_percentage": 10,
                    "validation_period": 300
                }
            },
            "notifications": {
                "email": {
                    "enabled": False,
                    "smtp_server": "smtp.company.com",
                    "smtp_port": 587,
                    "recipients": ["team@company.com"]
                },
                "slack": {
                    "enabled": False,
                    "webhook_url": "https://hooks.slack.com/services/..."
                }
            }
        }
    
    def initialize_environments(self):
        """Initialize deployment environments"""
        for env_name, env_config in self.config.get("environments", {}).items():
            environment = Environment(
                name=env_name,
                stage=DeploymentStage(env_config.get("stage", "development")),
                description=env_config.get("description", ""),
                api_endpoints=env_config.get("api_endpoints", {}),
                device_groups=env_config.get("device_groups", []),
                approval_required=env_config.get("approval_required", False),
                auto_rollback=env_config.get("auto_rollback", True),
                health_check_url=env_config.get("health_check_url"),
                notification_channels=env_config.get("notification_channels", []),
                deployment_window=env_config.get("deployment_window"),
                max_concurrent_deployments=env_config.get("max_concurrent_deployments", 10),
                rollback_timeout=env_config.get("rollback_timeout", 300)
            )
            self.environments[env_name] = environment
            self.logger.info(f"Initialized environment: {env_name}")
    
    def create_deployment_plan(self, plan_data: Dict[str, Any]) -> DeploymentPlan:
        """Create new deployment plan"""
        plan_id = f"plan_{int(time.time())}_{len(self.deployment_plans)}"
        
        plan = DeploymentPlan(
            plan_id=plan_id,
            name=plan_data["name"],
            description=plan_data.get("description", ""),
            firmware_version=plan_data["firmware_version"],
            source_environment=plan_data["source_environment"],
            target_environment=plan_data["target_environment"],
            strategy=DeploymentStrategy(plan_data.get("strategy", "rolling")),
            created_by=plan_data["created_by"],
            created_at=datetime.now(),
            scheduled_at=plan_data.get("scheduled_at"),
            device_filters=plan_data.get("device_filters", {}),
            rollout_percentage=plan_data.get("rollout_percentage", 100),
            canary_percentage=plan_data.get("canary_percentage", 10),
            validation_tests=plan_data.get("validation_tests", []),
            pre_deployment_checks=plan_data.get("pre_deployment_checks", []),
            post_deployment_checks=plan_data.get("post_deployment_checks", []),
            rollback_criteria=plan_data.get("rollback_criteria", {})
        )
        
        self.deployment_plans[plan_id] = plan
        self.logger.info(f"Created deployment plan: {plan_id}")
        
        return plan
    
    def validate_deployment_plan(self, plan_id: str) -> Dict[str, Any]:
        """Validate deployment plan"""
        if plan_id not in self.deployment_plans:
            return {
                "valid": False,
                "errors": ["Deployment plan not found"]
            }
        
        plan = self.deployment_plans[plan_id]
        validation_results = self.validator.validate_deployment_plan(plan)
        
        self.logger.info(f"Validated deployment plan {plan_id}: {'PASS' if validation_results['valid'] else 'FAIL'}")
        
        return validation_results
    
    def approve_deployment_plan(self, plan_id: str, approved_by: str) -> bool:
        """Approve deployment plan for execution"""
        if plan_id not in self.deployment_plans:
            return False
        
        plan = self.deployment_plans[plan_id]
        plan.approved_by = approved_by
        plan.approved_at = datetime.now()
        
        self.logger.info(f"Deployment plan {plan_id} approved by {approved_by}")
        
        # Send notification
        message = f"Deployment plan '{plan.name}' has been approved by {approved_by}"
        self._send_notifications(plan.target_environment, message, "info")
        
        return True
    
    def execute_deployment_plan(self, plan_id: str) -> Optional[str]:
        """Execute deployment plan"""
        if plan_id not in self.deployment_plans:
            self.logger.error(f"Deployment plan {plan_id} not found")
            return None
        
        plan = self.deployment_plans[plan_id]
        
        # Check if approval is required
        target_env = self.environments.get(plan.target_environment)
        if target_env and target_env.approval_required and not plan.approved_by:
            self.logger.error(f"Deployment plan {plan_id} requires approval")
            return None
        
        # Validate plan
        validation_results = self.validate_deployment_plan(plan_id)
        if not validation_results["valid"]:
            self.logger.error(f"Deployment plan {plan_id} validation failed: {validation_results['errors']}")
            return None
        
        # Create execution
        execution_id = f"exec_{int(time.time())}_{len(self.active_deployments)}"
        execution = DeploymentExecution(
            execution_id=execution_id,
            plan=plan,
            status=DeploymentStatus.PENDING,
            started_at=datetime.now()
        )
        
        self.active_deployments[execution_id] = execution
        
        # Start execution in background
        execution_thread = threading.Thread(
            target=self._execute_deployment,
            args=(execution,),
            daemon=True
        )
        execution_thread.start()
        
        self.logger.info(f"Started deployment execution: {execution_id}")
        
        # Send notification
        message = f"Deployment '{plan.name}' has been started (ID: {execution_id})"
        self._send_notifications(plan.target_environment, message, "info")
        
        return execution_id
    
    def _execute_deployment(self, execution: DeploymentExecution):
        """Execute deployment in background"""
        try:
            plan = execution.plan
            
            # Pre-deployment health check
            execution.status = DeploymentStatus.VALIDATING
            execution.current_stage = "pre_deployment_health_check"
            
            health_results = self.health_checker.check_system_health(
                self.environments[plan.target_environment]
            )
            
            if health_results["overall_status"] != "healthy":
                execution.status = DeploymentStatus.FAILED
                execution.error_message = "Pre-deployment health check failed"
                execution.health_check_results = health_results
                self._handle_deployment_failure(execution)
                return
            
            # Run pre-deployment checks
            execution.current_stage = "pre_deployment_checks"
            for check in plan.pre_deployment_checks:
                if not self._run_deployment_check(check, execution):
                    execution.status = DeploymentStatus.FAILED
                    execution.error_message = f"Pre-deployment check failed: {check}"
                    self._handle_deployment_failure(execution)
                    return
            
            # Execute deployment based on strategy
            execution.status = DeploymentStatus.DEPLOYING
            
            if plan.strategy == DeploymentStrategy.BLUE_GREEN:
                success = self._execute_blue_green_deployment(execution)
            elif plan.strategy == DeploymentStrategy.CANARY:
                success = self._execute_canary_deployment(execution)
            elif plan.strategy == DeploymentStrategy.ROLLING:
                success = self._execute_rolling_deployment(execution)
            else:  # IMMEDIATE
                success = self._execute_immediate_deployment(execution)
            
            if not success:
                execution.status = DeploymentStatus.FAILED
                self._handle_deployment_failure(execution)
                return
            
            # Post-deployment validation
            execution.current_stage = "post_deployment_validation"
            
            # Run post-deployment checks
            for check in plan.post_deployment_checks:
                if not self._run_deployment_check(check, execution):
                    execution.status = DeploymentStatus.FAILED
                    execution.error_message = f"Post-deployment check failed: {check}"
                    self._handle_deployment_failure(execution)
                    return
            
            # Final health check
            final_health = self.health_checker.check_system_health(
                self.environments[plan.target_environment]
            )
            
            if final_health["overall_status"] != "healthy":
                execution.status = DeploymentStatus.FAILED
                execution.error_message = "Post-deployment health check failed"
                execution.health_check_results = final_health
                self._handle_deployment_failure(execution)
                return
            
            # Success
            execution.status = DeploymentStatus.COMPLETED
            execution.completed_at = datetime.now()
            execution.progress = 100.0
            
            self.deployment_history.append(execution)
            if execution.execution_id in self.active_deployments:
                del self.active_deployments[execution.execution_id]
            
            self.logger.info(f"Deployment {execution.execution_id} completed successfully")
            
            # Send success notification
            message = f"Deployment '{plan.name}' completed successfully"
            self._send_notifications(plan.target_environment, message, "success")
            
        except Exception as e:
            execution.status = DeploymentStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now()
            
            self.logger.error(f"Deployment {execution.execution_id} failed: {e}")
            self._handle_deployment_failure(execution)
    
    def _execute_blue_green_deployment(self, execution: DeploymentExecution) -> bool:
        """Execute blue-green deployment"""
        try:
            plan = execution.plan
            execution.current_stage = "blue_green_deployment"
            
            # Deploy to green environment
            execution.progress = 10.0
            self.logger.info(f"Deploying to green environment for {execution.execution_id}")
            
            # Simulate deployment to green environment
            deployment_success = self._deploy_to_environment(
                plan.firmware_version,
                "green",
                execution
            )
            
            if not deployment_success:
                return False
            
            execution.progress = 50.0
            
            # Validate green environment
            self.logger.info(f"Validating green environment for {execution.execution_id}")
            time.sleep(10)  # Simulate validation time
            
            # Switch traffic to green
            execution.progress = 80.0
            self.logger.info(f"Switching traffic to green for {execution.execution_id}")
            
            # Simulate traffic switch
            time.sleep(5)
            
            execution.progress = 100.0
            return True
            
        except Exception as e:
            self.logger.error(f"Blue-green deployment failed: {e}")
            return False
    
    def _execute_canary_deployment(self, execution: DeploymentExecution) -> bool:
        """Execute canary deployment"""
        try:
            plan = execution.plan
            execution.current_stage = "canary_deployment"
            
            # Deploy to canary group
            execution.progress = 10.0
            self.logger.info(f"Deploying to canary group ({plan.canary_percentage}%) for {execution.execution_id}")
            
            canary_success = self._deploy_to_canary_group(
                plan.firmware_version,
                plan.canary_percentage,
                execution
            )
            
            if not canary_success:
                return False
            
            execution.progress = 30.0
            
            # Monitor canary deployment
            self.logger.info(f"Monitoring canary deployment for {execution.execution_id}")
            
            # Simulate canary monitoring period
            validation_period = self.config.get("deployment_strategies", {}).get("canary", {}).get("validation_period", 300)
            time.sleep(min(validation_period, 30))  # Simulate monitoring
            
            # Run validation tests
            for test in plan.validation_tests:
                if not self._run_validation_test(test, execution):
                    self.logger.error(f"Canary validation test failed: {test}")
                    return False
            
            execution.progress = 60.0
            
            # Full rollout
            self.logger.info(f"Proceeding with full rollout for {execution.execution_id}")
            
            full_rollout_success = self._deploy_to_environment(
                plan.firmware_version,
                plan.target_environment,
                execution
            )
            
            if not full_rollout_success:
                return False
            
            execution.progress = 100.0
            return True
            
        except Exception as e:
            self.logger.error(f"Canary deployment failed: {e}")
            return False
    
    def _execute_rolling_deployment(self, execution: DeploymentExecution) -> bool:
        """Execute rolling deployment"""
        try:
            plan = execution.plan
            execution.current_stage = "rolling_deployment"
            
            # Get device list
            devices = self._get_target_devices(plan.device_filters, plan.target_environment)
            execution.devices_targeted = len(devices)
            
            # Calculate batch size
            batch_size = max(1, len(devices) // 10)  # 10 batches
            
            # Deploy in batches
            for i in range(0, len(devices), batch_size):
                batch = devices[i:i + batch_size]
                
                self.logger.info(f"Deploying to batch {i//batch_size + 1} ({len(batch)} devices)")
                
                # Deploy to current batch
                batch_success = self._deploy_to_device_batch(
                    plan.firmware_version,
                    batch,
                    execution
                )
                
                if not batch_success:
                    return False
                
                # Update progress
                execution.progress = ((i + len(batch)) / len(devices)) * 100
                
                # Wait between batches
                time.sleep(5)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Rolling deployment failed: {e}")
            return False
    
    def _execute_immediate_deployment(self, execution: DeploymentExecution) -> bool:
        """Execute immediate deployment"""
        try:
            plan = execution.plan
            execution.current_stage = "immediate_deployment"
            
            # Deploy immediately to all targets
            deployment_success = self._deploy_to_environment(
                plan.firmware_version,
                plan.target_environment,
                execution
            )
            
            if not deployment_success:
                return False
            
            execution.progress = 100.0
            return True
            
        except Exception as e:
            self.logger.error(f"Immediate deployment failed: {e}")
            return False
    
    def _deploy_to_environment(self, firmware_version: str, environment: str, execution: DeploymentExecution) -> bool:
        """Deploy firmware to specific environment"""
        try:
            # Get environment configuration
            env_config = self.environments.get(environment)
            if not env_config:
                return False
            
            # Get device list
            devices = self._get_target_devices(execution.plan.device_filters, environment)
            execution.devices_targeted = len(devices)
            
            # Deploy to all devices
            return self._deploy_to_device_batch(firmware_version, devices, execution)
            
        except Exception as e:
            self.logger.error(f"Environment deployment failed: {e}")
            return False
    
    def _deploy_to_canary_group(self, firmware_version: str, percentage: int, execution: DeploymentExecution) -> bool:
        """Deploy to canary group"""
        try:
            # Get all target devices
            all_devices = self._get_target_devices(execution.plan.device_filters, execution.plan.target_environment)
            
            # Select canary devices
            canary_count = max(1, (len(all_devices) * percentage) // 100)
            canary_devices = all_devices[:canary_count]
            
            execution.devices_targeted = len(canary_devices)
            
            # Deploy to canary devices
            return self._deploy_to_device_batch(firmware_version, canary_devices, execution)
            
        except Exception as e:
            self.logger.error(f"Canary deployment failed: {e}")
            return False
    
    def _deploy_to_device_batch(self, firmware_version: str, devices: List[str], execution: DeploymentExecution) -> bool:
        """Deploy firmware to a batch of devices"""
        try:
            # This would integrate with the batch flashing system
            # For now, simulate the deployment
            
            for device in devices:
                try:
                    # Simulate device deployment
                    self.logger.info(f"Deploying {firmware_version} to {device}")
                    time.sleep(1)  # Simulate deployment time
                    
                    # Simulate success/failure
                    if device.endswith("_fail"):  # Simulate failure for testing
                        execution.devices_failed += 1
                    else:
                        execution.devices_successful += 1
                    
                except Exception as e:
                    self.logger.error(f"Failed to deploy to {device}: {e}")
                    execution.devices_failed += 1
            
            # Check success rate
            total_devices = execution.devices_successful + execution.devices_failed
            if total_devices > 0:
                success_rate = (execution.devices_successful / total_devices) * 100
                
                # Get minimum success rate from rollback criteria
                min_success_rate = execution.plan.rollback_criteria.get("min_success_rate", 80)
                
                if success_rate < min_success_rate:
                    self.logger.error(f"Success rate ({success_rate:.1f}%) below threshold ({min_success_rate}%)")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Device batch deployment failed: {e}")
            return False
    
    def _get_target_devices(self, filters: Dict[str, Any], environment: str) -> List[str]:
        """Get list of target devices based on filters"""
        # This would integrate with the device service to get actual device list
        # For now, simulate device list
        
        base_devices = [
            f"ESP32_{i:03d}" for i in range(1, 101)
        ]
        
        # Apply filters
        filtered_devices = base_devices
        
        if filters.get("device_type"):
            filtered_devices = [d for d in filtered_devices if d.startswith(filters["device_type"])]
        
        if filters.get("limit"):
            filtered_devices = filtered_devices[:filters["limit"]]
        
        return filtered_devices
    
    def _run_deployment_check(self, check: str, execution: DeploymentExecution) -> bool:
        """Run deployment check"""
        try:
            self.logger.info(f"Running deployment check: {check}")
            
            # Simulate check execution
            time.sleep(2)
            
            # Simulate check results
            if check == "fail_test":  # For testing
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Deployment check failed: {e}")
            return False
    
    def _run_validation_test(self, test: str, execution: DeploymentExecution) -> bool:
        """Run validation test"""
        try:
            self.logger.info(f"Running validation test: {test}")
            
            # Simulate test execution
            time.sleep(5)
            
            # Simulate test results
            if test == "fail_test":  # For testing
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Validation test failed: {e}")
            return False
    
    def _handle_deployment_failure(self, execution: DeploymentExecution):
        """Handle deployment failure"""
        plan = execution.plan
        
        # Move to history
        self.deployment_history.append(execution)
        if execution.execution_id in self.active_deployments:
            del self.active_deployments[execution.execution_id]
        
        # Check if auto-rollback is enabled
        target_env = self.environments.get(plan.target_environment)
        if target_env and target_env.auto_rollback:
            self.logger.info(f"Initiating auto-rollback for {execution.execution_id}")
            rollback_id = self._initiate_rollback(execution)
            if rollback_id:
                execution.rollback_execution_id = rollback_id
        
        # Send failure notification
        message = f"Deployment '{plan.name}' failed: {execution.error_message}"
        self._send_notifications(plan.target_environment, message, "error")
    
    def _initiate_rollback(self, failed_execution: DeploymentExecution) -> Optional[str]:
        """Initiate rollback deployment"""
        try:
            # Create rollback plan
            rollback_plan_data = {
                "name": f"Rollback - {failed_execution.plan.name}",
                "description": f"Automatic rollback for failed deployment {failed_execution.execution_id}",
                "firmware_version": "previous",  # This would be the previous version
                "source_environment": failed_execution.plan.target_environment,
                "target_environment": failed_execution.plan.target_environment,
                "strategy": "immediate",
                "created_by": "system",
                "device_filters": failed_execution.plan.device_filters
            }
            
            rollback_plan = self.create_deployment_plan(rollback_plan_data)
            
            # Auto-approve rollback
            self.approve_deployment_plan(rollback_plan.plan_id, "system")
            
            # Execute rollback
            rollback_execution_id = self.execute_deployment_plan(rollback_plan.plan_id)
            
            return rollback_execution_id
            
        except Exception as e:
            self.logger.error(f"Rollback initiation failed: {e}")
            return None
    
    def _send_notifications(self, environment: str, message: str, level: str):
        """Send notifications for deployment events"""
        env_config = self.environments.get(environment)
        if not env_config:
            return
        
        for channel in env_config.notification_channels:
            self.notification_manager.send_notification(channel, message, level)
    
    def _monitoring_worker(self):
        """Background monitoring worker"""
        while True:
            try:
                # Monitor active deployments
                for execution_id, execution in list(self.active_deployments.items()):
                    # Check for timeout
                    if execution.started_at:
                        elapsed = (datetime.now() - execution.started_at).total_seconds()
                        if elapsed > 3600:  # 1 hour timeout
                            self.logger.warning(f"Deployment {execution_id} timed out")
                            execution.status = DeploymentStatus.FAILED
                            execution.error_message = "Deployment timed out"
                            self._handle_deployment_failure(execution)
                
                # Check environment health
                for env_name, environment in self.environments.items():
                    if environment.health_check_url:
                        health_results = self.health_checker.check_system_health(environment)
                        if health_results["overall_status"] != "healthy":
                            self.logger.warning(f"Environment {env_name} health check failed")
                
                # Clean up old history
                self._cleanup_old_history()
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Monitoring worker error: {e}")
                time.sleep(60)
    
    def _cleanup_old_history(self):
        """Clean up old deployment history"""
        try:
            cutoff_date = datetime.now() - timedelta(days=30)
            self.deployment_history = [
                execution for execution in self.deployment_history
                if execution.started_at > cutoff_date
            ]
        except Exception as e:
            self.logger.error(f"History cleanup failed: {e}")
    
    def cancel_deployment(self, execution_id: str) -> bool:
        """Cancel active deployment"""
        if execution_id not in self.active_deployments:
            return False
        
        execution = self.active_deployments[execution_id]
        execution.status = DeploymentStatus.CANCELLED
        execution.completed_at = datetime.now()
        
        # Move to history
        self.deployment_history.append(execution)
        del self.active_deployments[execution_id]
        
        self.logger.info(f"Deployment {execution_id} cancelled")
        
        # Send notification
        message = f"Deployment '{execution.plan.name}' has been cancelled"
        self._send_notifications(execution.plan.target_environment, message, "warning")
        
        return True
    
    def get_deployment_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get deployment status"""
        execution = self.active_deployments.get(execution_id)
        if not execution:
            # Check history
            for hist_execution in self.deployment_history:
                if hist_execution.execution_id == execution_id:
                    execution = hist_execution
                    break
        
        if not execution:
            return None
        
        return {
            "execution_id": execution.execution_id,
            "plan_name": execution.plan.name,
            "status": execution.status.value,
            "progress": execution.progress,
            "current_stage": execution.current_stage,
            "started_at": execution.started_at.isoformat(),
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "devices_targeted": execution.devices_targeted,
            "devices_successful": execution.devices_successful,
            "devices_failed": execution.devices_failed,
            "error_message": execution.error_message,
            "rollback_execution_id": execution.rollback_execution_id
        }
    
    def list_deployments(self) -> List[Dict[str, Any]]:
        """List all deployments"""
        all_deployments = []
        
        # Active deployments
        for execution in self.active_deployments.values():
            all_deployments.append({
                "execution_id": execution.execution_id,
                "plan_name": execution.plan.name,
                "status": execution.status.value,
                "progress": execution.progress,
                "started_at": execution.started_at.isoformat(),
                "target_environment": execution.plan.target_environment
            })
        
        # Historical deployments
        for execution in self.deployment_history:
            all_deployments.append({
                "execution_id": execution.execution_id,
                "plan_name": execution.plan.name,
                "status": execution.status.value,
                "progress": execution.progress,
                "started_at": execution.started_at.isoformat(),
                "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
                "target_environment": execution.plan.target_environment
            })
        
        return sorted(all_deployments, key=lambda x: x["started_at"], reverse=True)
    
    def get_environment_status(self, environment_name: str) -> Optional[Dict[str, Any]]:
        """Get environment status"""
        if environment_name not in self.environments:
            return None
        
        environment = self.environments[environment_name]
        health_results = self.health_checker.check_system_health(environment)
        
        return {
            "environment": environment_name,
            "stage": environment.stage.value,
            "health_status": health_results["overall_status"],
            "health_details": health_results["checks"],
            "active_deployments": len([
                exec for exec in self.active_deployments.values()
                if exec.plan.target_environment == environment_name
            ])
        }
    
    def shutdown(self):
        """Shutdown the deployment manager"""
        self.logger.info("Shutting down deployment manager")
        
        # Cancel all active deployments
        for execution_id in list(self.active_deployments.keys()):
            self.cancel_deployment(execution_id)

def main():
    """Main function for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Production Deployment Manager')
    parser.add_argument('--config', '-c', default='deployment-config.yaml', help='Configuration file')
    parser.add_argument('--create-plan', help='Create deployment plan from JSON file')
    parser.add_argument('--execute-plan', help='Execute deployment plan by ID')
    parser.add_argument('--list-deployments', action='store_true', help='List all deployments')
    parser.add_argument('--status', help='Get deployment status by ID')
    parser.add_argument('--environment-status', help='Get environment status')
    
    args = parser.parse_args()
    
    # Create manager
    manager = ProductionDeploymentManager(args.config)
    
    try:
        if args.create_plan:
            with open(args.create_plan, 'r') as f:
                plan_data = json.load(f)
            
            plan = manager.create_deployment_plan(plan_data)
            print(f"Created deployment plan: {plan.plan_id}")
        
        elif args.execute_plan:
            execution_id = manager.execute_deployment_plan(args.execute_plan)
            if execution_id:
                print(f"Started deployment execution: {execution_id}")
            else:
                print("Failed to start deployment")
        
        elif args.list_deployments:
            deployments = manager.list_deployments()
            print("Deployments:")
            for deployment in deployments:
                print(f"  {deployment['execution_id']}: {deployment['plan_name']} ({deployment['status']})")
        
        elif args.status:
            status = manager.get_deployment_status(args.status)
            if status:
                print(json.dumps(status, indent=2))
            else:
                print("Deployment not found")
        
        elif args.environment_status:
            status = manager.get_environment_status(args.environment_status)
            if status:
                print(json.dumps(status, indent=2))
            else:
                print("Environment not found")
        
        else:
            print("Use --help for usage information")
    
    except KeyboardInterrupt:
        print("Interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        manager.shutdown()

if __name__ == "__main__":
    main()