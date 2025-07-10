from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from keycloak import KeycloakOpenID
import os
import jwt
from typing import Optional, Dict, Any, List
import redis
import json
import logging
from datetime import datetime
import hashlib
import aiofiles
from pathlib import Path
import paho.mqtt.client as mqtt

# Import our new modules
from firmware_manager import FirmwareManager
from models import DeviceType, FirmwareStatus, UpdateStatus, RolloutStrategy
from schemas import (
    FirmwareUploadSchema, FirmwareMetadataSchema, FirmwareUpdateSchema,
    FirmwareRolloutCreateSchema, FirmwareRolloutSchema, FirmwareRolloutUpdateSchema,
    DeviceUpdateStatusSchema, BulkUpdateRequestSchema, CompatibilityCheckSchema,
    CompatibilityResultSchema, FirmwareStatsSchema, UpdateStatsSchema,
    RolloutStatsSchema, FirmwareSearchSchema, DeviceUpdateRequestSchema,
    DeviceRollbackRequestSchema, FirmwareDiffSchema, FirmwareDiffResultSchema
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Home Automation OTA Service", version="2.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3002", "http://localhost:3003"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "home-automation")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "home-automation-backend")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6380")
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1884"))

# Firmware storage
FIRMWARE_DIR = Path("firmware_storage")
FIRMWARE_DIR.mkdir(exist_ok=True)

# Initialize Keycloak client
keycloak_openid = KeycloakOpenID(
    server_url=KEYCLOAK_URL,
    client_id=KEYCLOAK_CLIENT_ID,
    realm_name=KEYCLOAK_REALM,
)

# Redis client for caching
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# MQTT client for device communication
mqtt_client = mqtt.Client()

# Initialize firmware manager
firmware_manager = FirmwareManager(FIRMWARE_DIR, redis_client, mqtt_client)

# Security scheme
security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify JWT token with Keycloak"""
    try:
        token = credentials.credentials
        
        # Check cache first
        cached_user = redis_client.get(f"user_token:{token}")
        if cached_user:
            return json.loads(cached_user)
        
        # Get Keycloak public key and verify token
        public_key_raw = keycloak_openid.public_key()
        import textwrap
        formatted_key = '\\n'.join(textwrap.wrap(public_key_raw, 64))
        public_key = f"-----BEGIN PUBLIC KEY-----\\n{formatted_key}\\n-----END PUBLIC KEY-----"
        options = {"verify_signature": True, "verify_aud": False, "verify_exp": True}
        
        token_info = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options=options
        )
        
        # Cache the user info for 5 minutes
        redis_client.setex(f"user_token:{token}", 300, json.dumps(token_info))
        
        return token_info
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except (jwt.InvalidTokenError, jwt.DecodeError, jwt.InvalidSignatureError, jwt.InvalidKeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting OTA Service")
    
    # Connect to MQTT broker
    try:
        mqtt_client.connect(MQTT_HOST, MQTT_PORT, 60)
        mqtt_client.loop_start()
        logger.info("Connected to MQTT broker")
    except Exception as e:
        logger.error(f"Failed to connect to MQTT broker: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    logger.info("OTA Service stopped")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ota-service"}

# Firmware Management Endpoints

@app.post("/api/firmware/upload", response_model=Dict[str, str])
async def upload_firmware(
    firmware_file: UploadFile = File(...),
    device_type: str = Form(...),
    board_model: str = Form(...),
    version: str = Form(...),
    status: str = Form("development"),
    description: str = Form(""),
    changelog: str = Form(""),
    min_compatible_version: Optional[str] = Form(None),
    max_compatible_version: Optional[str] = Form(None),
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """Upload new firmware"""
    try:
        # Validate user permissions
        roles = current_user.get("realm_access", {}).get("roles", [])
        if "admin" not in roles and "firmware_manager" not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Read firmware file
        firmware_data = await firmware_file.read()
        
        # Create firmware upload schema
        firmware_schema = FirmwareUploadSchema(
            device_type=device_type,
            board_model=board_model,
            version=version,
            status=status,
            description=description,
            changelog=changelog,
            min_compatible_version=min_compatible_version,
            max_compatible_version=max_compatible_version
        )
        
        # Upload firmware
        firmware_id = await firmware_manager.upload_firmware(
            firmware_schema, 
            firmware_data, 
            current_user.get("sub")
        )
        
        return {"firmware_id": firmware_id, "message": "Firmware uploaded successfully"}
        
    except Exception as e:
        logger.error(f"Firmware upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Firmware upload failed"
        )

@app.get("/api/firmware", response_model=List[FirmwareMetadataSchema])
async def list_firmwares(
    device_type: Optional[str] = None,
    board_model: Optional[str] = None,
    status: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """List all firmwares with optional filters"""
    try:
        device_type_enum = DeviceType(device_type) if device_type else None
        status_enum = FirmwareStatus(status) if status else None
        
        firmwares = await firmware_manager.list_firmwares(
            device_type=device_type_enum,
            status=status_enum,
            board_model=board_model
        )
        
        return [
            FirmwareMetadataSchema(
                id=f"fw_{i}",
                device_type=fw.device_type,
                board_model=fw.board_model,
                version=str(fw.version),
                status=fw.status,
                description=fw.description,
                changelog=fw.changelog,
                build_date=fw.build_date,
                file_size=fw.file_size,
                checksum=fw.checksum,
                min_compatible_version=fw.min_compatible_version,
                max_compatible_version=fw.max_compatible_version,
                required_capabilities=fw.required_capabilities,
                breaking_changes=fw.breaking_changes,
                security_fixes=fw.security_fixes,
                performance_improvements=fw.performance_improvements,
                new_features=fw.new_features,
                bug_fixes=fw.bug_fixes,
                rollback_version=fw.rollback_version,
                created_by=fw.created_by,
                approved_by=fw.approved_by,
                approval_date=fw.approval_date,
                download_url=f"/api/firmware/{f'fw_{i}'}/download"
            )
            for i, fw in enumerate(firmwares)
        ]
        
    except Exception as e:
        logger.error(f"Failed to list firmwares: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list firmwares"
        )

@app.get("/api/firmware/{firmware_id}", response_model=FirmwareMetadataSchema)
async def get_firmware(
    firmware_id: str,
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """Get firmware metadata"""
    try:
        firmware = await firmware_manager.get_firmware_metadata(firmware_id)
        if not firmware:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Firmware not found"
            )
        
        return FirmwareMetadataSchema(
            id=firmware_id,
            device_type=firmware.device_type,
            board_model=firmware.board_model,
            version=str(firmware.version),
            status=firmware.status,
            description=firmware.description,
            changelog=firmware.changelog,
            build_date=firmware.build_date,
            file_size=firmware.file_size,
            checksum=firmware.checksum,
            min_compatible_version=firmware.min_compatible_version,
            max_compatible_version=firmware.max_compatible_version,
            required_capabilities=firmware.required_capabilities,
            breaking_changes=firmware.breaking_changes,
            security_fixes=firmware.security_fixes,
            performance_improvements=firmware.performance_improvements,
            new_features=firmware.new_features,
            bug_fixes=firmware.bug_fixes,
            rollback_version=firmware.rollback_version,
            created_by=firmware.created_by,
            approved_by=firmware.approved_by,
            approval_date=firmware.approval_date,
            download_url=f"/api/firmware/{firmware_id}/download"
        )
        
    except Exception as e:
        logger.error(f"Failed to get firmware: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get firmware"
        )

@app.get("/api/firmware/{firmware_id}/download")
async def download_firmware(
    firmware_id: str,
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """Download firmware file"""
    try:
        firmware_path = FIRMWARE_DIR / f"{firmware_id}.bin"
        if not firmware_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Firmware file not found"
            )
        
        return FileResponse(
            firmware_path,
            media_type="application/octet-stream",
            filename=f"{firmware_id}.bin"
        )
        
    except Exception as e:
        logger.error(f"Failed to download firmware: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download firmware"
        )

@app.post("/api/firmware/{firmware_id}/approve")
async def approve_firmware(
    firmware_id: str,
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """Approve firmware for production use"""
    try:
        # Check admin permissions
        roles = current_user.get("realm_access", {}).get("roles", [])
        if "admin" not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        success = await firmware_manager.approve_firmware(firmware_id, current_user.get("sub"))
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Firmware not found"
            )
        
        return {"message": "Firmware approved successfully"}
        
    except Exception as e:
        logger.error(f"Failed to approve firmware: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve firmware"
        )

# Device Update Endpoints

@app.post("/api/devices/{device_id}/update")
async def update_device(
    device_id: str,
    update_request: DeviceUpdateRequestSchema,
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """Update a single device"""
    try:
        success = await firmware_manager.update_single_device(
            device_id, 
            update_request.firmware_id,
            update_request.force_update
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to start device update"
            )
        
        return {"message": "Device update started successfully"}
        
    except Exception as e:
        logger.error(f"Failed to update device: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update device"
        )

@app.post("/api/devices/bulk-update")
async def bulk_update_devices(
    request: BulkUpdateRequestSchema,
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """Perform bulk update of devices"""
    try:
        # Check admin permissions
        roles = current_user.get("realm_access", {}).get("roles", [])
        if "admin" not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        rollout_id = await firmware_manager.bulk_update_devices(request)
        
        return {"rollout_id": rollout_id, "message": "Bulk update started successfully"}
        
    except Exception as e:
        logger.error(f"Failed to start bulk update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start bulk update"
        )

@app.post("/api/devices/{device_id}/compatibility-check")
async def check_device_compatibility(
    device_id: str,
    check_request: CompatibilityCheckSchema,
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """Check device compatibility with firmware"""
    try:
        result = await firmware_manager.check_device_compatibility(
            device_id, 
            check_request.firmware_id
        )
        
        return CompatibilityResultSchema(
            compatible=result["compatible"],
            issues=result.get("issues", []),
            warnings=result.get("warnings", []),
            recommendation=result.get("recommendation", "unknown"),
            risk_level=result.get("risk_level", "unknown"),
            upgrade_path=result.get("upgrade_path", [])
        )
        
    except Exception as e:
        logger.error(f"Failed to check compatibility: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check compatibility"
        )

# Rollout Management Endpoints

@app.post("/api/rollouts", response_model=Dict[str, str])
async def create_rollout(
    rollout_data: FirmwareRolloutCreateSchema,
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """Create a new firmware rollout"""
    try:
        # Check admin permissions
        roles = current_user.get("realm_access", {}).get("roles", [])
        if "admin" not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        rollout_id = await firmware_manager.create_rollout(rollout_data, current_user.get("sub"))
        
        return {"rollout_id": rollout_id, "message": "Rollout created successfully"}
        
    except Exception as e:
        logger.error(f"Failed to create rollout: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create rollout"
        )

@app.post("/api/rollouts/{rollout_id}/start")
async def start_rollout(
    rollout_id: str,
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """Start a firmware rollout"""
    try:
        # Check admin permissions
        roles = current_user.get("realm_access", {}).get("roles", [])
        if "admin" not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        success = await firmware_manager.start_rollout(rollout_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rollout not found"
            )
        
        return {"message": "Rollout started successfully"}
        
    except Exception as e:
        logger.error(f"Failed to start rollout: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start rollout"
        )

@app.get("/api/rollouts/{rollout_id}")
async def get_rollout(
    rollout_id: str,
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """Get rollout details"""
    try:
        rollout = await firmware_manager.get_rollout(rollout_id)
        if not rollout:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rollout not found"
            )
        
        return rollout.to_dict()
        
    except Exception as e:
        logger.error(f"Failed to get rollout: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get rollout"
        )

# Statistics Endpoints

@app.get("/api/stats/firmware", response_model=FirmwareStatsSchema)
async def get_firmware_stats(
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """Get firmware statistics"""
    try:
        stats = await firmware_manager.get_firmware_stats()
        return FirmwareStatsSchema(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get firmware stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get firmware stats"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3004)