#!/usr/bin/env python3
"""
Trading Bot Marketplace - Main Application
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, logger, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from sqlalchemy.orm import Session
from core.database import get_db
from services.telegram_service import TelegramService
from services.discord_service import DiscordService

# Import from new structure
from core.database import engine
from core.models import Base
from api.endpoints import auth, bots, subscriptions, admin
from api.endpoints import exchange_credentials, user_principals, futures_bot, marketplace

# Create database tables
Base.metadata.create_all(bind=engine)

telegram_service = TelegramService()
discord_service = DiscordService()
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await telegram_service.run()
        # await discord_service.run()
        yield
    except Exception as e:
        logger.error("Error occurred during lifespan: %s", str(e))
    finally:
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
