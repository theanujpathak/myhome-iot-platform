#!/usr/bin/env python3
"""
ESP32 Device Emulator
Simulates an ESP32 device with multiple I/O pins and MQTT communication
"""

import paho.mqtt.client as mqtt
import json
import time
import threading
import random
import uuid
import sys
from datetime import datetime
from typing import Dict, Any, List

class ESP32Pin:
    def __init__(self, pin_number: int, pin_type: str, function: str = None, name: str = None):
        self.pin_number = pin_number
        self.pin_type = pin_type  # 'digital_input', 'digital_output', 'analog_input', 'analog_output'
        self.function = function or f"pin_{pin_number}"
        self.name = name or f"Pin {pin_number}"
        self.value = 0
        self.last_updated = datetime.now()
        
    def set_value(self, value):
        if self.pin_type in ['digital_output', 'analog_output']:
            self.value = value
            self.last_updated = datetime.now()
            return True
        return False
    
    def get_value(self):
        if self.pin_type in ['digital_input', 'analog_input']:
            # Simulate sensor readings
            if self.function == 'temperature':
                return round(random.uniform(18.0, 32.0), 2)
            elif self.function == 'humidity':
                return round(random.uniform(30.0, 80.0), 2)
            elif self.function == 'motion':
                return random.choice([0, 1])
            elif self.function == 'light':
                return random.randint(0, 1023)
            else:
                return self.value
        return self.value
    
    def to_dict(self):
        return {
            'pin_number': self.pin_number,
            'pin_type': self.pin_type,
            'function': self.function,
            'name': self.name,
            'value': self.get_value() if self.pin_type.endswith('_input') else self.value,
            'last_updated': self.last_updated.isoformat()
        }

class ESP32Emulator:
    def __init__(self, device_id: str, device_secret: str, device_name: str = None):
        self.device_id = device_id
        self.device_secret = device_secret
        self.device_name = device_name or f"ESP32_{device_id[-6:]}"
        self.mqtt_client = None
        self.connected = False
        self.pins: Dict[int, ESP32Pin] = {}
        self.status = "offline"
        self.last_heartbeat = datetime.now()
        
        # MQTT Configuration
        self.mqtt_host = "localhost"
        self.mqtt_port = 1884
        self.mqtt_keepalive = 60
        
        # Topics
        self.command_topic = f"devices/{self.device_id}/commands"
        self.state_topic = f"devices/{self.device_id}/state"
        self.heartbeat_topic = f"devices/{self.device_id}/heartbeat"
        self.config_topic = f"devices/{self.device_id}/config"
        
        # Initialize default pins
        self.setup_default_pins()
        
    def setup_default_pins(self):
        """Setup default pin configuration"""
        # Digital outputs (LED, relay)
        self.pins[2] = ESP32Pin(2, 'digital_output', 'led', 'Built-in LED')
        self.pins[4] = ESP32Pin(4, 'digital_output', 'relay', 'Relay Output')
        
        # Digital inputs (buttons, switches)
        self.pins[18] = ESP32Pin(18, 'digital_input', 'button', 'Push Button')
        self.pins[19] = ESP32Pin(19, 'digital_input', 'motion', 'Motion Sensor')
        
        # Analog inputs (sensors)
        self.pins[34] = ESP32Pin(34, 'analog_input', 'temperature', 'Temperature Sensor')
        self.pins[35] = ESP32Pin(35, 'analog_input', 'light', 'Light Sensor')
        self.pins[36] = ESP32Pin(36, 'analog_input', 'humidity', 'Humidity Sensor')
        
        # PWM outputs
        self.pins[5] = ESP32Pin(5, 'analog_output', 'pwm', 'PWM Output')
        
    def connect_mqtt(self):
        """Connect to MQTT broker"""
        try:
            self.mqtt_client = mqtt.Client(client_id=f"esp32_{self.device_id}")
            self.mqtt_client.username_pw_set(self.device_id, self.device_secret)
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_message = self.on_mqtt_message
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
            
            print(f"[{self.device_name}] Connecting to MQTT broker at {self.mqtt_host}:{self.mqtt_port}")
            self.mqtt_client.connect(self.mqtt_host, self.mqtt_port, self.mqtt_keepalive)
            self.mqtt_client.loop_start()
            
        except Exception as e:
            print(f"[{self.device_name}] MQTT connection failed: {e}")
            
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            print(f"[{self.device_name}] Connected to MQTT broker")
            self.connected = True
            self.status = "online"
            
            # Subscribe to command topic
            client.subscribe(self.command_topic)
            client.subscribe(self.config_topic)
            
            # Send device info
            self.send_device_info()
            
            # Start heartbeat
            self.start_heartbeat()
            
        else:
            print(f"[{self.device_name}] MQTT connection failed with code {rc}")
            
    def on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        print(f"[{self.device_name}] Disconnected from MQTT broker")
        self.connected = False
        self.status = "offline"
        
    def on_mqtt_message(self, client, userdata, msg):
        """Handle incoming MQTT messages"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            print(f"[{self.device_name}] Received message on {topic}: {payload}")
            
            if topic == self.command_topic:
                self.handle_command(payload)
            elif topic == self.config_topic:
                self.handle_config(payload)
                
        except Exception as e:
            print(f"[{self.device_name}] Error processing message: {e}")
            
    def handle_command(self, command: Dict[str, Any]):
        """Handle device commands"""
        cmd_type = command.get('type')
        
        if cmd_type == 'set_pin':
            pin_number = command.get('pin')
            value = command.get('value')
            
            if pin_number in self.pins:
                pin = self.pins[pin_number]
                if pin.set_value(value):
                    print(f"[{self.device_name}] Set pin {pin_number} to {value}")
                    self.send_state_update()
                else:
                    print(f"[{self.device_name}] Cannot set input pin {pin_number}")
            else:
                print(f"[{self.device_name}] Pin {pin_number} not found")
                
        elif cmd_type == 'get_pin':
            pin_number = command.get('pin')
            if pin_number in self.pins:
                pin = self.pins[pin_number]
                value = pin.get_value()
                print(f"[{self.device_name}] Pin {pin_number} value: {value}")
                self.send_pin_response(pin_number, value)
            else:
                print(f"[{self.device_name}] Pin {pin_number} not found")
                
        elif cmd_type == 'get_status':
            self.send_device_info()
            
        elif cmd_type == 'reboot':
            print(f"[{self.device_name}] Rebooting...")
            self.reboot()
            
    def handle_config(self, config: Dict[str, Any]):
        """Handle device configuration"""
        if 'pins' in config:
            for pin_config in config['pins']:
                pin_number = pin_config['pin_number']
                pin_type = pin_config['pin_type']
                function = pin_config.get('function', f"pin_{pin_number}")
                name = pin_config.get('name', f"Pin {pin_number}")
                
                self.pins[pin_number] = ESP32Pin(pin_number, pin_type, function, name)
                
            print(f"[{self.device_name}] Pin configuration updated")
            self.send_device_info()
            
    def send_device_info(self):
        """Send device information"""
        device_info = {
            'device_id': self.device_id,
            'device_name': self.device_name,
            'status': self.status,
            'timestamp': datetime.now().isoformat(),
            'pins': [pin.to_dict() for pin in self.pins.values()],
            'capabilities': [
                'digital_io',
                'analog_io',
                'pwm',
                'mqtt',
                'ota_updates'
            ],
            'firmware_version': '1.0.0',
            'chip_model': 'ESP32',
            'mac_address': f"24:6F:28:{random.randint(10,99):02d}:{random.randint(10,99):02d}:{random.randint(10,99):02d}"
        }
        
        self.mqtt_client.publish(self.state_topic, json.dumps(device_info))
        
    def send_state_update(self):
        """Send state update for all pins"""
        state_update = {
            'device_id': self.device_id,
            'timestamp': datetime.now().isoformat(),
            'pins': [pin.to_dict() for pin in self.pins.values()]
        }
        
        self.mqtt_client.publish(self.state_topic, json.dumps(state_update))
        
    def send_pin_response(self, pin_number: int, value: Any):
        """Send response for pin query"""
        response = {
            'device_id': self.device_id,
            'pin_number': pin_number,
            'value': value,
            'timestamp': datetime.now().isoformat()
        }
        
        self.mqtt_client.publish(f"{self.state_topic}/pin_response", json.dumps(response))
        
    def start_heartbeat(self):
        """Start heartbeat thread"""
        def heartbeat():
            while self.connected:
                try:
                    heartbeat_data = {
                        'device_id': self.device_id,
                        'status': self.status,
                        'timestamp': datetime.now().isoformat(),
                        'uptime': int((datetime.now() - self.last_heartbeat).total_seconds())
                    }
                    
                    self.mqtt_client.publish(self.heartbeat_topic, json.dumps(heartbeat_data))
                    time.sleep(30)  # Send heartbeat every 30 seconds
                    
                except Exception as e:
                    print(f"[{self.device_name}] Heartbeat error: {e}")
                    break
                    
        threading.Thread(target=heartbeat, daemon=True).start()
        
    def start_sensor_simulation(self):
        """Start sensor value simulation"""
        def simulate_sensors():
            while self.connected:
                try:
                    # Simulate changing sensor values
                    for pin in self.pins.values():
                        if pin.pin_type in ['digital_input', 'analog_input']:
                            # Randomly update sensor values
                            if random.random() < 0.1:  # 10% chance to update
                                pin.get_value()  # This will generate new random value
                                
                    # Send periodic state updates
                    if random.random() < 0.2:  # 20% chance to send update
                        self.send_state_update()
                        
                    time.sleep(5)  # Check every 5 seconds
                    
                except Exception as e:
                    print(f"[{self.device_name}] Sensor simulation error: {e}")
                    break
                    
        threading.Thread(target=simulate_sensors, daemon=True).start()
        
    def reboot(self):
        """Simulate device reboot"""
        if self.mqtt_client:
            self.mqtt_client.disconnect()
            
        time.sleep(2)
        print(f"[{self.device_name}] Rebooted")
        self.connect_mqtt()
        
    def run(self):
        """Start the emulator"""
        print(f"[{self.device_name}] Starting ESP32 emulator...")
        print(f"[{self.device_name}] Device ID: {self.device_id}")
        print(f"[{self.device_name}] Device Secret: {self.device_secret}")
        
        self.connect_mqtt()
        self.start_sensor_simulation()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"[{self.device_name}] Shutting down...")
            if self.mqtt_client:
                self.mqtt_client.disconnect()
                self.mqtt_client.loop_stop()

def main():
    """Main function"""
    if len(sys.argv) < 3:
        print("Usage: python esp32_emulator.py <device_id> <device_secret> [device_name]")
        sys.exit(1)
        
    device_id = sys.argv[1]
    device_secret = sys.argv[2]
    device_name = sys.argv[3] if len(sys.argv) > 3 else None
    
    emulator = ESP32Emulator(device_id, device_secret, device_name)
    emulator.run()

if __name__ == "__main__":
    main()