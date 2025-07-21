import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# file: api/endpoints/admin.py

from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional

from core import crud, models, schemas, security
from core.database import get_db

router = APIRouter()

# --- Dashboard & Statistics ---
@router.get("/dashboard", response_model=schemas.AdminStats)
def get_admin_dashboard(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_admin)
):
    """Get admin dashboard statistics"""
    return crud.get_admin_stats(db)

# --- Bot Management ---
@router.get("/bots", response_model=List[schemas.BotInDB])
def get_all_bots(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[schemas.BotStatus] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_admin)
):
    """Get all bots with optional status filtering"""
    return crud.get_all_bots(db, skip=skip, limit=limit, status_filter=status_filter)

@router.get("/bots/pending", response_model=List[schemas.BotInDB])
def get_pending_bots(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_admin)
):
    """Get all pending bots for approval"""
    return crud.get_bots_by_status(db, status=schemas.BotStatus.PENDING)

@router.put("/bots/{bot_id}/approve", response_model=schemas.BotInDB)
def approve_bot(
    bot_id: int,
    approval_data: schemas.AdminBotApproval,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_admin)
):
    """Approve or reject a bot"""
    bot = crud.get_bot_by_id(db, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    if approval_data.status not in [schemas.BotStatus.APPROVED, schemas.BotStatus.REJECTED]:
        raise HTTPException(status_code=400, detail="Status must be APPROVED or REJECTED")
    
    # Update bot status and approval info
    updated_bot = crud.update_bot_approval(
        db, bot_id=bot_id, status=approval_data.status, 
        approved_by=current_user.id, approval_notes=approval_data.approval_notes
    )
    
    # If approved, notify developer (could add notification system here)
    if approval_data.status == schemas.BotStatus.APPROVED:
        # TODO: Send notification to developer
        pass
    
    return updated_bot

@router.post("/bots", response_model=schemas.BotInDB, status_code=status.HTTP_201_CREATED)
def create_bot_as_admin(
    bot_in: schemas.BotCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_admin)
):
    """Admin creates a bot and auto-approves it"""
    return crud.create_bot(
        db=db, bot=bot_in, developer_id=current_user.id, 
        status=schemas.BotStatus.APPROVED, approved_by=current_user.id
    )

@router.post("/bots/with-code", response_model=schemas.BotInDB, status_code=status.HTTP_201_CREATED)
async def create_bot_as_admin_with_code(
    name: str = Form(...),
    description: str = Form(...),
    category_id: int = Form(...),
    price_per_month: float = Form(0.0),
    is_free: bool = Form(True),
    bot_type: str = Form("TECHNICAL"),
    config_schema: str = Form("{}"),
    default_config: str = Form("{}"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_admin)
):
    """Admin creates a bot with code file and auto-approves it"""
    try:
        # Import here to avoid circular imports
        from core.bot_manager import BotManager
        from services.s3_manager import S3Manager
        import json
        from decimal import Decimal
        
        # Initialize managers
        bot_manager = BotManager()
        s3_manager = S3Manager()
        
        # Validate file type
        if not file.filename or not file.filename.endswith('.py'):
            raise HTTPException(status_code=400, detail="Only Python files are allowed")
        
        # Read file content
        content = await file.read()
        code_content = content.decode('utf-8')
        
        # Validate bot code
        validation_result = bot_manager.validate_bot_code(code_content)
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Bot code validation failed: {validation_result['error']}"
            )
        
        # Parse bot type
        try:
            bot_type_enum = schemas.BotType(bot_type)
        except ValueError:
            bot_type_enum = schemas.BotType.TECHNICAL
        
        # Create bot data
        bot_data = schemas.BotCreate(
            name=name,
            description=description,
            category_id=category_id,
            price_per_month=Decimal(str(price_per_month)),
            is_free=is_free,
            bot_type=bot_type_enum,
            config_schema=json.loads(config_schema),
            default_config=json.loads(default_config)
        )
        
        # Create bot with S3 upload and auto-approve as admin
        bot_record = crud.save_bot_with_s3(
            db=db,
            bot_data=bot_data,
            developer_id=current_user.id,
            file_content=code_content,
            file_name=file.filename,
            status=schemas.BotStatus.APPROVED,  # Admin bots are auto-approved
            approved_by=current_user.id
        )
        
        return bot_record
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in config fields")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create bot: {str(e)}")

@router.delete("/bots/{bot_id}")
def delete_bot(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_admin)
):
    """Permanently delete a bot (admin only)"""
    bot = crud.get_bot_by_id(db, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Check if bot has active subscriptions
    active_subs = crud.get_active_subscriptions_for_bot(db, bot_id)
    if active_subs:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete bot with {len(active_subs)} active subscriptions"
        )
    
    crud.delete_bot(db, bot_id)
    return {"message": "Bot deleted successfully"}

# --- User Management ---
@router.get("/users", response_model=List[schemas.UserInDB])
def get_all_users(
    skip: int = 0,
    limit: int = 100,
    role_filter: Optional[schemas.UserRole] = None,
    active_only: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_admin)
):
    """Get all users with filtering options"""
    return crud.get_all_users(
        db, skip=skip, limit=limit, role_filter=role_filter, active_only=active_only
    )

@router.put("/users/{user_id}", response_model=schemas.UserInDB)
def update_user_as_admin(
    user_id: int,
    user_update: schemas.AdminUserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_admin)
):
    """Update user status and role (admin only)"""
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent admin from deactivating themselves
    if user_id == current_user.id and not user_update.is_active:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    
    return crud.update_user_by_admin(db, user_id=user_id, user_update=user_update)

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_admin)
):
    """Permanently delete a user (admin only)"""
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent admin from deleting themselves
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    # Check if user has active subscriptions
    active_subs = crud.get_active_subscriptions_for_user(db, user_id)
    if active_subs:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete user with {len(active_subs)} active subscriptions"
        )
    
    crud.delete_user(db, user_id)
    return {"message": "User deleted successfully"}

# --- Subscription Management ---
@router.get("/subscriptions", response_model=List[schemas.SubscriptionWithBot])
def get_all_subscriptions(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[schemas.SubscriptionStatus] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_admin)
):
    """Get all subscriptions with filtering"""
    return crud.get_all_subscriptions(
        db, skip=skip, limit=limit, status_filter=status_filter
    )

@router.put("/subscriptions/{subscription_id}/status")
def update_subscription_status_admin(
    subscription_id: int,
    status: schemas.SubscriptionStatus,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_admin)
):
    """Update subscription status (admin only)"""
    subscription = crud.get_subscription_by_id(db, subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    updated_sub = crud.update_subscription_status(db, subscription_id, status)
    return {"message": f"Subscription status updated to {status.value}"}

# --- Performance & Analytics ---
@router.get("/performance/bots", response_model=List[schemas.BotPerformanceInDB])
def get_bot_performance_overview(
    days: int = 30,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_admin)
):
    """Get performance overview for all bots"""
    return crud.get_bot_performance_overview(db, days=days, limit=limit)

@router.get("/performance/users")
def get_user_performance_overview(
    days: int = 30,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_admin)
):
    """Get performance overview for users"""
    return crud.get_user_performance_overview(db, days=days, limit=limit)

# --- Reviews Management ---
@router.get("/reviews", response_model=List[schemas.BotReviewWithUser])
def get_all_reviews(
    skip: int = 0,
    limit: int = 100,
    bot_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_admin)
):
    """Get all bot reviews"""
    return crud.get_all_reviews(db, skip=skip, limit=limit, bot_id=bot_id)

@router.delete("/reviews/{review_id}")
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_admin)
):
    """Delete a review (admin only)"""
    review = crud.get_bot_review(db, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    crud.delete_bot_review(db, review_id)
    return {"message": "Review deleted successfully"}

# --- System Health ---
@router.get("/health")
def system_health(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_admin)
):
    """Get system health status"""
    return crud.get_system_health(db)

# --- Logs & Monitoring ---
@router.get("/logs/errors")
def get_error_logs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_admin)
):
    """Get system error logs"""
    # This would typically connect to your logging system
    return {"message": "Error logs endpoint - integrate with your logging system"}

@router.get("/logs/performance")
def get_performance_logs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_admin)
):
    """Get performance logs"""
    return crud.get_system_performance_logs(db, skip=skip, limit=limit)