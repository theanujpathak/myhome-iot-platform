// ESP32 Emulator Integration Service
// This service connects the user dashboard with the ESP32 emulator for live data

import { io } from 'socket.io-client';

class EmulatorService {
  constructor() {
    this.emulatorUrl = 'http://localhost:5000'; // ESP32 emulator endpoint
    this.socket = null;
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.subscriptions = new Map();
  }

  // Initialize connection to ESP32 emulator
  async connect() {
    try {
      // Try to establish WebSocket connection
      this.socket = io(this.emulatorUrl, {
        autoConnect: false,
        reconnection: true,
        reconnectionAttempts: this.maxReconnectAttempts,
        reconnectionDelay: 2000,
        timeout: 5000
      });
      
      this.setupSocketListeners();
      this.socket.connect();
    } catch (error) {
      console.error('Failed to connect to ESP32 emulator:', error);
      this.startPolling();
    }
  }

  setupSocketListeners() {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('Connected to ESP32 emulator');
      this.isConnected = true;
      this.reconnectAttempts = 0;
    });

    this.socket.on('disconnect', () => {
      console.log('Disconnected from ESP32 emulator');
      this.isConnected = false;
      this.attemptReconnect();
    });

    this.socket.on('device_state_changed', (data) => {
      this.notifySubscribers('device_state_changed', data);
    });

    this.socket.on('devices_updated', (deviceList) => {
      this.notifySubscribers('devices_updated', deviceList);
    });

    this.socket.on('sensor_reading', (data) => {
      this.notifySubscribers('sensor_reading', data);
    });
  }

  // HTTP polling fallback
  async startPolling() {
    console.log('Starting HTTP polling for ESP32 emulator data');
    
    setInterval(async () => {
      try {
        const response = await fetch(`${this.emulatorUrl}/api/devices`);
        if (response.ok) {
          const devices = await response.json();
          this.notifySubscribers('devices_updated', devices);
        }
      } catch (error) {
        console.warn('ESP32 emulator polling error:', error);
      }
    }, 5000); // Poll every 5 seconds
  }

  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect to ESP32 emulator (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      
      setTimeout(() => {
        if (this.socket) {
          this.socket.connect();
        } else {
          this.connect();
        }
      }, 2000 * this.reconnectAttempts); // Exponential backoff
    } else {
      console.log('Max reconnection attempts reached, falling back to HTTP polling');
      this.startPolling();
    }
  }

  // Subscribe to emulator events
  subscribe(event, callback) {
    if (!this.subscriptions.has(event)) {
      this.subscriptions.set(event, new Set());
    }
    this.subscriptions.get(event).add(callback);

    // Return unsubscribe function
    return () => {
      const callbacks = this.subscriptions.get(event);
      if (callbacks) {
        callbacks.delete(callback);
      }
    };
  }

  notifySubscribers(event, data) {
    const callbacks = this.subscriptions.get(event);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('Error in emulator subscription callback:', error);
        }
      });
    }
  }

  // Send commands to emulated devices
  async controlDevice(deviceId, command, parameters) {
    try {
      if (this.isConnected && this.socket) {
        // Use WebSocket if available
        this.socket.emit('device_command', {
          device_id: deviceId,
          command: command,
          parameters: parameters
        });
      } else {
        // Fallback to HTTP
        const response = await fetch(`${this.emulatorUrl}/api/devices/${deviceId}/control`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            [command]: parameters
          })
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
      }
    } catch (error) {
      console.error('Failed to control emulated device:', error);
      throw error;
    }
  }

  // Get current device states from emulator
  async getDeviceStates() {
    try {
      const response = await fetch(`${this.emulatorUrl}/api/devices`);
      if (response.ok) {
        return await response.json();
      }
      return [];
    } catch (error) {
      console.warn('Failed to get device states from emulator:', error);
      return [];
    }
  }

  // Simulate sensor reading for a device
  async simulateSensorReading(deviceId) {
    try {
      if (this.isConnected && this.socket) {
        this.socket.emit('simulate_sensor_reading', { device_id: deviceId });
      } else {
        // Generate mock sensor data
        const mockData = this.generateMockSensorData(deviceId);
        this.notifySubscribers('sensor_reading', mockData);
      }
    } catch (error) {
      console.error('Failed to simulate sensor reading:', error);
    }
  }

  generateMockSensorData(deviceId) {
    return {
      device_id: deviceId,
      timestamp: new Date().toISOString(),
      temperature: 20 + Math.random() * 15,
      humidity: 30 + Math.random() * 40,
      motion_detected: Math.random() > 0.8,
      light_level: 50 + Math.random() * 50,
      power_consumption: Math.random() * 25
    };
  }

  // Toggle device online/offline status
  async toggleDeviceOnline(deviceId) {
    try {
      if (this.isConnected && this.socket) {
        this.socket.emit('toggle_device_online', { device_id: deviceId });
      }
    } catch (error) {
      console.error('Failed to toggle device online status:', error);
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.isConnected = false;
    this.subscriptions.clear();
  }
}

// Create singleton instance
const emulatorService = new EmulatorService();

export default emulatorService;