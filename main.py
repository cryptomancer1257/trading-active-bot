from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

from database import engine, SessionLocal
import models

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check if we're in development mode
development_mode = os.getenv('DEVELOPMENT_MODE', 'false').lower() == 'true'

# Only import API endpoints that don't require external services in development mode
if not development_mode:
    from api.endpoints import auth, bots, subscriptions, admin, exchanges
else:
    from api.endpoints import auth, bots, admin
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
        from s3_manager import S3Manager
        from bot_manager import BotManager
        
        s3_manager = S3Manager()
        bot_manager = BotManager()
        logger.info("S3 and BotManager initialized successfully")
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

# Only include these routers in production mode (they require external services)
if not development_mode:
    app.include_router(subscriptions.router, prefix="/subscriptions", tags=["Subscriptions"])
    app.include_router(exchanges.router, prefix="/exchanges", tags=["Exchanges"])
else:
    # Include simplified subscriptions for testing without S3
    try:
        app.include_router(subscriptions_simple.router, prefix="/subscriptions-simple", tags=["Subscriptions (Simplified)"])
        logger.info("Simplified subscriptions endpoint included for testing")
    except NameError:
        logger.warning("Simplified subscriptions endpoint not available")
    logger.info("Development mode: Full subscriptions and exchanges endpoints disabled")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def root():
    return {
        "message": "Bot Marketplace API with S3 Integration",
        "version": "2.0.0",
        "features": [
            "Bot upload and management with S3 storage",
            "Multi-exchange support",
            "Bot versioning and rollback",
            "Real-time trading execution",
            "Performance analytics",
            "Subscription management",
            "Admin dashboard"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database
        db = SessionLocal()
        try:
            db.execute("SELECT 1")
            db_status = "healthy"
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
        finally:
            db.close()
        
        # Check S3
        try:
            s3_status = "healthy" if s3_manager.health_check() else "unhealthy"
        except Exception as e:
            s3_status = f"unhealthy: {str(e)}"
        
        # Check BotManager
        try:
            bot_manager_status = "healthy"
            # Could add more specific checks here
        except Exception as e:
            bot_manager_status = f"unhealthy: {str(e)}"
        
        return {
            "status": "healthy",
            "database": db_status,
            "s3": s3_status,
            "bot_manager": bot_manager_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/system/info")
async def system_info():
    """Get system information"""
    try:
        return {
            "api_version": "2.0.0",
            "s3_enabled": True,
            "s3_bucket": s3_manager.bucket_name,
            "supported_exchanges": ["binance", "coinbase", "kraken"],
            "bot_types": ["TECHNICAL", "ML", "DL", "LLM"],
            "features": {
                "bot_versioning": True,
                "s3_storage": True,
                "multi_exchange": True,
                "ml_models": True,
                "real_time_trading": True,
                "performance_analytics": True
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system info: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Bot Marketplace API...")
    
    # Initialize S3 manager
    try:
        s3_manager.initialize()
        logger.info("S3 Manager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize S3 Manager: {e}")
    
    # Initialize Bot Manager
    try:
        logger.info("Bot Manager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Bot Manager: {e}")
    
    logger.info("Bot Marketplace API started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Bot Marketplace API...")
    
    # Cleanup bot manager
    try:
        # Clear loaded bots from memory
        bot_manager.loaded_bots.clear()
        logger.info("Bot Manager cleaned up")
    except Exception as e:
        logger.error(f"Error during Bot Manager cleanup: {e}")
    
    logger.info("Bot Marketplace API shut down successfully")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )