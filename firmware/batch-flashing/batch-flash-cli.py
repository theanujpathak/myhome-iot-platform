#!/usr/bin/env python3
"""
Batch Flash CLI Tool
Command-line interface for batch firmware flashing operations
"""

import os
import sys
import json
import time
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Optional
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, TaskID
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
import yaml

# Import the batch flash manager
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from batch_flash_manager import BatchFlashManager, FlashTarget, DeviceType, FlashStatus

console = Console()

class BatchFlashCLI:
    """Command-line interface for batch firmware flashing"""
    
    def __init__(self, config_file: str = "batch-flash-config.yaml"):
        self.manager = BatchFlashManager(config_file)
        self.console = Console()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('batch-flash-cli.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def list_batches(self):
        """List all batches"""
        batches = self.manager.list_batches()
        
        if not batches:
            console.print("[yellow]No batches found[/yellow]")
            return
        
        table = Table(title="Batch List")
        table.add_column("Batch ID", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("Progress", style="blue")
        table.add_column("Success/Total", style="green")
        table.add_column("Created", style="dim")
        
        for batch in batches:
            status_color = {
                "created": "yellow",
                "running": "blue",
                "completed": "green",
                "failed": "red",
                "cancelled": "dim"
            }.get(batch["status"], "white")
            
            table.add_row(
                batch["batch_id"],
                batch["name"],
                f"[{status_color}]{batch['status']}[/{status_color}]",
                f"{batch['progress']:.1f}%",
                f"{batch['success_count']}/{batch['total_count']}",
                datetime.fromisoformat(batch["created_at"]).strftime("%Y-%m-%d %H:%M")
            )
        
        console.print(table)
    
    def create_batch_interactive(self):
        """Interactive batch creation"""
        console.print(Panel.fit("Create New Batch", style="bold blue"))
        
        # Get batch info
        name = Prompt.ask("Batch name")
        description = Prompt.ask("Description", default="")
        device_type = Prompt.ask("Device type", choices=["esp32", "esp8266", "arduino", "stm32", "pico"])
        version = Prompt.ask("Firmware version")
        firmware_file = Prompt.ask("Firmware file path")
        
        # Validate firmware file
        if not os.path.exists(firmware_file):
            console.print(f"[red]Error: Firmware file not found: {firmware_file}[/red]")
            return
        
        # Get flash settings
        strategy = Prompt.ask("Flash strategy", choices=["parallel", "sequential", "gradual"], default="parallel")
        max_concurrent = int(Prompt.ask("Max concurrent operations", default="5"))
        timeout = int(Prompt.ask("Timeout (seconds)", default="300"))
        rollback_on_failure = Confirm.ask("Enable rollback on failure?", default=True)
        
        # Get targets
        targets = []
        console.print("\\n[bold]Add target devices:[/bold]")
        
        while True:
            device_id = Prompt.ask("Device ID (empty to finish)")
            if not device_id:
                break
            
            target_device_type = Prompt.ask("Device type", choices=["esp32", "esp8266", "arduino", "stm32", "pico"], default=device_type)
            connection = Prompt.ask("Connection (port/IP)")
            
            target = FlashTarget(
                device_id=device_id,
                device_type=DeviceType(target_device_type),
                connection_info={"port": connection}
            )
            targets.append(target)
            
            console.print(f"[green]Added {device_id}[/green]")
        
        if not targets:
            console.print("[red]Error: No targets specified[/red]")
            return
        
        # Create firmware package
        try:
            firmware_package = self.manager.create_firmware_package(
                firmware_file, device_type, version
            )
            
            # Create batch
            batch = self.manager.create_flash_batch(
                name=name,
                firmware_package=firmware_package,
                targets=targets,
                description=description,
                strategy=strategy,
                max_concurrent=max_concurrent,
                timeout=timeout,
                rollback_on_failure=rollback_on_failure
            )
            
            console.print(f"[green]Batch created successfully: {batch.batch_id}[/green]")
            
            # Ask if user wants to start immediately
            if Confirm.ask("Start batch now?"):
                self.start_batch(batch.batch_id)
        
        except Exception as e:
            console.print(f"[red]Error creating batch: {e}[/red]")
    
    def create_batch_from_file(self, config_file: str):
        """Create batch from configuration file"""
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            # Create firmware package
            firmware_package = self.manager.create_firmware_package(
                config['firmware_file'],
                config['device_type'],
                config['version'],
                config.get('metadata', {})
            )
            
            # Create targets
            targets = []
            for target_config in config['targets']:
                target = FlashTarget(
                    device_id=target_config['device_id'],
                    device_type=DeviceType(target_config['device_type']),
                    connection_info=target_config['connection_info']
                )
                targets.append(target)
            
            # Create batch
            batch = self.manager.create_flash_batch(
                name=config['name'],
                firmware_package=firmware_package,
                targets=targets,
                description=config.get('description', ''),
                strategy=config.get('strategy', 'parallel'),
                max_concurrent=config.get('max_concurrent', 10),
                timeout=config.get('timeout', 300),
                rollback_on_failure=config.get('rollback_on_failure', False)
            )
            
            console.print(f"[green]Batch created from file: {batch.batch_id}[/green]")
            return batch.batch_id
            
        except Exception as e:
            console.print(f"[red]Error creating batch from file: {e}[/red]")
            return None
    
    def start_batch(self, batch_id: str):
        """Start batch execution"""
        if batch_id not in self.manager.batches:
            console.print(f"[red]Batch {batch_id} not found[/red]")
            return
        
        batch = self.manager.batches[batch_id]
        
        # Show batch info
        console.print(Panel.fit(f"Starting Batch: {batch.name}", style="bold green"))
        console.print(f"Strategy: {batch.strategy}")
        console.print(f"Target devices: {len(batch.targets)}")
        console.print(f"Firmware: {batch.firmware_package.version}")
        
        # Start the batch
        if self.manager.start_batch_flash(batch_id):
            console.print(f"[green]Batch {batch_id} started successfully[/green]")
            
            # Monitor progress
            self.monitor_batch_progress(batch_id)
        else:
            console.print(f"[red]Failed to start batch {batch_id}[/red]")
    
    def monitor_batch_progress(self, batch_id: str):
        """Monitor batch progress with real-time updates"""
        batch = self.manager.batches[batch_id]
        
        with Progress() as progress:
            task = progress.add_task(f"[green]Flashing {batch.name}...", total=100)
            
            while batch.status == "running":
                progress.update(task, completed=batch.progress)
                
                # Show current status
                console.print(f"\\rProgress: {batch.progress:.1f}% | "
                             f"Success: {batch.success_count} | "
                             f"Failed: {batch.failure_count} | "
                             f"Remaining: {batch.total_count - batch.success_count - batch.failure_count}",
                             end="")
                
                time.sleep(2)
            
            progress.update(task, completed=100)
            
            # Show final status
            if batch.status == "completed":
                console.print(f"\\n[green]Batch completed successfully![/green]")
                console.print(f"Total devices: {batch.total_count}")
                console.print(f"Successful: {batch.success_count}")
                console.print(f"Failed: {batch.failure_count}")
                
                if batch.failure_count > 0:
                    console.print("\\n[yellow]Failed devices:[/yellow]")
                    for target in batch.targets:
                        if target.status == FlashStatus.FAILED:
                            console.print(f"  - {target.device_id}: {target.error_message}")
            else:
                console.print(f"\\n[red]Batch {batch.status}[/red]")
    
    def show_batch_status(self, batch_id: str):
        """Show detailed batch status"""
        status = self.manager.get_batch_status(batch_id)
        
        if not status:
            console.print(f"[red]Batch {batch_id} not found[/red]")
            return
        
        # Main batch info
        console.print(Panel.fit(f"Batch Status: {status['name']}", style="bold blue"))
        
        table = Table(show_header=False)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Batch ID", status['batch_id'])
        table.add_row("Status", status['status'])
        table.add_row("Progress", f"{status['progress']:.1f}%")
        table.add_row("Total Devices", str(status['total_count']))
        table.add_row("Successful", str(status['success_count']))
        table.add_row("Failed", str(status['failure_count']))
        table.add_row("Cancelled", str(status['cancelled_count']))
        table.add_row("Created", datetime.fromisoformat(status['created_at']).strftime("%Y-%m-%d %H:%M:%S"))
        
        if status['started_at']:
            table.add_row("Started", datetime.fromisoformat(status['started_at']).strftime("%Y-%m-%d %H:%M:%S"))
        
        if status['completed_at']:
            table.add_row("Completed", datetime.fromisoformat(status['completed_at']).strftime("%Y-%m-%d %H:%M:%S"))
        
        console.print(table)
        
        # Target devices
        if status['targets']:
            console.print("\\n[bold]Target Devices:[/bold]")
            
            device_table = Table()
            device_table.add_column("Device ID", style="cyan")
            device_table.add_column("Status", style="green")
            device_table.add_column("Retries", style="yellow")
            device_table.add_column("Error", style="red")
            
            for target in status['targets']:
                status_color = {
                    "pending": "yellow",
                    "flashing": "blue",
                    "completed": "green",
                    "failed": "red",
                    "cancelled": "dim"
                }.get(target['status'], "white")
                
                device_table.add_row(
                    target['device_id'],
                    f"[{status_color}]{target['status']}[/{status_color}]",
                    str(target['retry_count']),
                    target['error_message'] or "-"
                )
            
            console.print(device_table)
    
    def cancel_batch(self, batch_id: str):
        """Cancel batch execution"""
        if batch_id not in self.manager.batches:
            console.print(f"[red]Batch {batch_id} not found[/red]")
            return
        
        batch = self.manager.batches[batch_id]
        
        if batch.status != "running":
            console.print(f"[yellow]Batch {batch_id} is not running[/yellow]")
            return
        
        if Confirm.ask(f"Are you sure you want to cancel batch '{batch.name}'?"):
            if self.manager.cancel_batch(batch_id):
                console.print(f"[green]Batch {batch_id} cancelled successfully[/green]")
            else:
                console.print(f"[red]Failed to cancel batch {batch_id}[/red]")
    
    def show_stats(self):
        """Show system statistics"""
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
        
        console.print(Panel.fit("System Statistics", style="bold green"))
        
        table = Table(show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Total Batches", str(stats['total_batches']))
        table.add_row("Active Batches", str(stats['active_batches']))
        table.add_row("Completed Batches", str(stats['completed_batches']))
        table.add_row("Failed Batches", str(stats['failed_batches']))
        table.add_row("Devices Flashed", str(stats['total_devices_flashed']))
        table.add_row("Devices Failed", str(stats['total_devices_failed']))
        table.add_row("Active Operations", str(stats['active_operations']))
        table.add_row("Available Interfaces", ', '.join(stats['available_interfaces']))
        
        if stats['total_devices_flashed'] + stats['total_devices_failed'] > 0:
            success_rate = (stats['total_devices_flashed'] / 
                          (stats['total_devices_flashed'] + stats['total_devices_failed'])) * 100
            table.add_row("Success Rate", f"{success_rate:.1f}%")
        
        console.print(table)
    
    def validate_firmware(self, firmware_file: str, device_type: str):
        """Validate firmware file"""
        if not os.path.exists(firmware_file):
            console.print(f"[red]Firmware file not found: {firmware_file}[/red]")
            return False
        
        file_size = os.path.getsize(firmware_file)
        
        # Size limits
        size_limits = {
            'esp32': 3 * 1024 * 1024,      # 3MB
            'esp8266': 1 * 1024 * 1024,    # 1MB
            'arduino': 30 * 1024,          # 30KB
            'stm32': 512 * 1024,           # 512KB
            'pico': 2 * 1024 * 1024        # 2MB
        }
        
        console.print(Panel.fit("Firmware Validation", style="bold blue"))
        
        table = Table(show_header=False)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("File Path", firmware_file)
        table.add_row("File Size", f"{file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
        table.add_row("Device Type", device_type)
        
        if device_type in size_limits:
            limit = size_limits[device_type]
            table.add_row("Size Limit", f"{limit:,} bytes ({limit/1024/1024:.2f} MB)")
            
            if file_size <= limit:
                table.add_row("Size Check", "[green]PASS[/green]")
            else:
                table.add_row("Size Check", "[red]FAIL[/red]")
                console.print(table)
                return False
        
        # Check file extension
        valid_extensions = {
            'esp32': ['.bin'],
            'esp8266': ['.bin'],
            'arduino': ['.hex'],
            'stm32': ['.bin', '.hex'],
            'pico': ['.uf2']
        }
        
        ext = os.path.splitext(firmware_file)[1].lower()
        if device_type in valid_extensions:
            if ext in valid_extensions[device_type]:
                table.add_row("Extension Check", "[green]PASS[/green]")
            else:
                table.add_row("Extension Check", f"[yellow]WARNING[/yellow] (expected: {valid_extensions[device_type]})")
        
        console.print(table)
        console.print("[green]Firmware validation passed[/green]")
        return True
    
    def generate_batch_template(self, output_file: str):
        """Generate batch configuration template"""
        template = {
            'name': 'Sample Batch',
            'description': 'Sample batch configuration',
            'firmware_file': '/path/to/firmware.bin',
            'device_type': 'esp32',
            'version': '1.0.0',
            'strategy': 'parallel',
            'max_concurrent': 5,
            'timeout': 300,
            'rollback_on_failure': True,
            'metadata': {
                'changelog': 'Sample firmware update',
                'build_date': '2024-01-01'
            },
            'targets': [
                {
                    'device_id': 'ESP32_001',
                    'device_type': 'esp32',
                    'connection_info': {
                        'port': '/dev/ttyUSB0'
                    }
                },
                {
                    'device_id': 'ESP32_002',
                    'device_type': 'esp32',
                    'connection_info': {
                        'port': '/dev/ttyUSB1'
                    }
                }
            ]
        }
        
        with open(output_file, 'w') as f:
            yaml.dump(template, f, default_flow_style=False, indent=2)
        
        console.print(f"[green]Template generated: {output_file}[/green]")
    
    def cleanup(self):
        """Cleanup old batches"""
        days = int(Prompt.ask("Delete batches older than (days)", default="30"))
        
        if Confirm.ask(f"Delete batches older than {days} days?"):
            initial_count = len(self.manager.batches)
            self.manager.cleanup_old_batches(days)
            final_count = len(self.manager.batches)
            
            deleted = initial_count - final_count
            console.print(f"[green]Deleted {deleted} old batches[/green]")

def main():
    """Main CLI function"""
    cli = BatchFlashCLI()
    
    try:
        # Create argument parser
        parser = argparse.ArgumentParser(description='Batch Firmware Flash CLI')
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # List command
        list_parser = subparsers.add_parser('list', help='List all batches')
        
        # Create command
        create_parser = subparsers.add_parser('create', help='Create new batch')
        create_parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')
        create_parser.add_argument('--config', '-c', help='Configuration file')
        create_parser.add_argument('--start', '-s', action='store_true', help='Start batch immediately')
        
        # Start command
        start_parser = subparsers.add_parser('start', help='Start batch execution')
        start_parser.add_argument('batch_id', help='Batch ID to start')
        
        # Status command
        status_parser = subparsers.add_parser('status', help='Show batch status')
        status_parser.add_argument('batch_id', help='Batch ID to check')
        
        # Cancel command
        cancel_parser = subparsers.add_parser('cancel', help='Cancel batch execution')
        cancel_parser.add_argument('batch_id', help='Batch ID to cancel')
        
        # Stats command
        stats_parser = subparsers.add_parser('stats', help='Show system statistics')
        
        # Validate command
        validate_parser = subparsers.add_parser('validate', help='Validate firmware file')
        validate_parser.add_argument('firmware_file', help='Firmware file path')
        validate_parser.add_argument('device_type', choices=['esp32', 'esp8266', 'arduino', 'stm32', 'pico'], help='Device type')
        
        # Template command
        template_parser = subparsers.add_parser('template', help='Generate batch template')
        template_parser.add_argument('output_file', help='Output file path')
        
        # Cleanup command
        cleanup_parser = subparsers.add_parser('cleanup', help='Cleanup old batches')
        
        # Parse arguments
        args = parser.parse_args()
        
        if not args.command:
            parser.print_help()
            return
        
        # Execute commands
        if args.command == 'list':
            cli.list_batches()
        
        elif args.command == 'create':
            if args.interactive:
                cli.create_batch_interactive()
            elif args.config:
                batch_id = cli.create_batch_from_file(args.config)
                if batch_id and args.start:
                    cli.start_batch(batch_id)
            else:
                console.print("[red]Either --interactive or --config must be specified[/red]")
        
        elif args.command == 'start':
            cli.start_batch(args.batch_id)
        
        elif args.command == 'status':
            cli.show_batch_status(args.batch_id)
        
        elif args.command == 'cancel':
            cli.cancel_batch(args.batch_id)
        
        elif args.command == 'stats':
            cli.show_stats()
        
        elif args.command == 'validate':
            cli.validate_firmware(args.firmware_file, args.device_type)
        
        elif args.command == 'template':
            cli.generate_batch_template(args.output_file)
        
        elif args.command == 'cleanup':
            cli.cleanup()
    
    except KeyboardInterrupt:
        console.print("\\n[yellow]Operation cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        cli.manager.shutdown()

if __name__ == "__main__":
    main()