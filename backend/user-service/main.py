from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from keycloak import KeycloakOpenID
import os
import httpx
import jwt
from typing import Optional, Dict, Any
import redis
import json

from database import get_db, engine
from models import User, Base
from schemas import UserCreate, UserResponse, UserUpdate

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Home Automation User Service", version="1.0.0")

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

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "user-service"}

@app.get("/api/user/profile", response_model=UserResponse)
async def get_user_profile(
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get current user profile"""
    user_id = current_user.get("sub")
    email = current_user.get("email")
    
    # Check if user exists in local database
    user = db.query(User).filter(User.keycloak_id == user_id).first()
    
    if not user:
        # Create user if doesn't exist
        user = User(
            keycloak_id=user_id,
            email=email,
            username=current_user.get("preferred_username"),
            first_name=current_user.get("given_name"),
            last_name=current_user.get("family_name"),
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return UserResponse(
        id=user.id,
        keycloak_id=user.keycloak_id,
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

@app.put("/api/user/profile", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    user_id = current_user.get("sub")
    
    user = db.query(User).filter(User.keycloak_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update user fields
    if user_update.first_name is not None:
        user.first_name = user_update.first_name
    if user_update.last_name is not None:
        user.last_name = user_update.last_name
    if user_update.username is not None:
        user.username = user_update.username
    
    db.commit()
    db.refresh(user)
    
    return UserResponse(
        id=user.id,
        keycloak_id=user.keycloak_id,
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

@app.get("/api/users", response_model=list[UserResponse])
async def get_users(
    current_user: Dict[str, Any] = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get all users (admin only)"""
    # Check if user has admin role
    roles = current_user.get("realm_access", {}).get("roles", [])
    if "admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    users = db.query(User).all()
    return [
        UserResponse(
            id=user.id,
            keycloak_id=user.keycloak_id,
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        for user in users
    ]

@app.post("/api/user/logout")
async def logout_user(
    current_user: Dict[str, Any] = Depends(verify_token),
):
    """Logout user and invalidate token"""
    try:
        # In a real implementation, you would invalidate the token in Keycloak
        # For now, we'll just remove it from our cache
        token = current_user.get("jti")  # JWT ID
        if token:
            redis_client.delete(f"user_token:{token}")
        
        return {"message": "Logout successful"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)