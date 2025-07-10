#!/usr/bin/env python3
"""
Monitoring CLI Tool
Command-line interface for monitoring and alerting system
"""

import os
import sys
import json
import time
import argparse
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, TaskID
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.live import Live
from rich.layout import Layout
import yaml
import requests

# Import the monitoring system
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from monitoring_alerting_system import MonitoringAlertingSystem, AlertSeverity, AlertStatus

console = Console()

class MonitoringCLI:
    """Command-line interface for monitoring and alerting system"""
    
    def __init__(self, config_file: str = "monitoring-config.yaml"):
        self.system = MonitoringAlertingSystem(config_file)
        self.console = Console()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('monitoring-cli.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def show_system_status(self):
        """Show system status"""
        try:
            active_alerts = self.system.get_active_alerts()
            
            # System overview
            console.print(Panel.fit("System Status", style="bold blue"))
            
            table = Table(show_header=False)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="white")
            
            table.add_row("System Health", "Healthy" if len(active_alerts) == 0 else "Warning")
            table.add_row("Active Alerts", str(len(active_alerts)))
            table.add_row("Monitoring Targets", str(len(self.system.monitoring_targets)))
            table.add_row("Alert Rules", str(len(self.system.alert_rules)))
            table.add_row("Health Checks", str(len(self.system.health_checks)))
            
            console.print(table)
            
            # Alert summary by severity
            if active_alerts:
                console.print("\n[bold]Active Alerts by Severity:[/bold]")
                severity_counts = {}
                for alert in active_alerts:
                    severity = alert.rule.severity.value
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                severity_table = Table()
                severity_table.add_column("Severity", style="cyan")
                severity_table.add_column("Count", style="white")
                
                for severity in AlertSeverity:
                    count = severity_counts.get(severity.value, 0)
                    color = {
                        'low': 'green',
                        'medium': 'yellow',
                        'high': 'orange',
                        'critical': 'red'
                    }.get(severity.value, 'white')
                    
                    severity_table.add_row(
                        f"[{color}]{severity.value.upper()}[/{color}]",
                        str(count)
                    )
                
                console.print(severity_table)
            
        except Exception as e:
            console.print(f"[red]Error getting system status: {e}[/red]")
    
    def show_alerts(self, status: str = None, severity: str = None):
        """Show alerts"""
        try:
            if status == 'active':
                alerts = self.system.get_active_alerts()
                alerts_data = []
                for alert in alerts:
                    alerts_data.append({
                        'alert_id': alert.alert_id,
                        'rule_name': alert.rule.name,
                        'severity': alert.rule.severity.value,
                        'value': alert.value,
                        'threshold': alert.rule.threshold,
                        'status': alert.status.value,
                        'triggered_at': alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'message': alert.message
                    })
            else:
                alerts_data = self.system.get_alert_history(24)
            
            # Filter by severity if specified
            if severity:
                alerts_data = [a for a in alerts_data if a.get('severity') == severity]
            
            if not alerts_data:
                console.print("[yellow]No alerts found[/yellow]")
                return
            
            table = Table(title="Alerts")
            table.add_column("Alert ID", style="cyan")
            table.add_column("Rule", style="magenta")
            table.add_column("Severity", style="white")
            table.add_column("Value", style="blue")
            table.add_column("Status", style="green")
            table.add_column("Triggered", style="dim")
            table.add_column("Message", style="white")
            
            for alert in alerts_data:
                severity_color = {
                    'low': 'green',
                    'medium': 'yellow',
                    'high': 'orange',
                    'critical': 'red'
                }.get(alert.get('severity'), 'white')
                
                status_color = {
                    'active': 'red',
                    'acknowledged': 'yellow',
                    'resolved': 'green'
                }.get(alert.get('status'), 'white')
                
                table.add_row(
                    str(alert.get('alert_id', '')),
                    alert.get('rule_name', alert.get('rule_id', '')),
                    f"[{severity_color}]{alert.get('severity', '').upper()}[/{severity_color}]",
                    f"{alert.get('value', 0):.2f}",
                    f"[{status_color}]{alert.get('status', '').upper()}[/{status_color}]",
                    alert.get('triggered_at', ''),
                    alert.get('message', '')[:50] + "..." if len(alert.get('message', '')) > 50 else alert.get('message', '')
                )
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]Error getting alerts: {e}[/red]")
    
    def acknowledge_alert(self, alert_id: str):
        """Acknowledge alert"""
        try:
            self.system.acknowledge_alert(alert_id, "cli_user")
            console.print(f"[green]Alert {alert_id} acknowledged[/green]")
        except Exception as e:
            console.print(f"[red]Error acknowledging alert: {e}[/red]")
    
    def resolve_alert(self, alert_id: str):
        """Resolve alert"""
        try:
            self.system.resolve_alert(alert_id, "cli_user")
            console.print(f"[green]Alert {alert_id} resolved[/green]")
        except Exception as e:
            console.print(f"[red]Error resolving alert: {e}[/red]")
    
    def show_alert_rules(self):
        """Show alert rules"""
        try:
            table = Table(title="Alert Rules")
            table.add_column("Rule ID", style="cyan")
            table.add_column("Name", style="magenta")
            table.add_column("Metric", style="blue")
            table.add_column("Threshold", style="white")
            table.add_column("Severity", style="yellow")
            table.add_column("Enabled", style="green")
            table.add_column("Silenced", style="dim")
            
            for rule_id, rule in self.system.alert_rules.items():
                enabled_text = "Yes" if rule.enabled else "No"
                enabled_color = "green" if rule.enabled else "red"
                
                silenced_text = "Yes" if rule.silenced_until and rule.silenced_until > datetime.utcnow() else "No"
                silenced_color = "yellow" if silenced_text == "Yes" else "white"
                
                severity_color = {
                    'low': 'green',
                    'medium': 'yellow',
                    'high': 'orange',
                    'critical': 'red'
                }.get(rule.severity.value, 'white')
                
                table.add_row(
                    rule_id,
                    rule.name,
                    rule.metric_query,
                    f"{rule.comparison} {rule.threshold}",
                    f"[{severity_color}]{rule.severity.value.upper()}[/{severity_color}]",
                    f"[{enabled_color}]{enabled_text}[/{enabled_color}]",
                    f"[{silenced_color}]{silenced_text}[/{silenced_color}]"
                )
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]Error getting alert rules: {e}[/red]")
    
    def silence_alert_rule(self, rule_id: str, duration_hours: int):
        """Silence alert rule"""
        try:
            self.system.silence_alert_rule(rule_id, duration_hours)
            console.print(f"[green]Alert rule {rule_id} silenced for {duration_hours} hours[/green]")
        except Exception as e:
            console.print(f"[red]Error silencing alert rule: {e}[/red]")
    
    def show_monitoring_targets(self):
        """Show monitoring targets"""
        try:
            table = Table(title="Monitoring Targets")
            table.add_column("Target ID", style="cyan")
            table.add_column("Name", style="magenta")
            table.add_column("Type", style="blue")
            table.add_column("Endpoint", style="white")
            table.add_column("Status", style="green")
            table.add_column("Check Interval", style="dim")
            table.add_column("Enabled", style="yellow")
            
            for target_id, target in self.system.monitoring_targets.items():
                status = "Up" if self.system.get_service_status(target_id) else "Down"
                status_color = "green" if status == "Up" else "red"
                
                enabled_text = "Yes" if target.enabled else "No"
                enabled_color = "green" if target.enabled else "red"
                
                table.add_row(
                    target_id,
                    target.name,
                    target.type,
                    target.endpoint,
                    f"[{status_color}]{status}[/{status_color}]",
                    f"{target.check_interval}s",
                    f"[{enabled_color}]{enabled_text}[/{enabled_color}]"
                )
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]Error getting monitoring targets: {e}[/red]")
    
    def show_health_checks(self):
        """Show health checks"""
        try:
            table = Table(title="Health Checks")
            table.add_column("Check ID", style="cyan")
            table.add_column("Name", style="magenta")
            table.add_column("Target", style="blue")
            table.add_column("Type", style="white")
            table.add_column("Status", style="green")
            table.add_column("Last Check", style="dim")
            table.add_column("Response Time", style="yellow")
            
            for check_id, check in self.system.health_checks.items():
                # Get latest health check result
                health_data = self.system.get_health_check_history(check.target.target_id, 1)
                latest_result = health_data[-1] if health_data else None
                
                if latest_result:
                    status = latest_result['status']
                    last_check = latest_result['timestamp']
                    response_time = f"{latest_result['response_time']:.3f}s" if latest_result['response_time'] else "N/A"
                else:
                    status = "Unknown"
                    last_check = "Never"
                    response_time = "N/A"
                
                status_color = "green" if status == "success" else "red"
                
                table.add_row(
                    check_id,
                    check.name,
                    check.target.name,
                    check.check_type,
                    f"[{status_color}]{status.upper()}[/{status_color}]",
                    last_check,
                    response_time
                )
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]Error getting health checks: {e}[/red]")
    
    def show_metrics(self, metric_name: str = None, hours: int = 24):
        """Show metrics"""
        try:
            if metric_name:
                # Show specific metric data
                data = self.system.get_metrics_data(metric_name, hours)
                
                if not data:
                    console.print(f"[yellow]No data found for metric {metric_name}[/yellow]")
                    return
                
                console.print(f"[bold]Metric: {metric_name}[/bold]")
                console.print(f"Data points: {len(data)}")
                
                if data:
                    values = [d['value'] for d in data]
                    console.print(f"Current: {values[-1]:.2f}")
                    console.print(f"Average: {sum(values) / len(values):.2f}")
                    console.print(f"Min: {min(values):.2f}")
                    console.print(f"Max: {max(values):.2f}")
                    
                    # Show recent values
                    console.print("\n[bold]Recent Values:[/bold]")
                    table = Table()
                    table.add_column("Timestamp", style="cyan")
                    table.add_column("Value", style="white")
                    table.add_column("Labels", style="dim")
                    
                    for point in data[-10:]:  # Show last 10 points
                        labels_str = ', '.join(f"{k}={v}" for k, v in point.get('labels', {}).items())
                        table.add_row(
                            point['timestamp'],
                            f"{point['value']:.2f}",
                            labels_str
                        )
                    
                    console.print(table)
            else:
                # Show metrics summary
                metrics_summary = {
                    'cpu_usage': self.system.get_metric_value('cpu_usage_percent'),
                    'memory_usage': self.system.get_metric_value('memory_usage_percent'),
                    'disk_free': self.system.get_metric_value('disk_free_percent'),
                    'active_alerts': len(self.system.get_active_alerts())
                }
                
                console.print(Panel.fit("Metrics Summary", style="bold green"))
                
                table = Table(show_header=False)
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="white")
                
                for metric, value in metrics_summary.items():
                    if value is not None:
                        if metric in ['cpu_usage', 'memory_usage']:
                            table.add_row(metric.replace('_', ' ').title(), f"{value:.1f}%")
                        elif metric == 'disk_free':
                            table.add_row("Disk Free", f"{value:.1f}%")
                        else:
                            table.add_row(metric.replace('_', ' ').title(), str(value))
                    else:
                        table.add_row(metric.replace('_', ' ').title(), "N/A")
                
                console.print(table)
            
        except Exception as e:
            console.print(f"[red]Error getting metrics: {e}[/red]")
    
    def live_dashboard(self):
        """Show live dashboard"""
        try:
            def generate_dashboard():
                # Create layout
                layout = Layout()
                
                layout.split_column(
                    Layout(name="header", size=3),
                    Layout(name="main"),
                    Layout(name="footer", size=3)
                )
                
                layout["main"].split_row(
                    Layout(name="left"),
                    Layout(name="right")
                )
                
                # Header
                layout["header"].update(
                    Panel("Monitoring Dashboard - Live View", style="bold blue")
                )
                
                # System metrics
                metrics_summary = {
                    'cpu_usage': self.system.get_metric_value('cpu_usage_percent'),
                    'memory_usage': self.system.get_metric_value('memory_usage_percent'),
                    'disk_free': self.system.get_metric_value('disk_free_percent')
                }
                
                metrics_table = Table(title="System Metrics")
                metrics_table.add_column("Metric", style="cyan")
                metrics_table.add_column("Value", style="white")
                
                for metric, value in metrics_summary.items():
                    if value is not None:
                        if metric in ['cpu_usage', 'memory_usage']:
                            metrics_table.add_row(metric.replace('_', ' ').title(), f"{value:.1f}%")
                        elif metric == 'disk_free':
                            metrics_table.add_row("Disk Free", f"{value:.1f}%")
                
                layout["left"].update(metrics_table)
                
                # Active alerts
                active_alerts = self.system.get_active_alerts()
                alerts_table = Table(title="Active Alerts")
                alerts_table.add_column("Rule", style="magenta")
                alerts_table.add_column("Severity", style="white")
                alerts_table.add_column("Value", style="blue")
                
                for alert in active_alerts[:5]:  # Show first 5 alerts
                    severity_color = {
                        'low': 'green',
                        'medium': 'yellow',
                        'high': 'orange',
                        'critical': 'red'
                    }.get(alert.rule.severity.value, 'white')
                    
                    alerts_table.add_row(
                        alert.rule.name,
                        f"[{severity_color}]{alert.rule.severity.value.upper()}[/{severity_color}]",
                        f"{alert.value:.2f}"
                    )
                
                if not active_alerts:
                    alerts_table.add_row("No active alerts", "", "")
                
                layout["right"].update(alerts_table)
                
                # Footer
                layout["footer"].update(
                    Panel(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}", style="dim")
                )
                
                return layout
            
            # Live dashboard
            with Live(generate_dashboard(), refresh_per_second=1) as live:
                try:
                    while True:
                        time.sleep(1)
                        live.update(generate_dashboard())
                except KeyboardInterrupt:
                    console.print("\n[yellow]Dashboard stopped[/yellow]")
                    
        except Exception as e:
            console.print(f"[red]Error running live dashboard: {e}[/red]")
    
    def test_notifications(self, channels: List[str]):
        """Test notification channels"""
        try:
            # Create test alert
            from monitoring_alerting_system import Alert, AlertRule, NotificationChannel
            
            test_rule = AlertRule(
                rule_id='test_rule',
                name='Test Alert',
                description='This is a test alert from CLI',
                metric_query='test_metric',
                threshold=0,
                comparison='>',
                severity=AlertSeverity.LOW,
                duration=0,
                notification_channels=[NotificationChannel(ch) for ch in channels]
            )
            
            test_alert = Alert(
                alert_id='test_alert_cli',
                rule=test_rule,
                value=1,
                status=AlertStatus.ACTIVE,
                triggered_at=datetime.utcnow(),
                message='This is a test alert message from CLI'
            )
            
            # Send test notifications
            self.system.send_alert_notifications(test_alert)
            
            console.print(f"[green]Test notifications sent to: {', '.join(channels)}[/green]")
            
        except Exception as e:
            console.print(f"[red]Error testing notifications: {e}[/red]")
    
    def generate_report(self, report_type: str, days: int = 7):
        """Generate report"""
        try:
            if report_type == 'alerts':
                alerts_data = self.system.get_alert_history(days * 24)
                
                console.print(f"[bold]Alerts Report - Last {days} days[/bold]")
                console.print(f"Total alerts: {len(alerts_data)}")
                
                # Count by severity
                severity_counts = {}
                for severity in AlertSeverity:
                    count = len([a for a in alerts_data if a.get('severity') == severity.value])
                    severity_counts[severity.value] = count
                
                console.print("\n[bold]By Severity:[/bold]")
                for severity, count in severity_counts.items():
                    console.print(f"  {severity.upper()}: {count}")
                
                # Count by status
                status_counts = {}
                for status in AlertStatus:
                    count = len([a for a in alerts_data if a.get('status') == status.value])
                    status_counts[status.value] = count
                
                console.print("\n[bold]By Status:[/bold]")
                for status, count in status_counts.items():
                    console.print(f"  {status.upper()}: {count}")
                
            elif report_type == 'performance':
                cpu_data = self.system.get_metrics_data('cpu_usage_percent', days * 24)
                memory_data = self.system.get_metrics_data('memory_usage_percent', days * 24)
                
                console.print(f"[bold]Performance Report - Last {days} days[/bold]")
                
                if cpu_data:
                    cpu_values = [d['value'] for d in cpu_data]
                    console.print(f"CPU Usage - Avg: {sum(cpu_values) / len(cpu_values):.1f}%, Peak: {max(cpu_values):.1f}%")
                
                if memory_data:
                    memory_values = [d['value'] for d in memory_data]
                    console.print(f"Memory Usage - Avg: {sum(memory_values) / len(memory_values):.1f}%, Peak: {max(memory_values):.1f}%")
                
        except Exception as e:
            console.print(f"[red]Error generating report: {e}[/red]")
    
    def cleanup_old_data(self, days: int = 30):
        """Cleanup old data"""
        try:
            if Confirm.ask(f"Delete data older than {days} days?"):
                self.system.cleanup_old_data()
                console.print("[green]Old data cleaned up successfully[/green]")
        except Exception as e:
            console.print(f"[red]Error cleaning up data: {e}[/red]")

def main():
    """Main CLI function"""
    cli = MonitoringCLI()
    
    try:
        # Create argument parser
        parser = argparse.ArgumentParser(description='Monitoring CLI Tool')
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Status command
        status_parser = subparsers.add_parser('status', help='Show system status')
        
        # Alerts commands
        alerts_parser = subparsers.add_parser('alerts', help='Alert management')
        alerts_parser.add_argument('action', choices=['list', 'ack', 'resolve'], help='Alert action')
        alerts_parser.add_argument('--status', choices=['active', 'all'], default='active', help='Alert status filter')
        alerts_parser.add_argument('--severity', choices=['low', 'medium', 'high', 'critical'], help='Severity filter')
        alerts_parser.add_argument('--alert-id', help='Alert ID for ack/resolve')
        
        # Alert rules commands
        rules_parser = subparsers.add_parser('rules', help='Alert rules management')
        rules_parser.add_argument('action', choices=['list', 'silence'], help='Rules action')
        rules_parser.add_argument('--rule-id', help='Rule ID')
        rules_parser.add_argument('--duration', type=int, default=1, help='Silence duration in hours')
        
        # Targets command
        targets_parser = subparsers.add_parser('targets', help='Show monitoring targets')
        
        # Health checks command
        health_parser = subparsers.add_parser('health', help='Show health checks')
        
        # Metrics commands
        metrics_parser = subparsers.add_parser('metrics', help='Metrics management')
        metrics_parser.add_argument('--metric', help='Specific metric name')
        metrics_parser.add_argument('--hours', type=int, default=24, help='Time range in hours')
        
        # Dashboard command
        dashboard_parser = subparsers.add_parser('dashboard', help='Live dashboard')
        
        # Notifications command
        notify_parser = subparsers.add_parser('notify', help='Test notifications')
        notify_parser.add_argument('--channels', nargs='+', default=['email'], help='Notification channels')
        
        # Reports command
        report_parser = subparsers.add_parser('report', help='Generate reports')
        report_parser.add_argument('type', choices=['alerts', 'performance'], help='Report type')
        report_parser.add_argument('--days', type=int, default=7, help='Number of days')
        
        # Cleanup command
        cleanup_parser = subparsers.add_parser('cleanup', help='Cleanup old data')
        cleanup_parser.add_argument('--days', type=int, default=30, help='Data retention days')
        
        # Parse arguments
        args = parser.parse_args()
        
        if not args.command:
            parser.print_help()
            return
        
        # Execute commands
        if args.command == 'status':
            cli.show_system_status()
        
        elif args.command == 'alerts':
            if args.action == 'list':
                cli.show_alerts(args.status, args.severity)
            elif args.action == 'ack':
                if args.alert_id:
                    cli.acknowledge_alert(args.alert_id)
                else:
                    console.print("[red]--alert-id is required for acknowledge[/red]")
            elif args.action == 'resolve':
                if args.alert_id:
                    cli.resolve_alert(args.alert_id)
                else:
                    console.print("[red]--alert-id is required for resolve[/red]")
        
        elif args.command == 'rules':
            if args.action == 'list':
                cli.show_alert_rules()
            elif args.action == 'silence':
                if args.rule_id:
                    cli.silence_alert_rule(args.rule_id, args.duration)
                else:
                    console.print("[red]--rule-id is required for silence[/red]")
        
        elif args.command == 'targets':
            cli.show_monitoring_targets()
        
        elif args.command == 'health':
            cli.show_health_checks()
        
        elif args.command == 'metrics':
            cli.show_metrics(args.metric, args.hours)
        
        elif args.command == 'dashboard':
            cli.live_dashboard()
        
        elif args.command == 'notify':
            cli.test_notifications(args.channels)
        
        elif args.command == 'report':
            cli.generate_report(args.type, args.days)
        
        elif args.command == 'cleanup':
            cli.cleanup_old_data(args.days)
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        cli.system.shutdown()

if __name__ == "__main__":
    main()