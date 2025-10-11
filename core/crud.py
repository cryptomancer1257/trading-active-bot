# file: crud.py

import sys
import os
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, asc, and_, or_
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
import hashlib
import json
import logging
from fastapi import HTTPException

# Initialize logger
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import models, schemas, security

# Lazy initialization - only create when needed
_s3_manager = None
_bot_manager = None

def get_s3_manager():
    """Get S3Manager instance (lazy initialization)"""
    global _s3_manager
    if _s3_manager is None:
        try:
            from services.s3_manager import S3Manager
            _s3_manager = S3Manager()
        except Exception as e:
            print(f"Warning: Could not initialize S3Manager: {e}")
            _s3_manager = None
    return _s3_manager

def get_bot_manager():
    """Get BotManager instance (lazy initialization)"""
    global _bot_manager
    if _bot_manager is None:
        try:
            from core.bot_manager import BotManager
            _bot_manager = BotManager()
        except Exception as e:
            print(f"Warning: Could not initialize BotManager: {e}")
            _bot_manager = None
    return _bot_manager

# --- User CRUD ---
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_api_key(db: Session, api_key: str):
    """Get user by API key for marketplace authentication"""
    return db.query(models.User).filter(models.User.api_key == api_key).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        role=user.role,
        developer_name=user.developer_name,
        developer_bio=user.developer_bio,
        developer_website=user.developer_website
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate):
    db_user = get_user(db, user_id)
    if db_user:
        update_data = user_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)
    return db_user

def get_user_profile(db: Session, user_id: int):
    user = get_user(db, user_id)
    if not user:
        return None
    
    # Get subscription counts (simplified to avoid enum issues)
    total_subscriptions = 0
    active_subscriptions = 0
    try:
        total_subscriptions = db.query(models.Subscription).filter(
            models.Subscription.user_id == user_id
        ).count()
        
        # Use string comparison for status to avoid enum issues
        active_subscriptions = db.query(models.Subscription).filter(
            models.Subscription.user_id == user_id,
            models.Subscription.status == "ACTIVE"
        ).count()
    except Exception:
        # If subscription table doesn't exist or has issues, use defaults
        pass
    
    # Get bot development stats
    total_developed_bots = 0
    approved_bots = 0
    try:
        total_developed_bots = db.query(models.Bot).filter(
            models.Bot.developer_id == user_id
        ).count()
        
        approved_bots = db.query(models.Bot).filter(
            models.Bot.developer_id == user_id,
            models.Bot.status == "APPROVED"
        ).count()
    except Exception:
        # If bot table doesn't exist or has issues, use defaults
        pass
    
    # Create profile response
    profile = schemas.UserProfile(
        id=user.id,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        developer_name=user.developer_name,
        developer_bio=user.developer_bio,
        developer_website=user.developer_website,
        created_at=user.created_at,
        updated_at=user.updated_at,
        total_subscriptions=total_subscriptions,
        active_subscriptions=active_subscriptions,
        total_developed_bots=total_developed_bots,
        approved_bots=approved_bots
    )
    
    return profile

def update_user_status(db: Session, user_id: int, user_update: schemas.AdminUserUpdate):
    db_user = get_user(db, user_id)
    if db_user:
        db_user.is_active = user_update.is_active
        if user_update.role:
            db_user.role = user_update.role
        db.commit()
        db.refresh(db_user)
    return db_user

def get_all_users(db: Session, skip: int = 0, limit: int = 100, role_filter: Optional[schemas.UserRole] = None, active_only: bool = False):
    query = db.query(models.User)
    
    if role_filter:
        query = query.filter(models.User.role == role_filter)
    
    if active_only:
        query = query.filter(models.User.is_active == True)
    
    return query.offset(skip).limit(limit).all()

def update_user_by_admin(db: Session, user_id: int, user_update: schemas.AdminUserUpdate):
    return update_user_status(db, user_id, user_update)

def delete_user(db: Session, user_id: int):
    user = get_user(db, user_id)
    if user:
        db.delete(user)
        db.commit()
    return True

# --- Bot Category CRUD ---
def get_bot_categories(db: Session):
    return db.query(models.BotCategory).all()

def create_bot_category(db: Session, category: schemas.BotCategoryCreate):
    db_category = models.BotCategory(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

# --- Bot CRUD ---
def create_bot(db: Session, bot: schemas.BotCreate, developer_id: int, status: schemas.BotStatus = schemas.BotStatus.PENDING, approved_by: Optional[int] = None):
    # Only include fields that exist in the Bot database model
    bot_dict = bot.dict()
    valid_fields = {
        'name', 'description', 'category_id', 'version', 'bot_type', 'price_per_month', 
        'is_free', 'config_schema', 'default_config', 'model_metadata', 'timeframes', 
        'timeframe', 'bot_mode', 'trading_pair', 'trading_pairs', 'exchange_type', 'strategy_config', 
        'image_url', 'code_path', 'code_path_rpa', 'version_rpa', 
        'risk_config', 'risk_management_mode'  # Risk management fields
    }
    filtered_bot_dict = {k: v for k, v in bot_dict.items() if k in valid_fields and v is not None}
    
    # Handle LLM configuration - merge into strategy_config
    llm_fields = ['llm_provider', 'llm_model', 'enable_image_analysis', 'enable_sentiment_analysis']
    llm_config = {}
    
    for field in llm_fields:
        if field in bot_dict and bot_dict[field] is not None:
            llm_config[field] = bot_dict[field]
    
    # Merge LLM config into strategy_config
    if llm_config:
        if 'strategy_config' not in filtered_bot_dict or filtered_bot_dict['strategy_config'] is None:
            filtered_bot_dict['strategy_config'] = {}
        filtered_bot_dict['strategy_config'].update(llm_config)
        logger.info(f"Creating bot with LLM config: {llm_config}")
    
    # 🛡️ Handle Risk Management Configuration - Map to risk_config
    risk_fields = ['leverage', 'risk_percentage', 'stop_loss_percentage', 'take_profit_percentage']
    risk_config = {}
    
    for field in risk_fields:
        if field in bot_dict and bot_dict[field] is not None:
            # Map frontend fields to risk_config fields
            if field == 'leverage':
                risk_config['max_leverage'] = bot_dict[field]
            elif field == 'risk_percentage':
                risk_config['risk_per_trade_percent'] = bot_dict[field]
                risk_config['max_position_size'] = bot_dict[field]  # Use same value for max position
            elif field == 'stop_loss_percentage':
                risk_config['stop_loss_percent'] = bot_dict[field]
            elif field == 'take_profit_percentage':
                risk_config['take_profit_percent'] = bot_dict[field]
    
    # Save risk_config to bot if any risk fields were provided
    if risk_config:
        # Add default mode
        risk_config['mode'] = 'DEFAULT'
        filtered_bot_dict['risk_config'] = risk_config
        filtered_bot_dict['risk_management_mode'] = 'DEFAULT'
        logger.info(f"✅ Creating bot with Risk Config: {risk_config}")
    
    # 🎯 AUTO-SET CODE_PATH for template bots (local files)
    template = bot_dict.get('template') or bot_dict.get('templateFile')
    if template:
        # Map template name to local file path
        TEMPLATE_FILE_MAPPING = {
            'universal_futures_bot': 'bot_files/universal_futures_bot.py',
            'universal_futures_bot.py': 'bot_files/universal_futures_bot.py',
            'universal_spot_bot': 'bot_files/universal_spot_bot.py',
            'universal_spot_bot.py': 'bot_files/universal_spot_bot.py',
            'binance_futures_bot': 'bot_files/binance_futures_bot.py',
            'binance_futures_bot.py': 'bot_files/binance_futures_bot.py',
            'binance_futures_rpa_bot': 'bot_files/binance_futures_rpa_bot.py',
            'binance_futures_rpa_bot.py': 'bot_files/binance_futures_rpa_bot.py',
            'binance_signals_bot': 'bot_files/binance_signals_bot.py',
            'binance_signals_bot.py': 'bot_files/binance_signals_bot.py',
        }
        
        code_path = TEMPLATE_FILE_MAPPING.get(template)
        if code_path:
            filtered_bot_dict['code_path'] = code_path
            logger.info(f"✅ Auto-set code_path for template '{template}' → {code_path}")
    
    db_bot = models.Bot(
        **filtered_bot_dict,
        developer_id=developer_id,
        status=status,
        approved_by=approved_by,
        approved_at=datetime.utcnow() if status == schemas.BotStatus.APPROVED else None
    )
    db.add(db_bot)
    db.commit()
    db.refresh(db_bot)
    return db_bot

def get_bot_by_id(db: Session, bot_id: int):
    return db.query(models.Bot).filter(models.Bot.id == bot_id).first()

def get_bot_with_developer(db: Session, bot_id: int):
    return db.query(models.Bot).join(models.User, models.Bot.developer_id == models.User.id).filter(models.Bot.id == bot_id).first()

def get_approved_bots(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Bot).filter(
        models.Bot.status == models.BotStatus.APPROVED
    ).offset(skip).limit(limit).all()

def get_public_bots(db: Session, skip: int = 0, limit: int = 50, category_id: Optional[int] = None, search: Optional[str] = None, sort_by: str = "created_at", order: str = "desc"):
    query = db.query(models.Bot).filter(models.Bot.status == schemas.BotStatus.APPROVED)
    
    if category_id:
        query = query.filter(models.Bot.category_id == category_id)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                models.Bot.name.ilike(search_term),
                models.Bot.description.ilike(search_term)
            )
        )
    
    # Apply sorting
    if sort_by == "created_at":
        query = query.order_by(desc(models.Bot.created_at) if order == "desc" else asc(models.Bot.created_at))
    elif sort_by == "rating":
        query = query.order_by(desc(models.Bot.average_rating) if order == "desc" else asc(models.Bot.average_rating))
    elif sort_by == "price":
        query = query.order_by(desc(models.Bot.price_per_month) if order == "desc" else asc(models.Bot.price_per_month))
    
    total = query.count()
    bots = query.offset(skip).limit(limit).all()
    
    return bots, total

def get_bots_by_developer(db: Session, developer_id: int):
    """Get all bots by developer with real-time counts"""
    from sqlalchemy import func
    
    # Get bots
    bots = db.query(models.Bot).filter(models.Bot.developer_id == developer_id).all()
    
    # Add real-time counts for each bot
    for bot in bots:
        # Count active subscribers
        bot.subscribers_count = db.query(func.count(models.Subscription.id)).filter(
            models.Subscription.bot_id == bot.id
        ).scalar() or 0
        
        # Count total transactions for this bot's subscriptions
        bot.transactions_count = db.query(func.count(models.Transaction.id)).join(
            models.Subscription,
            models.Subscription.id == models.Transaction.subscription_id
        ).filter(
            models.Subscription.bot_id == bot.id
        ).scalar() or 0
    
    return bots

def get_bot_analytics(db: Session, bot_id: int, developer_id: int, days: int = 30, page: int = 1, limit: int = 10):
    """Get comprehensive analytics for a bot with paginated recent transactions"""
    from sqlalchemy import func, and_, case
    from datetime import datetime, timedelta
    
    # Verify bot belongs to developer
    bot = db.query(models.Bot).filter(
        models.Bot.id == bot_id,
        models.Bot.developer_id == developer_id
    ).first()
    
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
    
    # Calculate P&L (realized + unrealized) and win rate
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
            total_pnl += unrealized  # Include unrealized in total P&L
    
    # Win rate only from CLOSED trades (can't determine if OPEN will win/lose)
    win_rate = (winning_trades / closed_positions * 100) if closed_positions > 0 else 0
    
    # Get transactions grouped by date for chart (ALL transactions - OPEN + CLOSED)
    # Use CASE statement to sum realized_pnl for CLOSED and unrealized_pnl for OPEN
    daily_stats = db.query(
        func.date(models.Transaction.created_at).label('date'),
        func.count(models.Transaction.id).label('count'),
        func.sum(
            case(
                (models.Transaction.status == 'CLOSED', models.Transaction.realized_pnl),
                else_=models.Transaction.unrealized_pnl
            )
        ).label('pnl'),
        func.sum(
            case(
                (models.Transaction.status == 'CLOSED', models.Transaction.realized_pnl),
                else_=0
            )
        ).label('realized_pnl'),
        func.sum(
            case(
                (models.Transaction.status == 'OPEN', models.Transaction.unrealized_pnl),
                else_=0
            )
        ).label('unrealized_pnl')
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
    
    # Format daily stats for chart
    chart_data = []
    for stat in daily_stats:
        chart_data.append({
            'date': stat.date.isoformat() if stat.date else None,
            'transactions': stat.count,
            'pnl': float(stat.pnl) if stat.pnl else 0,
            'realized_pnl': float(stat.realized_pnl) if stat.realized_pnl else 0,
            'unrealized_pnl': float(stat.unrealized_pnl) if stat.unrealized_pnl else 0
        })
    
    # Get total count of transactions for pagination
    total_transactions_count = db.query(func.count(models.Transaction.id)).join(
        models.Subscription,
        models.Subscription.id == models.Transaction.subscription_id
    ).filter(
        models.Subscription.bot_id == bot_id
    ).scalar() or 0
    
    # Calculate pagination offset
    offset = (page - 1) * limit
    
    # Get recent transactions with pagination (show both OPEN and CLOSED)
    recent_transactions = db.query(
        models.Transaction
    ).join(
        models.Subscription,
        models.Subscription.id == models.Transaction.subscription_id
    ).filter(
        models.Subscription.bot_id == bot_id
    ).order_by(
        models.Transaction.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    # Format recent transactions (include both OPEN and CLOSED)
    recent_txs = []
    for tx in recent_transactions:
        # Determine P&L based on status
        if tx.status == 'CLOSED':
            pnl = float(tx.realized_pnl) if tx.realized_pnl is not None else 0
        else:  # OPEN
            pnl = float(tx.unrealized_pnl) if tx.unrealized_pnl is not None else 0
            
        recent_txs.append({
            'id': tx.id,
            'subscription_id': tx.subscription_id,  # NEW: Include subscription ID
            'trading_pair': tx.symbol,  # Transaction model uses 'symbol' field
            'action': tx.action,
            'quantity': float(tx.quantity) if tx.quantity else 0,
            'entry_price': float(tx.entry_price) if tx.entry_price else 0,
            'exit_price': float(tx.exit_price) if tx.exit_price else 0,
            'realized_pnl': pnl,  # Use realized_pnl for CLOSED, unrealized_pnl for OPEN
            'status': tx.status,  # NEW: Include status (OPEN/CLOSED)
            'unrealized_pnl': float(tx.unrealized_pnl) if tx.unrealized_pnl is not None else 0,  # NEW
            'last_updated_price': float(tx.last_updated_price) if tx.last_updated_price else 0,  # NEW
            'created_at': tx.created_at.isoformat() if tx.created_at else None,
            'closed_at': tx.exit_time.isoformat() if tx.exit_time else None  # Use exit_time instead of closed_at
        })
    
    # Calculate total pages
    total_pages = (total_transactions_count + limit - 1) // limit if limit > 0 else 0
    
    return {
        'bot_id': bot_id,
        'bot_name': bot.name,
        'period_days': days,
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
        'chart_data': chart_data,
        'recent_transactions': recent_txs,
        'pagination': {
            'current_page': page,
            'total_pages': total_pages,
            'total_items': total_transactions_count,
            'items_per_page': limit,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    }

def get_bot_subscriptions(
    db: Session,
    bot_id: int,
    developer_id: int,
    page: int = 1,
    limit: int = 20,
    principal_id: Optional[str] = None,
    user_id: Optional[int] = None,
    trading_pair: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    search: Optional[str] = None
):
    """
    Get all subscriptions for a bot with advanced filtering and pagination
    """
    from datetime import datetime
    
    # Verify bot belongs to developer
    bot = db.query(models.Bot).filter(
        models.Bot.id == bot_id,
        models.Bot.developer_id == developer_id
    ).first()
    
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Build base query
    query = db.query(models.Subscription).filter(
        models.Subscription.bot_id == bot_id
    )
    
    # Apply filters
    if principal_id:
        query = query.filter(models.Subscription.user_principal_id == principal_id)
    
    if user_id:
        query = query.filter(models.Subscription.user_id == user_id)
    
    if trading_pair:
        query = query.filter(models.Subscription.trading_pair == trading_pair)
    
    if status:
        try:
            status_enum = models.SubscriptionStatus[status.upper()]
            query = query.filter(models.Subscription.status == status_enum)
        except KeyError:
            pass  # Invalid status, ignore filter
    
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(models.Subscription.started_at >= start_dt)
        except ValueError:
            pass  # Invalid date format, ignore filter
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(models.Subscription.expires_at <= end_dt)
        except ValueError:
            pass  # Invalid date format, ignore filter
    
    # Apply search (search in principal_id, instance_name, or trading_pair)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                models.Subscription.user_principal_id.like(search_pattern),
                models.Subscription.instance_name.like(search_pattern),
                models.Subscription.trading_pair.like(search_pattern)
            )
        )
    
    # Get total count for pagination
    total_count = query.count()
    
    # Calculate pagination
    offset = (page - 1) * limit
    total_pages = (total_count + limit - 1) // limit if limit > 0 else 0
    
    # Get subscriptions with pagination
    subscriptions = query.order_by(
        models.Subscription.started_at.desc()
    ).offset(offset).limit(limit).all()
    
    # Format subscriptions
    subscriptions_list = []
    for sub in subscriptions:
        # Get transaction stats for this subscription
        transactions = db.query(models.Transaction).filter(
            models.Transaction.subscription_id == sub.id
        ).all()
        
        total_trades = len(transactions)
        open_positions = sum(1 for tx in transactions if tx.status == 'OPEN')
        closed_positions = sum(1 for tx in transactions if tx.status == 'CLOSED')
        
        total_pnl = 0.0
        for tx in transactions:
            if tx.status == 'CLOSED' and tx.realized_pnl:
                total_pnl += float(tx.realized_pnl)
            elif tx.status == 'OPEN' and tx.unrealized_pnl:
                total_pnl += float(tx.unrealized_pnl)
        
        subscriptions_list.append({
            'id': sub.id,
            'instance_name': sub.instance_name,
            'user_principal_id': sub.user_principal_id,
            'user_id': sub.user_id,
            'status': sub.status.value if sub.status else None,
            'trading_pair': sub.trading_pair,
            'secondary_trading_pairs': sub.secondary_trading_pairs or [],
            'timeframe': sub.bot.timeframe if sub.bot else None,
            'timeframes': sub.bot.timeframes if sub.bot else [],
            'is_testnet': sub.is_testnet,
            'network_type': sub.network_type.value if sub.network_type else None,
            'started_at': sub.started_at.isoformat() if sub.started_at else None,
            'expires_at': sub.expires_at.isoformat() if sub.expires_at else None,
            'last_run_at': sub.last_run_at.isoformat() if sub.last_run_at else None,
            'next_run_at': sub.next_run_at.isoformat() if sub.next_run_at else None,
            'payment_method': sub.payment_method.value if sub.payment_method else None,
            # Stats
            'total_trades': total_trades,
            'open_positions': open_positions,
            'closed_positions': closed_positions,
            'total_pnl': round(total_pnl, 2)
        })
    
    return {
        'bot_id': bot_id,
        'bot_name': bot.name,
        'subscriptions': subscriptions_list,
        'pagination': {
            'current_page': page,
            'total_pages': total_pages,
            'total_items': total_count,
            'items_per_page': limit,
            'has_next': page < total_pages,
            'has_prev': page > 1
        },
        'filters_applied': {
            'principal_id': principal_id,
            'user_id': user_id,
            'trading_pair': trading_pair,
            'status': status,
            'start_date': start_date,
            'end_date': end_date,
            'search': search
        }
    }

def get_all_bots(db: Session, skip: int = 0, limit: int = 100, status_filter: Optional[schemas.BotStatus] = None):
    query = db.query(models.Bot)
    
    if status_filter:
        query = query.filter(models.Bot.status == status_filter)
    
    return query.offset(skip).limit(limit).all()

def get_bots_by_status(db: Session, status: schemas.BotStatus):
    return db.query(models.Bot).filter(models.Bot.status == status).all()

def update_bot(db: Session, bot_id: int, bot_update: schemas.BotUpdate):
    db_bot = get_bot_by_id(db, bot_id)
    if db_bot:
        update_data = bot_update.dict(exclude_unset=True)
        logger.info(f"🔧 update_bot called for bot {bot_id}")
        logger.info(f"📦 Received update_data: {update_data}")
        
        # Handle LLM configuration - merge into strategy_config
        llm_fields = ['llm_provider', 'llm_model', 'enable_image_analysis', 'enable_sentiment_analysis']
        llm_config = {}
        
        for field in llm_fields:
            if field in update_data:
                llm_config[field] = update_data.pop(field)
        
        # Merge LLM config into strategy_config
        if llm_config:
            from sqlalchemy.orm.attributes import flag_modified
            
            if db_bot.strategy_config is None:
                db_bot.strategy_config = {}
            
            logger.info(f"🔹 Old strategy_config: {db_bot.strategy_config}")
            
            # Create a new dict to ensure SQLAlchemy detects the change
            new_strategy_config = dict(db_bot.strategy_config)
            new_strategy_config.update(llm_config)
            db_bot.strategy_config = new_strategy_config
            
            # Explicitly mark as modified for SQLAlchemy
            flag_modified(db_bot, 'strategy_config')
            
            logger.info(f"🔸 New strategy_config: {db_bot.strategy_config}")
            logger.info(f"✅ Updated bot {bot_id} LLM config: {llm_config}")
        
        # 🛡️ Handle Risk Management Configuration - Map to risk_config
        risk_fields = ['leverage', 'risk_percentage', 'stop_loss_percentage', 'take_profit_percentage']
        risk_updates = {}
        
        for field in risk_fields:
            if field in update_data:
                value = update_data.pop(field)
                # Map frontend fields to risk_config fields
                if field == 'leverage':
                    risk_updates['max_leverage'] = value
                elif field == 'risk_percentage':
                    risk_updates['risk_per_trade_percent'] = value
                    risk_updates['max_position_size'] = value  # Use same value
                elif field == 'stop_loss_percentage':
                    risk_updates['stop_loss_percent'] = value
                elif field == 'take_profit_percentage':
                    risk_updates['take_profit_percent'] = value
        
        # Merge risk updates into risk_config
        if risk_updates:
            from sqlalchemy.orm.attributes import flag_modified
            
            if db_bot.risk_config is None:
                db_bot.risk_config = {}
            
            logger.info(f"🔹 Old risk_config: {db_bot.risk_config}")
            
            # Create a new dict to ensure SQLAlchemy detects the change
            new_risk_config = dict(db_bot.risk_config)
            new_risk_config.update(risk_updates)
            
            # Ensure mode is set
            if 'mode' not in new_risk_config:
                new_risk_config['mode'] = 'DEFAULT'
            
            db_bot.risk_config = new_risk_config
            db_bot.risk_management_mode = 'DEFAULT'
            
            # Explicitly mark as modified for SQLAlchemy
            flag_modified(db_bot, 'risk_config')
            
            logger.info(f"🔸 New risk_config: {db_bot.risk_config}")
            logger.info(f"✅ Updated bot {bot_id} risk config: {risk_updates}")
        
        # Apply remaining updates
        for key, value in update_data.items():
            setattr(db_bot, key, value)
        
        logger.info(f"💾 Committing changes to database...")
        db.commit()
        db.refresh(db_bot)
        logger.info(f"✅ Bot {bot_id} updated successfully!")
        logger.info(f"📊 Final strategy_config in DB: {db_bot.strategy_config}")
    return db_bot

def update_bot_status(db: Session, bot_id: int, status: schemas.BotStatus):
    db_bot = get_bot_by_id(db, bot_id)
    if db_bot:
        db_bot.status = status
        db.commit()
        db.refresh(db_bot)
    return db_bot

def update_bot_approval(db: Session, bot_id: int, status: schemas.BotStatus, approved_by: int, approval_notes: Optional[str] = None):
    db_bot = get_bot_by_id(db, bot_id)
    if db_bot:
        db_bot.status = status
        db_bot.approved_by = approved_by
        db_bot.approved_at = datetime.utcnow()
        if approval_notes:
            db_bot.approval_notes = approval_notes
        db.commit()
        db.refresh(db_bot)
    return db_bot

def save_bot_file_to_s3(db: Session, bot_id: int, file_content: bytes, file_name: str, version: Optional[str] = None) -> Dict[str, Any]:
    """Save bot file to S3 and return upload information"""
    try:
        # Upload to S3
        code_content = file_content.decode('utf-8')
        upload_result = get_s3_manager().upload_bot_code(
            bot_id=bot_id,
            code_content=code_content,
            filename=file_name,
            version=version
        )
        
        # Update bot record with S3 information
        db_bot = get_bot_by_id(db, bot_id)
        if db_bot:
            db_bot.code_path = upload_result['s3_key']
            db_bot.version = upload_result['version']
            db.commit()
            db.refresh(db_bot)
        
        return upload_result
        
    except Exception as e:
        raise Exception(f"Failed to save bot file to S3: {str(e)}")

def save_bot_file(db: Session, bot_id: int, file_content: bytes, file_name: str):
    """Legacy function - now uses S3"""
    upload_result = save_bot_file_to_s3(db, bot_id, file_content, file_name)
    return upload_result['s3_key']

def update_bot_code_path(db: Session, bot_id: int, code_path: str):
    """Update bot code path (S3 key)"""
    db_bot = get_bot_by_id(db, bot_id)
    if db_bot:
        db_bot.code_path = code_path
        db.commit()
        db.refresh(db_bot)
    return db_bot

def save_bot_with_s3(db: Session, bot_data: schemas.BotCreate, developer_id: int, 
                     file_content: Optional[str] = None, file_name: str = "bot.py", 
                     version: Optional[str] = None, file_content_rpa_robot: Optional[str] = None, file_name_rpa_robot: str = "rpa_robot.robot",
                     status: schemas.BotStatus = schemas.BotStatus.PENDING, approved_by: Optional[int] = None) -> models.Bot:
    """Create bot and upload code to S3 in one operation"""
    try:
        # Create bot record first
        db_bot = create_bot(db, bot_data, developer_id, status=status, approved_by=approved_by)
        
        # Check if this is a template bot (code_path already set to local file)
        is_template_bot = db_bot.code_path and not db_bot.code_path.startswith('bots/')
        
        if is_template_bot:
            logger.info(f"✅ Template bot created - using local file: {db_bot.code_path}")
            # Template bots use local files, no S3 upload needed
            return db_bot
        
        # Upload code to S3 if provided (for user-uploaded bots only)
        if file_content:
            upload_result = get_s3_manager().upload_bot_code(
                bot_id=db_bot.id,
                code_content=file_content,
                filename=file_name,
                version=version,
                file_type="code"
            )
            
            # Update bot with S3 information
            db_bot.code_path = upload_result['s3_key']
            db_bot.version = upload_result['version']
            db.commit()
            db.refresh(db_bot)
            logger.info(f"✅ User bot created - uploaded to S3: {db_bot.code_path}")

        if file_content_rpa_robot:
            upload_result = get_s3_manager().upload_bot_code(
                bot_id=db_bot.id,
                code_content=file_content_rpa_robot,
                filename=file_name_rpa_robot,
                version=version,
                file_type="rpa"
            )
            db_bot.code_path_rpa = upload_result['s3_key']
            db_bot.version_rpa = upload_result['version']
            db.commit()
            db.refresh(db_bot)

        return db_bot
        
    except Exception as e:
        # Rollback if something fails
        db.rollback()
        raise Exception(f"Failed to create bot with S3: {str(e)}")

def load_bot_from_s3(bot_id: int, version: Optional[str] = None, user_config: Optional[Dict[str, Any]] = None, 
                     user_api_keys: Optional[Dict[str, str]] = None):
    """Load bot from S3 using BotManager"""
    try:
        return get_bot_manager().load_bot_from_s3(bot_id, version, user_config, user_api_keys)
    except Exception as e:
        raise Exception(f"Failed to load bot from S3: {str(e)}")

def get_bot_s3_info(db: Session, bot_id: int) -> Optional[Dict[str, Any]]:
    """Get bot S3 information"""
    db_bot = get_bot_by_id(db, bot_id)
    if not db_bot:
        return None
    
    return {
        "bot_id": bot_id,
        "s3_key": db_bot.code_path,
        "version": db_bot.version,
        "updated_at": db_bot.updated_at
    }

def get_active_subscriptions_for_bot(db: Session, bot_id: int):
    return db.query(models.Subscription).filter(
        models.Subscription.bot_id == bot_id,
        models.Subscription.status == models.SubscriptionStatus.ACTIVE
    ).all()

def delete_bot(db: Session, bot_id: int):
    """Delete bot and its S3 files"""
    try:
        bot = get_bot_by_id(db, bot_id)
        if bot:
            # Delete from S3 first
            if bot.code_path:
                try:
                    get_s3_manager().delete_bot_files(bot_id)
                except Exception as e:
                    # Log but don't fail if S3 deletion fails
                    print(f"Warning: Failed to delete S3 files for bot {bot_id}: {e}")
            
            # Delete from database
            db.delete(bot)
            db.commit()
            
            # Clear from bot manager cache
            get_bot_manager().unload_bot(bot_id)
            
        return True
    except Exception as e:
        db.rollback()
        raise Exception(f"Failed to delete bot: {str(e)}")

# --- Bot Review CRUD ---
def create_bot_review(db: Session, review: schemas.BotReviewCreate, user_id: int, bot_id: int):
    db_review = models.BotReview(
        user_id=user_id,
        bot_id=bot_id,
        rating=review.rating,
        review_text=review.review_text
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    
    # Update bot's average rating
    update_bot_rating(db, bot_id)
    
    return db_review

def get_bot_reviews(db: Session, bot_id: int, skip: int = 0, limit: int = 20):
    return db.query(models.BotReview).options(
        joinedload(models.BotReview.user)
    ).filter(models.BotReview.bot_id == bot_id).offset(skip).limit(limit).all()

def get_user_bot_review(db: Session, user_id: int, bot_id: int):
    return db.query(models.BotReview).filter(
        models.BotReview.user_id == user_id,
        models.BotReview.bot_id == bot_id
    ).first()

def get_bot_review(db: Session, review_id: int):
    return db.query(models.BotReview).filter(models.BotReview.id == review_id).first()

def update_bot_review(db: Session, review_id: int, review_update: schemas.BotReviewBase):
    db_review = get_bot_review(db, review_id)
    if db_review:
        update_data = review_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_review, key, value)
        db.commit()
        db.refresh(db_review)
        
        # Update bot's average rating
        update_bot_rating(db, db_review.bot_id)
    
    return db_review

def delete_bot_review(db: Session, review_id: int):
    review = get_bot_review(db, review_id)
    if review:
        bot_id = review.bot_id
        db.delete(review)
        db.commit()
        
        # Update bot's average rating
        update_bot_rating(db, bot_id)
    
    return True

def update_bot_rating(db: Session, bot_id: int):
    """Update bot's average rating and total reviews"""
    avg_rating = db.query(func.avg(models.BotReview.rating)).filter(
        models.BotReview.bot_id == bot_id
    ).scalar() or 0.0
    
    total_reviews = db.query(models.BotReview).filter(
        models.BotReview.bot_id == bot_id
    ).count()
    
    bot = get_bot_by_id(db, bot_id)
    if bot:
        bot.average_rating = float(avg_rating)
        bot.total_reviews = total_reviews
        db.commit()

def get_all_reviews(db: Session, skip: int = 0, limit: int = 100, bot_id: Optional[int] = None):
    query = db.query(models.BotReview).options(
        joinedload(models.BotReview.user)
    )
    
    if bot_id:
        query = query.filter(models.BotReview.bot_id == bot_id)
    
    return query.offset(skip).limit(limit).all()

def user_has_bot_subscription(db: Session, user_id: int, bot_id: int):
    return db.query(models.Subscription).filter(
        models.Subscription.user_id == user_id,
        models.Subscription.bot_id == bot_id
    ).first() is not None

# --- Subscription CRUD ---
def create_subscription(db: Session, sub: schemas.SubscriptionCreate, user_id: int):
    db_sub = models.Subscription(
        user_id=user_id,
        bot_id=sub.bot_id,
        instance_name=sub.instance_name,
        trading_pair=sub.trading_pair,
        secondary_trading_pairs=sub.secondary_trading_pairs or [],
        timeframe=sub.timeframe,
        strategy_config=sub.strategy_config,
        execution_config=sub.execution_config.dict(),
        risk_config=sub.risk_config.dict(),
        is_testnet=sub.is_testnet,
        is_trial=sub.is_trial,
        status=models.SubscriptionStatus.ACTIVE
    )
    db.add(db_sub)
    db.commit()
    db.refresh(db_sub)
    
    # Update bot subscriber count
    update_bot_subscriber_count(db, sub.bot_id)
    
    return db_sub

def create_trial_subscription(db: Session, trial: schemas.SubscriptionTrialCreate, user_id: int):
    """Create a trial subscription with default safe settings for testnet"""
    from datetime import datetime, timedelta
    
    # Check if user already has an ACTIVE trial for this bot
    existing_active_trial = db.query(models.Subscription).filter(
        models.Subscription.user_id == user_id,
        models.Subscription.bot_id == trial.bot_id,
        models.Subscription.is_trial == True,
        models.Subscription.status == models.SubscriptionStatus.ACTIVE
    ).first()
    
    if existing_active_trial:
        raise ValueError("User already has an active trial subscription for this bot. Please cancel the existing trial first.")
    
    # Create trial subscription with safe defaults
    trial_expires = datetime.utcnow() + timedelta(hours=trial.trial_duration_hours)
    
    # Default safe execution config for trials
    default_execution_config = {
        "initial_balance": 1000.0,  # $1000 testnet balance
        "max_position_size": 0.1,   # 10% max position
        "order_type": "market",
        "slippage_tolerance": 0.001
    }
    
    # Default safe risk config for trials
    default_risk_config = {
        "max_loss_per_trade": 0.02,  # 2% max loss per trade
        "max_daily_loss": 0.05,      # 5% max daily loss
        "stop_loss_percentage": 0.02,
        "take_profit_percentage": 0.04,
        "trailing_stop": False
    }
    
    db_trial = models.Subscription(
        user_id=user_id,
        bot_id=trial.bot_id,
        instance_name=trial.instance_name,
        exchange_type=trial.exchange_type.value,
        trading_pair=trial.trading_pair,
        timeframe=trial.timeframe,
        strategy_config={},  # Use bot's default config
        execution_config=default_execution_config,
        risk_config=default_risk_config,
        is_testnet=True,     # Always testnet for trials
        is_trial=True,       # Mark as trial
        trial_expires_at=trial_expires,
        expires_at=trial_expires,  # Same as trial expiry
        status=models.SubscriptionStatus.ACTIVE
    )
    
    db.add(db_trial)
    db.commit()
    db.refresh(db_trial)
    
    # Update bot subscriber count
    update_bot_subscriber_count(db, trial.bot_id)
    
    return db_trial

def get_subscription_by_id(db: Session, sub_id: int):
    return db.query(models.Subscription).filter(models.Subscription.id == sub_id).first()

def get_all_subscription_by_principal_id(db: Session, principal_id: int, bot_mode: str):
    return (
        db.query(models.Subscription)
        .join(models.Subscription.bot)  # join bằng relationship
        .filter(
            models.Subscription.user_principal_id == principal_id,
            models.Bot.bot_mode == bot_mode
        )
        .all()
    )

def get_subscription_by_id_and_bot(db: Session, sub_id: int, bot_id: int):
    return db.query(models.Subscription).filter(models.Subscription.id == sub_id, models.Subscription.bot_id == bot_id).first()
# --- Exchange Credentials CRUD ---
def create_exchange_credentials(db: Session, credentials: schemas.ExchangeCredentialsCreate, user_id: int):
    """Create new exchange credentials for a user"""
    # Check if credentials already exist for this exchange + testnet combination
    existing = db.query(models.DeveloperExchangeCredentials).filter(
        models.DeveloperExchangeCredentials.user_id == user_id,
        models.DeveloperExchangeCredentials.exchange == credentials.exchange,
        models.DeveloperExchangeCredentials.is_testnet == credentials.is_testnet
    ).first()
    
    if existing:
        raise ValueError(f"Credentials for {credentials.exchange.value} ({'testnet' if credentials.is_testnet else 'mainnet'}) already exist")
    
    db_credentials = models.DeveloperExchangeCredentials(
        user_id=user_id,
        exchange=credentials.exchange,
        api_key=credentials.api_key,
        api_secret=credentials.api_secret,
        api_passphrase=credentials.api_passphrase,
        is_testnet=credentials.is_testnet,
        validation_status="pending"
    )
    db.add(db_credentials)
    db.commit()
    db.refresh(db_credentials)
    return db_credentials

def get_user_exchange_credentials(db: Session, user_id: int, exchange: str = None, is_testnet: bool = None):
    """Get user's exchange credentials with optional filtering (legacy - use principal_id version)"""
    query = db.query(models.DeveloperExchangeCredentials).filter(
        models.DeveloperExchangeCredentials.user_id == user_id,
        models.DeveloperExchangeCredentials.is_active == True
    )
    
    if exchange:
        query = query.filter(models.DeveloperExchangeCredentials.exchange == exchange)
    if is_testnet is not None:
        query = query.filter(models.DeveloperExchangeCredentials.is_testnet == is_testnet)
    
    return query.all()

def get_exchange_credentials_by_principal_id(db: Session, principal_id: str, exchange: str = None, is_testnet: bool = None):
    """Get exchange credentials by principal ID with optional filtering"""
    query = db.query(models.DeveloperExchangeCredentials).filter(
        models.DeveloperExchangeCredentials.principal_id == principal_id,
        models.DeveloperExchangeCredentials.is_active == True
    )
    
    if exchange:
        query = query.filter(models.DeveloperExchangeCredentials.exchange == exchange)
    if is_testnet is not None:
        query = query.filter(models.DeveloperExchangeCredentials.is_testnet == is_testnet)
    
    return query.all()

def get_exchange_credentials_by_id(db: Session, credentials_id: int, user_id: int):
    """Get specific exchange credentials by ID (user must own them)"""
    return db.query(models.DeveloperExchangeCredentials).filter(
        models.DeveloperExchangeCredentials.id == credentials_id,
        models.DeveloperExchangeCredentials.user_id == user_id
    ).first()

def update_exchange_credentials(db: Session, credentials_id: int, user_id: int, credentials_update: schemas.ExchangeCredentialsUpdate):
    """Update exchange credentials"""
    db_credentials = get_exchange_credentials_by_id(db, credentials_id, user_id)
    if not db_credentials:
        return None
    
    update_data = credentials_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_credentials, field, value)
    
    # Reset validation status if API keys changed
    if 'api_key' in update_data or 'api_secret' in update_data:
        db_credentials.validation_status = "pending"
        db_credentials.last_validated = None
    
    db.commit()
    db.refresh(db_credentials)
    return db_credentials

def delete_exchange_credentials(db: Session, credentials_id: int, user_id: int):
    """Delete exchange credentials"""
    db_credentials = get_exchange_credentials_by_id(db, credentials_id, user_id)
    if not db_credentials:
        return False
    
    db.delete(db_credentials)
    db.commit()
    return True

def update_credentials_validation(db: Session, credentials_id: int, is_valid: bool, message: str):
    """Update validation status of credentials"""
    from datetime import datetime
    
    db_credentials = db.query(models.DeveloperExchangeCredentials).filter(
        models.DeveloperExchangeCredentials.id == credentials_id
    ).first()
    
    if db_credentials:
        db_credentials.validation_status = "valid" if is_valid else "invalid"
        db_credentials.last_validated = datetime.utcnow()
        db.commit()
        db.refresh(db_credentials)
    
    return db_credentials

# === User Settings CRUD ===
def get_users_setting_by_telegram_username(db: Session, telegram_username: int) -> models.UserSettings:
    """Get users settings by Telegram ID"""
    return db.query(models.UserSettings).filter(models.UserSettings.social_telegram == telegram_username).all()

def get_users_setting_by_discord_username(db: Session, discord_username: int) -> models.UserSettings:
    """Get users settings by Discord ID"""
    return db.query(models.UserSettings).filter(models.UserSettings.social_discord == discord_username).all()

def get_user_settings_by_principal(db: Session, principal_id: str):
    return db.query(models.UserSettings).filter(models.UserSettings.principal_id == principal_id).first()

def upsert_user_settings_by_principal(db: Session, settings: "schemas.MarketplaceUserSettings") -> models.UserSettings:
    rec = get_user_settings_by_principal(db, settings.principal_id)
    if rec is None:
        rec = models.UserSettings(
            principal_id=settings.principal_id,
            email=settings.email,
            social_telegram=settings.social_telegram,
            social_discord=settings.social_discord,
            social_twitter=settings.social_twitter,
            social_whatsapp=settings.social_whatsapp,
            default_channel=settings.default_channel or "email",
            display_dark_mode=bool(settings.display_dark_mode),
            display_currency=settings.display_currency or "ICP",
            display_language=settings.display_language or "en",
            display_timezone=settings.display_timezone or "UTC",
        )
        db.add(rec)
    else:
        rec.email = settings.email
        rec.social_telegram = settings.social_telegram
        rec.social_discord = settings.social_discord
        rec.social_twitter = settings.social_twitter
        rec.social_whatsapp = settings.social_whatsapp
        if settings.default_channel is not None:
            rec.default_channel = settings.default_channel
        if settings.display_dark_mode is not None:
            rec.display_dark_mode = bool(settings.display_dark_mode)
        if settings.display_currency is not None:
            rec.display_currency = settings.display_currency
        if settings.display_language is not None:
            rec.display_language = settings.display_language
        if settings.display_timezone is not None:
            rec.display_timezone = settings.display_timezone

    db.commit()
    db.refresh(rec)
    return rec

def get_subscription_with_bot(db: Session, subscription_id: int):
    return db.query(models.Subscription).options(
        joinedload(models.Subscription.bot)
    ).filter(models.Subscription.id == subscription_id).first()

def get_user_subscriptions(db: Session, user_id: int):
    return db.query(models.Subscription).filter(models.Subscription.user_id == user_id).all()

def get_user_subscriptions_paginated(db: Session, user_id: int, skip: int = 0, limit: int = 50, status_filter: Optional[schemas.SubscriptionStatus] = None):
    query = db.query(models.Subscription).options(
        joinedload(models.Subscription.bot)
    ).filter(models.Subscription.user_id == user_id)
    
    if status_filter:
        query = query.filter(models.Subscription.status == status_filter)
    
    total = query.count()
    subscriptions = query.offset(skip).limit(limit).all()
    
    return subscriptions, total

def get_user_subscription_by_name(db: Session, user_id: int, instance_name: str):
    return db.query(models.Subscription).filter(
        models.Subscription.user_id == user_id,
        models.Subscription.instance_name == instance_name,
        models.Subscription.status == models.SubscriptionStatus.ACTIVE
    ).first()

def update_subscription(db: Session, subscription_id: int, sub_update: schemas.SubscriptionUpdate):
    db_sub = get_subscription_by_id(db, subscription_id)
    if db_sub:
        update_data = sub_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            if key in ['execution_config', 'risk_config'] and value:
                setattr(db_sub, key, value.dict() if hasattr(value, 'dict') else value)
            else:
                setattr(db_sub, key, value)
        db.commit()
        db.refresh(db_sub)
    return db_sub

def update_subscription_status(db: Session, sub_id: int, status: schemas.SubscriptionStatus):
    db_sub = get_subscription_by_id(db, sub_id)
    if db_sub:
        old_status = db_sub.status
        db_sub.status = status
        db.commit()
        db.refresh(db_sub)
        
        # Update bot subscriber count if subscription was cancelled
        if old_status == models.SubscriptionStatus.ACTIVE and status == models.SubscriptionStatus.CANCELLED:
            update_bot_subscriber_count(db, db_sub.bot_id)
    
    return db_sub

def get_all_subscriptions(db: Session, skip: int = 0, limit: int = 100, status_filter: Optional[schemas.SubscriptionStatus] = None):
    query = db.query(models.Subscription).options(
        joinedload(models.Subscription.bot)
    )
    
    if status_filter:
        query = query.filter(models.Subscription.status == status_filter)
    
    return query.offset(skip).limit(limit).all()

def get_active_subscriptions_for_user(db: Session, user_id: int):
    return db.query(models.Subscription).filter(
        models.Subscription.user_id == user_id,
        models.Subscription.status == models.SubscriptionStatus.ACTIVE
    ).all()

def get_active_subscriptions(db: Session):
    """Get all active subscriptions for scheduling"""
    return db.query(models.Subscription).options(
        joinedload(models.Subscription.bot),
        joinedload(models.Subscription.user)
    ).filter(
        models.Subscription.status == models.SubscriptionStatus.ACTIVE
    ).all()

def get_bot_signal_subscriptions(db: Session, user_principal_id: int):
    return db.query(models.Subscription).filter(
        models.Subscription.user_principal_id == user_principal_id,
        models.Subscription.status == models.SubscriptionStatus.ACTIVE,
        models.Bot.bot_mode == 'PASSIVE'
    ).all()

def update_subscription_next_run(db: Session, subscription_id: int, next_run: datetime):
    """Update subscription's next run time"""
    subscription = get_subscription_by_id(db, subscription_id)
    if subscription:
        subscription.next_run_at = next_run
        db.commit()
        return subscription
    return None

def update_bot_subscriber_count(db: Session, bot_id: int):
    """Update bot's total subscriber count"""
    total_subscribers = db.query(models.Subscription).filter(
        models.Subscription.bot_id == bot_id,
        models.Subscription.status == models.SubscriptionStatus.ACTIVE
    ).count()
    
    bot = get_bot_by_id(db, bot_id)
    if bot:
        bot.total_subscribers = total_subscribers
        db.commit()

def close_open_trades_for_subscription(db: Session, subscription_id: int):
    """Close all open trades for a subscription"""
    open_trades = db.query(models.Trade).filter(
        models.Trade.subscription_id == subscription_id,
        models.Trade.status == models.TradeStatus.OPEN
    ).all()
    
    for trade in open_trades:
        trade.status = models.TradeStatus.CLOSED
        trade.exit_time = datetime.utcnow()
        # You would calculate exit_price and pnl here based on current market price
    
    db.commit()

# --- Trade CRUD ---
def create_trade(db: Session, trade: schemas.TradeCreate):
    db_trade = models.Trade(**trade.dict())
    db.add(db_trade)
    db.commit()
    db.refresh(db_trade)
    
    # Update subscription trade count
    update_subscription_trade_stats(db, trade.subscription_id)
    
    return db_trade

def get_subscription_trades_paginated(db: Session, subscription_id: int, skip: int = 0, limit: int = 50, status_filter: Optional[schemas.TradeStatus] = None):
    query = db.query(models.Trade).filter(models.Trade.subscription_id == subscription_id)
    
    if status_filter:
        query = query.filter(models.Trade.status == status_filter)
    
    total = query.count()
    trades = query.order_by(desc(models.Trade.entry_time)).offset(skip).limit(limit).all()
    
    return trades, total

def update_subscription_trade_stats(db: Session, subscription_id: int):
    """Update subscription trade statistics"""
    total_trades = db.query(models.Trade).filter(
        models.Trade.subscription_id == subscription_id
    ).count()
    
    winning_trades = db.query(models.Trade).filter(
        models.Trade.subscription_id == subscription_id,
        models.Trade.pnl > 0
    ).count()
    
    total_pnl = db.query(func.sum(models.Trade.pnl)).filter(
        models.Trade.subscription_id == subscription_id
    ).scalar() or Decimal('0.0')
    
    subscription = get_subscription_by_id(db, subscription_id)
    if subscription:
        subscription.total_trades = total_trades
        subscription.winning_trades = winning_trades
        subscription.total_pnl = total_pnl
        db.commit()

# --- Performance CRUD ---
def get_bot_performance_metrics(db: Session, bot_id: int, days: int = 30):
    # This would calculate performance metrics for a specific bot
    # Implementation depends on your specific requirements
    pass

def get_subscription_performance_metrics(db: Session, subscription_id: int, days: int = 30):
    # This would calculate performance metrics for a specific subscription
    # Implementation depends on your specific requirements
    pass

def log_bot_action(db: Session, subscription_id: int, action: str, details: str = None, 
                  price: float = None, quantity: float = None, balance: float = None,
                  signal_data: dict = None, trade_result: dict = None, 
                  account_status: dict = None, notification_status: dict = None):
    """Log comprehensive bot action to performance log table with detailed trading information"""
    try:
        # Build comprehensive signal data
        comprehensive_signal_data = {}
        
        # Add basic details
        if details:
            comprehensive_signal_data["details"] = details
            
        # Add trading information
        if trade_result:
            comprehensive_signal_data.update({
                "trade_result": trade_result,
                "entry_price": trade_result.get("entry_price"),
                "stop_loss": trade_result.get("stop_loss"),
                "take_profit": trade_result.get("take_profit"),
                "order_id": trade_result.get("order_id"),
                "leverage": trade_result.get("leverage"),
                "risk_reward_ratio": trade_result.get("risk_reward_ratio"),
                "confidence": trade_result.get("confidence"),
                "reason": trade_result.get("reason")
            })
            
        # Add account information
        if account_status:
            # Serialize account_status to handle FuturesPosition and other non-JSON objects
            serialized_account_status = {}
            for key, value in account_status.items():
                try:
                    if hasattr(value, '__dict__'):
                        # Convert objects to dict
                        serialized_account_status[key] = {
                            k: v for k, v in value.__dict__.items() 
                            if not k.startswith('_') and not callable(v)
                        }
                    elif isinstance(value, (list, tuple)):
                        # Handle lists/tuples of objects
                        serialized_account_status[key] = [
                            {k: v for k, v in item.__dict__.items() if not k.startswith('_') and not callable(v)}
                            if hasattr(item, '__dict__') else item
                            for item in value
                        ]
                    else:
                        serialized_account_status[key] = value
                except Exception as e:
                    # Fallback to string representation if serialization fails
                    serialized_account_status[key] = str(value)
            
            comprehensive_signal_data.update({
                "account_status": serialized_account_status,
                "available_balance": account_status.get("available_balance"),
                "total_balance": account_status.get("total_balance"),
                "margin_level": account_status.get("margin_level"),
                "unrealized_pnl": account_status.get("unrealized_pnl")
            })
            
        # Add notification status
        if notification_status:
            comprehensive_signal_data.update({
                "notifications": notification_status,
                "telegram_sent": notification_status.get("telegram_sent", False),
                "discord_sent": notification_status.get("discord_sent", False),
                "email_sent": notification_status.get("email_sent", False)
            })
            
        # Add any additional signal data
        if signal_data:
            comprehensive_signal_data.update(signal_data)
            
        # Extract price, quantity, balance from various sources
        final_price = price
        final_quantity = quantity  
        final_balance = balance
        
        if not final_price and trade_result:
            final_price = trade_result.get("entry_price") or trade_result.get("current_price")
            
        if not final_quantity and trade_result:
            final_quantity = trade_result.get("quantity")
            
        if not final_balance and account_status:
            final_balance = account_status.get("available_balance") or account_status.get("total_balance")
            
        log_entry = models.PerformanceLog(
            subscription_id=subscription_id,
            action=action,
            price=final_price or 0.0,
            quantity=final_quantity or 0.0,
            balance=final_balance or 0.0,
            signal_data=comprehensive_signal_data
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry
    except Exception as e:
        print(f"Failed to log bot action: {e}")
        db.rollback()
        return None

def get_subscription_logs(db: Session, subscription_id: int, skip: int = 0, limit: int = 100, action_filter: Optional[str] = None):
    query = db.query(models.PerformanceLog).filter(
        models.PerformanceLog.subscription_id == subscription_id
    )
    
    if action_filter:
        query = query.filter(models.PerformanceLog.action == action_filter)
    
    return query.order_by(desc(models.PerformanceLog.timestamp)).offset(skip).limit(limit).all()

# --- Admin CRUD ---
def get_admin_stats(db: Session):
    total_users = db.query(models.User).count()
    total_developers = db.query(models.User).filter(models.User.role == models.UserRole.DEVELOPER).count()
    total_bots = db.query(models.Bot).count()
    approved_bots = db.query(models.Bot).filter(models.Bot.status == models.BotStatus.APPROVED).count()
    pending_bots = db.query(models.Bot).filter(models.Bot.status == models.BotStatus.PENDING).count()
    total_subscriptions = db.query(models.Subscription).count()
    active_subscriptions = db.query(models.Subscription).filter(
        models.Subscription.status == models.SubscriptionStatus.ACTIVE
    ).count()
    total_trades = db.query(models.Trade).count()
    
    # Calculate total revenue (you would need to implement payment tracking)
    total_revenue = Decimal('0.0')  # Placeholder
    
    return schemas.AdminStats(
        total_users=total_users,
        total_developers=total_developers,
        total_bots=total_bots,
        approved_bots=approved_bots,
        pending_bots=pending_bots,
        total_subscriptions=total_subscriptions,
        active_subscriptions=active_subscriptions,
        total_trades=total_trades,
        total_revenue=total_revenue
    )

def get_bot_performance_overview(db: Session, days: int = 30, limit: int = 50):
    # Implementation for bot performance overview
    pass

def get_user_performance_overview(db: Session, days: int = 30, limit: int = 50):
    # Implementation for user performance overview
    pass

def get_system_health(db: Session):
    # Implementation for system health check
    return {"status": "healthy", "database": "connected"}

def get_system_performance_logs(db: Session, skip: int = 0, limit: int = 100):
    # Implementation for system performance logs
    return []

# --- Pricing Plan CRUD ---
def create_pricing_plan(db: Session, plan_data: schemas.PricingPlanCreate, bot_id: int):
    """Create a new pricing plan for a bot"""
    db_plan = models.BotPricingPlan(
        bot_id=bot_id,
        **plan_data.dict()
    )
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan

def get_bot_pricing_plans(db: Session, bot_id: int, active_only: bool = True):
    """Get all pricing plans for a bot"""
    query = db.query(models.BotPricingPlan).filter(models.BotPricingPlan.bot_id == bot_id)
    if active_only:
        query = query.filter(models.BotPricingPlan.is_active == True)
    return query.order_by(models.BotPricingPlan.price_per_month).all()

def get_pricing_plan_by_id(db: Session, plan_id: int):
    """Get a specific pricing plan"""
    return db.query(models.BotPricingPlan).filter(models.BotPricingPlan.id == plan_id).first()

def update_pricing_plan(db: Session, plan_id: int, plan_data: schemas.PricingPlanUpdate):
    """Update a pricing plan"""
    db_plan = get_pricing_plan_by_id(db, plan_id)
    if not db_plan:
        return None
    
    update_data = plan_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_plan, field, value)
    
    db.commit()
    db.refresh(db_plan)
    return db_plan

def delete_pricing_plan(db: Session, plan_id: int):
    """Delete a pricing plan (soft delete by setting is_active=False)"""
    db_plan = get_pricing_plan_by_id(db, plan_id)
    if not db_plan:
        return False
    
    db_plan.is_active = False
    db.commit()
    return True

# --- Promotion CRUD ---
def create_promotion(db: Session, promotion_data: schemas.PromotionCreate, bot_id: int, created_by: int):
    """Create a new promotion for a bot"""
    db_promotion = models.BotPromotion(
        bot_id=bot_id,
        created_by=created_by,
        **promotion_data.dict()
    )
    db.add(db_promotion)
    db.commit()
    db.refresh(db_promotion)
    return db_promotion

def get_bot_promotions(db: Session, bot_id: int, active_only: bool = True):
    """Get all promotions for a bot"""
    query = db.query(models.BotPromotion).filter(models.BotPromotion.bot_id == bot_id)
    if active_only:
        query = query.filter(models.BotPromotion.is_active == True)
    return query.all()

def get_promotion_by_code(db: Session, promotion_code: str):
    """Get a promotion by its code"""
    return db.query(models.BotPromotion).filter(
        models.BotPromotion.promotion_code == promotion_code,
        models.BotPromotion.is_active == True
    ).first()

def validate_promotion(db: Session, promotion_code: str, bot_id: int, user_id: int):
    """Validate if a promotion code can be used"""
    promotion = get_promotion_by_code(db, promotion_code)
    if not promotion:
        return None, "Invalid promotion code"
    
    if promotion.bot_id != bot_id:
        return None, "Promotion code not valid for this bot"
    
    if promotion.used_count >= promotion.max_uses:
        return None, "Promotion code usage limit exceeded"
    
    now = datetime.utcnow()
    if now < promotion.valid_from or now > promotion.valid_until:
        return None, "Promotion code expired or not yet valid"
    
    return promotion, None

def use_promotion(db: Session, promotion_id: int):
    """Mark a promotion as used"""
    promotion = db.query(models.BotPromotion).filter(models.BotPromotion.id == promotion_id).first()
    if promotion:
        promotion.used_count += 1
        db.commit()
        return True
    return False

# --- Invoice CRUD ---
def create_invoice(db: Session, invoice_data: schemas.InvoiceCreate):
    """Create a new invoice"""
    # Generate invoice number
    invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{invoice_data.subscription_id:06d}"
    
    db_invoice = models.SubscriptionInvoice(
        invoice_number=invoice_number,
        **invoice_data.dict()
    )
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    return db_invoice

def get_user_invoices(db: Session, user_id: int, skip: int = 0, limit: int = 50):
    """Get invoices for a user"""
    return db.query(models.SubscriptionInvoice).filter(
        models.SubscriptionInvoice.user_id == user_id
    ).offset(skip).limit(limit).all()

def get_subscription_invoices(db: Session, subscription_id: int):
    """Get all invoices for a subscription"""
    return db.query(models.SubscriptionInvoice).filter(
        models.SubscriptionInvoice.subscription_id == subscription_id
    ).order_by(models.SubscriptionInvoice.created_at.desc()).all()

def update_invoice_status(db: Session, invoice_id: int, status: str, payment_date: datetime = None):
    """Update invoice status"""
    invoice = db.query(models.SubscriptionInvoice).filter(models.SubscriptionInvoice.id == invoice_id).first()
    if invoice:
        invoice.status = status
        if payment_date:
            invoice.payment_date = payment_date
        db.commit()
        return invoice
    return None

# --- Enhanced Subscription CRUD ---
def create_subscription_with_plan(
    db: Session, 
    sub: schemas.SubscriptionCreate, 
    user_id: int, 
    pricing_plan_id: int,
    promotion_code: str = None
):
    """Create subscription with pricing plan and promotion"""
    now = datetime.utcnow()
    
    # Get pricing plan
    pricing_plan = get_pricing_plan_by_id(db, pricing_plan_id)
    if not pricing_plan:
        raise ValueError(f"Pricing plan {pricing_plan_id} not found")
    
    # Validate promotion if provided
    promotion = None
    if promotion_code:
        promotion = validate_promotion(db, promotion_code, sub.bot_id, user_id)
        if not promotion:
            raise ValueError(f"Invalid promotion code: {promotion_code}")
    
    # Calculate trial period
    trial_expires = None
    is_trial = False
    if pricing_plan.trial_days > 0:
        trial_expires = now + timedelta(days=pricing_plan.trial_days)
        expires_at = trial_expires
        is_trial = True
    else:
        expires_at = now + timedelta(days=30)  # Default 30 days
        is_trial = False
    
    # Create subscription
    db_sub = models.Subscription(
        user_id=user_id,
        bot_id=sub.bot_id,
        # pricing_plan_id=pricing_plan_id,  # Tạm thời comment out
        instance_name=sub.instance_name,
        trading_pair=sub.trading_pair,
        timeframe=sub.timeframe,
        strategy_config=sub.strategy_config,
        execution_config=sub.execution_config.dict(),
        risk_config=sub.risk_config.dict(),
        is_testnet=sub.is_testnet,
        is_trial=is_trial,
        trial_expires_at=trial_expires if is_trial else None,
        expires_at=expires_at,
        status=models.SubscriptionStatus.ACTIVE,
        billing_cycle="MONTHLY",
        next_billing_date=expires_at
    )
    db.add(db_sub)
    db.commit()
    db.refresh(db_sub)
    
    # Create invoice
    base_price = pricing_plan.price_per_month
    discount_amount = Decimal('0.00')
    
    if promotion:
        if promotion.discount_type == "PERCENTAGE":
            discount_amount = base_price * (promotion.discount_value / 100)
        elif promotion.discount_type == "FIXED_AMOUNT":
            discount_amount = promotion.discount_value
        elif promotion.discount_type == "FREE_TRIAL":
            discount_amount = base_price
        
        # Mark promotion as used
        use_promotion(db, promotion.id)
    
    final_amount = base_price - discount_amount
    
    invoice_data = schemas.InvoiceCreate(
        subscription_id=db_sub.id,
        user_id=user_id,
        amount=base_price,
        base_price=base_price,
        discount_amount=discount_amount,
        final_amount=final_amount,
        billing_period_start=now,
        billing_period_end=expires_at,
        promotion_code=promotion_code if promotion else None,
        promotion_discount=discount_amount
    )
    
    create_invoice(db, invoice_data)
    
    # Update bot subscriber count
    update_bot_subscriber_count(db, sub.bot_id)
    
    return db_sub

# --- Pricing Calculation Functions ---
def calculate_subscription_price(
    pricing_plan: models.BotPricingPlan,
    billing_cycle: str = "MONTHLY",
    promotion: models.BotPromotion = None
) -> Dict[str, Decimal]:
    """Calculate subscription price with discounts"""
    if billing_cycle == "YEARLY" and pricing_plan.price_per_year:
        base_price = pricing_plan.price_per_year
    elif billing_cycle == "QUARTERLY" and pricing_plan.price_per_quarter:
        base_price = pricing_plan.price_per_quarter
    else:
        base_price = pricing_plan.price_per_month
    
    discount_amount = Decimal('0.00')
    
    if promotion:
        if promotion.discount_type == "PERCENTAGE":
            discount_amount = base_price * (promotion.discount_value / 100)
        elif promotion.discount_type == "FIXED_AMOUNT":
            discount_amount = promotion.discount_value
        elif promotion.discount_type == "FREE_TRIAL":
            discount_amount = base_price
    
    final_amount = base_price - discount_amount
    
    return {
        "base_price": base_price,
        "discount_amount": discount_amount,
        "final_amount": final_amount,
        "billing_cycle": billing_cycle
    }

def cleanup_old_bot_actions(cutoff_date: datetime) -> int:
    """Clean up old performance logs"""
    try:
        from core.database import SessionLocal
        db = SessionLocal()
        
        # Delete performance logs older than cutoff date
        deleted_count = db.query(models.PerformanceLog).filter(
            models.PerformanceLog.timestamp < cutoff_date
        ).delete()
        
        db.commit()
        db.close()
        
        return deleted_count
        
    except Exception as e:
        return 0

# --- Bot Registration CRUD for Marketplace ---
def create_bot_registration(
    db: Session, 
    registration: schemas.BotRegistrationRequest,
    marketplace_user_id: int
) -> models.Subscription:
    """Create a new bot registration/subscription for marketplace"""
    
    # Check if bot exists and is approved
    bot = db.query(models.Bot).filter(
        models.Bot.id == registration.bot_id,
        models.Bot.status == models.BotStatus.APPROVED
    ).first()
    
    if not bot:
        raise ValueError(f"Bot with ID {registration.bot_id} not found or not approved")
    
    # Check if user already has a subscription for this bot with same principal_id
    existing_sub = db.query(models.Subscription).filter(
        models.Subscription.user_id == marketplace_user_id,
        models.Subscription.bot_id == registration.bot_id,
        models.Subscription.user_principal_id == registration.user_principal_id,
        models.Subscription.status == models.SubscriptionStatus.ACTIVE
    ).first()
    
    if existing_sub:
        raise ValueError(f"Active subscription already exists for principal_id {registration.user_principal_id}")
    
    # Determine if testnet based on network_type
    is_testnet = registration.network_type == schemas.NetworkType.TESTNET
    
    # Create subscription
    db_subscription = models.Subscription(
        instance_name=f"{bot.name} - {registration.user_principal_id[:8]}",
        user_id=marketplace_user_id,
        bot_id=registration.bot_id,
        status=models.SubscriptionStatus.ACTIVE,
        
        # Marketplace specific fields
        user_principal_id=registration.user_principal_id,
        timeframes=registration.timeframes,
        trade_evaluation_period=registration.trade_evaluation_period,
        network_type=registration.network_type.value.upper(),
        trade_mode=registration.trade_mode.value.upper(),
        
        # Exchange and trading configuration
        exchange_type=registration.exchange_name,
        trading_pair=registration.symbol,
        timeframe=registration.timeframes[0] if registration.timeframes else "1h",  # Use first timeframe for backward compatibility
        is_testnet=is_testnet,
        
        # Time configuration
        started_at=registration.starttime,
        expires_at=registration.endtime,
        
        # Default configurations
        strategy_config={},
        execution_config={
            "buy_order_type": "PERCENTAGE",
            "buy_order_value": 10.0,
            "sell_order_type": "ALL",
            "sell_order_value": 100.0
        },
        risk_config={
            "stop_loss_percent": 5.0,
            "take_profit_percent": 10.0,
            "max_position_size": 0.1
        }
    )
    
    db.add(db_subscription)
    db.commit()
    db.refresh(db_subscription)
    
    # Update bot subscriber count
    update_bot_subscriber_count(db, registration.bot_id)
    
    return db_subscription

# --- Bot Marketplace Registration CRUD ---
import secrets
import string

def generate_bot_api_key(prefix: str = "bot") -> str:
    """Generate API key for bot"""
    # Generate random string: bot_abc123def456ghi789
    random_part = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(20))
    return f"{prefix}_{random_part}"

def create_bot_marketplace_registration(
    db: Session,
    registration: schemas.BotMarketplaceRegistrationRequest
) -> models.BotRegistration:
    """Register a bot for marketplace listing (idempotent per principal+bot).

    - If a record exists for (user_principal_id, bot_id), update api_key and metadata.
    - Else, create a new registration.
    """

    # Verify bot exists and is approved
    bot = db.query(models.Bot).filter(
        models.Bot.id == registration.bot_id,
        models.Bot.status == models.BotStatus.APPROVED
    ).first()

    if not bot:
        raise ValueError("Bot not found or not approved")

    # Generate a new API key
    bot_api_key = generate_bot_api_key()

    # Check existing registration by (principal, bot)
    existing = db.query(models.BotRegistration).filter(
        models.BotRegistration.user_principal_id == registration.user_principal_id,
        models.BotRegistration.bot_id == registration.bot_id
    ).first()

    if existing:
        # Update in-place (rotate API key and metadata)
        existing.api_key = bot_api_key
        existing.marketplace_name = registration.marketplace_name or existing.marketplace_name or bot.name
        existing.marketplace_description = registration.marketplace_description or existing.marketplace_description or bot.description
        if registration.price_on_marketplace is not None:
            existing.price_on_marketplace = registration.price_on_marketplace
        existing.status = models.BotRegistrationStatus.APPROVED
        db.commit()
        db.refresh(existing)
        return existing

    # Create registration with auto-approval
    db_registration = models.BotRegistration(
        user_principal_id=registration.user_principal_id,
        bot_id=registration.bot_id,
        api_key=bot_api_key,
        marketplace_name=registration.marketplace_name or bot.name,
        marketplace_description=registration.marketplace_description or bot.description,
        price_on_marketplace=registration.price_on_marketplace or bot.price_per_month,
        status=models.BotRegistrationStatus.APPROVED
    )

    db.add(db_registration)
    db.commit()
    db.refresh(db_registration)

    return db_registration

def get_marketplace_bots(
    db: Session,
    skip: int = 0,
    limit: int = 50
) -> List[models.BotRegistration]:
    """Get approved bots for marketplace display"""
    return db.query(models.BotRegistration).filter(
        models.BotRegistration.status == models.BotRegistrationStatus.APPROVED,
        models.BotRegistration.is_active == True
    ).order_by(
        models.BotRegistration.display_order.desc(),
        models.BotRegistration.registered_at.desc()
    ).offset(skip).limit(limit).all()

def get_bot_registration_by_api_key(
    db: Session,
    api_key: str
) -> models.BotRegistration:
    """Get bot registration by API key"""
    return db.query(models.BotRegistration).filter(
        models.BotRegistration.api_key == api_key,
        models.BotRegistration.status == models.BotRegistrationStatus.APPROVED,
        models.BotRegistration.is_active == True
    ).first()

def update_bot_registration(
    db: Session,
    subscription_id: int,
    update_data: schemas.BotRegistrationUpdate,
    marketplace_user_id: int
) -> tuple[models.Subscription, List[str]]:
    """Update an existing bot registration/subscription"""
    
    # Get subscription and verify ownership
    subscription = db.query(models.Subscription).filter(
        models.Subscription.id == subscription_id,
        models.Subscription.user_id == marketplace_user_id
    ).first()
    
    if not subscription:
        raise ValueError(f"Subscription {subscription_id} not found or not owned by user")
    
    # Track updated fields
    updated_fields = []
    
    # Update fields if provided
    if update_data.timeframes is not None:
        subscription.timeframes = update_data.timeframes
        # Update backward compatibility field
        subscription.timeframe = update_data.timeframes[0] if update_data.timeframes else subscription.timeframe
        updated_fields.append("timeframes")
    
    if update_data.trade_evaluation_period is not None:
        subscription.trade_evaluation_period = update_data.trade_evaluation_period
        updated_fields.append("trade_evaluation_period")
    
    if update_data.starttime is not None:
        subscription.started_at = update_data.starttime
        updated_fields.append("starttime")
    
    if update_data.endtime is not None:
        subscription.expires_at = update_data.endtime
        updated_fields.append("endtime")
    
    if update_data.exchange_name is not None:
        subscription.exchange_type = update_data.exchange_name
        updated_fields.append("exchange_name")
    
    if update_data.network_type is not None:
        subscription.network_type = update_data.network_type.value.upper()
        subscription.is_testnet = update_data.network_type == schemas.NetworkType.TESTNET
        updated_fields.append("network_type")
    
    if update_data.trade_mode is not None:
        subscription.trade_mode = update_data.trade_mode.value.upper()
        updated_fields.append("trade_mode")
    
    db.commit()
    db.refresh(subscription)
    
    return subscription, updated_fields

# ========================
# Prompt Template CRUD
# ========================

def create_prompt_template(db: Session, prompt: schemas.PromptTemplateCreate, created_by: int):
    """Create a new prompt template"""
    # If this is set as default, unset other defaults in the same category
    if prompt.is_default:
        db.query(models.LLMPromptTemplate).filter(
            models.LLMPromptTemplate.category == prompt.category,
            models.LLMPromptTemplate.is_default == True
        ).update({"is_default": False})
    
    db_prompt = models.LLMPromptTemplate(
        **prompt.dict(),
        created_by=created_by
    )
    db.add(db_prompt)
    db.commit()
    db.refresh(db_prompt)
    return db_prompt

def get_prompt_template_by_id(db: Session, prompt_id: int):
    """Get prompt template by ID"""
    return db.query(models.LLMPromptTemplate).filter(models.LLMPromptTemplate.id == prompt_id).first()

def get_prompt_templates(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    category: str = None,
    is_active: bool = None,
    created_by: int = None
):
    """Get prompt templates with optional filters"""
    query = db.query(models.LLMPromptTemplate)
    
    if category:
        query = query.filter(models.LLMPromptTemplate.category == category)
    if is_active is not None:
        query = query.filter(models.LLMPromptTemplate.is_active == is_active)
    if created_by:
        query = query.filter(models.LLMPromptTemplate.created_by == created_by)
    
    return query.order_by(models.LLMPromptTemplate.created_at.desc()).offset(skip).limit(limit).all()

def get_default_prompt_template(db: Session, category: str = "TRADING"):
    """Get the default prompt template for a category"""
    return db.query(models.LLMPromptTemplate).filter(
        models.LLMPromptTemplate.category == category,
        models.LLMPromptTemplate.is_default == True,
        models.LLMPromptTemplate.is_active == True
    ).first()

def update_prompt_template(db: Session, prompt_id: int, prompt_update: schemas.PromptTemplateUpdate):
    """Update a prompt template"""
    db_prompt = get_prompt_template_by_id(db, prompt_id)
    if not db_prompt:
        return None
    
    update_data = prompt_update.dict(exclude_unset=True)
    
    # If setting as default, unset other defaults in the same category
    if update_data.get('is_default') and db_prompt.category:
        db.query(models.LLMPromptTemplate).filter(
            models.LLMPromptTemplate.category == db_prompt.category,
            models.LLMPromptTemplate.is_default == True,
            models.LLMPromptTemplate.id != prompt_id
        ).update({"is_default": False})
    
    for key, value in update_data.items():
        setattr(db_prompt, key, value)
    
    db.commit()
    db.refresh(db_prompt)
    return db_prompt

def delete_prompt_template(db: Session, prompt_id: int):
    """Delete a prompt template (soft delete by setting is_active=False)"""
    db_prompt = get_prompt_template_by_id(db, prompt_id)
    if not db_prompt:
        return None
    
    # Check if any bots are using this template
    bots_using_template = db.query(models.Bot).filter(models.Bot.prompt_template_id == prompt_id).count()
    if bots_using_template > 0:
        # Soft delete - just deactivate
        db_prompt.is_active = False
        db.commit()
        db.refresh(db_prompt)
        return db_prompt
    else:
        # Hard delete if no bots are using it
        db.delete(db_prompt)
        db.commit()
        return db_prompt

def get_prompt_templates_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """Get prompt templates created by a specific user"""
    return db.query(models.LLMPromptTemplate).filter(
        models.LLMPromptTemplate.created_by == user_id
    ).order_by(models.LLMPromptTemplate.created_at.desc()).offset(skip).limit(limit).all()

def get_bot_registration_by_principal_id(
    db: Session,
    user_principal_id: str,
    bot_id: int = None
) -> List[models.Subscription]:
    """Get bot registrations by principal ID"""
    query = db.query(models.Subscription).filter(
        models.Subscription.user_principal_id == user_principal_id
    )
    
    if bot_id:
        query = query.filter(models.Subscription.bot_id == bot_id)
    
    return query.all()

def get_marketplace_subscription_by_id(
    db: Session,
    subscription_id: int,
    marketplace_user_id: int
) -> models.Subscription:
    """Get subscription by ID for marketplace user"""
    return db.query(models.Subscription).filter(
        models.Subscription.id == subscription_id,
        models.Subscription.user_id == marketplace_user_id
    ).first()

def get_bot_registration_by_api_key(db: Session, api_key: str) -> Optional[models.BotRegistration]:
    """Get bot registration by API key"""
    return db.query(models.BotRegistration).filter(
        models.BotRegistration.api_key == api_key,
        models.BotRegistration.is_active == True
    ).first()

def get_or_create_marketplace_user(db: Session, user_principal_id: str) -> models.User:
    """Get or create internal user for marketplace operations"""
    # Check if user exists
    user = db.query(models.User).filter(
        models.User.email == f"marketplace_{user_principal_id}@internal.com"
    ).first()
    
    if not user:
        # Create internal user
        user = models.User(
            email=f"marketplace_{user_principal_id}@internal.com",
            hashed_password="marketplace_internal_user",  # Not used for auth
            role=models.UserRole.USER,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return user

def get_subscription_by_id_and_principal(
    db: Session, 
    subscription_id: int, 
    principal_id: str
) -> Optional[models.Subscription]:
    """Get subscription by ID and principal ID for marketplace users"""
    return db.query(models.Subscription).filter(
        models.Subscription.id == subscription_id,
        models.Subscription.user_principal_id == principal_id,
        models.Subscription.is_marketplace_subscription == True
    ).first()


def update_subscription_status_by_principal(
    db: Session,
    subscription_id: int,
    principal_id: str,
    new_status: models.SubscriptionStatus
) -> Optional[models.Subscription]:
    """Update subscription status for marketplace user"""
    subscription = get_subscription_by_id_and_principal(db, subscription_id, principal_id)
    if subscription:
        subscription.status = new_status
        db.commit()
        db.refresh(subscription)
    return subscription


def validate_marketplace_subscription_access(
    db: Session,
    subscription_id: int,
    principal_id: str,
    api_key: str
) -> tuple[models.Subscription, models.BotRegistration]:
    """
    Validate marketplace subscription access with enhanced security:
    1. Verify API key exists and is active
    2. Get subscription by ID and principal ID
    3. Verify API key belongs to the subscription's bot
    4. Verify principal ID matches bot registration (optional but recommended)
    
    Returns: (subscription, bot_registration) if valid
    Raises: HTTPException if invalid
    """
    from fastapi import HTTPException, status
    
    # Step 1: Authenticate using bot API key
    bot_registration = get_bot_registration_by_api_key(db, api_key)
    if not bot_registration:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bot API key - authentication failed"
        )
    
    # Step 2: Get subscription by ID and principal ID
    subscription = get_subscription_by_id_and_principal(
        db, subscription_id, principal_id
    )
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found or access denied"
        )
    
    # Step 3: Verify API key belongs to this subscription's bot (SECURITY CHECK)
    if bot_registration.bot_id != subscription.bot_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key does not belong to this subscription's bot. Access denied."
        )
    
    # Note: Skip principal ID validation because in marketplace:
    # - Bot owner (bot_registration.user_principal_id) creates the bot
    # - Subscription user (principal_id) rents the bot
    # These are different users, which is expected in marketplace model
    
    return subscription, bot_registration

# PayPal Payment CRUD Operations
def create_paypal_payment(db: Session, payment_data: schemas.PayPalPaymentCreate) -> models.PayPalPayment:
    """Create a new PayPal payment record"""
    db_payment = models.PayPalPayment(**payment_data.dict())
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

def get_paypal_payment(db: Session, payment_id: str) -> models.PayPalPayment:
    """Get PayPal payment by ID"""
    return db.query(models.PayPalPayment).filter(models.PayPalPayment.id == payment_id).first()

def get_paypal_payment_by_order_id(db: Session, order_id: str) -> models.PayPalPayment:
    """Get PayPal payment by order ID"""
    return db.query(models.PayPalPayment).filter(models.PayPalPayment.order_id == order_id).first()

def get_paypal_payment_by_paypal_id(db: Session, paypal_payment_id: str) -> models.PayPalPayment:
    """Get PayPal payment by PayPal payment ID"""
    return db.query(models.PayPalPayment).filter(
        models.PayPalPayment.paypal_payment_id == paypal_payment_id
    ).first()

def update_paypal_payment_status(
    db: Session, 
    payment_id: str, 
    status: models.PayPalPaymentStatus,
    **kwargs
) -> models.PayPalPayment:
    """Update PayPal payment status and other fields"""
    db_payment = get_paypal_payment(db, payment_id)
    if db_payment:
        db_payment.status = status
        for key, value in kwargs.items():
            if hasattr(db_payment, key):
                setattr(db_payment, key, value)
        db.commit()
        db.refresh(db_payment)
    return db_payment

def get_paypal_payments_by_user(
    db: Session, 
    user_principal_id: str, 
    skip: int = 0, 
    limit: int = 50
) -> List[models.PayPalPayment]:
    """Get PayPal payments for a specific user"""
    return db.query(models.PayPalPayment).filter(
        models.PayPalPayment.user_principal_id == user_principal_id
    ).order_by(models.PayPalPayment.created_at.desc()).offset(skip).limit(limit).all()

def get_paypal_payments_by_status(
    db: Session, 
    status: models.PayPalPaymentStatus,
    skip: int = 0, 
    limit: int = 50
) -> List[models.PayPalPayment]:
    """Get PayPal payments by status"""
    return db.query(models.PayPalPayment).filter(
        models.PayPalPayment.status == status
    ).order_by(models.PayPalPayment.created_at.desc()).offset(skip).limit(limit).all()

def get_pending_rental_payments(db: Session) -> List[models.PayPalPayment]:
    """Get PayPal payments that need rental creation"""
    return db.query(models.PayPalPayment).filter(
        models.PayPalPayment.status == models.PayPalPaymentStatus.COMPLETED_PENDING_RENTAL
    ).order_by(models.PayPalPayment.created_at.asc()).all()

def get_paypal_payment_summaries(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    status_filter: str = None
) -> List[dict]:
    """Get PayPal payment summaries with bot information"""
    query = db.query(
        models.PayPalPayment.id,
        models.PayPalPayment.user_principal_id,
        models.Bot.name.label('bot_name'),
        models.PayPalPayment.amount_usd,
        models.PayPalPayment.status,
        models.PayPalPayment.created_at,
        models.PayPalPayment.completed_at,
        models.PayPalPayment.rental_id
    ).join(models.Bot, models.PayPalPayment.bot_id == models.Bot.id)
    
    if status_filter:
        query = query.filter(models.PayPalPayment.status == status_filter)
    
    return query.order_by(models.PayPalPayment.created_at.desc()).offset(skip).limit(limit).all()

# PayPal Configuration CRUD
def get_paypal_config(db: Session) -> models.PayPalConfig:
    """Get active PayPal configuration"""
    return db.query(models.PayPalConfig).filter(
        models.PayPalConfig.is_active == True
    ).first()

def create_paypal_config(db: Session, config_data: schemas.PayPalConfigCreate) -> models.PayPalConfig:
    """Create PayPal configuration"""
    # Deactivate existing configs
    db.query(models.PayPalConfig).update({"is_active": False})
    
    # Create new config
    db_config = models.PayPalConfig(**config_data.dict())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config

def update_paypal_config(
    db: Session, 
    config_id: int, 
    config_data: schemas.PayPalConfigCreate
) -> models.PayPalConfig:
    """Update PayPal configuration"""
    db_config = db.query(models.PayPalConfig).filter(models.PayPalConfig.id == config_id).first()
    if db_config:
        for key, value in config_data.dict().items():
            setattr(db_config, key, value)
        db.commit()
        db.refresh(db_config)
    return db_config

# PayPal Webhook Event CRUD
def create_webhook_event(db: Session, event_data: dict) -> models.PayPalWebhookEvent:
    """Create webhook event record"""
    db_event = models.PayPalWebhookEvent(
        id=event_data.get("id", str(uuid.uuid4())),
        event_type=event_data.get("event_type"),
        event_data=event_data,
        processed=False
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

def mark_webhook_processed(db: Session, webhook_id: str, payment_id: str = None):
    """Mark webhook event as processed"""
    db_event = db.query(models.PayPalWebhookEvent).filter(
        models.PayPalWebhookEvent.id == webhook_id
    ).first()
    if db_event:
        db_event.processed = True
        if payment_id:
            db_event.payment_id = payment_id
        db.commit()

# ========================
# Developer Exchange Credentials CRUD
# ========================

def create_developer_exchange_credentials(db: Session, credentials: schemas.DeveloperExchangeCredentialsCreate, user_id: int):
    """Create new exchange credentials for a developer"""
    
    # If this is set as default, unset other defaults for same exchange/type/network
    if credentials.is_default:
        db.query(models.DeveloperExchangeCredentials).filter(
            and_(
                models.DeveloperExchangeCredentials.user_id == user_id,
                models.DeveloperExchangeCredentials.exchange_type == credentials.exchange_type,
                models.DeveloperExchangeCredentials.credential_type == credentials.credential_type,
                models.DeveloperExchangeCredentials.network_type == credentials.network_type,
                models.DeveloperExchangeCredentials.is_default == True
            )
        ).update({"is_default": False})
    
    # Encrypt sensitive data (basic encryption - in production use proper encryption)
    encrypted_api_key = security.encrypt_sensitive_data(credentials.api_key)
    encrypted_api_secret = security.encrypt_sensitive_data(credentials.api_secret)
    encrypted_passphrase = security.encrypt_sensitive_data(credentials.passphrase) if credentials.passphrase else None
    
    db_credentials = models.DeveloperExchangeCredentials(
        user_id=user_id,
        exchange_type=credentials.exchange_type,
        credential_type=credentials.credential_type,
        network_type=credentials.network_type,
        name=credentials.name,
        api_key=encrypted_api_key,
        api_secret=encrypted_api_secret,
        passphrase=encrypted_passphrase,
        is_default=credentials.is_default,
        is_active=credentials.is_active
    )
    
    db.add(db_credentials)
    db.commit()
    db.refresh(db_credentials)
    return db_credentials

def get_user_developer_credentials(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """Get all credentials for a user"""
    return db.query(models.DeveloperExchangeCredentials).filter(
        and_(
            models.DeveloperExchangeCredentials.user_id == user_id,
            models.DeveloperExchangeCredentials.is_active == True
        )
    ).order_by(
        desc(models.DeveloperExchangeCredentials.is_default),
        models.DeveloperExchangeCredentials.exchange_type,
        models.DeveloperExchangeCredentials.credential_type,
        models.DeveloperExchangeCredentials.network_type
    ).offset(skip).limit(limit).all()

def get_developer_credentials_by_id(db: Session, credentials_id: int, user_id: int):
    """Get specific credentials by ID (only for the owner)"""
    return db.query(models.DeveloperExchangeCredentials).filter(
        and_(
            models.DeveloperExchangeCredentials.id == credentials_id,
            models.DeveloperExchangeCredentials.user_id == user_id,
            models.DeveloperExchangeCredentials.is_active == True
        )
    ).first()

def get_default_developer_credentials(db: Session, user_id: int, exchange_type: models.ExchangeType, 
                          credential_type: models.CredentialType, network_type: models.NetworkType):
    """Get default credentials for specific exchange/type/network combination"""
    return db.query(models.DeveloperExchangeCredentials).filter(
        and_(
            models.DeveloperExchangeCredentials.user_id == user_id,
            models.DeveloperExchangeCredentials.exchange_type == exchange_type,
            models.DeveloperExchangeCredentials.credential_type == credential_type,
            models.DeveloperExchangeCredentials.network_type == network_type,
            models.DeveloperExchangeCredentials.is_default == True,
            models.DeveloperExchangeCredentials.is_active == True
        )
    ).first()

def update_developer_exchange_credentials(db: Session, credentials_id: int, user_id: int, 
                              credentials_update: schemas.DeveloperExchangeCredentialsUpdate):
    """Update exchange credentials"""
    db_credentials = get_developer_credentials_by_id(db, credentials_id, user_id)
    if not db_credentials:
        return None
    
    # If setting as default, unset other defaults
    if credentials_update.is_default:
        db.query(models.DeveloperExchangeCredentials).filter(
            and_(
                models.DeveloperExchangeCredentials.user_id == user_id,
                models.DeveloperExchangeCredentials.exchange_type == db_credentials.exchange_type,
                models.DeveloperExchangeCredentials.credential_type == db_credentials.credential_type,
                models.DeveloperExchangeCredentials.network_type == db_credentials.network_type,
                models.DeveloperExchangeCredentials.is_default == True,
                models.DeveloperExchangeCredentials.id != credentials_id
            )
        ).update({"is_default": False})
    
    # Update fields
    for field, value in credentials_update.dict(exclude_unset=True).items():
        if field in ['api_key', 'api_secret', 'passphrase'] and value:
            # Encrypt sensitive data
            setattr(db_credentials, field, security.encrypt_sensitive_data(value))
        else:
            setattr(db_credentials, field, value)
    
    db.commit()
    db.refresh(db_credentials)
    return db_credentials

def delete_developer_exchange_credentials(db: Session, credentials_id: int, user_id: int):
    """Soft delete exchange credentials"""
    # Don't filter by is_active to allow deleting already soft-deleted credentials
    db_credentials = db.query(models.DeveloperExchangeCredentials).filter(
        and_(
            models.DeveloperExchangeCredentials.id == credentials_id,
            models.DeveloperExchangeCredentials.user_id == user_id
        )
    ).first()
    
    if not db_credentials:
        return None
    
    db_credentials.is_active = False
    db.commit()
    return db_credentials

def update_developer_credentials_last_used(db: Session, credentials_id: int, user_id: int):
    """Update last_used_at timestamp for credentials"""
    db_credentials = get_developer_credentials_by_id(db, credentials_id, user_id)
    if not db_credentials:
        return None
    
    db_credentials.last_used_at = func.now()
    db.commit()
    db.refresh(db_credentials)
    return db_credentials

def update_credentials_last_used(db: Session, credentials_id: int):
    """Update last_used_at timestamp"""
    db.query(models.DeveloperExchangeCredentials).filter(
        models.DeveloperExchangeCredentials.id == credentials_id
    ).update({"last_used_at": datetime.utcnow()})
    db.commit()

# --- Bot-Prompt CRUD ---

def get_bot_prompts(db: Session, bot_id: int) -> List[models.BotPrompt]:
    """Get all prompts attached to a bot"""
    return db.query(models.BotPrompt).filter(
        models.BotPrompt.bot_id == bot_id
    ).options(
        joinedload(models.BotPrompt.llm_prompt_template),  # Fixed: use llm_prompt_template not prompt_template
        joinedload(models.BotPrompt.bot)
    ).order_by(desc(models.BotPrompt.priority), desc(models.BotPrompt.attached_at)).all()

def get_prompt_bots(db: Session, prompt_id: int) -> List[models.BotPrompt]:
    """Get all bots using a specific prompt"""
    return db.query(models.BotPrompt).filter(
        models.BotPrompt.prompt_id == prompt_id
    ).options(
        joinedload(models.BotPrompt.bot),
        joinedload(models.BotPrompt.llm_prompt_template)  # Fixed: use llm_prompt_template not prompt_template
    ).order_by(desc(models.BotPrompt.priority), desc(models.BotPrompt.attached_at)).all()

def attach_prompt_to_bot(db: Session, bot_id: int, prompt_id: int, priority: int = 0, custom_override: str = None) -> models.BotPrompt:
    """Attach a prompt to a bot"""
    bot_prompt = models.BotPrompt(
        bot_id=bot_id,
        prompt_id=prompt_id,
        priority=priority,
        custom_override=custom_override,
        is_active=True
    )
    db.add(bot_prompt)
    db.commit()
    db.refresh(bot_prompt)
    return bot_prompt

def detach_prompt_from_bot(db: Session, bot_prompt_id: int):
    """Detach a prompt from a bot"""
    bot_prompt = db.query(models.BotPrompt).filter(models.BotPrompt.id == bot_prompt_id).first()
    if bot_prompt:
        db.delete(bot_prompt)
        db.commit()
    return bot_prompt

def update_bot_prompt(db: Session, bot_prompt_id: int, update_data: dict) -> models.BotPrompt:
    """Update bot-prompt relationship settings"""
    bot_prompt = db.query(models.BotPrompt).filter(models.BotPrompt.id == bot_prompt_id).first()
    if not bot_prompt:
        return None
    
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(bot_prompt, field, value)
    
    db.commit()
    db.refresh(bot_prompt)
    return bot_prompt

def get_suggested_prompts(db: Session, bot_id: int, limit: int = 10) -> List[models.LLMPromptTemplate]:
    """Get suggested prompts for a bot based on bot type and category"""
    bot = db.query(models.Bot).filter(models.Bot.id == bot_id).first()
    if not bot:
        return []
    
    # Get already attached prompt IDs
    attached_prompt_ids = db.query(models.BotPrompt.prompt_id).filter(
        models.BotPrompt.bot_id == bot_id
    ).subquery()
    
    # Build query based on bot characteristics
    query = db.query(models.LLMPromptTemplate).filter(
        models.LLMPromptTemplate.is_active == True,
        ~models.LLMPromptTemplate.id.in_(attached_prompt_ids)
    )
    
    # Smart suggestions based on bot type
    if bot.bot_type == "LLM":
        query = query.filter(models.LLMPromptTemplate.category == "TRADING")
    elif bot.bot_type == "TECHNICAL":
        query = query.filter(models.LLMPromptTemplate.category.in_(["TRADING", "ANALYSIS"]))
    elif bot.bot_type == "ML":
        query = query.filter(models.LLMPromptTemplate.category.in_(["ANALYSIS", "RISK_MANAGEMENT"]))
    
    return query.order_by(desc(models.LLMPromptTemplate.is_default), desc(models.LLMPromptTemplate.created_at)).limit(limit).all()

def get_suggested_bots(db: Session, prompt_id: int, limit: int = 10) -> List[models.Bot]:
    """Get suggested bots for a prompt"""
    prompt = db.query(models.LLMPromptTemplate).filter(models.LLMPromptTemplate.id == prompt_id).first()
    if not prompt:
        return []
    
    # Get bots already using this prompt
    attached_bot_ids = db.query(models.BotPrompt.bot_id).filter(
        models.BotPrompt.prompt_id == prompt_id
    ).subquery()
    
    # Build query based on prompt category
    query = db.query(models.Bot).filter(
        models.Bot.status == models.BotStatus.APPROVED,
        ~models.Bot.id.in_(attached_bot_ids)
    )
    
    # Smart suggestions based on prompt category
    if prompt.category == "TRADING":
        query = query.filter(models.Bot.bot_type.in_(["TECHNICAL", "LLM"]))
    elif prompt.category == "ANALYSIS":
        query = query.filter(models.Bot.bot_type.in_(["ML", "TECHNICAL"]))
    elif prompt.category == "RISK_MANAGEMENT":
        query = query.filter(models.Bot.bot_type.in_(["ML", "TECHNICAL"]))
    
    return query.order_by(desc(models.Bot.total_subscribers), desc(models.Bot.average_rating)).limit(limit).all()
