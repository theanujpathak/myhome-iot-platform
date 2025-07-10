from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

class DeviceTypeEnum(str, Enum):
    ESP32 = "ESP32"
    ESP8266 = "ESP8266"
    ARDUINO_UNO = "Arduino Uno"
    ARDUINO_NANO = "Arduino Nano"
    ARDUINO_MEGA = "Arduino Mega"
    STM32 = "STM32"
    RASPBERRY_PI_PICO = "Raspberry Pi Pico"
    CUSTOM = "Custom"

class FirmwareStatusEnum(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    STABLE = "stable"
    DEPRECATED = "deprecated"
    RECALLED = "recalled"

class UpdateStatusEnum(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    INSTALLING = "installing"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"

class RolloutStrategyEnum(str, Enum):
    IMMEDIATE = "immediate"
    GRADUAL = "gradual"
    SCHEDULED = "scheduled"
    MANUAL = "manual"

class FirmwareVersionSchema(BaseModel):
    major: int = Field(..., ge=0, description="Major version number")
    minor: int = Field(..., ge=0, description="Minor version number")
    patch: int = Field(..., ge=0, description="Patch version number")
    build: int = Field(0, ge=0, description="Build version number")
    
    def __str__(self):
        if self.build > 0:
            return f"{self.major}.{self.minor}.{self.patch}.{self.build}"
        return f"{self.major}.{self.minor}.{self.patch}"

class FirmwareUploadSchema(BaseModel):
    device_type: DeviceTypeEnum
    board_model: str = Field(..., min_length=1, max_length=100)
    version: str = Field(..., regex=r"^\d+\.\d+\.\d+(\.\d+)?$")
    status: FirmwareStatusEnum = FirmwareStatusEnum.DEVELOPMENT
    description: Optional[str] = Field(None, max_length=1000)
    changelog: Optional[str] = Field(None, max_length=5000)
    min_compatible_version: Optional[str] = Field(None, regex=r"^\d+\.\d+\.\d+(\.\d+)?$")
    max_compatible_version: Optional[str] = Field(None, regex=r"^\d+\.\d+\.\d+(\.\d+)?$")
    required_capabilities: List[str] = Field(default_factory=list)
    breaking_changes: List[str] = Field(default_factory=list)
    security_fixes: List[str] = Field(default_factory=list)
    performance_improvements: List[str] = Field(default_factory=list)
    new_features: List[str] = Field(default_factory=list)
    bug_fixes: List[str] = Field(default_factory=list)
    rollback_version: Optional[str] = Field(None, regex=r"^\d+\.\d+\.\d+(\.\d+)?$")

class FirmwareMetadataSchema(BaseModel):
    id: str
    device_type: DeviceTypeEnum
    board_model: str
    version: str
    status: FirmwareStatusEnum
    description: Optional[str] = None
    changelog: Optional[str] = None
    build_date: datetime
    file_size: int
    checksum: str
    min_compatible_version: Optional[str] = None
    max_compatible_version: Optional[str] = None
    required_capabilities: List[str] = Field(default_factory=list)
    breaking_changes: List[str] = Field(default_factory=list)
    security_fixes: List[str] = Field(default_factory=list)
    performance_improvements: List[str] = Field(default_factory=list)
    new_features: List[str] = Field(default_factory=list)
    bug_fixes: List[str] = Field(default_factory=list)
    rollback_version: Optional[str] = None
    created_by: str
    approved_by: Optional[str] = None
    approval_date: Optional[datetime] = None
    download_url: str
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class FirmwareUpdateSchema(BaseModel):
    status: Optional[FirmwareStatusEnum] = None
    description: Optional[str] = Field(None, max_length=1000)
    changelog: Optional[str] = Field(None, max_length=5000)
    approved_by: Optional[str] = None

class DeviceCompatibilitySchema(BaseModel):
    device_id: str
    device_type: DeviceTypeEnum
    board_model: str
    current_version: str
    capabilities: List[str] = Field(default_factory=list)
    hardware_revision: Optional[str] = None
    memory_size: Optional[int] = None
    flash_size: Optional[int] = None

class FirmwareRolloutCreateSchema(BaseModel):
    firmware_id: str
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    strategy: RolloutStrategyEnum
    target_devices: List[str] = Field(default_factory=list)
    target_device_types: List[DeviceTypeEnum] = Field(default_factory=list)
    target_versions: List[str] = Field(default_factory=list)
    exclude_devices: List[str] = Field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    gradual_percentage: int = Field(10, ge=1, le=100)
    gradual_interval: int = Field(3600, ge=60, le=86400)  # 1 minute to 24 hours
    max_concurrent_updates: int = Field(10, ge=1, le=1000)
    rollback_on_failure_rate: int = Field(50, ge=1, le=100)
    pause_on_failure: bool = True
    notification_channels: List[str] = Field(default_factory=list)
    
    @validator('end_time')
    def validate_end_time(cls, v, values):
        if v and 'start_time' in values and values['start_time']:
            if v <= values['start_time']:
                raise ValueError('end_time must be after start_time')
        return v

class FirmwareRolloutSchema(BaseModel):
    id: str
    firmware_id: str
    name: str
    description: Optional[str] = None
    strategy: RolloutStrategyEnum
    target_devices: List[str]
    target_device_types: List[DeviceTypeEnum]
    target_versions: List[str]
    exclude_devices: List[str]
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    gradual_percentage: int
    gradual_interval: int
    max_concurrent_updates: int
    rollback_on_failure_rate: int
    pause_on_failure: bool
    notification_channels: List[str]
    created_by: str
    created_at: datetime
    status: str
    total_devices: int
    successful_updates: int
    failed_updates: int
    pending_updates: int
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class FirmwareRolloutUpdateSchema(BaseModel):
    status: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    pause_on_failure: Optional[bool] = None

class DeviceUpdateStatusSchema(BaseModel):
    device_id: str
    rollout_id: str
    firmware_id: str
    status: UpdateStatusEnum
    current_version: str
    target_version: str
    progress: int = Field(0, ge=0, le=100)
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = Field(0, ge=0)
    max_retries: int = Field(3, ge=0, le=10)
    download_url: str
    checksum: str
    file_size: int
    downloaded_size: int = Field(0, ge=0)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class BulkUpdateRequestSchema(BaseModel):
    device_ids: List[str] = Field(..., min_items=1, max_items=1000)
    firmware_id: str
    strategy: RolloutStrategyEnum = RolloutStrategyEnum.IMMEDIATE
    max_concurrent_updates: int = Field(10, ge=1, le=100)
    rollback_on_failure_rate: int = Field(50, ge=1, le=100)

class CompatibilityCheckSchema(BaseModel):
    device_id: str
    firmware_id: str

class CompatibilityResultSchema(BaseModel):
    compatible: bool
    issues: List[str]
    warnings: List[str]
    recommendation: str
    risk_level: str
    upgrade_path: List[str] = Field(default_factory=list)

class FirmwareStatsSchema(BaseModel):
    total_firmwares: int
    by_device_type: Dict[str, int]
    by_status: Dict[str, int]
    recent_uploads: int
    total_size: int

class UpdateStatsSchema(BaseModel):
    total_updates: int
    successful_updates: int
    failed_updates: int
    pending_updates: int
    success_rate: float
    average_update_time: Optional[float] = None
    by_device_type: Dict[str, Dict[str, int]]
    by_firmware_version: Dict[str, Dict[str, int]]

class RolloutStatsSchema(BaseModel):
    total_rollouts: int
    active_rollouts: int
    completed_rollouts: int
    failed_rollouts: int
    devices_updated_today: int
    success_rate: float

class FirmwareSearchSchema(BaseModel):
    device_type: Optional[DeviceTypeEnum] = None
    board_model: Optional[str] = None
    status: Optional[FirmwareStatusEnum] = None
    min_version: Optional[str] = None
    max_version: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    created_by: Optional[str] = None
    has_security_fixes: Optional[bool] = None
    has_breaking_changes: Optional[bool] = None
    
class DeviceUpdateRequestSchema(BaseModel):
    device_id: str
    firmware_id: str
    force_update: bool = False
    schedule_time: Optional[datetime] = None
    
class DeviceRollbackRequestSchema(BaseModel):
    device_id: str
    target_version: Optional[str] = None  # If None, rollback to previous version
    
class FirmwareDiffSchema(BaseModel):
    from_version: str
    to_version: str
    
class FirmwareDiffResultSchema(BaseModel):
    version_diff: Dict[str, Any]
    breaking_changes: List[str]
    new_features: List[str]
    bug_fixes: List[str]
    security_fixes: List[str]
    performance_improvements: List[str]
    compatibility_changes: Dict[str, Any]
    size_diff: int
    upgrade_recommendation: str