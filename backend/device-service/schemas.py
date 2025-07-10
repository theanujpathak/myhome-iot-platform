from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

class LocationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

class LocationCreate(LocationBase):
    pass

class LocationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None

class LocationResponse(LocationBase):
    id: int
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class DeviceTypeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    icon: Optional[str] = None
    capabilities: Optional[List[str]] = []

class DeviceTypeCreate(DeviceTypeBase):
    pass

class DeviceTypeResponse(DeviceTypeBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class DeviceStateBase(BaseModel):
    state_key: str = Field(..., min_length=1, max_length=50)
    state_value: str
    state_type: str = Field(..., pattern="^(boolean|number|string|json)$")

class DeviceStateCreate(DeviceStateBase):
    pass

class DeviceStateResponse(DeviceStateBase):
    id: int
    device_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class DeviceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    device_id: str = Field(..., min_length=1, max_length=100)
    mac_address: Optional[str] = None
    ip_address: Optional[str] = None
    device_type_id: int
    location_id: Optional[int] = None
    firmware_version: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = {}

class DeviceCreate(DeviceBase):
    pass

class DeviceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    location_id: Optional[int] = None
    is_active: Optional[bool] = None
    configuration: Optional[Dict[str, Any]] = None

class DeviceResponse(DeviceBase):
    id: int
    user_id: str
    is_online: bool
    is_active: bool
    last_seen: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    device_type: Optional[DeviceTypeResponse] = None
    location: Optional[LocationResponse] = None
    device_states: Optional[List[DeviceStateResponse]] = []

    class Config:
        from_attributes = True

class DeviceCommand(BaseModel):
    command: str = Field(..., min_length=1)
    parameters: Optional[Dict[str, Any]] = {}

class DeviceCommandResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class DeviceStatusUpdate(BaseModel):
    device_id: str
    is_online: bool
    states: Optional[List[DeviceStateCreate]] = []
    last_seen: Optional[datetime] = None

class DeviceRegistrationBase(BaseModel):
    device_name: str = Field(..., min_length=1, max_length=100)
    device_type: str = "ESP32"
    device_model: str = Field(..., min_length=1, max_length=50)  # ESP32-WROOM-32, etc.
    mac_address: str = Field(..., pattern="^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")
    manufacturer: str = "Espressif"
    firmware_version: Optional[str] = None
    hardware_revision: Optional[str] = None
    description: Optional[str] = None

class DeviceRegistrationCreate(DeviceRegistrationBase):
    pass

class DeviceRegistrationUpdate(BaseModel):
    device_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    status: Optional[str] = None

class DeviceRegistrationResponse(DeviceRegistrationBase):
    id: int
    device_id: str
    device_secret: str
    status: str
    paired: bool
    provisioned: bool
    user_id: Optional[str] = None
    location_id: Optional[int] = None
    paired_device_id: Optional[int] = None
    qr_code_data: Optional[str] = None
    qr_code_url: Optional[str] = None
    public_key_hash: Optional[str] = None
    batch_id: Optional[str] = None
    installer_id: Optional[str] = None
    created_at: datetime
    provisioned_at: Optional[datetime] = None
    paired_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None

    class Config:
        from_attributes = True

class DeviceRegistrationPublic(BaseModel):
    """Public view of device registration (without secret)"""
    id: int
    device_id: str
    device_name: str
    device_type: str
    manufacturer: str
    description: Optional[str] = None
    status: str
    paired: bool
    created_at: datetime
    paired_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None

    class Config:
        from_attributes = True

class DevicePairRequest(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=50)
    device_secret: str = Field(..., min_length=1, max_length=100)
    device_name: Optional[str] = None
    location_id: Optional[int] = None

class DevicePairResponse(BaseModel):
    success: bool
    message: str
    device: Optional[DeviceResponse] = None

# Bulk Provisioning Schemas
class BulkDeviceRegistration(BaseModel):
    device_name: str
    device_model: str
    mac_address: str
    manufacturer: str = "Espressif"
    firmware_version: Optional[str] = None
    hardware_revision: Optional[str] = None
    description: Optional[str] = None

class ProvisioningBatchCreate(BaseModel):
    batch_name: str = Field(..., min_length=1, max_length=100)
    manufacturer: str = Field(..., min_length=1, max_length=50)
    device_model: str = Field(..., min_length=1, max_length=50)
    firmware_version: Optional[str] = None
    installer_id: Optional[str] = None
    notes: Optional[str] = None
    devices: List[BulkDeviceRegistration]

class ProvisioningBatchResponse(BaseModel):
    id: int
    batch_id: str
    batch_name: str
    manufacturer: str
    device_model: str
    firmware_version: Optional[str] = None
    total_devices: int
    provisioned_devices: int
    status: str
    created_by: str
    installer_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class BulkProvisioningResult(BaseModel):
    success: bool
    message: str
    batch: Optional[ProvisioningBatchResponse] = None
    created_devices: List[DeviceRegistrationResponse] = []
    errors: List[str] = []

class QRCodeData(BaseModel):
    device_uid: str
    device_id: str
    provisioning_token: str
    public_key_hash: str
    device_model: str
    manufacturer: str