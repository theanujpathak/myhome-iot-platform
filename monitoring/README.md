# Monitoring and Alerting System

A comprehensive monitoring and alerting system for IoT device platform with real-time metrics collection, intelligent alerting, and multiple notification channels.

## Features

### Core Capabilities
- **Real-time Monitoring**: System metrics, service health, and custom metrics
- **Intelligent Alerting**: Rule-based alerts with multiple severity levels
- **Multiple Notification Channels**: Email, Slack, SMS, webhooks, PagerDuty
- **Health Checks**: HTTP, TCP, ping, and custom health checks
- **Prometheus Integration**: Metrics export and collection
- **Multiple Interfaces**: CLI, Web dashboard, and REST API

### Advanced Features
- **Alert Management**: Acknowledgment, resolution, and silencing
- **Escalation Policies**: Automated alert escalation based on severity
- **Metric Retention**: Configurable data retention and cleanup
- **Dashboard**: Real-time web dashboard with charts and graphs
- **Audit Logging**: Comprehensive logging and audit trails
- **Auto-discovery**: Automatic service and device discovery

## Architecture

```
Monitoring and Alerting System
├── monitoring-alerting-system.py      # Core monitoring engine
├── monitoring-api.py                  # REST API service
├── monitoring-cli.py                  # Command-line interface
├── monitoring-dashboard.html          # Web dashboard
├── monitoring-config.yaml             # Configuration file
├── requirements.txt                   # Python dependencies
└── README.md                          # This file
```

## Quick Start

### Prerequisites

1. **Python 3.8+**
2. **SQLite** (for metrics storage)
3. **SMTP Server** (for email notifications)
4. **Slack Webhook** (optional, for Slack notifications)
5. **Redis** (optional, for caching)

### Installation

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure the system**:
   - Edit `monitoring-config.yaml` to match your environment
   - Update notification settings
   - Configure monitoring targets

3. **Initialize the database**:
   ```bash
   python monitoring-alerting-system.py --daemon
   ```

4. **Start the API service**:
   ```bash
   python monitoring-api.py
   ```

### Basic Usage

#### CLI Interface

1. **Show system status**:
   ```bash
   python monitoring-cli.py status
   ```

2. **List active alerts**:
   ```bash
   python monitoring-cli.py alerts list --status active
   ```

3. **Acknowledge alert**:
   ```bash
   python monitoring-cli.py alerts ack --alert-id ALERT_ID
   ```

4. **Show live dashboard**:
   ```bash
   python monitoring-cli.py dashboard
   ```

#### Web Dashboard

1. **Start API service**:
   ```bash
   python monitoring-api.py
   ```

2. **Open web dashboard**:
   ```bash
   open monitoring-dashboard.html
   ```

#### API Usage

```bash
# Get system status
curl -H "X-API-Key: monitoring-api-key-1" http://localhost:5002/api/status

# List active alerts
curl -H "X-API-Key: monitoring-api-key-1" http://localhost:5002/api/alerts?status=active

# Acknowledge alert
curl -X POST -H "X-API-Key: monitoring-api-key-1" \
  -H "Content-Type: application/json" \
  -d '{"acknowledged_by": "admin"}' \
  http://localhost:5002/api/alerts/ALERT_ID/acknowledge
```

## Configuration

### Main Configuration (`monitoring-config.yaml`)

```yaml
# Global settings
global:
  organization: "MyHome IoT"
  project: "Device Management Platform"
  environment: "production"

# Metrics collection
metrics:
  collection_interval: 60
  retention_days: 30
  prometheus_port: 8080

# Alerting
alerting:
  evaluation_interval: 60
  notification_timeout: 300
  max_retries: 3

# Notifications
notifications:
  email:
    enabled: true
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    from_email: "alerts@company.com"
    recipients:
      - "admin@company.com"
  
  slack:
    enabled: true
    webhook_url: "https://hooks.slack.com/services/..."
    channel: "#alerts"
```

### Monitoring Targets

```yaml
monitoring_targets:
  device_service:
    name: "Device Service"
    type: "service"
    endpoint: "http://localhost:3002/health"
    check_interval: 30
    timeout: 10
    
  database:
    name: "PostgreSQL Database"
    type: "database"
    endpoint: "localhost:5432"
    check_interval: 60
    timeout: 5
```

### Alert Rules

```yaml
alert_rules:
  service_down:
    name: "Service Down"
    description: "Service is not responding"
    metric_query: "service_up"
    threshold: 1
    comparison: "<"
    severity: "critical"
    duration: 60
    notification_channels:
      - "email"
      - "slack"
      
  high_cpu_usage:
    name: "High CPU Usage"
    description: "CPU usage is above 80%"
    metric_query: "cpu_usage_percent"
    threshold: 80
    comparison: ">"
    severity: "high"
    duration: 300
    notification_channels:
      - "email"
```

## Metrics

### System Metrics

- **CPU Usage**: `cpu_usage_percent`
- **Memory Usage**: `memory_usage_percent`
- **Disk Usage**: `disk_usage_percent`
- **Disk Free**: `disk_free_percent`

### Service Metrics

- **Service Up**: `service_up`
- **Service Response Time**: `service_response_time_seconds`
- **Service Requests**: `service_requests_total`

### Device Metrics

- **Device Count**: `device_count`
- **Device Connectivity**: `device_connectivity`
- **Firmware Version Distribution**: `firmware_version_distribution`

### Deployment Metrics

- **Deployment Success Rate**: `deployment_success_rate`
- **Deployment Duration**: `deployment_duration_seconds`
- **Deployment Failures**: `deployment_failures_total`

### Alert Metrics

- **Active Alerts**: `active_alerts`
- **Alert Notifications**: `alert_notifications_total`

## Alert Rules

### Rule Definition

```yaml
alert_rule:
  rule_id: "unique_rule_id"
  name: "Human Readable Name"
  description: "Detailed description"
  metric_query: "metric_name"
  threshold: 80
  comparison: ">"  # >, <, >=, <=, ==, !=
  severity: "high"  # low, medium, high, critical
  duration: 300  # seconds
  notification_channels:
    - "email"
    - "slack"
  enabled: true
```

### Alert Severities

- **Low**: Minor issues that don't require immediate attention
- **Medium**: Issues that should be addressed within hours
- **High**: Issues that require prompt attention
- **Critical**: Issues that require immediate attention

### Alert States

- **Active**: Alert is currently firing
- **Acknowledged**: Alert has been acknowledged by someone
- **Resolved**: Alert condition is no longer true
- **Silenced**: Alert is temporarily suppressed

## Health Checks

### HTTP Health Check

```yaml
health_check:
  check_id: "service_health"
  name: "Service Health Check"
  check_type: "http"
  config:
    method: "GET"
    expected_status: 200
    expected_content: "healthy"
```

### TCP Health Check

```yaml
health_check:
  check_id: "database_health"
  name: "Database Health Check"
  check_type: "tcp"
  config:
    host: "localhost"
    port: 5432
```

### Ping Health Check

```yaml
health_check:
  check_id: "network_health"
  name: "Network Health Check"
  check_type: "ping"
  config:
    host: "8.8.8.8"
    packet_count: 3
```

### Custom Health Check

```yaml
health_check:
  check_id: "custom_health"
  name: "Custom Health Check"
  check_type: "custom"
  config:
    command: "/usr/local/bin/check_script.sh"
    timeout: 60
```

## Notifications

### Email Notifications

```yaml
notifications:
  email:
    enabled: true
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    use_tls: true
    username: "alerts@company.com"
    password: "app_password"
    from_email: "alerts@company.com"
    recipients:
      - "admin@company.com"
      - "devops@company.com"
```

### Slack Notifications

```yaml
notifications:
  slack:
    enabled: true
    webhook_url: "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
    channel: "#alerts"
    username: "MonitoringBot"
    icon_emoji: ":warning:"
    mention_channel: true
```

### SMS Notifications

```yaml
notifications:
  sms:
    enabled: true
    provider: "twilio"
    account_sid: "YOUR_TWILIO_ACCOUNT_SID"
    auth_token: "YOUR_TWILIO_AUTH_TOKEN"
    from_number: "+1234567890"
    recipients:
      - "+1987654321"
```

### Webhook Notifications

```yaml
notifications:
  webhook:
    enabled: true
    url: "https://api.company.com/webhook/alerts"
    method: "POST"
    headers:
      Content-Type: "application/json"
      Authorization: "Bearer YOUR_TOKEN"
    timeout: 30
```

### PagerDuty Notifications

```yaml
notifications:
  pagerduty:
    enabled: true
    integration_key: "YOUR_PAGERDUTY_INTEGRATION_KEY"
    severity_mapping:
      low: "info"
      medium: "warning"
      high: "error"
      critical: "critical"
```

## API Reference

### Authentication

All API endpoints require authentication via API key:

```bash
curl -H "X-API-Key: monitoring-api-key-1" ...
```

### System Status

```http
GET /api/status
```

Response:
```json
{
  "success": true,
  "status": {
    "system_health": "healthy",
    "active_alerts": 0,
    "monitoring_targets": 5,
    "alert_rules": 10,
    "health_checks": 5
  }
}
```

### Metrics

```http
GET /api/metrics
GET /api/metrics?metric=cpu_usage_percent
GET /api/metrics?metric=cpu_usage_percent&hours=24
```

### Alerts

```http
# List alerts
GET /api/alerts
GET /api/alerts?status=active
GET /api/alerts?severity=critical

# Acknowledge alert
POST /api/alerts/{alert_id}/acknowledge
{
  "acknowledged_by": "admin"
}

# Resolve alert
POST /api/alerts/{alert_id}/resolve
{
  "resolved_by": "admin"
}
```

### Alert Rules

```http
# List alert rules
GET /api/alert-rules

# Silence alert rule
POST /api/alert-rules/{rule_id}/silence
{
  "duration_hours": 1
}

# Enable/disable alert rule
POST /api/alert-rules/{rule_id}/enable
POST /api/alert-rules/{rule_id}/disable
```

### Health Checks

```http
# List health checks
GET /api/health-checks

# Run health checks
POST /api/health-checks/run

# Get target health history
GET /api/targets/{target_id}/health?hours=24
```

### Notifications

```http
# List notification history
GET /api/notifications?hours=24

# Test notifications
POST /api/notifications/test
{
  "channels": ["email", "slack"]
}
```

## CLI Commands

### Status Commands

```bash
# System status
python monitoring-cli.py status

# Live dashboard
python monitoring-cli.py dashboard
```

### Alert Commands

```bash
# List alerts
python monitoring-cli.py alerts list
python monitoring-cli.py alerts list --status active --severity critical

# Acknowledge alert
python monitoring-cli.py alerts ack --alert-id ALERT_ID

# Resolve alert
python monitoring-cli.py alerts resolve --alert-id ALERT_ID
```

### Alert Rules Commands

```bash
# List alert rules
python monitoring-cli.py rules list

# Silence rule
python monitoring-cli.py rules silence --rule-id RULE_ID --duration 2
```

### Monitoring Commands

```bash
# List monitoring targets
python monitoring-cli.py targets

# Show health checks
python monitoring-cli.py health

# Show metrics
python monitoring-cli.py metrics
python monitoring-cli.py metrics --metric cpu_usage_percent --hours 24
```

### Notification Commands

```bash
# Test notifications
python monitoring-cli.py notify --channels email slack

# Generate reports
python monitoring-cli.py report alerts --days 7
python monitoring-cli.py report performance --days 30
```

### Maintenance Commands

```bash
# Cleanup old data
python monitoring-cli.py cleanup --days 30
```

## Web Dashboard

The web dashboard provides a real-time view of your monitoring system:

### Features

- **System Overview**: Key metrics and health indicators
- **Alert Management**: View, acknowledge, and resolve alerts
- **Metrics Visualization**: Charts and graphs for system metrics
- **Health Check Status**: Real-time health check results
- **Target Management**: Monitor configured targets
- **Log Viewer**: View system logs and events

### Navigation

- **Overview**: System summary and key metrics
- **Alerts**: Alert management and history
- **Metrics**: Detailed metrics and charts
- **Health**: Health check status and history
- **Targets**: Monitoring target configuration
- **Logs**: System logs and events

### Auto-refresh

The dashboard automatically refreshes every 30 seconds. You can:

- Toggle auto-refresh on/off
- Change refresh interval
- Manually refresh data
- Export data to JSON

## Prometheus Integration

The monitoring system exports metrics in Prometheus format:

```bash
# Metrics endpoint
curl http://localhost:8080/metrics
```

### Grafana Integration

You can visualize metrics using Grafana:

1. Add Prometheus data source pointing to `http://localhost:8080`
2. Import dashboards or create custom ones
3. Set up alerting rules in Grafana (optional)

## Performance Optimization

### Database Optimization

```yaml
database:
  retention_days: 30
  cleanup_interval: 3600
  batch_size: 1000
```

### Caching

```yaml
performance:
  cache_enabled: true
  cache_type: "memory"
  cache_size: "128MB"
  cache_ttl: 300
```

### Threading

```yaml
performance:
  max_worker_threads: 20
  thread_pool_size: 10
```

## Security

### Authentication

```yaml
security:
  authentication:
    enabled: true
    method: "api_key"
    api_keys:
      - "monitoring-api-key-1"
      - "monitoring-api-key-2"
```

### Authorization

```yaml
security:
  authorization:
    enabled: true
    roles:
      admin:
        - "view_all"
        - "manage_alerts"
        - "configure_system"
      viewer:
        - "view_metrics"
        - "view_alerts"
```

### Encryption

```yaml
security:
  encryption:
    enabled: true
    algorithm: "AES-256-GCM"
    key_rotation_days: 90
```

## Troubleshooting

### Common Issues

1. **Database Connection Issues**:
   - Check database file permissions
   - Verify disk space
   - Check database locks

2. **Notification Failures**:
   - Verify SMTP settings
   - Check webhook URLs
   - Validate API keys

3. **High CPU Usage**:
   - Reduce collection interval
   - Optimize alert rules
   - Check for infinite loops

4. **Memory Issues**:
   - Reduce data retention
   - Enable cleanup
   - Optimize queries

### Debug Mode

Enable debug logging:

```yaml
logging:
  level: "DEBUG"
  detailed_logging: true
  verbose_output: true
```

### Log Analysis

```bash
# View logs
tail -f monitoring.log

# Filter errors
grep "ERROR" monitoring.log

# Monitor specific component
grep "health_check" monitoring.log
```

## Best Practices

### Alert Rule Design

1. **Avoid Alert Fatigue**: Set appropriate thresholds
2. **Use Meaningful Names**: Clear, descriptive rule names
3. **Set Proper Durations**: Avoid flapping alerts
4. **Test Rules**: Validate rules before deployment
5. **Document Rules**: Add descriptions and context

### Monitoring Strategy

1. **Monitor What Matters**: Focus on critical metrics
2. **Set SLOs**: Define service level objectives
3. **Regular Reviews**: Review and update rules
4. **Incident Response**: Have clear escalation procedures
5. **Documentation**: Maintain runbooks and procedures

### Performance Tuning

1. **Optimize Queries**: Use efficient database queries
2. **Batch Operations**: Process data in batches
3. **Cache Results**: Cache frequently accessed data
4. **Resource Limits**: Set appropriate resource limits
5. **Monitoring Overhead**: Monitor the monitoring system

### Security Practices

1. **API Key Rotation**: Regularly rotate API keys
2. **Access Control**: Implement proper access controls
3. **Secure Communications**: Use TLS/SSL
4. **Audit Logging**: Log all administrative actions
5. **Regular Updates**: Keep dependencies updated

## Integration

### CI/CD Integration

```yaml
# GitHub Actions
- name: Run Monitoring Tests
  run: |
    python monitoring-cli.py status
    python monitoring-cli.py health
```

### Docker Integration

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "monitoring-alerting-system.py", "--daemon"]
```

### Kubernetes Integration

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: monitoring-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: monitoring-system
  template:
    metadata:
      labels:
        app: monitoring-system
    spec:
      containers:
      - name: monitoring-system
        image: monitoring-system:latest
        ports:
        - containerPort: 5002
        - containerPort: 8080
```

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
- Review system logs
- Contact development team

## Changelog

### v1.0.0
- Initial release
- Core monitoring and alerting functionality
- Multiple notification channels
- Web dashboard and CLI
- Prometheus integration
- Health checks and metrics collection
- Alert management and escalation
- API for external integration

### v1.1.0 (Planned)
- Advanced analytics and ML-based anomaly detection
- Enhanced dashboard with more visualizations
- Mobile app for alert management
- Advanced reporting and analytics
- Integration with more external services
- Performance optimizations
- Enhanced security features