#!/usr/bin/env python3
"""
Batch Processing Script for Factory Provisioning
Automated batch processing with scheduling and monitoring
"""

import os
import sys
import json
import time
import signal
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import threading
from dataclasses import dataclass
import argparse

# Import the main factory provisioning system
from factory_flash import FactoryProvisioning, DeviceRecord

@dataclass
class BatchJob:
    """Represents a batch processing job"""
    job_id: str
    batch_size: int
    stations: List[str]
    board_type: str
    firmware_version: str
    priority: int = 1
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"  # pending, running, completed, failed, cancelled
    progress: int = 0
    total_devices: int = 0
    successful_devices: int = 0
    failed_devices: int = 0
    error_message: Optional[str] = None

class BatchProcessor:
    """Advanced batch processing with scheduling and monitoring"""
    
    def __init__(self, config_file: str = "factory-config.yaml"):
        self.config_file = config_file
        self.factory = FactoryProvisioning(config_file)
        self.jobs: Dict[str, BatchJob] = {}
        self.running = False
        self.worker_threads: List[threading.Thread] = []
        self.job_queue: List[BatchJob] = []
        self.max_concurrent_jobs = 2
        self.current_jobs: Dict[str, threading.Thread] = {}
        
        # Setup logging
        self.setup_logging()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('batch-processor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
    
    def generate_job_id(self) -> str:
        """Generate unique job ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"JOB_{timestamp}_{len(self.jobs)}"
    
    def create_job(
        self,
        batch_size: int,
        stations: Optional[List[str]] = None,
        board_type: str = "esp32",
        firmware_version: str = "latest",
        priority: int = 1
    ) -> BatchJob:
        """Create a new batch processing job"""
        job_id = self.generate_job_id()
        
        if stations is None:
            stations = list(self.factory.stations.keys())
        
        job = BatchJob(
            job_id=job_id,
            batch_size=batch_size,
            stations=stations,
            board_type=board_type,
            firmware_version=firmware_version,
            priority=priority,
            created_at=datetime.now()
        )
        
        self.jobs[job_id] = job
        self.job_queue.append(job)
        self.job_queue.sort(key=lambda x: x.priority, reverse=True)
        
        self.logger.info(f"Created job {job_id} with batch size {batch_size}")
        return job
    
    def get_job_status(self, job_id: str) -> Optional[BatchJob]:
        """Get job status"""
        return self.jobs.get(job_id)
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job"""
        job = self.jobs.get(job_id)
        if not job:
            return False
        
        if job.status == "running":
            # Signal the worker thread to stop
            job.status = "cancelled"
            self.logger.info(f"Job {job_id} marked for cancellation")
        elif job.status == "pending":
            job.status = "cancelled"
            # Remove from queue
            self.job_queue = [j for j in self.job_queue if j.job_id != job_id]
            self.logger.info(f"Job {job_id} cancelled")
        
        return True
    
    def process_job(self, job: BatchJob):
        """Process a single job"""
        try:
            self.logger.info(f"Starting job {job.job_id}")
            job.status = "running"
            job.started_at = datetime.now()
            
            # Calculate devices per station
            devices_per_station = max(1, job.batch_size // len(job.stations))
            
            # Process each station
            for station_id in job.stations:
                if job.status == "cancelled":
                    self.logger.info(f"Job {job.job_id} cancelled, stopping processing")
                    return
                
                if station_id not in self.factory.stations:
                    self.logger.error(f"Station {station_id} not found")
                    continue
                
                self.logger.info(f"Processing station {station_id} for job {job.job_id}")
                
                # Process the station
                try:
                    self.factory.process_station(station_id, devices_per_station)
                    
                    # Update job progress
                    station = self.factory.stations[station_id]
                    job.successful_devices += station.success_count
                    job.failed_devices += station.failure_count
                    job.total_devices += station.total_flashed
                    
                    if job.total_devices > 0:
                        job.progress = int((job.successful_devices / job.total_devices) * 100)
                    
                except Exception as e:
                    self.logger.error(f"Error processing station {station_id}: {e}")
                    job.error_message = str(e)
            
            # Mark job as completed
            if job.status != "cancelled":
                job.status = "completed"
                job.completed_at = datetime.now()
                self.logger.info(f"Job {job.job_id} completed successfully")
                
                # Generate job report
                self.generate_job_report(job)
            
        except Exception as e:
            self.logger.error(f"Job {job.job_id} failed: {e}")
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.now()
        
        finally:
            # Remove from current jobs
            if job.job_id in self.current_jobs:
                del self.current_jobs[job.job_id]
    
    def generate_job_report(self, job: BatchJob):
        """Generate a report for a completed job"""
        report = {
            "job_id": job.job_id,
            "batch_size": job.batch_size,
            "stations": job.stations,
            "board_type": job.board_type,
            "firmware_version": job.firmware_version,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "status": job.status,
            "progress": job.progress,
            "total_devices": job.total_devices,
            "successful_devices": job.successful_devices,
            "failed_devices": job.failed_devices,
            "success_rate": f"{(job.successful_devices / job.total_devices * 100):.1f}%" if job.total_devices > 0 else "0%",
            "error_message": job.error_message
        }
        
        # Save report to file
        report_file = f"job_report_{job.job_id}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Job report saved to {report_file}")
    
    def worker_thread(self):
        """Worker thread for processing jobs"""
        while self.running:
            try:
                # Check for available jobs
                if self.job_queue and len(self.current_jobs) < self.max_concurrent_jobs:
                    job = self.job_queue.pop(0)
                    
                    if job.status == "pending":
                        # Start processing the job
                        thread = threading.Thread(target=self.process_job, args=(job,))
                        thread.daemon = True
                        thread.start()
                        
                        self.current_jobs[job.job_id] = thread
                
                # Sleep briefly to avoid busy waiting
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error in worker thread: {e}")
                time.sleep(5)
    
    def start(self):
        """Start the batch processor"""
        self.logger.info("Starting batch processor...")
        self.running = True
        
        # Start worker threads
        for i in range(2):  # Start 2 worker threads
            thread = threading.Thread(target=self.worker_thread)
            thread.daemon = True
            thread.start()
            self.worker_threads.append(thread)
        
        self.logger.info("Batch processor started")
    
    def stop(self):
        """Stop the batch processor"""
        self.logger.info("Stopping batch processor...")
        self.running = False
        
        # Wait for worker threads to finish
        for thread in self.worker_threads:
            thread.join(timeout=5)
        
        # Wait for current jobs to finish
        for job_id, thread in self.current_jobs.items():
            self.logger.info(f"Waiting for job {job_id} to finish...")
            thread.join(timeout=30)
        
        self.logger.info("Batch processor stopped")
    
    def shutdown(self):
        """Graceful shutdown"""
        self.logger.info("Shutting down batch processor...")
        
        # Cancel all pending jobs
        for job in self.job_queue:
            if job.status == "pending":
                job.status = "cancelled"
        
        # Stop the processor
        self.stop()
        
        # Generate final report
        self.generate_final_report()
        
        self.logger.info("Batch processor shutdown complete")
    
    def generate_final_report(self):
        """Generate final processing report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_jobs": len(self.jobs),
            "completed_jobs": len([j for j in self.jobs.values() if j.status == "completed"]),
            "failed_jobs": len([j for j in self.jobs.values() if j.status == "failed"]),
            "cancelled_jobs": len([j for j in self.jobs.values() if j.status == "cancelled"]),
            "total_devices": sum(j.total_devices for j in self.jobs.values()),
            "successful_devices": sum(j.successful_devices for j in self.jobs.values()),
            "failed_devices": sum(j.failed_devices for j in self.jobs.values()),
            "jobs": [
                {
                    "job_id": job.job_id,
                    "status": job.status,
                    "batch_size": job.batch_size,
                    "total_devices": job.total_devices,
                    "successful_devices": job.successful_devices,
                    "failed_devices": job.failed_devices,
                    "created_at": job.created_at.isoformat(),
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None
                }
                for job in self.jobs.values()
            ]
        }
        
        report_file = f"final_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Final report saved to {report_file}")
    
    def get_status(self) -> Dict:
        """Get current processor status"""
        return {
            "running": self.running,
            "total_jobs": len(self.jobs),
            "pending_jobs": len([j for j in self.jobs.values() if j.status == "pending"]),
            "running_jobs": len([j for j in self.jobs.values() if j.status == "running"]),
            "completed_jobs": len([j for j in self.jobs.values() if j.status == "completed"]),
            "failed_jobs": len([j for j in self.jobs.values() if j.status == "failed"]),
            "cancelled_jobs": len([j for j in self.jobs.values() if j.status == "cancelled"]),
            "current_jobs": list(self.current_jobs.keys()),
            "queue_size": len(self.job_queue)
        }
    
    def interactive_mode(self):
        """Interactive mode for managing jobs"""
        print("Batch Processor Interactive Mode")
        print("=" * 50)
        print("Commands:")
        print("  create <batch_size> [stations] [board_type] - Create new job")
        print("  status [job_id] - Show status")
        print("  cancel <job_id> - Cancel job")
        print("  list - List all jobs")
        print("  quit - Exit")
        print()
        
        while True:
            try:
                command = input("batch> ").strip().split()
                
                if not command:
                    continue
                
                if command[0] == "quit":
                    break
                
                elif command[0] == "create":
                    if len(command) < 2:
                        print("Usage: create <batch_size> [stations] [board_type]")
                        continue
                    
                    batch_size = int(command[1])
                    stations = command[2].split(",") if len(command) > 2 else None
                    board_type = command[3] if len(command) > 3 else "esp32"
                    
                    job = self.create_job(batch_size, stations, board_type)
                    print(f"Created job {job.job_id}")
                
                elif command[0] == "status":
                    if len(command) > 1:
                        job = self.get_job_status(command[1])
                        if job:
                            print(f"Job {job.job_id}:")
                            print(f"  Status: {job.status}")
                            print(f"  Progress: {job.progress}%")
                            print(f"  Total: {job.total_devices}")
                            print(f"  Successful: {job.successful_devices}")
                            print(f"  Failed: {job.failed_devices}")
                        else:
                            print("Job not found")
                    else:
                        status = self.get_status()
                        print("Processor Status:")
                        for key, value in status.items():
                            print(f"  {key}: {value}")
                
                elif command[0] == "cancel":
                    if len(command) < 2:
                        print("Usage: cancel <job_id>")
                        continue
                    
                    if self.cancel_job(command[1]):
                        print(f"Job {command[1]} cancelled")
                    else:
                        print("Job not found")
                
                elif command[0] == "list":
                    print("Jobs:")
                    for job in self.jobs.values():
                        print(f"  {job.job_id}: {job.status} ({job.progress}%)")
                
                else:
                    print("Unknown command")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Batch Processor for Factory Provisioning')
    parser.add_argument('--config', '-c', default='factory-config.yaml', help='Configuration file')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')
    parser.add_argument('--batch-size', '-b', type=int, default=50, help='Batch size')
    parser.add_argument('--stations', '-s', help='Comma-separated list of stations')
    parser.add_argument('--board-type', '-t', default='esp32', help='Board type')
    parser.add_argument('--daemon', '-d', action='store_true', help='Run as daemon')
    
    args = parser.parse_args()
    
    # Create batch processor
    processor = BatchProcessor(args.config)
    
    # Start the processor
    processor.start()
    
    try:
        if args.interactive:
            processor.interactive_mode()
        else:
            # Create and run a single job
            stations = args.stations.split(",") if args.stations else None
            job = processor.create_job(
                batch_size=args.batch_size,
                stations=stations,
                board_type=args.board_type
            )
            
            print(f"Started job {job.job_id}")
            
            if args.daemon:
                # Run indefinitely
                while True:
                    time.sleep(10)
            else:
                # Wait for job completion
                while job.status in ["pending", "running"]:
                    time.sleep(1)
                
                print(f"Job {job.job_id} completed with status: {job.status}")
                
                if job.status == "completed":
                    print(f"Processed {job.total_devices} devices")
                    print(f"Success rate: {(job.successful_devices / job.total_devices * 100):.1f}%")
    
    except KeyboardInterrupt:
        print("\nShutting down...")
    
    finally:
        processor.shutdown()

if __name__ == "__main__":
    main()