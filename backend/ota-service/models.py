from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import json

class DeviceType(str, Enum):
    ESP32 = "ESP32"
    ESP8266 = "ESP8266"
    ARDUINO_UNO = "Arduino Uno"
    ARDUINO_NANO = "Arduino Nano"
    ARDUINO_MEGA = "Arduino Mega"
    STM32 = "STM32"
    RASPBERRY_PI_PICO = "Raspberry Pi Pico"
    CUSTOM = "Custom"

class FirmwareStatus(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    STABLE = "stable"
    DEPRECATED = "deprecated"
    RECALLED = "recalled"

class UpdateStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    INSTALLING = "installing"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"

class RolloutStrategy(str, Enum):
    IMMEDIATE = "immediate"
    GRADUAL = "gradual"
    SCHEDULED = "scheduled"
    MANUAL = "manual"

class FirmwareVersion:
    def __init__(self, major: int, minor: int, patch: int, build: Optional[int] = None):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.build = build or 0
    
    def __str__(self):
        if self.build > 0:
            return f"{self.major}.{self.minor}.{self.patch}.{self.build}"
        return f"{self.major}.{self.minor}.{self.patch}"
    
    def __eq__(self, other):
        if not isinstance(other, FirmwareVersion):
            return False
        return (self.major, self.minor, self.patch, self.build) == (other.major, other.minor, other.patch, other.build)
    
    def __lt__(self, other):
        if not isinstance(other, FirmwareVersion):
            return NotImplemented
        return (self.major, self.minor, self.patch, self.build) < (other.major, other.minor, other.patch, other.build)
    
    def __le__(self, other):
        return self < other or self == other
    
    def __gt__(self, other):
        return not self <= other
    
    def __ge__(self, other):
        return not self < other
    
    @classmethod
    def from_string(cls, version_string: str):
        parts = version_string.split('.')
        major = int(parts[0])
        minor = int(parts[1])
        patch = int(parts[2])
        build = int(parts[3]) if len(parts) > 3 else 0
        return cls(major, minor, patch, build)
    
    def to_dict(self):
        return {
            "major": self.major,
            "minor": self.minor,
            "patch": self.patch,
            "build": self.build
        }

class FirmwareMetadata:
    def __init__(self, data: Dict[str, Any]):
        self.device_type = DeviceType(data.get("device_type", "Custom"))
        self.board_model = data.get("board_model", "")
        self.version = FirmwareVersion.from_string(data.get("version", "1.0.0"))
        self.status = FirmwareStatus(data.get("status", "development"))
        self.description = data.get("description", "")
        self.changelog = data.get("changelog", "")
        self.build_date = datetime.fromisoformat(data.get("build_date", datetime.now().isoformat()))
        self.file_size = data.get("file_size", 0)
        self.checksum = data.get("checksum", "")
        self.min_compatible_version = data.get("min_compatible_version")
        self.max_compatible_version = data.get("max_compatible_version")
        self.required_capabilities = data.get("required_capabilities", [])
        self.breaking_changes = data.get("breaking_changes", [])
        self.security_fixes = data.get("security_fixes", [])
        self.performance_improvements = data.get("performance_improvements", [])
        self.new_features = data.get("new_features", [])
        self.bug_fixes = data.get("bug_fixes", [])
        self.rollback_version = data.get("rollback_version")
        self.created_by = data.get("created_by", "")
        self.approved_by = data.get("approved_by", "")
        self.approval_date = data.get("approval_date")
        
    def to_dict(self):
        return {
            "device_type": self.device_type,
            "board_model": self.board_model,
            "version": str(self.version),
            "status": self.status,
            "description": self.description,
            "changelog": self.changelog,
            "build_date": self.build_date.isoformat(),
            "file_size": self.file_size,
            "checksum": self.checksum,
            "min_compatible_version": self.min_compatible_version,
            "max_compatible_version": self.max_compatible_version,
            "required_capabilities": self.required_capabilities,
            "breaking_changes": self.breaking_changes,
            "security_fixes": self.security_fixes,
            "performance_improvements": self.performance_improvements,
            "new_features": self.new_features,
            "bug_fixes": self.bug_fixes,
            "rollback_version": self.rollback_version,
            "created_by": self.created_by,
            "approved_by": self.approved_by,
            "approval_date": self.approval_date
        }

class DeviceCompatibility:
    def __init__(self, device_type: DeviceType, board_model: str, current_version: str):
        self.device_type = device_type
        self.board_model = board_model
        self.current_version = FirmwareVersion.from_string(current_version)
        self.capabilities = []
        self.hardware_revision = ""
        self.memory_size = 0
        self.flash_size = 0
        
    def is_compatible_with(self, firmware: FirmwareMetadata) -> bool:
        """Check if device is compatible with firmware"""
        # Check device type
        if self.device_type != firmware.device_type:
            return False
        
        # Check board model
        if self.board_model != firmware.board_model:
            return False
        
        # Check version compatibility
        if firmware.min_compatible_version:
            min_version = FirmwareVersion.from_string(firmware.min_compatible_version)
            if self.current_version < min_version:
                return False
        
        if firmware.max_compatible_version:
            max_version = FirmwareVersion.from_string(firmware.max_compatible_version)
            if self.current_version > max_version:
                return False
        
        # Check required capabilities
        for capability in firmware.required_capabilities:
            if capability not in self.capabilities:
                return False
        
        return True
    
    def can_rollback_to(self, firmware: FirmwareMetadata) -> bool:
        """Check if device can rollback to firmware version"""
        if not self.is_compatible_with(firmware):
            return False
        
        # Can only rollback to older versions
        return firmware.version < self.current_version

class FirmwareRollout:
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get("id", "")
        self.firmware_id = data.get("firmware_id", "")
        self.name = data.get("name", "")
        self.description = data.get("description", "")
        self.strategy = RolloutStrategy(data.get("strategy", "manual"))
        self.target_devices = data.get("target_devices", [])
        self.target_device_types = data.get("target_device_types", [])
        self.target_versions = data.get("target_versions", [])
        self.exclude_devices = data.get("exclude_devices", [])
        self.start_time = data.get("start_time")
        self.end_time = data.get("end_time")
        self.gradual_percentage = data.get("gradual_percentage", 10)
        self.gradual_interval = data.get("gradual_interval", 3600)  # seconds
        self.max_concurrent_updates = data.get("max_concurrent_updates", 10)
        self.rollback_on_failure_rate = data.get("rollback_on_failure_rate", 50)  # percentage
        self.pause_on_failure = data.get("pause_on_failure", True)
        self.notification_channels = data.get("notification_channels", [])
        self.created_by = data.get("created_by", "")
        self.created_at = datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
        self.status = data.get("status", "pending")
        self.total_devices = data.get("total_devices", 0)
        self.successful_updates = data.get("successful_updates", 0)
        self.failed_updates = data.get("failed_updates", 0)
        self.pending_updates = data.get("pending_updates", 0)
        
    def to_dict(self):
        return {
            "id": self.id,
            "firmware_id": self.firmware_id,
            "name": self.name,
            "description": self.description,
            "strategy": self.strategy,
            "target_devices": self.target_devices,
            "target_device_types": self.target_device_types,
            "target_versions": self.target_versions,
            "exclude_devices": self.exclude_devices,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "gradual_percentage": self.gradual_percentage,
            "gradual_interval": self.gradual_interval,
            "max_concurrent_updates": self.max_concurrent_updates,
            "rollback_on_failure_rate": self.rollback_on_failure_rate,
            "pause_on_failure": self.pause_on_failure,
            "notification_channels": self.notification_channels,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "total_devices": self.total_devices,
            "successful_updates": self.successful_updates,
            "failed_updates": self.failed_updates,
            "pending_updates": self.pending_updates
        }

class DeviceUpdateStatus:
    def __init__(self, data: Dict[str, Any]):
        self.device_id = data.get("device_id", "")
        self.rollout_id = data.get("rollout_id", "")
        self.firmware_id = data.get("firmware_id", "")
        self.status = UpdateStatus(data.get("status", "pending"))
        self.current_version = data.get("current_version", "")
        self.target_version = data.get("target_version", "")
        self.progress = data.get("progress", 0)
        self.error_message = data.get("error_message", "")
        self.started_at = data.get("started_at")
        self.completed_at = data.get("completed_at")
        self.retry_count = data.get("retry_count", 0)
        self.max_retries = data.get("max_retries", 3)
        self.download_url = data.get("download_url", "")
        self.checksum = data.get("checksum", "")
        self.file_size = data.get("file_size", 0)
        self.downloaded_size = data.get("downloaded_size", 0)
        
    def to_dict(self):
        return {
            "device_id": self.device_id,
            "rollout_id": self.rollout_id,
            "firmware_id": self.firmware_id,
            "status": self.status,
            "current_version": self.current_version,
            "target_version": self.target_version,
            "progress": self.progress,
            "error_message": self.error_message,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "download_url": self.download_url,
            "checksum": self.checksum,
            "file_size": self.file_size,
            "downloaded_size": self.downloaded_size
        }

class FirmwareCompatibilityChecker:
    """Utility class for checking firmware compatibility"""
    
    @staticmethod
    def check_backward_compatibility(current_firmware: FirmwareMetadata, new_firmware: FirmwareMetadata) -> Dict[str, Any]:
        """Check backward compatibility between firmware versions"""
        issues = []
        warnings = []
        
        # Check for breaking changes
        if new_firmware.breaking_changes:
            issues.extend([f"Breaking change: {change}" for change in new_firmware.breaking_changes])
        
        # Check version compatibility
        if new_firmware.min_compatible_version:
            min_version = FirmwareVersion.from_string(new_firmware.min_compatible_version)
            if current_firmware.version < min_version:
                issues.append(f"Current version {current_firmware.version} is below minimum compatible version {min_version}")
        
        # Check required capabilities
        for capability in new_firmware.required_capabilities:
            if capability not in current_firmware.required_capabilities:
                warnings.append(f"New capability required: {capability}")
        
        return {
            "compatible": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "recommendation": "upgrade" if len(issues) == 0 else "manual_review"
        }
    
    @staticmethod
    def get_upgrade_path(current_version: str, target_version: str, available_firmwares: List[FirmwareMetadata]) -> List[str]:
        """Get the optimal upgrade path from current to target version"""
        current = FirmwareVersion.from_string(current_version)
        target = FirmwareVersion.from_string(target_version)
        
        # Sort firmwares by version
        sorted_firmwares = sorted(available_firmwares, key=lambda f: f.version)
        
        # Find intermediate versions if needed
        path = []
        for firmware in sorted_firmwares:
            if current < firmware.version <= target:
                # Check if we can skip to this version
                if firmware.min_compatible_version:
                    min_version = FirmwareVersion.from_string(firmware.min_compatible_version)
                    if current >= min_version:
                        path.append(str(firmware.version))
                        current = firmware.version
                else:
                    path.append(str(firmware.version))
                    current = firmware.version
        
        return path
    
    @staticmethod
    def estimate_update_risk(firmware: FirmwareMetadata) -> str:
        """Estimate the risk level of updating to this firmware"""
        risk_score = 0
        
        # Check status
        if firmware.status == FirmwareStatus.DEVELOPMENT:
            risk_score += 50
        elif firmware.status == FirmwareStatus.TESTING:
            risk_score += 30
        elif firmware.status == FirmwareStatus.STABLE:
            risk_score += 10
        
        # Check for breaking changes
        risk_score += len(firmware.breaking_changes) * 20
        
        # Check version jump
        if firmware.version.major > 1:
            risk_score += 15
        if firmware.version.minor > 5:
            risk_score += 10
        
        # Check security fixes (reduces risk)
        risk_score -= len(firmware.security_fixes) * 5
        
        # Determine risk level
        if risk_score <= 20:
            return "low"
        elif risk_score <= 50:
            return "medium"
        else:
            return "high"