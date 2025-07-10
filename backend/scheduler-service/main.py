from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from keycloak import KeycloakOpenID
import os
import jwt
from typing import Optional, Dict, Any, List
import redis
import json
import logging
from datetime import datetime

from database import get_db, engine
from models import Schedule, ScheduleExecution, AutomationRule, Base
from schemas import (
    ScheduleCreate, ScheduleUpdate, ScheduleResponse, ScheduleExecuteRequest, ScheduleExecuteResponse,
    ScheduleExecutionResponse, AutomationRuleCreate, AutomationRuleUpdate, AutomationRuleResponse
)
from scheduler import scheduler_service
from ai_engine import ai_engine

# Create tables
Base.metadata.create_all(bind=engine)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Home Automation Scheduler Service", version="1.0.0")

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

# Initialize Keycloak client
keycloak_openid = KeycloakOpenID(
    server_url=KEYCLOAK_URL,
    client_id=KEYCLOAK_CLIENT_ID,
    realm_name=KEYCLOAK_REALM,
)

# Redis client for caching
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

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
        # Format the public key properly for PyJWT with line breaks every 64 chars
        import textwrap
        formatted_key = '\n'.join(textwrap.wrap(public_key_raw, 64))
        public_key = f"-----BEGIN PUBLIC KEY-----\n{formatted_key}\n-----END PUBLIC KEY-----"
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
    """Initialize scheduler and AI engine on startup"""
    logger.info("Starting Scheduler Service")
    await scheduler_service.start()
    await ai_engine.start()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Stopping Scheduler Service")
    await scheduler_service.stop()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "scheduler-service"}

# Schedule endpoints
@app.get("/api/schedules", response_model=List[ScheduleResponse])
async def get_schedules(
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get user's schedules"""
    user_id = current_user.get("sub")
    schedules = db.query(Schedule).filter(Schedule.user_id == user_id).all()
    return schedules

@app.post("/api/schedules", response_model=ScheduleResponse)
async def create_schedule(
    schedule: ScheduleCreate,
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Create new schedule"""
    user_id = current_user.get("sub")
    
    db_schedule = Schedule(**schedule.dict(), user_id=user_id)
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    
    # Schedule the job
    await scheduler_service.schedule_job(db_schedule)
    
    return db_schedule

@app.get("/api/schedules/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: int,
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get specific schedule"""
    user_id = current_user.get("sub")
    schedule = db.query(Schedule).filter(
        Schedule.id == schedule_id,
        Schedule.user_id == user_id
    ).first()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    return schedule

@app.put("/api/schedules/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int,
    schedule: ScheduleUpdate,
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Update schedule"""
    user_id = current_user.get("sub")
    db_schedule = db.query(Schedule).filter(
        Schedule.id == schedule_id,
        Schedule.user_id == user_id
    ).first()
    
    if not db_schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    update_data = schedule.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_schedule, key, value)
    
    db.commit()
    db.refresh(db_schedule)
    
    # Reschedule the job
    await scheduler_service.schedule_job(db_schedule)
    
    return db_schedule

@app.delete("/api/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: int,
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Delete schedule"""
    user_id = current_user.get("sub")
    db_schedule = db.query(Schedule).filter(
        Schedule.id == schedule_id,
        Schedule.user_id == user_id
    ).first()
    
    if not db_schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    # Remove the scheduled job
    job_id = f"schedule_{schedule_id}"
    if scheduler_service.scheduler.get_job(job_id):
        scheduler_service.scheduler.remove_job(job_id)
    
    db.delete(db_schedule)
    db.commit()
    
    return {"message": "Schedule deleted successfully"}

@app.post("/api/schedules/{schedule_id}/execute", response_model=ScheduleExecuteResponse)
async def execute_schedule(
    schedule_id: int,
    execute_request: ScheduleExecuteRequest,
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Manually execute schedule"""
    user_id = current_user.get("sub")
    schedule = db.query(Schedule).filter(
        Schedule.id == schedule_id,
        Schedule.user_id == user_id
    ).first()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    try:
        # Execute the schedule
        await scheduler_service.execute_schedule(schedule_id)
        
        # Get the latest execution
        execution = db.query(ScheduleExecution).filter(
            ScheduleExecution.schedule_id == schedule_id
        ).order_by(ScheduleExecution.execution_time.desc()).first()
        
        return ScheduleExecuteResponse(
            success=execution.success if execution else True,
            message="Schedule executed successfully",
            execution_id=execution.id if execution else None,
            actions_executed=execution.actions_executed if execution else []
        )
        
    except Exception as e:
        return ScheduleExecuteResponse(
            success=False,
            message=f"Failed to execute schedule: {str(e)}"
        )

@app.get("/api/schedules/{schedule_id}/executions", response_model=List[ScheduleExecutionResponse])
async def get_schedule_executions(
    schedule_id: int,
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get schedule execution history"""
    user_id = current_user.get("sub")
    
    # Verify schedule belongs to user
    schedule = db.query(Schedule).filter(
        Schedule.id == schedule_id,
        Schedule.user_id == user_id
    ).first()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    executions = db.query(ScheduleExecution).filter(
        ScheduleExecution.schedule_id == schedule_id
    ).order_by(ScheduleExecution.execution_time.desc()).limit(limit).all()
    
    return executions

# Automation Rule endpoints
@app.get("/api/automation-rules", response_model=List[AutomationRuleResponse])
async def get_automation_rules(
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get user's automation rules"""
    user_id = current_user.get("sub")
    rules = db.query(AutomationRule).filter(AutomationRule.user_id == user_id).all()
    return rules

@app.post("/api/automation-rules", response_model=AutomationRuleResponse)
async def create_automation_rule(
    rule: AutomationRuleCreate,
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Create new automation rule"""
    user_id = current_user.get("sub")
    
    db_rule = AutomationRule(**rule.dict(), user_id=user_id)
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    
    return db_rule

@app.get("/api/automation-rules/{rule_id}", response_model=AutomationRuleResponse)
async def get_automation_rule(
    rule_id: int,
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get specific automation rule"""
    user_id = current_user.get("sub")
    rule = db.query(AutomationRule).filter(
        AutomationRule.id == rule_id,
        AutomationRule.user_id == user_id
    ).first()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Automation rule not found"
        )
    
    return rule

@app.put("/api/automation-rules/{rule_id}", response_model=AutomationRuleResponse)
async def update_automation_rule(
    rule_id: int,
    rule: AutomationRuleUpdate,
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Update automation rule"""
    user_id = current_user.get("sub")
    db_rule = db.query(AutomationRule).filter(
        AutomationRule.id == rule_id,
        AutomationRule.user_id == user_id
    ).first()
    
    if not db_rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Automation rule not found"
        )
    
    update_data = rule.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_rule, key, value)
    
    db.commit()
    db.refresh(db_rule)
    
    return db_rule

@app.delete("/api/automation-rules/{rule_id}")
async def delete_automation_rule(
    rule_id: int,
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Delete automation rule"""
    user_id = current_user.get("sub")
    db_rule = db.query(AutomationRule).filter(
        AutomationRule.id == rule_id,
        AutomationRule.user_id == user_id
    ).first()
    
    if not db_rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Automation rule not found"
        )
    
    db.delete(db_rule)
    db.commit()
    
    return {"message": "Automation rule deleted successfully"}

@app.get("/api/scheduler/status")
async def get_scheduler_status(
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """Get scheduler status"""
    # Check if user has admin role
    roles = current_user.get("realm_access", {}).get("roles", [])
    if "admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return {
        "running": scheduler_service.scheduler.running,
        "job_count": len(scheduler_service.scheduler.get_jobs()),
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None
            }
            for job in scheduler_service.scheduler.get_jobs()
        ]
    }

# AI and Analytics endpoints
@app.post("/api/ai/record-usage")
async def record_device_usage(
    usage_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """Record device usage for AI learning"""
    user_id = current_user.get("sub")
    
    try:
        await ai_engine.record_device_usage(
            user_id=user_id,
            device_id=usage_data.get("device_id"),
            action=usage_data.get("action"),
            states=usage_data.get("states", {}),
            timestamp=datetime.fromisoformat(usage_data.get("timestamp")) if usage_data.get("timestamp") else None
        )
        
        return {"success": True, "message": "Usage recorded"}
        
    except Exception as e:
        logger.error(f"Error recording usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record usage"
        )

@app.get("/api/ai/insights")
async def get_user_insights(
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """Get AI insights for the current user"""
    user_id = current_user.get("sub")
    
    try:
        insights = await ai_engine.get_user_insights(user_id)
        return insights
        
    except Exception as e:
        logger.error(f"Error getting insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get insights"
        )

@app.post("/api/ai/predict-usage")
async def predict_device_usage(
    prediction_request: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(verify_token)
):
    """Predict device usage probability"""
    user_id = current_user.get("sub")
    
    try:
        device_id = prediction_request.get("device_id")
        target_time_str = prediction_request.get("target_time")
        target_time = datetime.fromisoformat(target_time_str)
        
        probability = await ai_engine.predict_device_usage(user_id, device_id, target_time)
        
        return {
            "device_id": device_id,
            "target_time": target_time_str,
            "usage_probability": probability
        }
        
    except Exception as e:
        logger.error(f"Error predicting usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to predict usage"
        )

@app.post("/api/ai/create-suggested-automation")
async def create_suggested_automation(
    suggestion_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Create an automation rule from AI suggestion"""
    user_id = current_user.get("sub")
    
    try:
        # Create schedule from AI suggestion
        schedule_data = {
            "name": suggestion_data.get("name"),
            "description": suggestion_data.get("description"),
            "trigger_type": suggestion_data.get("trigger_type"),
            "trigger_config": suggestion_data.get("trigger_config"),
            "actions": suggestion_data.get("actions"),
            "enabled": True
        }
        
        db_schedule = Schedule(**schedule_data, user_id=user_id)
        db.add(db_schedule)
        db.commit()
        db.refresh(db_schedule)
        
        # Schedule the job
        await scheduler_service.schedule_job(db_schedule)
        
        return {
            "success": True,
            "message": "AI-suggested automation created",
            "schedule_id": db_schedule.id
        }
        
    except Exception as e:
        logger.error(f"Error creating suggested automation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create automation"
        )

@app.get("/api/analytics/system-stats")
async def get_system_analytics(
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get system analytics (admin only)"""
    # Check if user has admin role
    roles = current_user.get("realm_access", {}).get("roles", [])
    if "admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        # Get schedule statistics
        total_schedules = db.query(Schedule).count()
        active_schedules = db.query(Schedule).filter(Schedule.enabled == True).count()
        
        # Get execution statistics
        total_executions = db.query(ScheduleExecution).count()
        successful_executions = db.query(ScheduleExecution).filter(ScheduleExecution.success == True).count()
        
        # Get recent executions
        recent_executions = db.query(ScheduleExecution).order_by(
            ScheduleExecution.execution_time.desc()
        ).limit(10).all()
        
        # Get automation rules statistics
        total_rules = db.query(AutomationRule).count()
        active_rules = db.query(AutomationRule).filter(AutomationRule.enabled == True).count()
        
        return {
            "schedules": {
                "total": total_schedules,
                "active": active_schedules,
                "inactive": total_schedules - active_schedules
            },
            "executions": {
                "total": total_executions,
                "successful": successful_executions,
                "failed": total_executions - successful_executions,
                "success_rate": (successful_executions / total_executions * 100) if total_executions > 0 else 0
            },
            "automation_rules": {
                "total": total_rules,
                "active": active_rules,
                "inactive": total_rules - active_rules
            },
            "recent_executions": [
                {
                    "id": exec.id,
                    "schedule_id": exec.schedule_id,
                    "success": exec.success,
                    "execution_time": exec.execution_time,
                    "duration": exec.execution_duration
                }
                for exec in recent_executions
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting system analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get analytics"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3003)