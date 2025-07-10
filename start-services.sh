#!/bin/bash

# Environment variables for the updated configuration
export DATABASE_URL="postgresql://homeuser:homepass@localhost:5433/home_automation"
export REDIS_URL="redis://localhost:6380"
export MQTT_HOST="localhost"
export MQTT_PORT="1884"
export KEYCLOAK_URL="http://localhost:8080"
export KEYCLOAK_REALM="home-automation"
export KEYCLOAK_CLIENT_ID="home-automation-backend"

echo "Starting Home Automation services with updated configuration..."
echo "Database: $DATABASE_URL"
echo "Redis: $REDIS_URL"
echo "MQTT: $MQTT_HOST:$MQTT_PORT"
echo "Keycloak: $KEYCLOAK_URL"

# Start User Service
echo "Starting User Service..."
cd backend/user-service
source venv/bin/activate
python main.py > user-service.log 2>&1 & echo $! > user-service.pid
cd ../..

# Start Device Service  
echo "Starting Device Service..."
cd backend/device-service
source venv/bin/activate
python main.py > device-service.log 2>&1 & echo $! > device-service.pid
cd ../..

# Start Scheduler Service
echo "Starting Scheduler Service..."
cd backend/scheduler-service
source venv/bin/activate
python main.py > scheduler-service.log 2>&1 & echo $! > scheduler-service.pid
cd ../..

# Start OTA Service
echo "Starting OTA Service..."
cd backend/ota-service
source venv/bin/activate
python main.py > ota-service.log 2>&1 & echo $! > ota-service.pid
cd ../..

echo "All services started. Waiting for initialization..."
sleep 5

echo "Service Status:"
echo "User Service (3001): $(curl -s http://localhost:3001/health 2>/dev/null || echo 'Not responding')"
echo "Device Service (3002): $(curl -s http://localhost:3002/health 2>/dev/null || echo 'Not responding')"
echo "Scheduler Service (3003): $(curl -s http://localhost:3003/health 2>/dev/null || echo 'Not responding')"
echo "OTA Service (3004): $(curl -s http://localhost:3004/health 2>/dev/null || echo 'Not responding')"