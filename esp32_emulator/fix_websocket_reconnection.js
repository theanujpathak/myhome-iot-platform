// Enhanced WebSocket connection with automatic reconnection
// This code snippet can be added to the emulator dashboard

// Replace the existing socket connection code with this enhanced version:

let socket;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;
let isConnected = false;

function connectWebSocket() {
    try {
        socket = io();
        
        socket.on('connect', function() {
            console.log('✅ Connected to emulator WebSocket');
            updateMQTTStatus(true);
            isConnected = true;
            reconnectAttempts = 0;
        });

        socket.on('disconnect', function() {
            console.log('❌ Disconnected from emulator WebSocket');
            updateMQTTStatus(false);
            isConnected = false;
            
            // Attempt to reconnect
            if (reconnectAttempts < maxReconnectAttempts) {
                setTimeout(() => {
                    reconnectAttempts++;
                    console.log(`Attempting to reconnect... (${reconnectAttempts}/${maxReconnectAttempts})`);
                    connectWebSocket();
                }, 2000 * reconnectAttempts); // Exponential backoff
            } else {
                console.log('Max reconnection attempts reached. Using polling fallback.');
                startPollingFallback();
            }
        });

        socket.on('device_list', function(deviceList) {
            devices = {};
            deviceList.forEach(device => {
                devices[device.device_id] = device;
            });
            updateDeviceDisplay();
            updateSensorReadings();
            updateChart();
        });

        socket.on('device_state_changed', function(data) {
            devices[data.device_id] = data.state;
            updateDeviceDisplay();
            updateSensorReadings();
            updateChart();
        });

        socket.on('devices_updated', function(deviceList) {
            deviceList.forEach(device => {
                devices[device.device_id] = device;
            });
            updateDeviceDisplay();
            updateSensorReadings();
            updateChart();
        });

        socket.on('connect_error', function(error) {
            console.error('WebSocket connection error:', error);
            updateMQTTStatus(false);
            
            // Fall back to polling if WebSocket fails
            if (reconnectAttempts < maxReconnectAttempts) {
                setTimeout(() => {
                    reconnectAttempts++;
                    connectWebSocket();
                }, 3000);
            } else {
                startPollingFallback();
            }
        });

    } catch (error) {
        console.error('Failed to initialize WebSocket:', error);
        startPollingFallback();
    }
}

// Polling fallback when WebSocket fails
function startPollingFallback() {
    console.log('Starting polling fallback...');
    updateMQTTStatus(false); // Indicate WebSocket is down but polling is active
    
    setInterval(async () => {
        try {
            const response = await fetch('/api/devices');
            if (response.ok) {
                const deviceList = await response.json();
                
                // Update devices
                devices = {};
                deviceList.forEach(device => {
                    devices[device.device_id] = device;
                });
                
                updateDeviceDisplay();
                updateSensorReadings();
                updateChart();
                
                // Try to reconnect WebSocket periodically
                if (!isConnected && reconnectAttempts < maxReconnectAttempts) {
                    reconnectAttempts++;
                    console.log('Attempting WebSocket reconnection during polling...');
                    connectWebSocket();
                }
            }
        } catch (error) {
            console.error('Polling fallback error:', error);
        }
    }, 5000); // Poll every 5 seconds
}

// Enhanced control functions that work with both WebSocket and HTTP
function simulateSensor(deviceId) {
    if (isConnected && socket) {
        socket.emit('simulate_sensor_reading', {device_id: deviceId});
    } else {
        // Fallback to HTTP API + manual refresh
        fetch('/api/devices', { method: 'GET' })
            .then(response => response.json())
            .then(deviceList => {
                devices = {};
                deviceList.forEach(device => {
                    devices[device.device_id] = device;
                });
                updateDeviceDisplay();
                updateSensorReadings();
                updateChart();
            });
    }
}

function toggleOnline(deviceId) {
    if (isConnected && socket) {
        socket.emit('toggle_device_online', {device_id: deviceId});
    } else {
        // For demonstration - simulate toggle
        if (devices[deviceId]) {
            devices[deviceId].is_online = !devices[deviceId].is_online;
            updateDeviceDisplay();
        }
    }
}

// Initialize connection when page loads
document.addEventListener('DOMContentLoaded', function() {
    initChart();
    connectWebSocket();
});

console.log('Enhanced WebSocket reconnection loaded!');