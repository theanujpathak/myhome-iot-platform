# 🏠 MyHome IoT Platform - Complete Access Guide

## 🚀 Quick Start (5 Minutes)

### **1. Start the Platform**
```bash
cd /Users/anujpathak/Projects/myhome.i4planet.com
./start-platform.sh
```

### **2. Open the Admin Portal**
```bash
open admin-portal/admin-portal.html
```

**That's it!** You now have access to the complete IoT platform through a unified admin portal.

---

## 🎯 **Access Methods Summary**

| System | Method | URL/Command | Port |
|--------|--------|-------------|------|
| **🏠 Admin Portal** | Web | `admin-portal/admin-portal.html` | - |
| **📊 Monitoring** | Web/CLI/API | `monitoring-dashboard.html` | 5002 |
| **🚀 Deployment** | Web/CLI/API | `deployment-web.html` | 5001 |
| **⚡ Batch Flashing** | Web/CLI/API | `web-interface.html` | 5000 |
| **📱 Device Service** | API | `http://localhost:3002` | 3002 |
| **🏭 Factory Provisioning** | CLI | `python factory-flash.py` | - |
| **🧪 Testing Framework** | CLI | `python test-framework.py` | - |

---

## 🏠 **Admin Portal - Your Main Dashboard**

The **Admin Portal** is your unified control center for the entire IoT platform.

### **Access:**
```bash
# Method 1: Direct file open
open admin-portal/admin-portal.html

# Method 2: From browser
# Navigate to: file:///Users/anujpathak/Projects/myhome.i4planet.com/admin-portal/admin-portal.html
```

### **Features:**
- **📊 System Overview**: Real-time health and metrics
- **🚨 Alert Management**: View and manage all alerts
- **📱 Device Management**: Monitor connected devices
- **🔄 Firmware Updates**: Deploy firmware updates
- **⚡ Quick Actions**: Emergency stops, health checks
- **🖥️ Embedded Dashboards**: All systems in one place

### **Navigation:**
- **Dashboard** → System overview and quick actions
- **Monitoring** → Real-time monitoring and alerts
- **Deployment** → Firmware deployment automation
- **Batch Flashing** → Mass firmware updates
- **Provisioning** → Factory device provisioning
- **Testing** → Automated testing framework

---

## 📊 **Monitoring System**

### **Web Dashboard:**
```bash
# Open monitoring dashboard
open monitoring/monitoring-dashboard.html

# Or via admin portal
open admin-portal/admin-portal.html → Click "Monitoring"
```

### **CLI Access:**
```bash
cd monitoring

# System status
python monitoring-cli.py status

# Live dashboard
python monitoring-cli.py dashboard

# List alerts
python monitoring-cli.py alerts list

# Show metrics
python monitoring-cli.py metrics
```

### **API Access:**
```bash
# System status
curl -H "X-API-Key: monitoring-api-key-1" http://localhost:5002/api/status

# Active alerts
curl -H "X-API-Key: monitoring-api-key-1" http://localhost:5002/api/alerts?status=active

# Run health checks
curl -X POST -H "X-API-Key: monitoring-api-key-1" http://localhost:5002/api/health-checks/run
```

---

## 🚀 **Deployment System**

### **Web Dashboard:**
```bash
# Open deployment dashboard
open deployment/deployment-web.html

# Or via admin portal
open admin-portal/admin-portal.html → Click "Deployment"
```

### **CLI Access:**
```bash
cd deployment

# List environments
python deployment-cli.py env list

# Create deployment plan
python deployment-cli.py plan create --interactive

# Execute deployment
python deployment-cli.py deploy execute --plan-id PLAN_ID

# Monitor deployment
python deployment-cli.py deploy status --execution-id EXECUTION_ID
```

### **API Access:**
```bash
# List environments
curl -H "X-API-Key: your-api-key" http://localhost:5001/api/environments

# Create deployment plan
curl -X POST -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d @deployment-plan.json \
  http://localhost:5001/api/deployment-plans
```

---

## ⚡ **Batch Flashing System**

### **Web Interface:**
```bash
# Open batch flashing interface
open firmware/batch-flashing/web-interface.html

# Or via admin portal
open admin-portal/admin-portal.html → Click "Batch Flashing"
```

### **CLI Access:**
```bash
cd firmware/batch-flashing

# List batches
python batch-flash-cli.py list

# Create batch interactively
python batch-flash-cli.py create --interactive

# Start batch
python batch-flash-cli.py create --config batch-config.yaml --start

# Monitor batch
python batch-flash-cli.py status BATCH_ID
```

### **API Access:**
```bash
# List batches
curl http://localhost:5000/api/batches

# Create batch
curl -X POST -H "Content-Type: application/json" \
  -d @batch-config.json \
  http://localhost:5000/api/batches
```

---

## 🏭 **Factory Provisioning**

### **Direct Script Execution:**
```bash
cd firmware/factory-provisioning

# Run factory provisioning
python factory-flash.py

# Run with specific configuration
python factory-flash.py --config factory-config.yaml

# Run specific batch
python factory-flash.py --batch-id BATCH_001
```

### **Via Admin Portal:**
```bash
# Open admin portal and navigate to Provisioning tab
open admin-portal/admin-portal.html → Click "Provisioning" → "Start Provisioning"
```

---

## 🧪 **Testing Framework**

### **Direct Script Execution:**
```bash
cd firmware/testing

# Run all tests
python test-framework.py --run-all

# Run specific test
python test-framework.py --test-id TEST_ID

# Generate report
python test-framework.py --generate-report
```

### **Via Admin Portal:**
```bash
# Open admin portal and navigate to Testing tab
open admin-portal/admin-portal.html → Click "Testing" → "Run All Tests"
```

---

## 📱 **Device Service (Your Existing System)**

### **API Access:**
```bash
# Health check
curl http://localhost:3002/health

# List devices
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:3002/api/devices

# Device management
# Your existing device service continues to work as before
```

---

## 🔧 **Platform Management**

### **Start Platform:**
```bash
./start-platform.sh
```
This starts all services with proper dependency management.

### **Stop Platform:**
```bash
./stop-platform.sh
```
This gracefully stops all services.

### **View Logs:**
```bash
# All logs
tail -f logs/*.log

# Specific service
tail -f logs/monitoring-api.log
tail -f logs/deployment-api.log
tail -f logs/batch-flashing-api.log
```

### **Service Status:**
```bash
# Check if services are running
lsof -i :5002  # Monitoring API
lsof -i :5001  # Deployment API
lsof -i :5000  # Batch Flashing API
lsof -i :3002  # Device Service
```

---

## 🔑 **Authentication & API Keys**

### **Default API Keys:**
- **Monitoring API**: `monitoring-api-key-1`
- **Deployment API**: `your-api-key`
- **Batch Flashing**: No authentication (configurable)

### **Usage:**
```bash
# Monitoring API
curl -H "X-API-Key: monitoring-api-key-1" http://localhost:5002/api/status

# Deployment API
curl -H "X-API-Key: your-api-key" http://localhost:5001/api/environments
```

---

## 🛠️ **Development & Customization**

### **Configuration Files:**
- `monitoring/monitoring-config.yaml` - Monitoring system config
- `deployment/deployment-config.yaml` - Deployment system config
- `firmware/batch-flashing/batch-flash-config.yaml` - Batch flashing config

### **Extending the Platform:**
1. **Add New Monitoring Targets**: Edit `monitoring-config.yaml`
2. **Create New Alert Rules**: Add rules to monitoring config
3. **Add New Environments**: Update deployment config
4. **Custom Notifications**: Configure notification channels

---

## 📋 **Common Use Cases**

### **🚨 Respond to Alerts:**
1. Open admin portal → Monitoring tab
2. View active alerts
3. Acknowledge or resolve alerts
4. Or use CLI: `cd monitoring && python monitoring-cli.py alerts list`

### **🔄 Deploy Firmware:**
1. Open admin portal → Deployment tab
2. Create deployment plan
3. Execute deployment
4. Monitor progress
5. Or use CLI: `cd deployment && python deployment-cli.py plan create --interactive`

### **⚡ Flash Multiple Devices:**
1. Open admin portal → Batch Flashing tab
2. Create new batch
3. Add target devices
4. Start flashing
5. Or use CLI: `cd firmware/batch-flashing && python batch-flash-cli.py create --interactive`

### **🏭 Provision New Devices:**
1. Open admin portal → Provisioning tab
2. Click "Start Provisioning"
3. Or use CLI: `cd firmware/factory-provisioning && python factory-flash.py`

### **🧪 Run Tests:**
1. Open admin portal → Testing tab
2. Click "Run All Tests"
3. Or use CLI: `cd firmware/testing && python test-framework.py --run-all`

---

## 🆘 **Troubleshooting**

### **Platform Won't Start:**
```bash
# Check for port conflicts
lsof -i :5000,5001,5002,3002

# Stop any conflicting processes
./stop-platform.sh

# Check logs
tail -f logs/*.log

# Manual dependency installation
cd monitoring && pip install -r requirements.txt
cd ../deployment && pip install -r requirements.txt
cd ../firmware/batch-flashing && pip install -r requirements.txt
```

### **Services Not Responding:**
```bash
# Check service health
curl http://localhost:5002/health  # Monitoring
curl http://localhost:5001/health  # Deployment  
curl http://localhost:5000/health  # Batch Flashing
curl http://localhost:3002/health  # Device Service

# Restart specific service
./stop-platform.sh
./start-platform.sh
```

### **Admin Portal Issues:**
1. Ensure all APIs are running
2. Check browser console for errors
3. Verify file paths in admin portal
4. Check CORS settings if accessing from different domain

---

## 🎉 **Success! You Now Have:**

✅ **Unified Admin Portal** - Single access point for everything  
✅ **Real-time Monitoring** - System health and alerts  
✅ **Automated Deployment** - Production firmware deployment  
✅ **Batch Operations** - Mass device management  
✅ **Factory Provisioning** - Manufacturing support  
✅ **Automated Testing** - Quality assurance  
✅ **CLI Tools** - Power user access  
✅ **REST APIs** - Integration support  

**Your IoT platform is now fully operational and accessible through multiple interfaces!** 🚀

---

## 📞 **Need Help?**

1. **Check this guide** - Most common questions are answered here
2. **View logs** - `tail -f logs/*.log` for troubleshooting
3. **Use CLI help** - Most CLI tools have `--help` flags
4. **Check README files** - Each system has detailed documentation

**Happy IoT managing!** 🏠✨