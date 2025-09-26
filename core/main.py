from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
import uvicorn
import logging
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv('.env')

from core.database import engine, SessionLocal
from core import models

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check if we're in development mode
development_mode = os.getenv('DEVELOPMENT_MODE', 'false').lower() == 'true'

# Only import API endpoints that don't require external services in development mode
if not development_mode:
    from api.endpoints import auth, bots, subscriptions, admin, exchanges, exchange_credentials, credentials
    from api.endpoints import marketplace, futures_bot, user_principals, paypal_payments
else:
    from api.endpoints import auth, bots, admin, exchange_credentials, credentials, futures_bot, user_principals
    # Import marketplace for publish-token functionality in development
    from api.endpoints import marketplace
    # Import simplified subscriptions for testing without S3
    try:
        from api.endpoints import subscriptions_simple
        logger.info("Simplified subscriptions endpoint loaded for testing")
    except ImportError:
        logger.warning("Simplified subscriptions endpoint not available")
    logger.info("Development mode: Skipping endpoints that require external services")

# Initialize managers on startup
s3_manager = None
bot_manager = None

if development_mode:
    logger.info("Running in DEVELOPMENT MODE - S3 and BotManager disabled")
else:
    # Initialize S3 and BotManager only in production mode
    try:
        from services.s3_manager import S3Manager
        from core.bot_manager import BotManager
        
        s3_manager = S3Manager()
        bot_manager = BotManager()
        logger.info("S3, BotManager,  initialized successfully")
    except Exception as e:
                 logger.error(f"Failed to initialize S3/BotManager: {e}")

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="Bot Marketplace API",
    description="A marketplace for trading bot rentals with S3 integration",
    version="2.0.0"
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

# Include API routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(bots.router, prefix="/bots", tags=["Bots"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(exchange_credentials.router, prefix="/exchange-credentials", tags=["Exchange Credentials"])
app.include_router(credentials.router, prefix="/developer/credentials", tags=["Developer API Credentials"])
app.include_router(user_principals.router, prefix="/user-principals", tags=["User Principals"])
app.include_router(futures_bot.router, prefix="/api", tags=["Futures Bot"])  # Available in both modes

# Only include these routers in production mode (they require external services)
if not development_mode:
    app.include_router(subscriptions.router, prefix="/subscriptions", tags=["Subscriptions"])
    app.include_router(marketplace.router, prefix="/marketplace", tags=["Marketplace"])
    app.include_router(exchanges.router, prefix="/exchanges", tags=["Exchanges"])
    app.include_router(paypal_payments.router, prefix="/payments", tags=["PayPal Payments"])
else:
    # Include marketplace for publish-token functionality in development
    app.include_router(marketplace.router, prefix="/marketplace", tags=["Marketplace (Dev)"])
    # Include simplified subscriptions for testing without S3
    try:
        app.include_router(subscriptions_simple.router, prefix="/subscriptions-simple", tags=["Subscriptions (Simplified)"])
        logger.info("Simplified subscriptions endpoint included for testing")
    except NameError:
        logger.warning("Simplified subscriptions endpoint not available")
    logger.info("Development mode: Marketplace enabled, full subscriptions and exchanges endpoints disabled")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Bot Marketplace API",
        "version": "2.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "development_mode": development_mode,
        "endpoints": {
            "auth": "/auth",
            "bots": "/bots", 
            "admin": "/admin",
            "subscriptions": "/subscriptions" if not development_mode else "/subscriptions-simple",
            "exchanges": "/exchanges" if not development_mode else "disabled",
            "docs": "/docs",
            "health": "/health",
            "exchange-credentials": "/exchange-credentials"
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected",
            "s3_manager": "initialized" if s3_manager else "disabled",
            "bot_manager": "initialized" if bot_manager else "disabled",
            "development_mode": development_mode
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

# System info endpoint
@app.get("/system/info")
async def system_info():
    """Get system information"""
    try:
        import psutil
        import platform
        
        return {
            "system": {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "disk_usage": psutil.disk_usage('/').percent
            },
            "application": {
                "version": "2.0.0",
                "development_mode": development_mode,
                "s3_enabled": s3_manager is not None,
                "bot_manager_enabled": bot_manager is not None
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except ImportError:
        return {
            "error": "psutil not available",
            "timestamp": datetime.utcnow().isoformat()
        }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("Bot Marketplace API starting up...")
    logger.info(f"Development mode: {development_mode}")
    
    if s3_manager:
        logger.info("S3 Manager initialized")
    if bot_manager:
        logger.info("Bot Manager initialized")
    
    logger.info("Bot Marketplace API startup complete")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Bot Marketplace API shutting down...")
    
    if s3_manager:
        logger.info("S3 Manager shutdown")
    if bot_manager:
        logger.info("Bot Manager shutdown")
    
    logger.info("Bot Marketplace API shutdown complete")

if __name__ == "__main__":
    uvicorn.run("core.main:app", host="0.0.0.0", port=8000, reload=True)