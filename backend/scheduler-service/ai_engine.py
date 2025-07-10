import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass
import json
import statistics
import math
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Schedule, ScheduleExecution, AutomationRule

logger = logging.getLogger(__name__)

@dataclass
class DeviceUsagePattern:
    device_id: str
    hour: int
    day_of_week: int
    usage_probability: float
    avg_duration: float
    common_states: Dict[str, Any]

@dataclass
class UserBehaviorPattern:
    user_id: str
    wake_time_range: Tuple[int, int]  # (start_hour, end_hour)
    sleep_time_range: Tuple[int, int]
    weekday_patterns: List[DeviceUsagePattern]
    weekend_patterns: List[DeviceUsagePattern]
    location_preferences: Dict[str, float]

class AIAutomationEngine:
    def __init__(self):
        self.device_usage_history = defaultdict(lambda: deque(maxlen=1000))
        self.user_patterns = {}
        self.learning_enabled = True
        self.min_data_points = 10
        
    async def start(self):
        """Start the AI engine and begin learning"""
        logger.info("Starting AI Automation Engine")
        # Start periodic analysis
        asyncio.create_task(self.periodic_analysis())
        
    async def periodic_analysis(self):
        """Periodically analyze patterns and suggest automations"""
        while True:
            try:
                await self.analyze_user_patterns()
                await self.suggest_automations()
                await self.optimize_existing_rules()
                
                # Run every hour
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"Error in periodic analysis: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
                
    async def record_device_usage(self, user_id: str, device_id: str, action: str, 
                                 states: Dict[str, Any], timestamp: datetime = None):
        """Record device usage for pattern learning"""
        if not self.learning_enabled:
            return
            
        if timestamp is None:
            timestamp = datetime.utcnow()
            
        usage_record = {
            'user_id': user_id,
            'device_id': device_id,
            'action': action,
            'states': states,
            'timestamp': timestamp,
            'hour': timestamp.hour,
            'day_of_week': timestamp.weekday(),
            'is_weekend': timestamp.weekday() >= 5
        }
        
        self.device_usage_history[user_id].append(usage_record)
        
        # Trigger pattern analysis if we have enough data
        if len(self.device_usage_history[user_id]) >= self.min_data_points:
            await self.analyze_user_patterns(user_id)
            
    async def analyze_user_patterns(self, user_id: str = None):
        """Analyze user behavior patterns"""
        try:
            users_to_analyze = [user_id] if user_id else list(self.device_usage_history.keys())
            
            for uid in users_to_analyze:
                if uid not in self.device_usage_history:
                    continue
                    
                usage_data = list(self.device_usage_history[uid])
                if len(usage_data) < self.min_data_points:
                    continue
                    
                # Analyze wake/sleep patterns
                wake_sleep = self._analyze_wake_sleep_patterns(usage_data)
                
                # Analyze device usage patterns
                weekday_patterns = self._analyze_device_patterns(usage_data, is_weekend=False)
                weekend_patterns = self._analyze_device_patterns(usage_data, is_weekend=True)
                
                # Analyze location preferences
                location_prefs = self._analyze_location_preferences(usage_data)
                
                self.user_patterns[uid] = UserBehaviorPattern(
                    user_id=uid,
                    wake_time_range=wake_sleep['wake_time'],
                    sleep_time_range=wake_sleep['sleep_time'],
                    weekday_patterns=weekday_patterns,
                    weekend_patterns=weekend_patterns,
                    location_preferences=location_prefs
                )
                
                logger.info(f"Updated behavior patterns for user {uid}")
                
        except Exception as e:
            logger.error(f"Error analyzing user patterns: {e}")
            
    def _analyze_wake_sleep_patterns(self, usage_data: List[Dict]) -> Dict[str, Tuple[int, int]]:
        """Analyze wake and sleep time patterns"""
        morning_activities = []
        evening_activities = []
        
        for record in usage_data:
            hour = record['hour']
            if 5 <= hour <= 11:  # Morning activities
                morning_activities.append(hour)
            elif 20 <= hour <= 23:  # Evening activities
                evening_activities.append(hour)
                
        wake_time = (
            min(morning_activities) if morning_activities else 7,
            max(morning_activities) if morning_activities else 9
        )
        
        sleep_time = (
            min(evening_activities) if evening_activities else 22,
            max(evening_activities) if evening_activities else 23
        )
        
        return {
            'wake_time': wake_time,
            'sleep_time': sleep_time
        }
        
    def _analyze_device_patterns(self, usage_data: List[Dict], is_weekend: bool) -> List[DeviceUsagePattern]:
        """Analyze device usage patterns for weekdays or weekends"""
        filtered_data = [r for r in usage_data if (r['is_weekend'] == is_weekend)]
        
        if not filtered_data:
            return []
            
        device_patterns = defaultdict(lambda: defaultdict(list))
        
        # Group by device and hour
        for record in filtered_data:
            device_id = record['device_id']
            hour = record['hour']
            device_patterns[device_id][hour].append(record)
            
        patterns = []
        for device_id, hourly_data in device_patterns.items():
            for hour, records in hourly_data.items():
                if len(records) < 3:  # Need at least 3 occurrences
                    continue
                    
                # Calculate usage probability (frequency)
                total_possible_times = len([r for r in filtered_data if r['hour'] == hour])
                usage_probability = len(records) / max(total_possible_times, 1)
                
                # Calculate average duration (simplified)
                avg_duration = 30.0  # Default 30 minutes
                
                # Find common states
                common_states = self._find_common_states(records)
                
                patterns.append(DeviceUsagePattern(
                    device_id=device_id,
                    hour=hour,
                    day_of_week=records[0]['day_of_week'],
                    usage_probability=usage_probability,
                    avg_duration=avg_duration,
                    common_states=common_states
                ))
                
        return patterns
        
    def _find_common_states(self, records: List[Dict]) -> Dict[str, Any]:
        """Find the most common states for a device usage pattern"""
        state_counts = defaultdict(lambda: defaultdict(int))
        
        for record in records:
            for key, value in record['states'].items():
                state_counts[key][str(value)] += 1
                
        common_states = {}
        for state_key, value_counts in state_counts.items():
            if value_counts:
                most_common_value = max(value_counts.items(), key=lambda x: x[1])[0]
                # Try to convert back to appropriate type
                try:
                    if most_common_value.lower() in ['true', 'false']:
                        common_states[state_key] = most_common_value.lower() == 'true'
                    elif most_common_value.replace('.', '').isdigit():
                        common_states[state_key] = float(most_common_value)
                    else:
                        common_states[state_key] = most_common_value
                except:
                    common_states[state_key] = most_common_value
                    
        return common_states
        
    def _analyze_location_preferences(self, usage_data: List[Dict]) -> Dict[str, float]:
        """Analyze location usage preferences"""
        # This would require location data in the usage records
        # For now, return empty preferences
        return {}
        
    async def suggest_automations(self):
        """Suggest new automation rules based on learned patterns"""
        try:
            db = SessionLocal()
            
            for user_id, pattern in self.user_patterns.items():
                suggestions = []
                
                # Morning routine suggestions
                morning_devices = [p for p in pattern.weekday_patterns 
                                 if pattern.wake_time_range[0] <= p.hour <= pattern.wake_time_range[1]]
                
                if morning_devices:
                    suggestion = self._create_morning_routine_suggestion(user_id, morning_devices)
                    if suggestion:
                        suggestions.append(suggestion)
                
                # Evening routine suggestions
                evening_devices = [p for p in pattern.weekday_patterns 
                                 if pattern.sleep_time_range[0] <= p.hour <= pattern.sleep_time_range[1]]
                
                if evening_devices:
                    suggestion = self._create_evening_routine_suggestion(user_id, evening_devices)
                    if suggestion:
                        suggestions.append(suggestion)
                
                # Energy saving suggestions
                energy_suggestion = self._create_energy_saving_suggestion(user_id, pattern)
                if energy_suggestion:
                    suggestions.append(energy_suggestion)
                
                # Store suggestions (in a real implementation, you'd have a suggestions table)
                for suggestion in suggestions:
                    logger.info(f"AI Suggestion for {user_id}: {suggestion['name']}")
                    
            db.close()
            
        except Exception as e:
            logger.error(f"Error suggesting automations: {e}")
            
    def _create_morning_routine_suggestion(self, user_id: str, morning_devices: List[DeviceUsagePattern]) -> Optional[Dict]:
        """Create a morning routine automation suggestion"""
        if len(morning_devices) < 2:
            return None
            
        # Find the earliest morning activity
        earliest_hour = min(p.hour for p in morning_devices)
        
        actions = []
        for pattern in morning_devices:
            if pattern.usage_probability > 0.6:  # High confidence
                actions.append({
                    "type": "device_command",
                    "device_id": pattern.device_id,
                    "command": "set_state",
                    "parameters": pattern.common_states
                })
                
        if not actions:
            return None
            
        return {
            "name": "AI Morning Routine",
            "description": f"Automatically suggested based on your morning habits",
            "trigger_type": "time",
            "trigger_config": {
                "time": f"{earliest_hour:02d}:00",
                "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                "timezone": "UTC"
            },
            "actions": actions,
            "confidence": sum(p.usage_probability for p in morning_devices) / len(morning_devices)
        }
        
    def _create_evening_routine_suggestion(self, user_id: str, evening_devices: List[DeviceUsagePattern]) -> Optional[Dict]:
        """Create an evening routine automation suggestion"""
        if len(evening_devices) < 2:
            return None
            
        # Find the latest evening activity
        latest_hour = max(p.hour for p in evening_devices)
        
        actions = []
        for pattern in evening_devices:
            if pattern.usage_probability > 0.6:  # High confidence
                # For evening, often we want to turn things off
                if "power" in pattern.common_states:
                    evening_action = pattern.common_states.copy()
                    if pattern.device_id.lower() in ['light', 'lamp', 'tv']:
                        evening_action["power"] = False
                else:
                    evening_action = pattern.common_states
                    
                actions.append({
                    "type": "device_command",
                    "device_id": pattern.device_id,
                    "command": "set_state",
                    "parameters": evening_action
                })
                
        if not actions:
            return None
            
        return {
            "name": "AI Evening Routine",
            "description": f"Automatically suggested goodnight routine",
            "trigger_type": "time",
            "trigger_config": {
                "time": f"{latest_hour:02d}:30",
                "days": ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"],
                "timezone": "UTC"
            },
            "actions": actions,
            "confidence": sum(p.usage_probability for p in evening_devices) / len(evening_devices)
        }
        
    def _create_energy_saving_suggestion(self, user_id: str, pattern: UserBehaviorPattern) -> Optional[Dict]:
        """Create energy saving automation suggestions"""
        # Find devices that are commonly left on when user is likely asleep
        sleep_start = pattern.sleep_time_range[1]
        wake_start = pattern.wake_time_range[0]
        
        overnight_patterns = []
        for p in pattern.weekday_patterns + pattern.weekend_patterns:
            if p.hour >= sleep_start or p.hour <= wake_start:
                if "power" in p.common_states and p.common_states["power"]:
                    overnight_patterns.append(p)
                    
        if not overnight_patterns:
            return None
            
        actions = []
        for pattern in overnight_patterns:
            actions.append({
                "type": "device_command",
                "device_id": pattern.device_id,
                "command": "set_power",
                "parameters": {"power": False}
            })
            
        return {
            "name": "AI Energy Saver",
            "description": "Turn off devices during sleep hours to save energy",
            "trigger_type": "time",
            "trigger_config": {
                "time": f"{sleep_start + 1:02d}:00",
                "days": ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"],
                "timezone": "UTC"
            },
            "actions": actions,
            "confidence": 0.8
        }
        
    async def optimize_existing_rules(self):
        """Optimize existing automation rules based on execution history"""
        try:
            db = SessionLocal()
            
            # Find underperforming rules
            rules = db.query(AutomationRule).filter(AutomationRule.enabled == True).all()
            
            for rule in rules:
                # Analyze execution history (would need execution tracking for automation rules)
                # For now, just log optimization opportunities
                logger.info(f"Analyzing rule {rule.name} for optimization opportunities")
                
            db.close()
            
        except Exception as e:
            logger.error(f"Error optimizing rules: {e}")
            
    async def predict_device_usage(self, user_id: str, device_id: str, 
                                  target_time: datetime) -> float:
        """Predict the probability of device usage at a specific time"""
        if user_id not in self.user_patterns:
            return 0.5  # Default probability
            
        pattern = self.user_patterns[user_id]
        target_hour = target_time.hour
        is_weekend = target_time.weekday() >= 5
        
        patterns_to_check = pattern.weekend_patterns if is_weekend else pattern.weekday_patterns
        
        for device_pattern in patterns_to_check:
            if (device_pattern.device_id == device_id and 
                device_pattern.hour == target_hour):
                return device_pattern.usage_probability
                
        return 0.1  # Low probability if no pattern found
        
    async def get_user_insights(self, user_id: str) -> Dict[str, Any]:
        """Get AI insights for a specific user"""
        if user_id not in self.user_patterns:
            return {"message": "Not enough data for insights"}
            
        pattern = self.user_patterns[user_id]
        
        insights = {
            "wake_time_range": f"{pattern.wake_time_range[0]:02d}:00 - {pattern.wake_time_range[1]:02d}:00",
            "sleep_time_range": f"{pattern.sleep_time_range[0]:02d}:00 - {pattern.sleep_time_range[1]:02d}:00",
            "most_used_devices": self._get_most_used_devices(pattern),
            "energy_saving_opportunities": self._get_energy_opportunities(pattern),
            "automation_suggestions": await self._get_automation_suggestions(user_id, pattern)
        }
        
        return insights
        
    def _get_most_used_devices(self, pattern: UserBehaviorPattern) -> List[Dict]:
        """Get most frequently used devices"""
        device_usage = defaultdict(float)
        
        for p in pattern.weekday_patterns + pattern.weekend_patterns:
            device_usage[p.device_id] += p.usage_probability
            
        sorted_devices = sorted(device_usage.items(), key=lambda x: x[1], reverse=True)
        
        return [{"device_id": device, "usage_score": score} 
                for device, score in sorted_devices[:5]]
        
    def _get_energy_opportunities(self, pattern: UserBehaviorPattern) -> List[str]:
        """Identify energy saving opportunities"""
        opportunities = []
        
        # Check for devices left on during sleep hours
        sleep_start = pattern.sleep_time_range[1]
        wake_start = pattern.wake_time_range[0]
        
        for p in pattern.weekday_patterns + pattern.weekend_patterns:
            if (p.hour >= sleep_start or p.hour <= wake_start) and \
               "power" in p.common_states and p.common_states["power"]:
                opportunities.append(f"Device {p.device_id} is often on during sleep hours")
                
        return opportunities
        
    async def _get_automation_suggestions(self, user_id: str, pattern: UserBehaviorPattern) -> List[Dict]:
        """Get automation suggestions for the user"""
        suggestions = []
        
        # Morning routine
        morning_devices = [p for p in pattern.weekday_patterns 
                          if pattern.wake_time_range[0] <= p.hour <= pattern.wake_time_range[1]]
        if len(morning_devices) >= 2:
            suggestions.append({
                "type": "morning_routine",
                "confidence": sum(p.usage_probability for p in morning_devices) / len(morning_devices),
                "description": "Create a morning automation routine"
            })
            
        # Evening routine
        evening_devices = [p for p in pattern.weekday_patterns 
                          if pattern.sleep_time_range[0] <= p.hour <= pattern.sleep_time_range[1]]
        if len(evening_devices) >= 2:
            suggestions.append({
                "type": "evening_routine",
                "confidence": sum(p.usage_probability for p in evening_devices) / len(evening_devices),
                "description": "Create an evening automation routine"
            })
            
        return suggestions

# Global AI engine instance
ai_engine = AIAutomationEngine()