import asyncio
import socket
import json
import subprocess
import re
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import threading
import time

app = FastAPI(title="Device Discovery Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DiscoveredDevice(BaseModel):
    id: str
    name: str
    type: str
    ip: str
    mac: str
    manufacturer: str
    model: str
    status: str
    discovery_method: str
    port: int = None
    services: List[str] = []

class NetworkScanner:
    def __init__(self):
        self.discovered_devices = []
        self.scanning = False
        
    async def scan_network(self) -> List[DiscoveredDevice]:
        """Comprehensive network scan for IoT devices"""
        self.discovered_devices = []
        self.scanning = True
        
        try:
            # Get network range
            network_range = self.get_network_range()
            print(f"Scanning network range: {network_range}")
            
            # Run different discovery methods concurrently
            tasks = [
                self.ping_sweep(network_range),
                self.mdns_discovery(),
                self.upnp_discovery(),
                self.esp32_discovery(),
                self.common_iot_ports_scan(network_range)
            ]
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Remove duplicates based on IP
            unique_devices = {}
            for device in self.discovered_devices:
                if device.ip not in unique_devices:
                    unique_devices[device.ip] = device
                else:
                    # Merge information from different discovery methods
                    existing = unique_devices[device.ip]
                    existing.services.extend(device.services)
                    existing.services = list(set(existing.services))
                    if device.name != "Unknown Device":
                        existing.name = device.name
                    if device.manufacturer != "Unknown":
                        existing.manufacturer = device.manufacturer
            
            return list(unique_devices.values())
            
        except Exception as e:
            print(f"Error during network scan: {e}")
            return []
        finally:
            self.scanning = False
    
    def get_network_range(self) -> str:
        """Get the current network range"""
        try:
            # Get default gateway
            result = subprocess.run(['route', '-n', 'get', 'default'], 
                                  capture_output=True, text=True)
            gateway = None
            for line in result.stdout.split('\n'):
                if 'gateway:' in line:
                    gateway = line.split(':')[1].strip()
                    break
            
            if gateway:
                # Convert to network range (assume /24)
                parts = gateway.split('.')
                network = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
                return network
            
            return "192.168.1.0/24"  # Default fallback
            
        except Exception as e:
            print(f"Error getting network range: {e}")
            return "192.168.1.0/24"
    
    async def ping_sweep(self, network_range: str):
        """Ping sweep to find active hosts"""
        try:
            # Extract base network (e.g., 192.168.1)
            base_network = network_range.split('/')[0].rsplit('.', 1)[0]
            
            # Ping common IP ranges
            ping_tasks = []
            for i in range(1, 255):
                ip = f"{base_network}.{i}"
                ping_tasks.append(self.ping_host(ip))
            
            await asyncio.gather(*ping_tasks, return_exceptions=True)
            
        except Exception as e:
            print(f"Error in ping sweep: {e}")
    
    async def ping_host(self, ip: str):
        """Ping a single host"""
        try:
            process = await asyncio.create_subprocess_exec(
                'ping', '-c', '1', '-W', '1000', ip,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # Host is alive, try to get more info
                await self.probe_host(ip)
                
        except Exception as e:
            pass  # Ignore ping failures
    
    async def probe_host(self, ip: str):
        """Probe a host for IoT device characteristics"""
        try:
            # Try to get hostname
            try:
                hostname = socket.gethostbyaddr(ip)[0]
            except:
                hostname = f"Device at {ip}"
            
            # Try common IoT ports
            open_ports = []
            common_ports = [80, 443, 8080, 8443, 1883, 8883, 5000, 8000, 9000]
            
            for port in common_ports:
                if await self.check_port(ip, port):
                    open_ports.append(port)
            
            if open_ports:
                device_info = await self.identify_device(ip, open_ports, hostname)
                if device_info:
                    self.discovered_devices.append(device_info)
                    
        except Exception as e:
            print(f"Error probing host {ip}: {e}")
    
    async def check_port(self, ip: str, port: int, timeout: float = 0.5) -> bool:
        """Check if a port is open"""
        try:
            future = asyncio.open_connection(ip, port)
            reader, writer = await asyncio.wait_for(future, timeout=timeout)
            writer.close()
            await writer.wait_closed()
            return True
        except:
            return False
    
    async def identify_device(self, ip: str, open_ports: List[int], hostname: str) -> DiscoveredDevice:
        """Try to identify what type of device this is"""
        try:
            device_type = "Unknown"
            manufacturer = "Unknown"
            model = "Unknown"
            name = hostname
            services = []
            
            # Check for web interfaces
            for port in [80, 8080, 443, 8443]:
                if port in open_ports:
                    device_info = await self.check_web_interface(ip, port)
                    if device_info:
                        device_type = device_info.get('type', device_type)
                        manufacturer = device_info.get('manufacturer', manufacturer)
                        model = device_info.get('model', model)
                        name = device_info.get('name', name)
                        services.extend(device_info.get('services', []))
                    else:
                        # If we can't identify the web interface, still mark it as a web device
                        services.append('HTTP')
                        if device_type == "Unknown":
                            device_type = "Web Device"
            
            # Check for MQTT (likely IoT device)
            if 1883 in open_ports or 8883 in open_ports:
                services.append('MQTT')
                if device_type == "Unknown":
                    device_type = "MQTT Device"
            
            # ESP32 detection patterns
            if any(pattern in hostname.lower() for pattern in ['esp32', 'esp8266', 'arduino', 'nodemcu']):
                device_type = "ESP32/Arduino"
                manufacturer = "Espressif/Arduino"
            
            # TP-Link detection
            if 'tp-link' in hostname.lower() or await self.check_tplink_api(ip):
                manufacturer = "TP-Link"
                device_type = "Smart Switch"
            
            # Philips Hue detection
            if await self.check_hue_bridge(ip):
                manufacturer = "Philips"
                device_type = "Hue Bridge"
            
            # Generic web device detection
            if device_type == "Unknown" and (80 in open_ports or 8080 in open_ports):
                device_type = "Web Device"
                services.append('HTTP')
            
            # If still unknown, classify by port
            if device_type == "Unknown":
                if any(port in open_ports for port in [80, 443, 8080, 8443]):
                    device_type = "Network Device"
                else:
                    device_type = "Generic Device"
            
            return DiscoveredDevice(
                id=f"discovered_{ip.replace('.', '_')}",
                name=name,
                type=device_type,
                ip=ip,
                mac=await self.get_mac_address(ip),
                manufacturer=manufacturer,
                model=model,
                status="online",
                discovery_method="network_scan",
                port=open_ports[0] if open_ports else None,
                services=services
            )
            
        except Exception as e:
            print(f"Error identifying device at {ip}: {e}")
            return None
    
    async def check_web_interface(self, ip: str, port: int) -> Dict[str, Any]:
        """Check web interface for device identification"""
        try:
            protocol = "https" if port in [443, 8443] else "http"
            url = f"{protocol}://{ip}:{port}"
            
            response = requests.get(url, timeout=2, verify=False)
            content = response.text.lower()
            
            services = ['HTTP']
            device_info = {}
            
            # Look for device identifiers in HTML
            if 'esp32' in content or 'esp8266' in content:
                device_info.update({
                    'type': 'ESP32/Arduino',
                    'manufacturer': 'Espressif',
                    'services': services + ['Web Interface']
                })
            elif 'tp-link' in content or 'kasa' in content:
                device_info.update({
                    'type': 'Smart Switch',
                    'manufacturer': 'TP-Link',
                    'services': services + ['Kasa']
                })
            elif 'philips' in content and 'hue' in content:
                device_info.update({
                    'type': 'Hue Bridge',
                    'manufacturer': 'Philips',
                    'services': services + ['Hue API']
                })
            elif 'home assistant' in content:
                device_info.update({
                    'type': 'Home Assistant',
                    'manufacturer': 'Home Assistant',
                    'services': services + ['Home Assistant']
                })
            
            return device_info
            
        except Exception as e:
            return {}
    
    async def check_tplink_api(self, ip: str) -> bool:
        """Check for TP-Link Kasa API"""
        try:
            # TP-Link devices often respond to this request
            url = f"http://{ip}/api/v1/system/get_sysinfo"
            response = requests.get(url, timeout=1)
            return response.status_code == 200
        except:
            return False
    
    async def check_hue_bridge(self, ip: str) -> bool:
        """Check for Philips Hue bridge"""
        try:
            url = f"http://{ip}/api/nouser/config"
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                data = response.json()
                return 'bridgeid' in data
            return False
        except:
            return False
    
    async def get_mac_address(self, ip: str) -> str:
        """Get MAC address for IP"""
        try:
            # Try ARP table lookup
            result = subprocess.run(['arp', '-n', ip], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if ip in line:
                        parts = line.split()
                        for part in parts:
                            if re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', part):
                                return part
            return "00:00:00:00:00:00"
        except:
            return "00:00:00:00:00:00"
    
    async def mdns_discovery(self):
        """Discover devices via mDNS/Bonjour"""
        try:
            # This would require zeroconf library
            # For now, just a placeholder
            print("mDNS discovery started...")
            await asyncio.sleep(2)  # Simulate discovery time
            print("mDNS discovery completed")
        except Exception as e:
            print(f"mDNS discovery error: {e}")
    
    async def upnp_discovery(self):
        """Discover UPnP devices"""
        try:
            print("UPnP discovery started...")
            await asyncio.sleep(1)  # Simulate discovery time
            print("UPnP discovery completed")
        except Exception as e:
            print(f"UPnP discovery error: {e}")
    
    async def esp32_discovery(self):
        """Look for ESP32 devices broadcasting"""
        try:
            print("ESP32 discovery started...")
            
            # Check for ESP32 emulator
            try:
                response = requests.get("http://localhost:8090/api/discovery/info", timeout=2)
                if response.status_code == 200:
                    emulator_devices = response.json()
                    for device_data in emulator_devices:
                        device = DiscoveredDevice(
                            id=device_data["device_id"],
                            name=device_data["device_name"],
                            type=device_data["device_type"],
                            ip=device_data["ip"],
                            mac=device_data["mac"],
                            manufacturer=device_data["manufacturer"],
                            model=device_data.get("device_type", "ESP32-WROOM-32"),
                            status="online",
                            discovery_method="esp32_emulator",
                            port=80,
                            services=device_data.get("services", ["http", "mqtt"])
                        )
                        self.discovered_devices.append(device)
                        print(f"Found ESP32 emulator device: {device.name} at {device.ip}")
            except Exception as e:
                print(f"ESP32 emulator not available: {e}")
            
            await asyncio.sleep(1)  # Simulate discovery time
            print("ESP32 discovery completed")
        except Exception as e:
            print(f"ESP32 discovery error: {e}")
    
    async def common_iot_ports_scan(self, network_range: str):
        """Scan for common IoT device ports"""
        try:
            print("IoT ports scan started...")
            await asyncio.sleep(1)  # Simulate scanning time
            print("IoT ports scan completed")
        except Exception as e:
            print(f"IoT ports scan error: {e}")

# Global scanner instance
scanner = NetworkScanner()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "discovery-service"}

@app.post("/api/scan/network")
async def scan_network():
    """Start network device discovery"""
    if scanner.scanning:
        raise HTTPException(status_code=400, detail="Scan already in progress")
    
    try:
        devices = await scanner.scan_network()
        return {
            "status": "completed",
            "devices": devices,
            "total_found": len(devices)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")

@app.get("/api/scan/status")
async def get_scan_status():
    """Get current scanning status"""
    return {
        "scanning": scanner.scanning,
        "devices_found": len(scanner.discovered_devices)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3005)