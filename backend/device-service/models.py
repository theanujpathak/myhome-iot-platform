from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    user_id = Column(String, nullable=False)  # Keycloak user ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    devices = relationship("Device", back_populates="location")

class DeviceType(Base):
    __tablename__ = "device_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    icon = Column(String)
    capabilities = Column(JSON)  # JSON array of capabilities like ["switch", "dimmer", "temperature"]
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    devices = relationship("Device", back_populates="device_type")

class DeviceRegistration(Base):
    __tablename__ = "device_registrations"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, unique=True, nullable=False)  # ESP32_XXXXXXXX (legacy support)
    device_secret = Column(String, nullable=False)  # Secure secret for authentication
    device_name = Column(String, nullable=False)
    device_type = Column(String, default="ESP32")
    device_model = Column(String, nullable=False)  # ESP32-WROOM-32, ESP8266, etc.
    mac_address = Column(String, nullable=False)  # Device MAC address
    manufacturer = Column(String, default="Espressif")
    firmware_version = Column(String)  # Current firmware version
    hardware_revision = Column(String)  # Hardware revision
    description = Column(Text)
    status = Column(String, default="registered")  # registered, paired, offline, provisioned
    paired = Column(Boolean, default=False)
    provisioned = Column(Boolean, default=False)  # Has been provisioned/configured
    user_id = Column(String)  # Keycloak user ID when paired
    location_id = Column(Integer, ForeignKey("locations.id"))
    paired_device_id = Column(Integer, ForeignKey("devices.id"))  # Reference to actual device
    
    # Provisioning metadata
    qr_code_data = Column(Text)  # QR code JSON data
    qr_code_url = Column(String)  # URL to QR code image
    public_key_hash = Column(String)  # Hash of device public key
    provisioning_token = Column(String)  # One-time provisioning token
    batch_id = Column(String)  # Batch ID for bulk provisioning
    installer_id = Column(String)  # ID of installer/technician
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    provisioned_at = Column(DateTime(timezone=True))
    paired_at = Column(DateTime(timezone=True))
    last_seen = Column(DateTime(timezone=True))
    
    # Relationships
    location = relationship("Location")
    paired_device = relationship("Device")

class ProvisioningBatch(Base):
    __tablename__ = "provisioning_batches"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String, unique=True, nullable=False)
    batch_name = Column(String, nullable=False)
    manufacturer = Column(String, nullable=False)
    device_model = Column(String, nullable=False)
    firmware_version = Column(String)
    total_devices = Column(Integer, default=0)
    provisioned_devices = Column(Integer, default=0)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    created_by = Column(String, nullable=False)  # User ID who created the batch
    installer_id = Column(String)  # Assigned installer/technician
    notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    device_id = Column(String, unique=True, nullable=False)  # Unique device identifier
    mac_address = Column(String, unique=True)
    ip_address = Column(String)
    device_type_id = Column(Integer, ForeignKey("device_types.id"))
    location_id = Column(Integer, ForeignKey("locations.id"))
    user_id = Column(String, nullable=False)  # Keycloak user ID
    is_online = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    last_seen = Column(DateTime(timezone=True))
    firmware_version = Column(String)
    configuration = Column(JSON)  # Device-specific configuration
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    device_type = relationship("DeviceType", back_populates="devices")
    location = relationship("Location", back_populates="devices")
    device_states = relationship("DeviceState", back_populates="device")

class DeviceState(Base):
    __tablename__ = "device_states"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    state_key = Column(String, nullable=False)  # e.g., "power", "brightness", "temperature"
    state_value = Column(String, nullable=False)  # JSON string value
    state_type = Column(String, nullable=False)  # "boolean", "number", "string", "json"
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    device = relationship("Device", back_populates="device_states")

    def __repr__(self):
        return f"<DeviceState(device_id={self.device_id}, key={self.state_key}, value={self.state_value})>"