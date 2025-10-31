import sys
import os

from services.telegram_service import TelegramService

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# file: api/endpoints/bots.py

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional, Any
from datetime import datetime
from decimal import Decimal
import json
import uuid
from PIL import Image
from io import BytesIO
from google.cloud import storage

from core import crud, models, schemas, security
from core.database import get_db
from core.bot_manager import BotManager
from core.api_key_manager import api_key_manager
from core.plan_checker import plan_checker
from services.s3_manager import S3Manager
import logging
from pathlib import Path

# Initialize managers
bot_manager = BotManager()
s3_manager = S3Manager()

# Initialize logger
logger = logging.getLogger(__name__)

router = APIRouter()

# --- Public endpoints ---
@router.get("/{bot_id}/trading-pairs")
def get_bot_trading_pairs(bot_id: int, db: Session = Depends(get_db)):
    """Get bot's supported trading pairs (public endpoint for marketplace - NO AUTH REQUIRED)"""
    try:
        bot = db.query(models.Bot).filter(
            models.Bot.id == bot_id,
            models.Bot.status == models.BotStatus.APPROVED
        ).first()
        
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bot not found or not approved (ID: {bot_id})"
            )
        
        # Return trading pairs
        trading_pairs = bot.trading_pairs if bot.trading_pairs else (
            [bot.trading_pair] if bot.trading_pair else ["BTCUSDT"]  # Default fallback
        )
        
        # Normalize trading pairs: replace "//" with "/" and ensure proper format
        normalized_pairs = []
        for pair in trading_pairs:
            if pair:
                # Replace multiple slashes with single slash
                normalized_pair = pair.replace('//', '/')
                # If no slash at all, try to format it (e.g., BTCUSDT -> BTC/USDT)
                if '/' not in normalized_pair and len(normalized_pair) >= 6:
                    # Common format: first 3-4 chars are base, rest is quote
                    # This is a simple heuristic, might need adjustment
                    if normalized_pair.endswith('USDT'):
                        base = normalized_pair[:-4]
                        normalized_pair = f"{base}/USDT"
                    elif normalized_pair.endswith('BTC'):
                        base = normalized_pair[:-3]
                        normalized_pair = f"{base}/BTC"
                    elif normalized_pair.endswith('ETH'):
                        base = normalized_pair[:-3]
                        normalized_pair = f"{base}/ETH"
                normalized_pairs.append(normalized_pair)
        
        return {
            "bot_id": bot.id,
            "bot_name": bot.name,
            "trading_pairs": normalized_pairs,
            "primary_pair": normalized_pairs[0] if normalized_pairs else "BTC/USDT",
            "count": len(normalized_pairs)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bot trading pairs for {bot_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve bot trading pairs: {str(e)}"
        )

@router.get("/stats")
def get_public_stats(db: Session = Depends(get_db)):
    """Get public statistics for landing page"""
    try:
        total_bots = db.query(models.Bot).filter(
            models.Bot.status == models.BotStatus.APPROVED
        ).count()
        
        total_subscriptions = db.query(models.Subscription).filter(
            models.Subscription.status == models.SubscriptionStatus.ACTIVE
        ).count()
        
        # Calculate average rating from approved bots
        bots_with_ratings = db.query(models.Bot).filter(
            models.Bot.status == models.BotStatus.APPROVED,
            models.Bot.average_rating > 0
        ).all()
        
        avg_rating = 0.0
        if bots_with_ratings:
            avg_rating = sum(bot.average_rating or 0 for bot in bots_with_ratings) / len(bots_with_ratings)
        
        # Count total developers
        total_developers = db.query(models.User).filter(
            models.User.role == models.UserRole.DEVELOPER
        ).count()
        
        return {
            "total_bots": total_bots,
            "total_subscriptions": total_subscriptions,
            "avg_rating": round(avg_rating, 1),
            "total_developers": total_developers
        }
    except Exception as e:
        logger.error(f"Failed to get public stats: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Return default values on error
        return {
            "total_bots": 0,
            "total_subscriptions": 0,
            "avg_rating": 0.0,
            "total_developers": 0
        }

@router.get("/check-name/{bot_name}")
def check_bot_name_availability(
    bot_name: str,
    db: Session = Depends(get_db)
):
    """Check if bot name is available (not taken by existing bots)"""
    try:
        # Check if bot name already exists (case-insensitive)
        existing_bot = db.query(models.Bot).filter(
            models.Bot.name.ilike(f"%{bot_name}%")
        ).first()
        
        is_available = existing_bot is None
        
        return {
            "name": bot_name,
            "available": is_available,
            "message": "Name is available" if is_available else f"Name '{bot_name}' is already taken"
        }
        
    except Exception as e:
        logger.error(f"Failed to check bot name availability: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check name availability: {str(e)}"
        )

@router.get("/templates", response_model=List[schemas.BotInDB])
def get_bot_templates(
    skip: int = 0,
    limit: int = 50,
    bot_type: Optional[str] = None,
    exchange_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get bot templates for creating new bots (only platform templates, not user-created bots)"""
    try:
        query = db.query(models.Bot).filter(
            models.Bot.status == models.BotStatus.APPROVED,
            # Filter for template bots only: Created by admin (developer_id = 1)
            # These are the official platform templates, not user-created bots
            models.Bot.developer_id == 1
        )
        
        # Filter by bot type if specified
        if bot_type:
            try:
                bot_type_enum = models.BotType(bot_type.upper())
                query = query.filter(models.Bot.bot_type == bot_type_enum)
            except ValueError:
                pass  # Invalid bot type, ignore filter
        
        # Filter by exchange type if specified
        if exchange_type:
            try:
                exchange_type_enum = models.ExchangeType(exchange_type.upper())
                query = query.filter(models.Bot.exchange_type == exchange_type_enum)
            except ValueError:
                pass  # Invalid exchange type, ignore filter
        
        # Order by creation date (newest first)
        query = query.order_by(models.Bot.created_at.desc())
        
        # Apply pagination
        templates = query.offset(skip).limit(limit).all()
        
        logger.info(f"Found {len(templates)} bot templates (filtered for platform templates only)")
        return templates
        
    except Exception as e:
        logger.error(f"Failed to get bot templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve bot templates: {str(e)}"
        )

@router.get("/", response_model=schemas.BotListResponse)
def get_public_bots(
    skip: int = 0,
    limit: int = 50,
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    order: str = "desc",
    network_filter: Optional[str] = Query(None, description="Filter by network: 'mainnet' or 'testnet'"),
    db: Session = Depends(get_db)
):
    """Get public approved bots with pagination and filtering"""
    bots, total = crud.get_public_bots(
        db, skip=skip, limit=limit, category_id=category_id, 
        search=search, sort_by=sort_by, order=order,
        network_filter=network_filter
    )
    return {
        "bots": bots,
        "total": total,
        "page": skip // limit + 1,
        "per_page": limit
    }

@router.get("/{bot_id}", response_model=schemas.BotInDB)
def get_bot_details(bot_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific bot"""
    bot = crud.get_bot_by_id(db, bot_id=bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    return bot

@router.get("/{bot_id}/historical-stats")
def get_bot_historical_stats(
    bot_id: int,
    current_user: models.User = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get historical transaction statistics for bot learning (AUTH REQUIRED)"""
    try:
        # Verify bot ownership
        bot = db.query(models.Bot).filter(models.Bot.id == bot_id).first()
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        # Only bot developer can access historical stats
        if bot.developer_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to view bot statistics")
        
        # Import TransactionService
        from services.transaction_service import TransactionService
        
        # Get stats
        transaction_service = TransactionService()
        limit = getattr(bot, 'historical_transaction_limit', 25)
        stats = transaction_service.get_transaction_summary_stats(bot_id=bot_id, limit=limit)
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching historical stats for bot {bot_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{bot_id}/reviews", response_model=List[schemas.BotReviewWithUser])
def get_bot_reviews(
    bot_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get reviews for a specific bot"""
    return crud.get_bot_reviews(db, bot_id=bot_id, skip=skip, limit=limit)

@router.get("/{bot_id}/performance")
def get_bot_performance_public(
    bot_id: int,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    Get bot performance metrics for public display (NO AUTH REQUIRED)
    Returns summary stats and chart data only (no recent transactions)
    Used by marketplace frontend to display performance tab
    """
    from sqlalchemy import func, and_, case
    from datetime import datetime, timedelta
    
    # Get bot to verify it exists
    bot = db.query(models.Bot).filter(models.Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Get subscription stats
    total_subscriptions = db.query(func.count(models.Subscription.id)).filter(
        models.Subscription.bot_id == bot_id
    ).scalar() or 0
    
    active_subscriptions = db.query(func.count(models.Subscription.id)).filter(
        models.Subscription.bot_id == bot_id,
        models.Subscription.status == models.SubscriptionStatus.ACTIVE
    ).scalar() or 0
    
    # Get transaction stats
    transactions_query = db.query(models.Transaction).join(
        models.Subscription,
        models.Subscription.id == models.Transaction.subscription_id
    ).filter(
        models.Subscription.bot_id == bot_id
    )
    
    # Get ALL transactions in period (OPEN + CLOSED)
    all_transactions_in_period = transactions_query.filter(
        models.Transaction.created_at >= start_date
    ).all()
    
    total_transactions = len(all_transactions_in_period)
    
    # Calculate P&L and win rate
    total_pnl = 0.0
    total_realized_pnl = 0.0
    total_unrealized_pnl = 0.0
    winning_trades = 0
    losing_trades = 0
    open_positions = 0
    closed_positions = 0
    
    for tx in all_transactions_in_period:
        if tx.status == 'CLOSED':
            closed_positions += 1
            realized = float(tx.realized_pnl or 0)
            total_realized_pnl += realized
            total_pnl += realized
            if realized > 0:
                winning_trades += 1
            elif realized < 0:
                losing_trades += 1
        else:  # OPEN
            open_positions += 1
            unrealized = float(tx.unrealized_pnl or 0)
            total_unrealized_pnl += unrealized
            total_pnl += unrealized
    
    win_rate = (winning_trades / closed_positions * 100) if closed_positions > 0 else 0
    
    # Get daily stats for chart
    daily_stats = db.query(
        func.date(models.Transaction.created_at).label('date'),
        func.count(models.Transaction.id).label('count'),
        func.sum(
            case(
                (models.Transaction.status == 'CLOSED', models.Transaction.realized_pnl),
                else_=models.Transaction.unrealized_pnl
            )
        ).label('pnl')
    ).join(
        models.Subscription,
        models.Subscription.id == models.Transaction.subscription_id
    ).filter(
        models.Subscription.bot_id == bot_id,
        models.Transaction.created_at >= start_date
    ).group_by(
        func.date(models.Transaction.created_at)
    ).order_by(
        func.date(models.Transaction.created_at)
    ).all()
    
    # Format chart data
    chart_data = []
    for stat in daily_stats:
        chart_data.append({
            'date': stat.date.isoformat() if stat.date else None,
            'transactions': stat.count,
            'pnl': float(stat.pnl) if stat.pnl else 0
        })
    
    return {
        'bot_id': bot_id,
        'bot_name': bot.name,
        'period_days': days,
        'exchange_type': bot.exchange_type.value if bot.exchange_type else 'BINANCE',  # Add exchange info
        'summary': {
            'total_subscriptions': total_subscriptions,
            'active_subscriptions': active_subscriptions,
            'total_transactions': total_transactions,
            'open_positions': open_positions,
            'closed_positions': closed_positions,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': round(win_rate, 2),
            'total_pnl': round(total_pnl, 2),
            'realized_pnl': round(total_realized_pnl, 2),
            'unrealized_pnl': round(total_unrealized_pnl, 2)
        },
        'chart_data': chart_data
    }

# --- Bot categories ---
@router.get("/categories/", response_model=List[schemas.BotCategoryInDB])
def get_bot_categories(db: Session = Depends(get_db)):
    """Get all bot categories"""
    return crud.get_bot_categories(db)

@router.post("/categories/", response_model=schemas.BotCategoryInDB)
def create_bot_category(
    category: schemas.BotCategoryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_admin)
):
    """Create a new bot category (admin only)"""
    return crud.create_bot_category(db, category=category)

# --- Developer endpoints ---
@router.post("/", response_model=schemas.BotInDB, status_code=status.HTTP_201_CREATED)
def submit_new_bot(
    bot_in: schemas.BotCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_developer)
):
    """Developer submit a new bot, bot will be in PENDING status"""
    
    # Check plan limits
    plan_checker.check_bot_creation_limit(current_user, db)
    
    # For template bots, just create bot record pointing to local template file
    # create_bot will auto-set code_path based on template field
    # NO S3 upload needed - template files are local
    return crud.create_bot(
        db=db, 
        bot=bot_in, 
        developer_id=current_user.id,
        status=schemas.BotStatus.APPROVED,  # Auto-approve for developers
        approved_by=current_user.id
    )

def parse_timeframes(timeframes: str = Form(...)) -> List[str]:
    return json.loads(timeframes)

@router.post("/with-code", response_model=schemas.BotInDB, status_code=status.HTTP_201_CREATED)
async def submit_new_bot_with_code(
    name: str = Form(...),
    description: str = Form(...),
    category_id: int = Form(...),
    image_url: Optional[str] = Form(None),
    timeframes: List[str] = Depends(parse_timeframes),
    timeframe: Optional[str] = Form(None),
    bot_mode: Optional[schemas.BotMode] = Form(None),
    trading_pair: Optional[str] = Form(None),
    strategy_config: Optional[Any] = Form(None),
    exchange_type: Optional[schemas.ExchangeType] = Form(None),
    price_per_month: float = Form(0.0),
    is_free: bool = Form(True),
    bot_type: str = Form("TECHNICAL"),
    config_schema: str = Form("{}"),
    default_config: str = Form("{}"),
    file: UploadFile = File(...),
    file_rpa_robot: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_developer)
):
    """Developer submit a new bot with code file"""
    try:
        # Check plan limits FIRST before any processing
        plan_checker.check_bot_creation_limit(current_user, db)
        
        logger.info(f"[SUBMIT BOT] Start submission with data ")
        # Validate file type
        if not file.filename or not file.filename.endswith('.py'):
            raise HTTPException(status_code=400, detail="Only Python files are allowed")
        
        # Read file content
        content = await file.read()
        code_content = content.decode('utf-8')
        code_content_rpa_robot = None
        file_rpa_robot_name = None
        if file_rpa_robot:
            content_rpa_robot = await file_rpa_robot.read()
            code_content_rpa_robot = content_rpa_robot.decode('utf-8')
            file_rpa_robot_name = file_rpa_robot.filename
            logger.info(f"[SUBMIT BOT] File rpa robot: {file_rpa_robot.filename}, size={len(await file_rpa_robot.read())} bytes")

        logger.info(f"[SUBMIT BOT] File read successfully: {file.filename}, size={len(content)} bytes")
        
        # Validate bot code
        validation_result = bot_manager.validate_bot_code(code_content)
        logger.info(f"[SUBMIT BOT] Bot code validation result: {validation_result}")    
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Bot code validation failed: {validation_result['error']}"
            )
        logger.info(f"[SUBMIT BOT] Bot code validation passed")
        # Parse bot type
        try:
            bot_type_enum = schemas.BotType(bot_type)
        except ValueError:
            bot_type_enum = schemas.BotType.TECHNICAL

        logger.info(f"[SUBMIT BOT] Bot code validated successfully for user_id={current_user.id}, filename={file.filename}")
        
        # Create bot data
        bot_data = schemas.BotCreate(
            name=name,
            description=description,
            category_id=category_id,
            price_per_month=Decimal(str(price_per_month)),
            is_free=is_free,
            bot_type=bot_type_enum,
            config_schema=json.loads(config_schema),
            default_config=json.loads(default_config),
            image_url=image_url or "",
            timeframes=timeframes or [],
            timeframe=timeframe or None,
            bot_mode=bot_mode or None,
            exchange_type=exchange_type or None,
            trading_pair=trading_pair or None,
            strategy_config=json.loads(strategy_config) if strategy_config else None
        )

        logger.info(f"[SUBMIT BOT] Bot data created successfully for bot_data={bot_data}")

        # Create bot with S3 upload
        bot_record = crud.save_bot_with_s3(
            db=db,
            bot_data=bot_data,
            developer_id=current_user.id,
            file_content=code_content,
            file_name=file.filename,
            file_content_rpa_robot=code_content_rpa_robot,
            file_name_rpa_robot=file_rpa_robot_name
        )

        logger.info(f"[SUBMIT BOT] upload s3 {file.filename}")

        return bot_record
        
    except json.JSONDecodeError:
        import traceback
        logger.error(f"ERROR: {traceback.format_exc()}")
        raise HTTPException(status_code=400, detail="Invalid JSON in config fields")
    except Exception as e:
        import traceback
        logger.error(f"ERROR: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to create bot: {str(e)}")

@router.get("/me/bots", response_model=List[schemas.BotInDB])
def get_my_bots(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_developer)
):
    """Developer get list of their own bots"""
    return crud.get_bots_by_developer(db=db, developer_id=current_user.id)

@router.put("/{bot_id}", response_model=schemas.BotInDB)
def update_my_bot(
    bot_id: int,
    bot_in: schemas.BotUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_developer)
):
    """Developer update their own bot"""
    db_bot = crud.get_bot_by_id(db, bot_id)
    if not db_bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    if db_bot.developer_id != current_user.id and current_user.role != schemas.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return crud.update_bot(db=db, bot_id=bot_id, bot_update=bot_in)

@router.delete("/{bot_id}", response_model=schemas.BotInDB)
def archive_my_bot(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_developer)
):
    """Developer archive their own bot"""
    db_bot = crud.get_bot_by_id(db, bot_id)
    if not db_bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    if db_bot.developer_id != current_user.id and current_user.role != schemas.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return crud.update_bot_status(db=db, bot_id=bot_id, status=schemas.BotStatus.ARCHIVED)

@router.post("/{bot_id}/upload", response_model=schemas.BotInDB)
async def upload_bot_code(
    bot_id: int,
    file: UploadFile = File(...),
    version: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_developer)
):
    """Upload bot code file to S3"""
    try:
        logger.debug(f"[UPLOAD] Start upload for bot_id={bot_id}, user_id={current_user.id}, filename={file.filename}")
        db_bot = crud.get_bot_by_id(db, bot_id)
        if not db_bot:
            logger.error(f"[UPLOAD] Bot not found: bot_id={bot_id}")
            raise HTTPException(status_code=404, detail="Bot not found")
        if db_bot.developer_id != current_user.id and current_user.role != schemas.UserRole.ADMIN:
            logger.error(f"[UPLOAD] Permission denied: bot_id={bot_id}, user_id={current_user.id}, dev_id={db_bot.developer_id}, role={current_user.role}")
            raise HTTPException(status_code=403, detail="Not enough permissions")

        # Validate file type
        if not file.filename or not file.filename.endswith('.py'):
            logger.error(f"[UPLOAD] Invalid file type: {file.filename}")
            raise HTTPException(status_code=400, detail="Only Python files are allowed")

        # Read file content
        try:
            content = await file.read()
            code_content = content.decode('utf-8')
        except UnicodeDecodeError as ude:
            logger.error(f"[UPLOAD] Unicode decode error: {ude}")
            raise HTTPException(status_code=400, detail="File must be valid UTF-8 text")

        logger.debug(f"[UPLOAD] File read successfully: {file.filename}, size={len(content)} bytes")

        # Validate bot code
        validation_result = bot_manager.validate_bot_code(code_content)
        if not validation_result["valid"]:
            logger.error(f"[UPLOAD] Bot code validation failed: {validation_result['error']}")
            raise HTTPException(
                status_code=400, 
                detail=f"Bot code validation failed: {validation_result['error']}"
            )

        logger.debug(f"[UPLOAD] Bot code validated successfully for bot_id={bot_id}")

        # Upload to S3
        try:
            upload_result = crud.save_bot_file_to_s3(
                db=db,
                bot_id=bot_id,
                file_content=content,
                file_name=file.filename,
                version=version or None
            )
            logger.debug(f"[UPLOAD] S3 upload result: {upload_result}")
        except Exception as s3e:
            logger.error(f"[UPLOAD] S3 upload failed: {s3e}")
            raise HTTPException(status_code=500, detail=f"S3 upload failed: {str(s3e)}")

        # Update bot status back to PENDING for review
        try:
            crud.update_bot_status(db=db, bot_id=bot_id, status=schemas.BotStatus.PENDING)
            logger.debug(f"[UPLOAD] Bot status updated to PENDING for bot_id={bot_id}")
        except Exception as stse:
            logger.error(f"[UPLOAD] Failed to update bot status: {stse}")

        # Get updated bot
        updated_bot = crud.get_bot_by_id(db, bot_id)
        logger.info(f"[UPLOAD] Bot upload completed successfully for bot_id={bot_id}, user_id={current_user.id}")
        return updated_bot

    except HTTPException as he:
        logger.error(f"[UPLOAD] HTTPException: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"[UPLOAD] Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to upload bot code: {str(e)}")

@router.get("/{bot_id}/versions", response_model=List[str])
def get_bot_versions(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_developer)
):
    """Get all versions of a bot from S3"""
    try:
        db_bot = crud.get_bot_by_id(db, bot_id)
        if not db_bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        if db_bot.developer_id != current_user.id and current_user.role != schemas.UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        
        # Return current version as fallback
        return [db_bot.version] if db_bot.version else ["1.0.0"]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get bot versions: {str(e)}")

@router.get("/{bot_id}/download/{version}")
def download_bot_code(
    bot_id: int,
    version: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_developer)
):
    """Download bot code from S3"""
    try:
        db_bot = crud.get_bot_by_id(db, bot_id)
        if not db_bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        if db_bot.developer_id != current_user.id and current_user.role != schemas.UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        
        code_content = s3_manager.download_bot_code(bot_id, version)
        
        return {
            "bot_id": bot_id,
            "version": version,
            "code_content": code_content,
            "download_time": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download bot code: {str(e)}")

@router.post("/{bot_id}/test")
def test_bot_code(
    bot_id: int,
    test_data: dict = {"symbol": "BTCUSDT", "amount": 100},
    version: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_developer)
):
    """Test bot code from S3"""
    try:
        db_bot = crud.get_bot_by_id(db, bot_id)
        if not db_bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        if db_bot.developer_id != current_user.id and current_user.role != schemas.UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        
        # Load bot from S3
        bot_instance = crud.load_bot_from_s3(
            bot_id=bot_id,
            version=version,
            user_config=test_data,
            user_api_keys={
                'key': current_user.api_key,
                'secret': current_user.api_secret
            }
        )
        
        if not bot_instance:
            raise HTTPException(status_code=400, detail="Failed to load bot from S3")
        
        # Test bot
        test_result = bot_manager.test_bot(bot_id, test_data)
        
        return {
            "bot_id": bot_id,
            "version": version or "latest",
            "test_result": test_result,
            "test_time": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test bot: {str(e)}")

# --- User endpoints ---
@router.post("/{bot_id}/reviews", response_model=schemas.BotReviewInDB)
def create_bot_review(
    bot_id: int,
    review: schemas.BotReviewCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Create a review for a bot"""
    # Check if bot exists and is approved
    bot = crud.get_bot_by_id(db, bot_id)
    if not bot or bot.status != schemas.BotStatus.APPROVED:
        raise HTTPException(status_code=404, detail="Bot not found or not approved")
    
    # Check if user has already reviewed this bot
    existing_review = crud.get_user_bot_review(db, user_id=current_user.id, bot_id=bot_id)
    if existing_review:
        raise HTTPException(status_code=400, detail="You have already reviewed this bot")
    
    # Check if user has subscribed to this bot
    has_subscription = crud.user_has_bot_subscription(db, user_id=current_user.id, bot_id=bot_id)
    if not has_subscription:
        raise HTTPException(status_code=400, detail="You must subscribe to this bot before reviewing")
    
    return crud.create_bot_review(db, review=review, user_id=current_user.id, bot_id=bot_id)

@router.put("/{bot_id}/reviews/{review_id}", response_model=schemas.BotReviewInDB)
def update_bot_review(
    bot_id: int,
    review_id: int,
    review_update: schemas.BotReviewBase,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Update a bot review"""
    review = crud.get_bot_review(db, review_id=review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return crud.update_bot_review(db, review_id=review_id, review_update=review_update)

@router.delete("/{bot_id}/reviews/{review_id}")
def delete_bot_review(
    bot_id: int,
    review_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Delete a bot review"""
    review = crud.get_bot_review(db, review_id=review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.user_id != current_user.id and current_user.role != schemas.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    crud.delete_bot_review(db, review_id=review_id)
    return {"message": "Review deleted successfully"}

# --- Marketplace Bot Registration Endpoints ---
@router.post("/register", response_model=schemas.BotMarketplaceRegistrationResponse, status_code=status.HTTP_201_CREATED)
def register_bot_for_marketplace(
    registration: schemas.BotMarketplaceRegistrationRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(security.validate_marketplace_api_key)  # Just validate API key, no user object
):
    """
    Register a bot for marketplace listing using hardcoded API key.
    This endpoint allows marketplace to register bots with auto-generated API keys.
    """
    try:
        # Create marketplace registration (auto-approved)
        registration_record = crud.create_bot_marketplace_registration(
            db=db,
            registration=registration
        )
        
        # Prepare response with generated API key
        response = schemas.BotMarketplaceRegistrationResponse(
            registration_id=registration_record.id,
            user_principal_id=registration.user_principal_id,
            bot_id=registration.bot_id,
            api_key=registration_record.api_key,
            status="approved",
            message="Bot registered successfully for marketplace with auto-generated API key",
            registration_details={
                "marketplace_name": registration_record.marketplace_name,
                "marketplace_description": registration_record.marketplace_description,
                "price_on_marketplace": str(registration_record.price_on_marketplace),
                "commission_rate": registration_record.commission_rate,
                "registered_at": registration_record.registered_at.isoformat(),
                "status": registration_record.status.value,
                "api_key": registration_record.api_key
            }
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register bot for marketplace: {str(e)}"
        )

@router.get("/marketplace", response_model=List[schemas.BotMarketplaceRegistrationInDB])
def get_marketplace_bots_list(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get approved bots available on marketplace"""
    return crud.get_marketplace_bots(db, skip=skip, limit=limit)

@router.get("/analytics/overview", response_model=dict)
def get_developer_analytics_overview(
    days: int = 30,
    network_filter: Optional[str] = Query(None, description="Filter by network: 'mainnet' or 'testnet'"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_developer)
):
    """Get analytics overview for all developer's bots"""
    try:
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        # Get all developer's bots
        bots = db.query(models.Bot).filter(
            models.Bot.developer_id == current_user.id
        ).all()
        
        if not bots:
            return {
                'total_bots': 0,
                'total_subscriptions': 0,
                'active_subscriptions': 0,
                'total_transactions': 0,
                'total_pnl': 0.0,
                'win_rate': 0.0,
                'top_bots': []
            }
        
        bot_ids = [bot.id for bot in bots]
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get subscription stats (apply network filter)
        total_sub_query = db.query(func.count(models.Subscription.id)).filter(
            models.Subscription.bot_id.in_(bot_ids)
        )
        if network_filter == "mainnet":
            total_sub_query = total_sub_query.filter(models.Subscription.is_testnet == False)
        elif network_filter == "testnet":
            total_sub_query = total_sub_query.filter(models.Subscription.is_testnet == True)
        total_subscriptions = total_sub_query.scalar() or 0
        
        active_sub_query = db.query(func.count(models.Subscription.id)).filter(
            models.Subscription.bot_id.in_(bot_ids),
            models.Subscription.status == models.SubscriptionStatus.ACTIVE
        )
        if network_filter == "mainnet":
            active_sub_query = active_sub_query.filter(models.Subscription.is_testnet == False)
        elif network_filter == "testnet":
            active_sub_query = active_sub_query.filter(models.Subscription.is_testnet == True)
        active_subscriptions = active_sub_query.scalar() or 0
        
        # Get transaction stats (apply network filter)
        tx_query = db.query(models.Transaction).join(
            models.Subscription,
            models.Subscription.id == models.Transaction.subscription_id
        ).filter(
            models.Subscription.bot_id.in_(bot_ids),
            models.Transaction.created_at >= start_date
        )
        if network_filter == "mainnet":
            tx_query = tx_query.filter(models.Subscription.is_testnet == False)
        elif network_filter == "testnet":
            tx_query = tx_query.filter(models.Subscription.is_testnet == True)
        transactions = tx_query.all()
        
        total_transactions = len(transactions)
        total_pnl = sum(float(tx.realized_pnl or 0) for tx in transactions)
        winning_trades = len([tx for tx in transactions if float(tx.realized_pnl or 0) > 0])
        win_rate = (winning_trades / total_transactions * 100) if total_transactions > 0 else 0
        
        # Get top performing bots (apply network filter)
        top_bots = []
        for bot in bots[:5]:  # Top 5 bots
            bot_sub_query = db.query(func.count(models.Subscription.id)).filter(
                models.Subscription.bot_id == bot.id,
                models.Subscription.status == models.SubscriptionStatus.ACTIVE
            )
            if network_filter == "mainnet":
                bot_sub_query = bot_sub_query.filter(models.Subscription.is_testnet == False)
            elif network_filter == "testnet":
                bot_sub_query = bot_sub_query.filter(models.Subscription.is_testnet == True)
            bot_subs = bot_sub_query.scalar() or 0
            
            bot_tx_query = db.query(models.Transaction).join(
                models.Subscription,
                models.Subscription.id == models.Transaction.subscription_id
            ).filter(
                models.Subscription.bot_id == bot.id,
                models.Transaction.created_at >= start_date
            )
            if network_filter == "mainnet":
                bot_tx_query = bot_tx_query.filter(models.Subscription.is_testnet == False)
            elif network_filter == "testnet":
                bot_tx_query = bot_tx_query.filter(models.Subscription.is_testnet == True)
            bot_txs = bot_tx_query.all()
            
            bot_pnl = sum(float(tx.realized_pnl or 0) for tx in bot_txs)
            bot_trades = len(bot_txs)
            bot_wins = len([tx for tx in bot_txs if float(tx.realized_pnl or 0) > 0])
            bot_win_rate = (bot_wins / bot_trades * 100) if bot_trades > 0 else 0
            
            top_bots.append({
                'id': bot.id,
                'name': bot.name,
                'active_subscriptions': bot_subs,
                'total_trades': bot_trades,
                'pnl': round(bot_pnl, 2),
                'win_rate': round(bot_win_rate, 2)
            })
        
        # Sort by PnL
        top_bots.sort(key=lambda x: x['pnl'], reverse=True)
        
        return {
            'total_bots': len(bots),
            'total_subscriptions': total_subscriptions,
            'active_subscriptions': active_subscriptions,
            'total_transactions': total_transactions,
            'total_pnl': round(total_pnl, 2),
            'win_rate': round(win_rate, 2),
            'top_bots': top_bots[:5]
        }
    except Exception as e:
        logger.error(f"Failed to get developer analytics: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{bot_id}/analytics", response_model=dict)
def get_bot_analytics(
    bot_id: int,
    days: int = 30,
    page: int = 1,
    limit: int = 10,
    network_filter: Optional[str] = Query(None, description="Filter by network: 'mainnet' or 'testnet'"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Get bot analytics including transactions, subscribers, and performance metrics with pagination"""
    # Allow all authenticated users to view analytics, not just the bot owner
    return crud.get_bot_analytics(db, bot_id=bot_id, developer_id=None, days=days, page=page, limit=limit, network_filter=network_filter)

@router.get("/{bot_id}/subscriptions", response_model=dict)
def get_bot_subscriptions(
    bot_id: int,
    page: int = 1,
    limit: int = 20,
    principal_id: Optional[str] = None,
    user_id: Optional[int] = None,
    trading_pair: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """
    Get all subscriptions for a bot with advanced filtering and search
    
    Filters:
    - principal_id: Filter by user principal ID
    - user_id: Filter by developer user ID
    - trading_pair: Filter by trading pair (e.g., BTC/USDT)
    - status: Filter by subscription status (ACTIVE, PAUSED, CANCELLED, EXPIRED)
    - start_date: Filter by subscription start date (YYYY-MM-DD)
    - end_date: Filter by subscription end date (YYYY-MM-DD)
    - search: Search in principal_id, instance_name, or trading_pair
    """
    # Allow all authenticated users to view subscriptions, not just the bot owner
    return crud.get_bot_subscriptions(
        db=db,
        bot_id=bot_id,
        developer_id=None,
        page=page,
        limit=limit,
        principal_id=principal_id,
        user_id=user_id,
        trading_pair=trading_pair,
        status=status,
        start_date=start_date,
        end_date=end_date,
        search=search
    )

@router.get("/validate-bot-key/{api_key}", response_model=schemas.BotMarketplaceRegistrationInDB)
def validate_bot_api_key(
    api_key: str,
    db: Session = Depends(get_db)
):
    """Validate bot API key and return registration info"""
    registration = crud.get_bot_registration_by_api_key(db, api_key)
    
    if not registration:
        raise HTTPException(status_code=404, detail="Invalid or inactive bot API key")
    
    return registration

@router.put("/update-registration/{subscription_id}", response_model=schemas.BotRegistrationUpdateResponse)
def update_bot_registration(
    subscription_id: int,
    update_data: schemas.BotRegistrationUpdate,
    db: Session = Depends(get_db),
    marketplace_user: models.User = Depends(security.get_marketplace_user)
):
    """
    Update an existing bot registration for marketplace user.
    Allows updating timeframes, trade_evaluation_period, starttime, endtime, 
    exchange_name, network_type, and trade_mode.
    """
    try:
        # Update bot registration
        subscription, updated_fields = crud.update_bot_registration(
            db=db,
            subscription_id=subscription_id,
            update_data=update_data,
            marketplace_user_id=marketplace_user.id
        )
        
        # Prepare response
        response = schemas.BotRegistrationUpdateResponse(
            subscription_id=subscription.id,
            user_principal_id=subscription.user_principal_id,
            status="success",
            message=f"Bot registration updated successfully. Updated fields: {', '.join(updated_fields)}",
            updated_fields=updated_fields
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update bot registration: {str(e)}"
        )

@router.get("/registrations/{user_principal_id}", response_model=List[schemas.SubscriptionInDB])
def get_bot_registrations_by_principal_id(
    user_principal_id: str,
    bot_id: Optional[int] = None,
    db: Session = Depends(get_db),
    marketplace_user: models.User = Depends(security.get_marketplace_user)
):
    """
    Get bot registrations by user principal ID.
    Optionally filter by bot_id.
    """
    try:
        subscriptions = crud.get_bot_registration_by_principal_id(
            db=db,
            user_principal_id=user_principal_id,
            bot_id=bot_id
        )
        
        return subscriptions
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get bot registrations: {str(e)}"
        )

@router.get("/marketplace/test-credentials")
async def test_retrieve_credentials(
    principal_id: str,
    exchange: str = "BINANCE",
    is_testnet: bool = True,
    db: Session = Depends(get_db),
    api_key: str = Depends(security.validate_marketplace_api_key)
):
    """
    Test endpoint to retrieve and verify credentials by principal ID
    """
    try:
        credentials = api_key_manager.get_user_credentials_by_principal_id(
            db=db,
            user_principal_id=principal_id,
            exchange=exchange,
            is_testnet=is_testnet
        )
        
        if credentials:
            return {
                "status": "success",
                "principal_id": principal_id,
                "exchange": exchange,
                "is_testnet": is_testnet,
                "api_key_found": bool(credentials.get('api_key')),
                "api_secret_found": bool(credentials.get('api_secret')),
                "api_key_preview": credentials['api_key'][:20] + "..." if credentials.get('api_key') else None
            }
        else:
            return {
                "status": "not_found",
                "principal_id": principal_id,
                "exchange": exchange,
                "is_testnet": is_testnet
            }
            
    except Exception as e:
        logger.error(f"Failed to test credentials: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test credentials: {str(e)}"
        )


@router.post("/upload-image", response_model=dict)
async def upload_bot_image(
    file: UploadFile = File(...),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """
    Upload bot image to GCS
    Returns the public URL of the uploaded image
    """
    try:
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/webp"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail="Only JPEG, PNG, WebP formats are supported"
            )
        
        # Validate file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        file_content = await file.read()
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=400,
                detail="File size cannot exceed 5MB"
            )
        
        # Initialize GCS client
        GCS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME', 'cryptomancer_ai')
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        if not credentials_path:
            raise HTTPException(
                status_code=500,
                detail="GCS credentials not configured"
            )
        
        client = storage.Client.from_service_account_json(credentials_path)
        storage_client = client.bucket(GCS_BUCKET_NAME)
        
        # Process image
        image = Image.open(BytesIO(file_content))
        
        # Resize if too large (max width 1024px)
        max_width = 1024
        if image.width > max_width:
            ratio = max_width / float(image.width)
            new_height = int(image.height * ratio)
            image = image.resize((max_width, new_height), Image.LANCZOS)
        
        # Convert to JPEG and optimize
        output_buffer = BytesIO()
        image = image.convert("RGB")
        image.save(output_buffer, format="JPEG", quality=95, optimize=True)
        output_buffer.seek(0)
        
        # Generate unique filename
        file_extension = "jpg"
        file_name = f"uploads/bot-images/{uuid.uuid4()}.{file_extension}"
        
        # Upload to GCS
        blob = storage_client.blob(file_name)
        blob.upload_from_file(output_buffer, content_type="image/jpeg")
        
        # Generate public URL
        GCS_PUBLIC_URL = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}"
        public_url = f"{GCS_PUBLIC_URL}/{file_name}"
        
        logger.info(f"Bot image uploaded successfully: {public_url}")
        
        return {
            "success": True,
            "url": public_url,
            "filename": file_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload bot image: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload image: {str(e)}"
        )
