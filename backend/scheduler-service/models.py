from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
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

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    user_id = Column(String, nullable=False)  # Keycloak user ID
    trigger_type = Column(String, nullable=False)  # TriggerType enum
    trigger_config = Column(JSON, nullable=False)  # Configuration for the trigger
    actions = Column(JSON, nullable=False)  # List of actions to execute
    conditions = Column(JSON, default=[])  # Optional conditions that must be met
    enabled = Column(Boolean, default=True)
    status = Column(String, default=ScheduleStatus.ACTIVE)
    last_run = Column(DateTime(timezone=True))
    next_run = Column(DateTime(timezone=True))
    run_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    last_error = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    executions = relationship("ScheduleExecution", back_populates="schedule")

class ScheduleExecution(Base):
    __tablename__ = "schedule_executions"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id"))
    execution_time = Column(DateTime(timezone=True), server_default=func.now())
    success = Column(Boolean, nullable=False)
    error_message = Column(Text)
    execution_duration = Column(Integer)  # Duration in milliseconds
    actions_executed = Column(JSON)  # Record of which actions were executed
    trigger_data = Column(JSON)  # Data that triggered the execution

    # Relationships
    schedule = relationship("Schedule", back_populates="executions")

class AutomationRule(Base):
    __tablename__ = "automation_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    user_id = Column(String, nullable=False)  # Keycloak user ID
    conditions = Column(JSON, nullable=False)  # List of conditions
    actions = Column(JSON, nullable=False)  # List of actions
    enabled = Column(Boolean, default=True)
    priority = Column(Integer, default=0)  # Higher priority rules run first
    cooldown_seconds = Column(Integer, default=0)  # Minimum time between executions
    last_triggered = Column(DateTime(timezone=True))
    trigger_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<AutomationRule(id={self.id}, name={self.name})>"