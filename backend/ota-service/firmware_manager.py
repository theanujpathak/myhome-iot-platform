import os
import json
import hashlib
import asyncio
import aiofiles
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import redis
import logging
from models import (
    FirmwareMetadata, DeviceCompatibility, FirmwareRollout, 
    DeviceUpdateStatus, FirmwareCompatibilityChecker, 
    DeviceType, FirmwareStatus, UpdateStatus, RolloutStrategy
)
from schemas import (
    FirmwareUploadSchema, FirmwareRolloutCreateSchema, 
    DeviceCompatibilitySchema, BulkUpdateRequestSchema
)
import paho.mqtt.client as mqtt
import uuid

logger = logging.getLogger(__name__)

class FirmwareManager:
    def __init__(self, firmware_dir: Path, redis_client: redis.Redis, mqtt_client: mqtt.Client):
        self.firmware_dir = firmware_dir
        self.redis_client = redis_client
        self.mqtt_client = mqtt_client
        self.metadata_dir = firmware_dir / "metadata"
        self.rollouts_dir = firmware_dir / "rollouts"
        self.updates_dir = firmware_dir / "updates"
        
        # Create directories
        self.metadata_dir.mkdir(exist_ok=True)
        self.rollouts_dir.mkdir(exist_ok=True)
        self.updates_dir.mkdir(exist_ok=True)
        
        # Cache for firmware metadata
        self.firmware_cache = {}
        self.load_firmware_cache()
        
    def load_firmware_cache(self):
        """Load firmware metadata into cache"""
        try:
            for metadata_file in self.metadata_dir.glob("*.json"):
                with open(metadata_file, 'r') as f:
                    data = json.load(f)
                    firmware_id = metadata_file.stem
                    self.firmware_cache[firmware_id] = FirmwareMetadata(data)
        except Exception as e:
            logger.error(f"Failed to load firmware cache: {e}")
    
    async def upload_firmware(self, firmware_data: FirmwareUploadSchema, 
                            firmware_file: bytes, user_id: str) -> str:
        """Upload and register new firmware"""
        try:
            # Generate firmware ID
            firmware_id = str(uuid.uuid4())
            
            # Calculate checksum
            checksum = hashlib.sha256(firmware_file).hexdigest()
            
            # Save firmware file
            firmware_path = self.firmware_dir / f"{firmware_id}.bin"
            async with aiofiles.open(firmware_path, 'wb') as f:
                await f.write(firmware_file)
            
            # Create metadata
            metadata = FirmwareMetadata({
                "device_type": firmware_data.device_type,
                "board_model": firmware_data.board_model,
                "version": firmware_data.version,
                "status": firmware_data.status,
                "description": firmware_data.description or "",
                "changelog": firmware_data.changelog or "",
                "build_date": datetime.now().isoformat(),
                "file_size": len(firmware_file),
                "checksum": checksum,
                "min_compatible_version": firmware_data.min_compatible_version,
                "max_compatible_version": firmware_data.max_compatible_version,
                "required_capabilities": firmware_data.required_capabilities,
                "breaking_changes": firmware_data.breaking_changes,
                "security_fixes": firmware_data.security_fixes,
                "performance_improvements": firmware_data.performance_improvements,
                "new_features": firmware_data.new_features,
                "bug_fixes": firmware_data.bug_fixes,
                "rollback_version": firmware_data.rollback_version,
                "created_by": user_id,
                "approved_by": None,
                "approval_date": None
            })
            
            # Save metadata
            metadata_path = self.metadata_dir / f"{firmware_id}.json"
            async with aiofiles.open(metadata_path, 'w') as f:
                await f.write(json.dumps(metadata.to_dict(), indent=2))
            
            # Update cache
            self.firmware_cache[firmware_id] = metadata
            
            logger.info(f"Firmware {firmware_id} uploaded successfully")
            return firmware_id
            
        except Exception as e:
            logger.error(f"Failed to upload firmware: {e}")
            raise
    
    async def get_firmware_metadata(self, firmware_id: str) -> Optional[FirmwareMetadata]:
        """Get firmware metadata"""
        return self.firmware_cache.get(firmware_id)
    
    async def list_firmwares(self, device_type: Optional[DeviceType] = None,
                           status: Optional[FirmwareStatus] = None,
                           board_model: Optional[str] = None) -> List[FirmwareMetadata]:
        """List firmwares with optional filters"""
        firmwares = list(self.firmware_cache.values())
        
        if device_type:
            firmwares = [f for f in firmwares if f.device_type == device_type]
        
        if status:
            firmwares = [f for f in firmwares if f.status == status]
        
        if board_model:
            firmwares = [f for f in firmwares if f.board_model == board_model]
        
        # Sort by version (newest first)
        firmwares.sort(key=lambda f: f.version, reverse=True)
        return firmwares
    
    async def approve_firmware(self, firmware_id: str, user_id: str) -> bool:
        """Approve firmware for production use"""
        try:
            firmware = self.firmware_cache.get(firmware_id)
            if not firmware:
                return False
            
            # Update metadata
            firmware.approved_by = user_id
            firmware.approval_date = datetime.now()
            firmware.status = FirmwareStatus.STABLE
            
            # Save updated metadata
            metadata_path = self.metadata_dir / f"{firmware_id}.json"
            async with aiofiles.open(metadata_path, 'w') as f:
                await f.write(json.dumps(firmware.to_dict(), indent=2))
            
            logger.info(f"Firmware {firmware_id} approved by {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to approve firmware: {e}")
            return False
    
    async def check_device_compatibility(self, device_id: str, 
                                       firmware_id: str) -> Dict[str, Any]:
        """Check if device is compatible with firmware"""
        try:
            # Get device info from device service
            device_info = await self.get_device_info(device_id)
            if not device_info:
                return {"compatible": False, "error": "Device not found"}
            
            # Get firmware metadata
            firmware = self.firmware_cache.get(firmware_id)
            if not firmware:
                return {"compatible": False, "error": "Firmware not found"}
            
            # Create device compatibility object
            device_compat = DeviceCompatibility(
                device_type=DeviceType(device_info.get("device_type", "Custom")),
                board_model=device_info.get("board_model", ""),
                current_version=device_info.get("firmware_version", "1.0.0")
            )
            device_compat.capabilities = device_info.get("capabilities", [])
            
            # Check compatibility
            compatible = device_compat.is_compatible_with(firmware)
            
            # Get current firmware for comparison
            current_firmware = await self.find_firmware_by_version(
                device_compat.device_type,
                device_compat.board_model,
                device_compat.current_version
            )
            
            # Check backward compatibility
            compatibility_result = {}
            if current_firmware:
                compatibility_result = FirmwareCompatibilityChecker.check_backward_compatibility(
                    current_firmware, firmware
                )
            
            # Get upgrade path
            available_firmwares = await self.list_firmwares(
                device_type=device_compat.device_type,
                status=FirmwareStatus.STABLE
            )
            
            upgrade_path = FirmwareCompatibilityChecker.get_upgrade_path(
                str(device_compat.current_version),
                str(firmware.version),
                available_firmwares
            )
            
            # Estimate risk
            risk_level = FirmwareCompatibilityChecker.estimate_update_risk(firmware)
            
            return {
                "compatible": compatible,
                "issues": compatibility_result.get("issues", []),
                "warnings": compatibility_result.get("warnings", []),
                "recommendation": compatibility_result.get("recommendation", "unknown"),
                "risk_level": risk_level,
                "upgrade_path": upgrade_path,
                "current_version": str(device_compat.current_version),
                "target_version": str(firmware.version)
            }
            
        except Exception as e:
            logger.error(f"Failed to check compatibility: {e}")
            return {"compatible": False, "error": str(e)}
    
    async def create_rollout(self, rollout_data: FirmwareRolloutCreateSchema,
                           user_id: str) -> str:
        """Create a new firmware rollout"""
        try:
            rollout_id = str(uuid.uuid4())
            
            # Get target devices
            target_devices = await self.get_target_devices(rollout_data)
            
            # Create rollout object
            rollout = FirmwareRollout({
                "id": rollout_id,
                "firmware_id": rollout_data.firmware_id,
                "name": rollout_data.name,
                "description": rollout_data.description,
                "strategy": rollout_data.strategy,
                "target_devices": target_devices,
                "target_device_types": rollout_data.target_device_types,
                "target_versions": rollout_data.target_versions,
                "exclude_devices": rollout_data.exclude_devices,
                "start_time": rollout_data.start_time.isoformat() if rollout_data.start_time else None,
                "end_time": rollout_data.end_time.isoformat() if rollout_data.end_time else None,
                "gradual_percentage": rollout_data.gradual_percentage,
                "gradual_interval": rollout_data.gradual_interval,
                "max_concurrent_updates": rollout_data.max_concurrent_updates,
                "rollback_on_failure_rate": rollout_data.rollback_on_failure_rate,
                "pause_on_failure": rollout_data.pause_on_failure,
                "notification_channels": rollout_data.notification_channels,
                "created_by": user_id,
                "created_at": datetime.now().isoformat(),
                "status": "pending",
                "total_devices": len(target_devices),
                "successful_updates": 0,
                "failed_updates": 0,
                "pending_updates": len(target_devices)
            })
            
            # Save rollout
            rollout_path = self.rollouts_dir / f"{rollout_id}.json"
            async with aiofiles.open(rollout_path, 'w') as f:
                await f.write(json.dumps(rollout.to_dict(), indent=2))
            
            # Create update status for each device
            for device_id in target_devices:
                await self.create_device_update_status(device_id, rollout_id, rollout_data.firmware_id)
            
            logger.info(f"Rollout {rollout_id} created with {len(target_devices)} target devices")
            return rollout_id
            
        except Exception as e:
            logger.error(f"Failed to create rollout: {e}")
            raise
    
    async def start_rollout(self, rollout_id: str) -> bool:
        """Start a firmware rollout"""
        try:
            rollout = await self.get_rollout(rollout_id)
            if not rollout:
                return False
            
            rollout.status = "active"
            await self.save_rollout(rollout)
            
            # Start update process based on strategy
            if rollout.strategy == RolloutStrategy.IMMEDIATE:
                await self.start_immediate_rollout(rollout)
            elif rollout.strategy == RolloutStrategy.GRADUAL:
                await self.start_gradual_rollout(rollout)
            elif rollout.strategy == RolloutStrategy.SCHEDULED:
                await self.schedule_rollout(rollout)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start rollout: {e}")
            return False
    
    async def update_single_device(self, device_id: str, firmware_id: str,
                                 force_update: bool = False) -> bool:
        """Update a single device"""
        try:
            # Check compatibility first
            if not force_update:
                compatibility = await self.check_device_compatibility(device_id, firmware_id)
                if not compatibility["compatible"]:
                    logger.warning(f"Device {device_id} not compatible with firmware {firmware_id}")
                    return False
            
            # Get firmware metadata
            firmware = self.firmware_cache.get(firmware_id)
            if not firmware:
                return False
            
            # Create update command
            update_command = {
                "action": "update",
                "firmware_id": firmware_id,
                "url": f"http://localhost:3004/api/firmware/{firmware_id}/download",
                "version": str(firmware.version),
                "checksum": firmware.checksum,
                "size": firmware.file_size
            }
            
            # Send update command via MQTT
            topic = f"homeautomation/devices/{device_id}/ota"
            message = json.dumps(update_command)
            
            self.mqtt_client.publish(topic, message, qos=1)
            logger.info(f"Update command sent to device {device_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update device {device_id}: {e}")
            return False
    
    async def bulk_update_devices(self, request: BulkUpdateRequestSchema) -> str:
        """Perform bulk update of devices"""
        try:
            # Create a rollout for bulk update
            rollout_data = FirmwareRolloutCreateSchema(
                firmware_id=request.firmware_id,
                name=f"Bulk Update - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                description="Bulk firmware update",
                strategy=request.strategy,
                target_devices=request.device_ids,
                max_concurrent_updates=request.max_concurrent_updates,
                rollback_on_failure_rate=request.rollback_on_failure_rate
            )
            
            rollout_id = await self.create_rollout(rollout_data, "system")
            await self.start_rollout(rollout_id)
            
            return rollout_id
            
        except Exception as e:
            logger.error(f"Failed to perform bulk update: {e}")
            raise
    
    async def get_device_info(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get device information from device service"""
        try:
            # This should make an HTTP request to the device service
            # For now, we'll simulate with cached data
            cached_info = self.redis_client.get(f"device_info:{device_id}")
            if cached_info:
                return json.loads(cached_info)
            
            # Mock device info
            return {
                "device_id": device_id,
                "device_type": "ESP32",
                "board_model": "ESP32-WROOM-32",
                "firmware_version": "1.0.0",
                "capabilities": ["wifi", "bluetooth", "ota"],
                "hardware_revision": "1.0",
                "memory_size": 4194304,
                "flash_size": 4194304
            }
            
        except Exception as e:
            logger.error(f"Failed to get device info: {e}")
            return None
    
    async def get_target_devices(self, rollout_data: FirmwareRolloutCreateSchema) -> List[str]:
        """Get list of target devices for rollout"""
        target_devices = []
        
        # Add explicitly specified devices
        target_devices.extend(rollout_data.target_devices)
        
        # Add devices by type and version criteria
        if rollout_data.target_device_types or rollout_data.target_versions:
            # This should query the device service
            # For now, we'll simulate with mock data
            all_devices = await self.get_all_devices()
            
            for device in all_devices:
                if device["device_id"] in rollout_data.exclude_devices:
                    continue
                
                if rollout_data.target_device_types:
                    if device["device_type"] not in rollout_data.target_device_types:
                        continue
                
                if rollout_data.target_versions:
                    if device["firmware_version"] not in rollout_data.target_versions:
                        continue
                
                target_devices.append(device["device_id"])
        
        return list(set(target_devices))  # Remove duplicates
    
    async def get_all_devices(self) -> List[Dict[str, Any]]:
        """Get all devices from device service"""
        # This should make an HTTP request to the device service
        # For now, we'll return mock data
        return [
            {
                "device_id": "device_001",
                "device_type": "ESP32",
                "board_model": "ESP32-WROOM-32",
                "firmware_version": "1.0.0"
            },
            {
                "device_id": "device_002",
                "device_type": "ESP8266",
                "board_model": "NodeMCU",
                "firmware_version": "1.0.0"
            }
        ]
    
    async def create_device_update_status(self, device_id: str, rollout_id: str, firmware_id: str):
        """Create update status for a device"""
        firmware = self.firmware_cache.get(firmware_id)
        if not firmware:
            return
        
        device_info = await self.get_device_info(device_id)
        current_version = device_info.get("firmware_version", "1.0.0") if device_info else "1.0.0"
        
        update_status = DeviceUpdateStatus({
            "device_id": device_id,
            "rollout_id": rollout_id,
            "firmware_id": firmware_id,
            "status": "pending",
            "current_version": current_version,
            "target_version": str(firmware.version),
            "progress": 0,
            "download_url": f"http://localhost:3004/api/firmware/{firmware_id}/download",
            "checksum": firmware.checksum,
            "file_size": firmware.file_size,
            "downloaded_size": 0
        })
        
        # Save update status
        update_path = self.updates_dir / f"{device_id}_{rollout_id}.json"
        async with aiofiles.open(update_path, 'w') as f:
            await f.write(json.dumps(update_status.to_dict(), indent=2))
    
    async def start_immediate_rollout(self, rollout: FirmwareRollout):
        """Start immediate rollout"""
        concurrent_updates = 0
        
        for device_id in rollout.target_devices:
            if concurrent_updates >= rollout.max_concurrent_updates:
                break
            
            await self.update_single_device(device_id, rollout.firmware_id)
            concurrent_updates += 1
    
    async def start_gradual_rollout(self, rollout: FirmwareRollout):
        """Start gradual rollout"""
        # Calculate number of devices for first batch
        batch_size = max(1, int(len(rollout.target_devices) * rollout.gradual_percentage / 100))
        
        # Update first batch
        for i in range(min(batch_size, len(rollout.target_devices))):
            device_id = rollout.target_devices[i]
            await self.update_single_device(device_id, rollout.firmware_id)
    
    async def schedule_rollout(self, rollout: FirmwareRollout):
        """Schedule rollout for later execution"""
        # This would typically use a task scheduler like Celery
        # For now, we'll just log the schedule
        logger.info(f"Rollout {rollout.id} scheduled for {rollout.start_time}")
    
    async def get_rollout(self, rollout_id: str) -> Optional[FirmwareRollout]:
        """Get rollout by ID"""
        try:
            rollout_path = self.rollouts_dir / f"{rollout_id}.json"
            if rollout_path.exists():
                async with aiofiles.open(rollout_path, 'r') as f:
                    data = json.loads(await f.read())
                    return FirmwareRollout(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get rollout: {e}")
            return None
    
    async def save_rollout(self, rollout: FirmwareRollout):
        """Save rollout to file"""
        try:
            rollout_path = self.rollouts_dir / f"{rollout.id}.json"
            async with aiofiles.open(rollout_path, 'w') as f:
                await f.write(json.dumps(rollout.to_dict(), indent=2))
        except Exception as e:
            logger.error(f"Failed to save rollout: {e}")
    
    async def find_firmware_by_version(self, device_type: DeviceType, 
                                     board_model: str, version: str) -> Optional[FirmwareMetadata]:
        """Find firmware by device type, board model, and version"""
        for firmware in self.firmware_cache.values():
            if (firmware.device_type == device_type and 
                firmware.board_model == board_model and
                str(firmware.version) == version):
                return firmware
        return None
    
    async def get_firmware_stats(self) -> Dict[str, Any]:
        """Get firmware statistics"""
        firmwares = list(self.firmware_cache.values())
        
        by_device_type = {}
        by_status = {}
        total_size = 0
        
        for firmware in firmwares:
            # Count by device type
            device_type = firmware.device_type
            by_device_type[device_type] = by_device_type.get(device_type, 0) + 1
            
            # Count by status
            status = firmware.status
            by_status[status] = by_status.get(status, 0) + 1
            
            # Sum total size
            total_size += firmware.file_size
        
        # Count recent uploads (last 7 days)
        recent_uploads = 0
        week_ago = datetime.now() - timedelta(days=7)
        for firmware in firmwares:
            if firmware.build_date > week_ago:
                recent_uploads += 1
        
        return {
            "total_firmwares": len(firmwares),
            "by_device_type": by_device_type,
            "by_status": by_status,
            "recent_uploads": recent_uploads,
            "total_size": total_size
        }