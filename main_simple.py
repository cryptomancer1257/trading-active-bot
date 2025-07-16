"""
Simplified Bot Marketplace API - Standalone Version
Runs without Docker Compose, Celery, or Redis
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn
import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from database import engine, SessionLocal
import models
import schemas, crud, security

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="Bot Marketplace API (Standalone)",
    description="Trading Bot Marketplace - Simplified version for development",
    version="2.0.0-simple"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2 setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Simplified API routes (without complex dependencies)

@app.get("/")
async def root():
    return {
        "message": "Bot Marketplace API - Standalone Version",
        "version": "2.0.0-simple",
        "mode": "development",
        "features": [
            "User authentication",
            "Bot management (local storage)",
            "Basic subscription management",
            "SQLite database"
        ],
        "note": "This is a simplified version without S3, Celery, or Redis dependencies"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database
        db = SessionLocal()
        db.execute("SELECT 1")
        db_status = "healthy"
        db.close()
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": db_status,
            "mode": "standalone"
        }
    }

# ===== AUTH ROUTES =====
from passlib.context import CryptContext
from datetime import timedelta
from jose import JWTError, jwt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@app.post("/auth/register", response_model=schemas.UserInDB)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user exists
    existing_user = crud.get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    db_user = crud.create_user(db, user)
    return db_user

@app.post("/auth/token")
def login_for_access_token(form_data: schemas.UserLogin, db: Session = Depends(get_db)):
    """Login and get access token"""
    user = crud.authenticate_user(db, form_data.email, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# ===== BOT ROUTES =====

@app.get("/bots", response_model=list[schemas.BotInDB])
def list_bots(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all approved bots"""
    bots = crud.get_bots(db, skip=skip, limit=limit)
    return bots

@app.post("/bots", response_model=schemas.BotInDB)
def create_bot(bot: schemas.BotCreate, db: Session = Depends(get_db)):
    """Create a new bot (simplified - stores code in database)"""
    # In simplified version, we store bot code directly in database
    db_bot = crud.create_bot(db, bot)
    return db_bot

@app.get("/bots/{bot_id}", response_model=schemas.BotInDB)
def get_bot(bot_id: int, db: Session = Depends(get_db)):
    """Get bot by ID"""
    bot = crud.get_bot_by_id(db, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    return bot

# ===== SUBSCRIPTION ROUTES =====

@app.get("/subscriptions", response_model=list[schemas.SubscriptionInDB])
def list_my_subscriptions(db: Session = Depends(get_db)):
    """List user's subscriptions (simplified)"""
    # In simplified version, return all subscriptions
    subscriptions = crud.get_subscriptions(db, skip=0, limit=100)
    return subscriptions

@app.post("/subscriptions", response_model=schemas.SubscriptionInDB)
def create_subscription(subscription: schemas.SubscriptionCreate, db: Session = Depends(get_db)):
    """Create a new subscription (simplified - no background execution)"""
    # Check if bot exists
    bot = crud.get_bot_by_id(db, subscription.bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Create subscription
    db_subscription = crud.create_subscription(db, subscription)
    return db_subscription

# ===== ADMIN ROUTES =====

@app.get("/admin/stats")
def get_admin_stats(db: Session = Depends(get_db)):
    """Get admin statistics"""
    try:
        total_users = db.query(models.User).count()
        total_bots = db.query(models.Bot).count()
        total_subscriptions = db.query(models.Subscription).count()
        
        return {
            "total_users": total_users,
            "total_bots": total_bots,
            "total_subscriptions": total_subscriptions,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting Bot Marketplace API in STANDALONE mode")
    logger.info("Features: Basic CRUD operations, SQLite database, no external dependencies")
    uvicorn.run(app, host="0.0.0.0", port=8000) 