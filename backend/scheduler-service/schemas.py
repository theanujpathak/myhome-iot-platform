from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, time
from enum import Enum

class TriggerType(str, Enum):
    TIME = "time"
    DEVICE_STATE = "device_state"
    CONDITIONAL = "conditional"
    MANUAL = "manual"

class ActionType(str, Enum):
    DEVICE_COMMAND = "device_command"
    NOTIFICATION = "notification"
    WEBHOOK = "webhook"

class ScheduleStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"
    ERROR = "error"

class TimeTriggerConfig(BaseModel):
    time: str = Field(..., pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")  # HH:MM format
    days: List[str] = Field(..., min_items=1)  # ["monday", "tuesday", etc.] or ["weekdays", "weekends", "all"]
    timezone: Optional[str] = "UTC"

class DeviceStateTriggerConfig(BaseModel):
    device_id: str
    state_key: str
    operator: str = Field(..., pattern=r"^(eq|ne|gt|lt|gte|lte|contains)$")
    value: Union[str, int, float, bool]

class ConditionalTriggerConfig(BaseModel):
    conditions: List[Dict[str, Any]]
    operator: str = Field("and", pattern=r"^(and|or)$")

class DeviceAction(BaseModel):
    type: ActionType = ActionType.DEVICE_COMMAND
    device_id: str
    command: str
    parameters: Optional[Dict[str, Any]] = {}

class NotificationAction(BaseModel):
    type: ActionType = ActionType.NOTIFICATION
    title: str
    message: str
    recipients: Optional[List[str]] = []

class WebhookAction(BaseModel):
    type: ActionType = ActionType.WEBHOOK
    url: str
    method: str = "POST"
    headers: Optional[Dict[str, str]] = {}
    payload: Optional[Dict[str, Any]] = {}

class ConditionBase(BaseModel):
    device_id: Optional[str] = None
    state_key: Optional[str] = None
    operator: str = Field(..., pattern=r"^(eq|ne|gt|lt|gte|lte|contains)$")
    value: Union[str, int, float, bool]
    time_start: Optional[str] = None  # HH:MM format
    time_end: Optional[str] = None    # HH:MM format

class ScheduleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    trigger_type: TriggerType
    trigger_config: Dict[str, Any]
    actions: List[Dict[str, Any]]
    conditions: Optional[List[Dict[str, Any]]] = []
    enabled: bool = True

    @validator('trigger_config')
    def validate_trigger_config(cls, v, values):
        trigger_type = values.get('trigger_type')
        if trigger_type == TriggerType.TIME:
            TimeTriggerConfig(**v)
        elif trigger_type == TriggerType.DEVICE_STATE:
            DeviceStateTriggerConfig(**v)
        elif trigger_type == TriggerType.CONDITIONAL:
            ConditionalTriggerConfig(**v)
        return v

class ScheduleCreate(ScheduleBase):
    pass

class ScheduleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    trigger_config: Optional[Dict[str, Any]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    conditions: Optional[List[Dict[str, Any]]] = None
    enabled: Optional[bool] = None

class ScheduleResponse(ScheduleBase):
    id: int
    user_id: str
    status: ScheduleStatus
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int
    error_count: int
    last_error: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ScheduleExecutionResponse(BaseModel):
    id: int
    schedule_id: int
    execution_time: datetime
    success: bool
    error_message: Optional[str] = None
    execution_duration: Optional[int] = None
    actions_executed: Optional[List[Dict[str, Any]]] = None
    trigger_data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class AutomationRuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    conditions: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    enabled: bool = True
    priority: int = Field(0, ge=0, le=100)
    cooldown_seconds: int = Field(0, ge=0)

class AutomationRuleCreate(AutomationRuleBase):
    pass

class AutomationRuleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    conditions: Optional[List[Dict[str, Any]]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    enabled: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0, le=100)
    cooldown_seconds: Optional[int] = Field(None, ge=0)

class AutomationRuleResponse(AutomationRuleBase):
    id: int
    user_id: str
    last_triggered: Optional[datetime] = None
    trigger_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ScheduleExecuteRequest(BaseModel):
    override_conditions: bool = False
    test_mode: bool = False

class ScheduleExecuteResponse(BaseModel):
    success: bool
    message: str
    execution_id: Optional[int] = None
    actions_executed: Optional[List[Dict[str, Any]]] = None