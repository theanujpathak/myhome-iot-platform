#!/usr/bin/env python3
"""
Production Deployment CLI
Command-line interface for deployment automation
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
import yaml
import requests

# Import the deployment manager
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from production_deployment_manager import ProductionDeploymentManager

console = Console()

class DeploymentCLI:
    """Command-line interface for deployment automation"""
    
    def __init__(self, config_file: str = "deployment-config.yaml"):
        self.manager = ProductionDeploymentManager(config_file)
        self.console = Console()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('deployment-cli.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def list_environments(self):
        """List all environments"""
        environments = list(self.manager.environments.values())
        
        if not environments:
            console.print("[yellow]No environments configured[/yellow]")
            return
        
        table = Table(title="Deployment Environments")
        table.add_column("Name", style="cyan")
        table.add_column("Stage", style="magenta")
        table.add_column("Description", style="green")
        table.add_column("Approval Required", style="yellow")
        table.add_column("Auto Rollback", style="blue")
        table.add_column("Device Groups", style="dim")
        
        for env in environments:
            table.add_row(
                env.name,
                env.stage.value,
                env.description,
                "Yes" if env.approval_required else "No",
                "Yes" if env.auto_rollback else "No",
                ", ".join(env.device_groups)
            )
        
        console.print(table)
    
    def list_deployment_plans(self):
        """List all deployment plans"""
        plans = list(self.manager.deployment_plans.values())
        
        if not plans:
            console.print("[yellow]No deployment plans found[/yellow]")
            return
        
        table = Table(title="Deployment Plans")
        table.add_column("Plan ID", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Firmware Version", style="green")
        table.add_column("Source → Target", style="blue")
        table.add_column("Strategy", style="yellow")
        table.add_column("Status", style="white")
        table.add_column("Created", style="dim")
        
        for plan in plans:
            status = "Approved" if plan.approved_by else "Pending"
            status_color = "green" if plan.approved_by else "yellow"
            
            table.add_row(
                plan.plan_id,
                plan.name,
                plan.firmware_version,
                f"{plan.source_environment} → {plan.target_environment}",
                plan.strategy.value,
                f"[{status_color}]{status}[/{status_color}]",
                plan.created_at.strftime("%Y-%m-%d %H:%M")
            )
        
        console.print(table)
    
    def create_deployment_plan_interactive(self):
        """Interactive deployment plan creation"""
        console.print(Panel.fit("Create Deployment Plan", style="bold blue"))
        
        # Get basic info
        name = Prompt.ask("Plan name")
        description = Prompt.ask("Description", default="")
        firmware_version = Prompt.ask("Firmware version")
        
        # Get environments
        env_names = list(self.manager.environments.keys())
        console.print(f"Available environments: {', '.join(env_names)}")
        
        source_env = Prompt.ask("Source environment", choices=env_names)
        target_env = Prompt.ask("Target environment", choices=env_names)
        
        # Get strategy
        strategies = ["blue_green", "canary", "rolling", "immediate"]
        strategy = Prompt.ask("Deployment strategy", choices=strategies, default="rolling")
        
        # Get rollout settings
        rollout_percentage = int(Prompt.ask("Rollout percentage", default="100"))
        
        if strategy == "canary":
            canary_percentage = int(Prompt.ask("Canary percentage", default="10"))
        else:
            canary_percentage = 10
        
        # Get scheduling
        schedule_now = Confirm.ask("Schedule immediately?", default=True)
        scheduled_at = None
        if not schedule_now:
            schedule_date = Prompt.ask("Schedule date (YYYY-MM-DD HH:MM)")
            try:
                scheduled_at = datetime.strptime(schedule_date, "%Y-%m-%d %H:%M")
            except ValueError:
                console.print("[red]Invalid date format[/red]")
                return
        
        # Get validation tests
        validation_tests = []
        if Confirm.ask("Add validation tests?"):
            console.print("Available tests: health_check, functionality_test, performance_test")
            while True:
                test = Prompt.ask("Test name (empty to finish)")
                if not test:
                    break
                validation_tests.append(test)
        
        # Create device filters
        device_filters = {}
        if Confirm.ask("Add device filters?"):
            while True:
                filter_key = Prompt.ask("Filter key (empty to finish)")
                if not filter_key:
                    break
                filter_value = Prompt.ask(f"Filter value for {filter_key}")
                device_filters[filter_key] = filter_value
        
        try:
            # Create deployment plan
            plan = self.manager.create_deployment_plan(
                name=name,
                description=description,
                firmware_version=firmware_version,
                source_environment=source_env,
                target_environment=target_env,
                strategy=strategy,
                created_by="cli_user",
                scheduled_at=scheduled_at,
                device_filters=device_filters,
                rollout_percentage=rollout_percentage,
                canary_percentage=canary_percentage,
                validation_tests=validation_tests
            )
            
            console.print(f"[green]Deployment plan created: {plan.plan_id}[/green]")
            
            # Ask for approval if required
            target_env_obj = self.manager.environments[target_env]
            if target_env_obj.approval_required:
                if Confirm.ask("Approve plan now?"):
                    self.manager.approve_deployment_plan(plan.plan_id, "cli_user")
                    console.print("[green]Plan approved[/green]")
                else:
                    console.print("[yellow]Plan requires approval before execution[/yellow]")
            
            # Ask to execute
            if Confirm.ask("Execute deployment now?"):
                self.execute_deployment(plan.plan_id)
        
        except Exception as e:
            console.print(f"[red]Error creating deployment plan: {e}[/red]")
    
    def create_deployment_plan_from_file(self, config_file: str):
        """Create deployment plan from configuration file"""
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            plan = self.manager.create_deployment_plan(
                name=config['name'],
                description=config.get('description', ''),
                firmware_version=config['firmware_version'],
                source_environment=config['source_environment'],
                target_environment=config['target_environment'],
                strategy=config['strategy'],
                created_by=config.get('created_by', 'cli_user'),
                scheduled_at=datetime.fromisoformat(config['scheduled_at']) if config.get('scheduled_at') else None,
                device_filters=config.get('device_filters', {}),
                rollout_percentage=config.get('rollout_percentage', 100),
                canary_percentage=config.get('canary_percentage', 10),
                validation_tests=config.get('validation_tests', []),
                pre_deployment_checks=config.get('pre_deployment_checks', []),
                post_deployment_checks=config.get('post_deployment_checks', []),
                rollback_criteria=config.get('rollback_criteria', {})
            )
            
            console.print(f"[green]Deployment plan created from file: {plan.plan_id}[/green]")
            return plan.plan_id
            
        except Exception as e:
            console.print(f"[red]Error creating deployment plan from file: {e}[/red]")
            return None
    
    def approve_deployment_plan(self, plan_id: str):
        """Approve deployment plan"""
        if plan_id not in self.manager.deployment_plans:
            console.print(f"[red]Plan {plan_id} not found[/red]")
            return
        
        plan = self.manager.deployment_plans[plan_id]
        
        if plan.approved_by:
            console.print(f"[yellow]Plan already approved by {plan.approved_by}[/yellow]")
            return
        
        # Show plan details
        console.print(Panel.fit(f"Approve Plan: {plan.name}", style="bold yellow"))
        console.print(f"Firmware Version: {plan.firmware_version}")
        console.print(f"Source: {plan.source_environment} → Target: {plan.target_environment}")
        console.print(f"Strategy: {plan.strategy.value}")
        console.print(f"Rollout: {plan.rollout_percentage}%")
        
        if Confirm.ask("Approve this deployment plan?"):
            success = self.manager.approve_deployment_plan(plan_id, "cli_user")
            if success:
                console.print("[green]Plan approved successfully[/green]")
            else:
                console.print("[red]Failed to approve plan[/red]")
    
    def execute_deployment(self, plan_id: str):
        """Execute deployment plan"""
        if plan_id not in self.manager.deployment_plans:
            console.print(f"[red]Plan {plan_id} not found[/red]")
            return
        
        plan = self.manager.deployment_plans[plan_id]
        
        # Check if plan is approved
        target_env = self.manager.environments[plan.target_environment]
        if target_env.approval_required and not plan.approved_by:
            console.print("[red]Plan requires approval before execution[/red]")
            return
        
        # Show execution info
        console.print(Panel.fit(f"Executing: {plan.name}", style="bold green"))
        console.print(f"Firmware: {plan.firmware_version}")
        console.print(f"Target: {plan.target_environment}")
        console.print(f"Strategy: {plan.strategy.value}")
        
        # Execute deployment
        execution = self.manager.execute_deployment(plan_id)
        
        if execution:
            console.print(f"[green]Deployment started: {execution.execution_id}[/green]")
            
            # Monitor progress
            self.monitor_deployment_progress(execution.execution_id)
        else:
            console.print("[red]Failed to start deployment[/red]")
    
    def monitor_deployment_progress(self, execution_id: str):
        """Monitor deployment progress with real-time updates"""
        execution = self.manager.active_deployments.get(execution_id)
        if not execution:
            console.print(f"[red]Deployment {execution_id} not found[/red]")
            return
        
        with Progress() as progress:
            task = progress.add_task(f"[green]Deploying {execution.plan.name}...", total=100)
            
            while execution.status.value in ['pending', 'running', 'validating']:
                progress.update(task, completed=execution.progress)
                
                # Show current status
                console.print(f"\\rPhase: {execution.current_phase} | "
                             f"Progress: {execution.progress:.1f}% | "
                             f"Success: {execution.success_count}/{execution.total_devices} | "
                             f"Failed: {execution.failure_count}",
                             end="")
                
                time.sleep(3)
            
            progress.update(task, completed=100)
            
            # Show final status
            if execution.status.value == 'completed':
                console.print(f"\\n[green]Deployment completed successfully![/green]")
                console.print(f"Total devices: {execution.total_devices}")
                console.print(f"Successful: {execution.success_count}")
                console.print(f"Failed: {execution.failure_count}")
                console.print(f"Success rate: {execution.success_count/execution.total_devices*100:.1f}%")
            else:
                console.print(f"\\n[red]Deployment {execution.status.value}[/red]")
                if execution.failure_count > 0:
                    console.print(f"Failed devices: {execution.failure_count}")
    
    def list_deployments(self):
        """List all deployments"""
        deployments = list(self.manager.active_deployments.values())
        
        if not deployments:
            console.print("[yellow]No deployments found[/yellow]")
            return
        
        table = Table(title="Active Deployments")
        table.add_column("Execution ID", style="cyan")
        table.add_column("Plan Name", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("Progress", style="blue")
        table.add_column("Success/Total", style="green")
        table.add_column("Phase", style="yellow")
        table.add_column("Started", style="dim")
        
        for deployment in deployments:
            status_color = {
                "pending": "yellow",
                "running": "blue",
                "validating": "cyan",
                "completed": "green",
                "failed": "red",
                "cancelled": "dim",
                "rolled_back": "orange"
            }.get(deployment.status.value, "white")
            
            table.add_row(
                deployment.execution_id,
                deployment.plan.name,
                f"[{status_color}]{deployment.status.value}[/{status_color}]",
                f"{deployment.progress:.1f}%",
                f"{deployment.success_count}/{deployment.total_devices}",
                deployment.current_phase or "-",
                deployment.started_at.strftime("%Y-%m-%d %H:%M") if deployment.started_at else "-"
            )
        
        console.print(table)
    
    def show_deployment_status(self, execution_id: str):
        """Show detailed deployment status"""
        execution = self.manager.active_deployments.get(execution_id)
        
        if not execution:
            console.print(f"[red]Deployment {execution_id} not found[/red]")
            return
        
        # Main deployment info
        console.print(Panel.fit(f"Deployment Status: {execution.plan.name}", style="bold blue"))
        
        table = Table(show_header=False)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Execution ID", execution.execution_id)
        table.add_row("Plan ID", execution.plan.plan_id)
        table.add_row("Status", execution.status.value)
        table.add_row("Progress", f"{execution.progress:.1f}%")
        table.add_row("Current Phase", execution.current_phase or "N/A")
        table.add_row("Total Devices", str(execution.total_devices))
        table.add_row("Successful", str(execution.success_count))
        table.add_row("Failed", str(execution.failure_count))
        table.add_row("Success Rate", f"{execution.success_count/execution.total_devices*100:.1f}%" if execution.total_devices > 0 else "0%")
        
        if execution.started_at:
            table.add_row("Started", execution.started_at.strftime("%Y-%m-%d %H:%M:%S"))
        
        if execution.completed_at:
            table.add_row("Completed", execution.completed_at.strftime("%Y-%m-%d %H:%M:%S"))
            duration = execution.completed_at - execution.started_at
            table.add_row("Duration", str(duration))
        
        table.add_row("Rollback Available", "Yes" if execution.rollback_available else "No")
        table.add_row("Health Status", execution.health_status)
        
        console.print(table)
        
        # Show recent logs
        if execution.logs:
            console.print("\\n[bold]Recent Logs:[/bold]")
            for log in execution.logs[-10:]:  # Show last 10 logs
                timestamp = log.get('timestamp', 'N/A')
                level = log.get('level', 'INFO')
                message = log.get('message', '')
                
                level_color = {
                    'DEBUG': 'dim',
                    'INFO': 'blue',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red bold'
                }.get(level, 'white')
                
                console.print(f"[dim]{timestamp}[/dim] [{level_color}]{level}[/{level_color}] {message}")
    
    def cancel_deployment(self, execution_id: str):
        """Cancel deployment"""
        execution = self.manager.active_deployments.get(execution_id)
        
        if not execution:
            console.print(f"[red]Deployment {execution_id} not found[/red]")
            return
        
        if execution.status.value not in ['pending', 'running', 'validating']:
            console.print(f"[yellow]Deployment is not in a cancellable state[/yellow]")
            return
        
        if Confirm.ask(f"Are you sure you want to cancel deployment '{execution.plan.name}'?"):
            success = self.manager.cancel_deployment(execution_id)
            if success:
                console.print("[green]Deployment cancelled successfully[/green]")
            else:
                console.print("[red]Failed to cancel deployment[/red]")
    
    def rollback_deployment(self, execution_id: str):
        """Rollback deployment"""
        execution = self.manager.active_deployments.get(execution_id)
        
        if not execution:
            console.print(f"[red]Deployment {execution_id} not found[/red]")
            return
        
        if not execution.rollback_available:
            console.print("[yellow]Rollback not available for this deployment[/yellow]")
            return
        
        if Confirm.ask(f"Are you sure you want to rollback deployment '{execution.plan.name}'?"):
            success = self.manager.rollback_deployment(execution_id)
            if success:
                console.print("[green]Deployment rollback initiated[/green]")
            else:
                console.print("[red]Failed to rollback deployment[/red]")
    
    def run_health_checks(self):
        """Run health checks for all environments"""
        console.print(Panel.fit("Environment Health Checks", style="bold green"))
        
        table = Table()
        table.add_column("Environment", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Response Time", style="blue")
        table.add_column("Details", style="dim")
        
        for env_name, env in self.manager.environments.items():
            if env.health_check_url:
                with console.status(f"Checking {env_name}..."):
                    health_result = self.manager.perform_health_check(env_name)
                
                status = health_result['status']
                status_color = "green" if status == "healthy" else "red"
                
                table.add_row(
                    env_name,
                    f"[{status_color}]{status}[/{status_color}]",
                    f"{health_result['response_time']:.2f}s",
                    health_result.get('details', {}).get('error', '') or "OK"
                )
            else:
                table.add_row(
                    env_name,
                    "[dim]No health check configured[/dim]",
                    "-",
                    "-"
                )
        
        console.print(table)
    
    def show_metrics(self):
        """Show system metrics"""
        console.print(Panel.fit("System Metrics", style="bold green"))
        
        # Calculate metrics
        total_deployments = len(self.manager.active_deployments)
        completed_deployments = len([d for d in self.manager.active_deployments.values() 
                                   if d.status.value == 'completed'])
        failed_deployments = len([d for d in self.manager.active_deployments.values() 
                                if d.status.value == 'failed'])
        
        success_rate = (completed_deployments / total_deployments * 100) if total_deployments > 0 else 0
        
        table = Table(show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Total Deployments", str(total_deployments))
        table.add_row("Completed", str(completed_deployments))
        table.add_row("Failed", str(failed_deployments))
        table.add_row("Success Rate", f"{success_rate:.1f}%")
        table.add_row("Active Deployments", str(len([d for d in self.manager.active_deployments.values() 
                                                   if d.status.value in ['pending', 'running', 'validating']])))
        table.add_row("Environments", str(len(self.manager.environments)))
        table.add_row("Deployment Plans", str(len(self.manager.deployment_plans)))
        
        console.print(table)
    
    def generate_plan_template(self, output_file: str):
        """Generate deployment plan template"""
        template = {
            'name': 'Sample Deployment Plan',
            'description': 'Sample deployment plan configuration',
            'firmware_version': '1.0.0',
            'source_environment': 'staging',
            'target_environment': 'production',
            'strategy': 'rolling',
            'created_by': 'cli_user',
            'scheduled_at': None,
            'device_filters': {
                'location': 'datacenter-1',
                'device_type': 'esp32'
            },
            'rollout_percentage': 100,
            'canary_percentage': 10,
            'validation_tests': [
                'health_check',
                'functionality_test'
            ],
            'pre_deployment_checks': [
                'firmware_validation',
                'device_compatibility_check'
            ],
            'post_deployment_checks': [
                'health_check',
                'performance_validation'
            ],
            'rollback_criteria': {
                'max_failure_rate': 10,
                'health_check_failure': True
            }
        }
        
        with open(output_file, 'w') as f:
            yaml.dump(template, f, default_flow_style=False, indent=2)
        
        console.print(f"[green]Template generated: {output_file}[/green]")
    
    def cleanup(self):
        """Cleanup old deployments"""
        days = int(Prompt.ask("Delete deployments older than (days)", default="30"))
        
        if Confirm.ask(f"Delete deployments older than {days} days?"):
            initial_count = len(self.manager.active_deployments)
            self.manager.cleanup_old_deployments(days)
            final_count = len(self.manager.active_deployments)
            
            deleted = initial_count - final_count
            console.print(f"[green]Deleted {deleted} old deployments[/green]")

def main():
    """Main CLI function"""
    cli = DeploymentCLI()
    
    try:
        # Create argument parser
        parser = argparse.ArgumentParser(description='Production Deployment CLI')
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Environment commands
        env_parser = subparsers.add_parser('env', help='Environment management')
        env_parser.add_argument('action', choices=['list'], help='Environment action')
        
        # Plan commands
        plan_parser = subparsers.add_parser('plan', help='Deployment plan management')
        plan_parser.add_argument('action', choices=['list', 'create', 'approve'], help='Plan action')
        plan_parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')
        plan_parser.add_argument('--config', '-c', help='Configuration file')
        plan_parser.add_argument('--plan-id', help='Plan ID')
        
        # Deployment commands
        deploy_parser = subparsers.add_parser('deploy', help='Deployment execution')
        deploy_parser.add_argument('action', choices=['list', 'execute', 'status', 'cancel', 'rollback'], help='Deployment action')
        deploy_parser.add_argument('--plan-id', help='Plan ID')
        deploy_parser.add_argument('--execution-id', help='Execution ID')
        
        # Health commands
        health_parser = subparsers.add_parser('health', help='Health check management')
        health_parser.add_argument('action', choices=['check'], help='Health action')
        
        # Metrics commands
        metrics_parser = subparsers.add_parser('metrics', help='System metrics')
        
        # Utility commands
        util_parser = subparsers.add_parser('util', help='Utility commands')
        util_parser.add_argument('action', choices=['template', 'cleanup'], help='Utility action')
        util_parser.add_argument('--output', help='Output file')
        
        # Parse arguments
        args = parser.parse_args()
        
        if not args.command:
            parser.print_help()
            return
        
        # Execute commands
        if args.command == 'env':
            if args.action == 'list':
                cli.list_environments()
        
        elif args.command == 'plan':
            if args.action == 'list':
                cli.list_deployment_plans()
            elif args.action == 'create':
                if args.interactive:
                    cli.create_deployment_plan_interactive()
                elif args.config:
                    cli.create_deployment_plan_from_file(args.config)
                else:
                    console.print("[red]Either --interactive or --config must be specified[/red]")
            elif args.action == 'approve':
                if args.plan_id:
                    cli.approve_deployment_plan(args.plan_id)
                else:
                    console.print("[red]--plan-id is required[/red]")
        
        elif args.command == 'deploy':
            if args.action == 'list':
                cli.list_deployments()
            elif args.action == 'execute':
                if args.plan_id:
                    cli.execute_deployment(args.plan_id)
                else:
                    console.print("[red]--plan-id is required[/red]")
            elif args.action == 'status':
                if args.execution_id:
                    cli.show_deployment_status(args.execution_id)
                else:
                    console.print("[red]--execution-id is required[/red]")
            elif args.action == 'cancel':
                if args.execution_id:
                    cli.cancel_deployment(args.execution_id)
                else:
                    console.print("[red]--execution-id is required[/red]")
            elif args.action == 'rollback':
                if args.execution_id:
                    cli.rollback_deployment(args.execution_id)
                else:
                    console.print("[red]--execution-id is required[/red]")
        
        elif args.command == 'health':
            if args.action == 'check':
                cli.run_health_checks()
        
        elif args.command == 'metrics':
            cli.show_metrics()
        
        elif args.command == 'util':
            if args.action == 'template':
                output_file = args.output or 'deployment-plan-template.yaml'
                cli.generate_plan_template(output_file)
            elif args.action == 'cleanup':
                cli.cleanup()
    
    except KeyboardInterrupt:
        console.print("\\n[yellow]Operation cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        cli.manager.shutdown()

if __name__ == "__main__":
    main()