import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from croniter import croniter
import json
import httpx
import os

from database import SessionLocal
from models import Schedule, ScheduleExecution, AutomationRule
from schemas import TriggerType, ActionType

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.device_service_url = os.getenv("DEVICE_SERVICE_URL", "http://localhost:3002")
        self.user_service_url = os.getenv("USER_SERVICE_URL", "http://localhost:3001")
        
    async def start(self):
        """Start the scheduler and load all active schedules"""
        self.scheduler.start()
        await self.load_schedules()
        logger.info("Scheduler service started")
        
    async def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Scheduler service stopped")
        
    async def load_schedules(self):
        """Load all active schedules from database"""
        db = SessionLocal()
        try:
            schedules = db.query(Schedule).filter(
                Schedule.enabled == True,
                Schedule.status == "active"
            ).all()
            
            for schedule in schedules:
                await self.schedule_job(schedule)
                
            logger.info(f"Loaded {len(schedules)} active schedules")
        except Exception as e:
            logger.error(f"Error loading schedules: {e}")
        finally:
            db.close()
            
    async def schedule_job(self, schedule: Schedule):
        """Schedule a job based on schedule configuration"""
        try:
            job_id = f"schedule_{schedule.id}"
            
            # Remove existing job if it exists
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            
            if schedule.trigger_type == TriggerType.TIME:
                trigger = self.create_time_trigger(schedule.trigger_config)
                self.scheduler.add_job(
                    self.execute_schedule,
                    trigger=trigger,
                    id=job_id,
                    args=[schedule.id],
                    misfire_grace_time=60
                )
                
                # Update next run time
                next_run = self.scheduler.get_job(job_id).next_run_time
                db = SessionLocal()
                try:
                    db_schedule = db.query(Schedule).filter(Schedule.id == schedule.id).first()
                    if db_schedule:
                        db_schedule.next_run = next_run
                        db.commit()
                finally:
                    db.close()
                    
            elif schedule.trigger_type == TriggerType.DEVICE_STATE:
                # Device state triggers are handled by the device state monitor
                pass
                
            elif schedule.trigger_type == TriggerType.CONDITIONAL:
                # Conditional triggers are checked periodically
                self.scheduler.add_job(
                    self.check_conditional_schedule,
                    trigger=IntervalTrigger(minutes=1),
                    id=job_id,
                    args=[schedule.id],
                    misfire_grace_time=30
                )
                
            logger.info(f"Scheduled job for schedule {schedule.id}: {schedule.name}")
            
        except Exception as e:
            logger.error(f"Error scheduling job for schedule {schedule.id}: {e}")
            
    def create_time_trigger(self, trigger_config: Dict[str, Any]) -> CronTrigger:
        """Create a cron trigger from time configuration"""
        time_str = trigger_config.get("time", "00:00")
        days = trigger_config.get("days", [])
        
        hour, minute = time_str.split(":")
        hour = int(hour)
        minute = int(minute)
        
        # Convert days to cron format
        day_of_week = None
        if "all" in days:
            day_of_week = "*"
        elif "weekdays" in days:
            day_of_week = "mon-fri"
        elif "weekends" in days:
            day_of_week = "sat,sun"
        else:
            # Convert day names to numbers
            day_map = {
                "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
                "friday": 4, "saturday": 5, "sunday": 6
            }
            day_numbers = [str(day_map.get(day.lower(), 0)) for day in days if day.lower() in day_map]
            day_of_week = ",".join(day_numbers) if day_numbers else "*"
        
        return CronTrigger(
            hour=hour,
            minute=minute,
            day_of_week=day_of_week,
            timezone=trigger_config.get("timezone", "UTC")
        )
        
    async def execute_schedule(self, schedule_id: int):
        """Execute a schedule"""
        execution_start = datetime.utcnow()
        db = SessionLocal()
        
        try:
            schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
            if not schedule or not schedule.enabled:
                return
                
            logger.info(f"Executing schedule {schedule_id}: {schedule.name}")
            
            # Check conditions
            if not await self.check_conditions(schedule.conditions):
                logger.info(f"Schedule {schedule_id} conditions not met, skipping execution")
                return
                
            # Execute actions
            success = True
            error_message = None
            actions_executed = []
            
            for action in schedule.actions:
                try:
                    action_result = await self.execute_action(action)
                    actions_executed.append({
                        "action": action,
                        "success": action_result.get("success", False),
                        "message": action_result.get("message", "")
                    })
                    if not action_result.get("success", False):
                        success = False
                        error_message = action_result.get("message", "Action failed")
                except Exception as e:
                    logger.error(f"Error executing action: {e}")
                    success = False
                    error_message = str(e)
                    actions_executed.append({
                        "action": action,
                        "success": False,
                        "message": str(e)
                    })
            
            # Record execution
            execution_duration = int((datetime.utcnow() - execution_start).total_seconds() * 1000)
            
            execution = ScheduleExecution(
                schedule_id=schedule_id,
                success=success,
                error_message=error_message,
                execution_duration=execution_duration,
                actions_executed=actions_executed,
                trigger_data={"type": "scheduled", "time": execution_start.isoformat()}
            )
            db.add(execution)
            
            # Update schedule
            schedule.last_run = execution_start
            schedule.run_count += 1
            if not success:
                schedule.error_count += 1
                schedule.last_error = error_message
                
            db.commit()
            
            logger.info(f"Schedule {schedule_id} executed successfully: {success}")
            
        except Exception as e:
            logger.error(f"Error executing schedule {schedule_id}: {e}")
            
            # Record failed execution
            execution = ScheduleExecution(
                schedule_id=schedule_id,
                success=False,
                error_message=str(e),
                execution_duration=int((datetime.utcnow() - execution_start).total_seconds() * 1000),
                trigger_data={"type": "scheduled", "time": execution_start.isoformat()}
            )
            db.add(execution)
            
            # Update schedule error count
            schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
            if schedule:
                schedule.error_count += 1
                schedule.last_error = str(e)
                
            db.commit()
            
        finally:
            db.close()
            
    async def check_conditional_schedule(self, schedule_id: int):
        """Check if conditional schedule should be triggered"""
        db = SessionLocal()
        try:
            schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
            if not schedule or not schedule.enabled:
                return
                
            # Check if conditions are met
            if await self.check_conditions(schedule.trigger_config.get("conditions", [])):
                await self.execute_schedule(schedule_id)
                
        except Exception as e:
            logger.error(f"Error checking conditional schedule {schedule_id}: {e}")
        finally:
            db.close()
            
    async def check_conditions(self, conditions: List[Dict[str, Any]]) -> bool:
        """Check if all conditions are met"""
        if not conditions:
            return True
            
        try:
            for condition in conditions:
                if not await self.check_single_condition(condition):
                    return False
            return True
        except Exception as e:
            logger.error(f"Error checking conditions: {e}")
            return False
            
    async def check_single_condition(self, condition: Dict[str, Any]) -> bool:
        """Check a single condition"""
        try:
            # Time-based conditions
            if "time_start" in condition and "time_end" in condition:
                current_time = datetime.now().time()
                start_time = datetime.strptime(condition["time_start"], "%H:%M").time()
                end_time = datetime.strptime(condition["time_end"], "%H:%M").time()
                
                if start_time <= end_time:
                    if not (start_time <= current_time <= end_time):
                        return False
                else:  # Overnight period
                    if not (current_time >= start_time or current_time <= end_time):
                        return False
            
            # Device state conditions
            if "device_id" in condition and "state_key" in condition:
                device_state = await self.get_device_state(
                    condition["device_id"], 
                    condition["state_key"]
                )
                
                if device_state is None:
                    return False
                    
                operator = condition.get("operator", "eq")
                expected_value = condition.get("value")
                
                return self.compare_values(device_state, operator, expected_value)
                
            return True
            
        except Exception as e:
            logger.error(f"Error checking condition: {e}")
            return False
            
    def compare_values(self, actual: Any, operator: str, expected: Any) -> bool:
        """Compare two values using the specified operator"""
        try:
            if operator == "eq":
                return actual == expected
            elif operator == "ne":
                return actual != expected
            elif operator == "gt":
                return float(actual) > float(expected)
            elif operator == "lt":
                return float(actual) < float(expected)
            elif operator == "gte":
                return float(actual) >= float(expected)
            elif operator == "lte":
                return float(actual) <= float(expected)
            elif operator == "contains":
                return str(expected).lower() in str(actual).lower()
            else:
                return False
        except (ValueError, TypeError):
            return False
            
    async def get_device_state(self, device_id: str, state_key: str) -> Optional[Any]:
        """Get device state from device service"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.device_service_url}/api/devices/{device_id}/states")
                if response.status_code == 200:
                    states = response.json()
                    for state in states:
                        if state["state_key"] == state_key:
                            return state["state_value"]
            return None
        except Exception as e:
            logger.error(f"Error getting device state: {e}")
            return None
            
    async def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single action"""
        action_type = action.get("type")
        
        try:
            if action_type == ActionType.DEVICE_COMMAND:
                return await self.execute_device_command(action)
            elif action_type == ActionType.NOTIFICATION:
                return await self.execute_notification(action)
            elif action_type == ActionType.WEBHOOK:
                return await self.execute_webhook(action)
            else:
                return {"success": False, "message": f"Unknown action type: {action_type}"}
                
        except Exception as e:
            logger.error(f"Error executing action: {e}")
            return {"success": False, "message": str(e)}
            
    async def execute_device_command(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute device command action"""
        try:
            device_id = action.get("device_id")
            command = action.get("command")
            parameters = action.get("parameters", {})
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.device_service_url}/api/devices/{device_id}/command",
                    json={"command": command, "parameters": parameters}
                )
                
                if response.status_code == 200:
                    return {"success": True, "message": "Device command executed"}
                else:
                    return {"success": False, "message": f"Device command failed: {response.text}"}
                    
        except Exception as e:
            return {"success": False, "message": str(e)}
            
    async def execute_notification(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute notification action"""
        # TODO: Implement notification system
        logger.info(f"Notification: {action.get('title')} - {action.get('message')}")
        return {"success": True, "message": "Notification sent"}
        
    async def execute_webhook(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute webhook action"""
        try:
            url = action.get("url")
            method = action.get("method", "POST")
            headers = action.get("headers", {})
            payload = action.get("payload", {})
            
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=payload
                )
                
                if response.status_code < 400:
                    return {"success": True, "message": "Webhook executed"}
                else:
                    return {"success": False, "message": f"Webhook failed: {response.status_code}"}
                    
        except Exception as e:
            return {"success": False, "message": str(e)}

# Global scheduler instance
scheduler_service = SchedulerService()