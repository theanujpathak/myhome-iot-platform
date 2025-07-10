import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Device, DeviceState
import os

logger = logging.getLogger(__name__)

class MQTTClient:
    def __init__(self):
        self.client = mqtt.Client()
        self.mqtt_host = os.getenv("MQTT_HOST", "localhost")
        self.mqtt_port = int(os.getenv("MQTT_PORT", "1884"))
        self.mqtt_user = os.getenv("MQTT_USER", "")
        self.mqtt_password = os.getenv("MQTT_PASSWORD", "")
        
        # Setup callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        # Authentication if provided
        if self.mqtt_user and self.mqtt_password:
            self.client.username_pw_set(self.mqtt_user, self.mqtt_password)
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("Connected to MQTT broker")
            # Subscribe to device topics
            client.subscribe("homeautomation/devices/+/status")
            client.subscribe("homeautomation/devices/+/state")
            client.subscribe("homeautomation/devices/+/online")
        else:
            logger.error(f"Failed to connect to MQTT broker: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        logger.warning(f"Disconnected from MQTT broker: {rc}")
    
    def on_message(self, client, userdata, msg):
        try:
            topic_parts = msg.topic.split('/')
            if len(topic_parts) < 4:
                return
            
            device_id = topic_parts[2]
            message_type = topic_parts[3]
            payload = json.loads(msg.payload.decode())
            
            logger.info(f"Received MQTT message: {msg.topic} - {payload}")
            
            # Process message based on type
            if message_type == "status":
                self.handle_device_status(device_id, payload)
            elif message_type == "state":
                self.handle_device_state(device_id, payload)
            elif message_type == "online":
                self.handle_device_online(device_id, payload)
                
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def handle_device_status(self, device_id: str, payload: Dict[str, Any]):
        """Handle device status updates"""
        db = SessionLocal()
        try:
            device = db.query(Device).filter(Device.device_id == device_id).first()
            if device:
                device.is_online = payload.get("online", False)
                device.last_seen = datetime.utcnow()
                if "firmware_version" in payload:
                    device.firmware_version = payload["firmware_version"]
                db.commit()
        except Exception as e:
            logger.error(f"Error updating device status: {e}")
        finally:
            db.close()
    
    def handle_device_state(self, device_id: str, payload: Dict[str, Any]):
        """Handle device state updates"""
        db = SessionLocal()
        try:
            device = db.query(Device).filter(Device.device_id == device_id).first()
            if device:
                # Update device states
                for state_key, state_value in payload.items():
                    # Determine state type
                    state_type = "string"
                    if isinstance(state_value, bool):
                        state_type = "boolean"
                    elif isinstance(state_value, (int, float)):
                        state_type = "number"
                    elif isinstance(state_value, dict):
                        state_type = "json"
                    
                    device_state = DeviceState(
                        device_id=device.id,
                        state_key=state_key,
                        state_value=json.dumps(state_value) if state_type == "json" else str(state_value),
                        state_type=state_type
                    )
                    db.add(device_state)
                
                device.last_seen = datetime.utcnow()
                db.commit()
        except Exception as e:
            logger.error(f"Error updating device state: {e}")
        finally:
            db.close()
    
    def handle_device_online(self, device_id: str, payload: Dict[str, Any]):
        """Handle device online/offline status"""
        db = SessionLocal()
        try:
            device = db.query(Device).filter(Device.device_id == device_id).first()
            if device:
                device.is_online = payload.get("online", False)
                device.last_seen = datetime.utcnow()
                db.commit()
        except Exception as e:
            logger.error(f"Error updating device online status: {e}")
        finally:
            db.close()
    
    def publish_device_command(self, device_id: str, command: str, parameters: Optional[Dict[str, Any]] = None):
        """Publish command to device"""
        try:
            topic = f"homeautomation/devices/{device_id}/command"
            payload = {
                "command": command,
                "parameters": parameters or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.client.publish(topic, json.dumps(payload))
            logger.info(f"Published command to {topic}: {payload}")
            return True
        except Exception as e:
            logger.error(f"Error publishing device command: {e}")
            return False
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            self.client.connect(self.mqtt_host, self.mqtt_port, 60)
            self.client.loop_start()
            return True
        except Exception as e:
            logger.error(f"Error connecting to MQTT broker: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.client.loop_stop()
        self.client.disconnect()

# Global MQTT client instance
mqtt_client = MQTTClient()