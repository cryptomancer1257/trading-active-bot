#!/usr/bin/env python3
"""
Trading Bot Marketplace - Main Application
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from sqlalchemy.orm import Session
from core.database import get_db
from services.telegram_service import TelegramService
from services.discord_service import DiscordService
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import from new structure
from core.database import engine
from core.models import Base
from api.endpoints import auth, bots, subscriptions, admin
from api.endpoints import exchange_credentials, user_principals, futures_bot, marketplace
from api.endpoints import paypal_payments
from api.endpoints import prompts, llm_prompts
from api.endpoints import bot_prompts
from api.endpoints import llm_providers
from api.endpoints import credentials
from api.endpoints import risk_management
from api.endpoints import dashboard
from api.endpoints import plans
from api.endpoints import feature_flags

import logging
logger = logging.getLogger("uvicorn.error")
# Create database tables
Base.metadata.create_all(bind=engine)

telegram_service = TelegramService()
discord_service = DiscordService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start background services
    telegram_task = asyncio.create_task(telegram_service.run())
    discord_task = asyncio.create_task(discord_service.run())
    
    try:
        yield
    except Exception as e:
        logger.error("Error occurred during lifespan: %s", str(e))
    finally:
        # Cancel background tasks gracefully
        telegram_task.cancel()
        discord_task.cancel()
        
        # Wait for tasks to complete
        try:
            await asyncio.gather(telegram_task, discord_task, return_exceptions=True)
        except Exception as e:
            logger.error("Error during task cleanup: %s", str(e))
        
        await app.stop()
        await app.shutdown()

# Create FastAPI app
app = FastAPI(
    lifespan=lifespan,
    title="Trading Bot Marketplace",
    description="A comprehensive marketplace for trading bot rental",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(bots.router, prefix="/bots", tags=["Bots"])
app.include_router(subscriptions.router, prefix="/subscriptions", tags=["Subscriptions"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(exchange_credentials.router, prefix="/exchange-credentials", tags=["Exchange Credentials"])
app.include_router(user_principals.router, prefix="/user-principals", tags=["User Principals"])
app.include_router(futures_bot.router, prefix="/api", tags=["Futures Bot"])  # Available in both modes
app.include_router(marketplace.router, prefix="/marketplace", tags=["Marketplace"])
app.include_router(paypal_payments.router, prefix="/payments", tags=["PayPal Payments"])
# Register prompts routers - ORDER MATTERS! More specific routes first
app.include_router(prompts.router, prefix="/prompts", tags=["Trading Strategy Templates"])  # /prompts/templates/* routes
app.include_router(llm_prompts.router, prefix="/prompts", tags=["LLM Prompts"])  # /prompts/* routes (less specific)
app.include_router(bot_prompts.router, prefix="/bot-prompts", tags=["Bot prompts"])
app.include_router(llm_providers.router, prefix="/developer/llm-providers", tags=["LLM Providers"])
app.include_router(credentials.router, prefix="/developer/credentials", tags=["Developer"])
app.include_router(risk_management.router, prefix="/v1/risk-management", tags=["Risk Management"])
app.include_router(dashboard.router, prefix="/v1/dashboard", tags=["Dashboard"])
app.include_router(plans.router, prefix="/api", tags=["Plans"])
app.include_router(feature_flags.router, tags=["Feature Flags"])


@app.post("/webhook")
async def webhook(req: Request, db: Session = Depends(get_db)):
    try:
        body = await req.json()
        return await telegram_service.handle_telegram_message(body)
    except Exception as e:
        db.rollback()
        logger.error("Telegram webhook error: %s", str(e), exc_info=True)
        return {"ok": False}

@app.get("/")
async def root():
    return {"message": "Trading Bot Marketplace API", "version": "2.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
