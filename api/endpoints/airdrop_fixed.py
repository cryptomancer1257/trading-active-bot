# file: api/endpoints/airdrop_fixed.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from core import crud, models, schemas, security
from core.database import get_db
from core.models import (
    AirdropTask, AirdropClaim, UserActivity, ReferralCode, AirdropReferral,
    TelegramVerification, AirdropContentSubmission, BotTemplateSubmission,
    AirdropConfig, Bot, Transaction, UserPrincipal
)
from core.security import get_current_active_user
from core.schemas import (
    AirdropTaskResponse, AirdropClaimRequest, AirdropClaimResponse,
    VerificationResult, DiscordVerification, TelegramVerificationRequest,
    ContentSubmission, BotTemplateSubmissionRequest, ReferralCodeResponse,
    AirdropStats, UserAirdropStatus
)

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/airdrop", tags=["airdrop"])

# Add rate limiting to router
router.state.limiter = limiter
router.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

logger = logging.getLogger(__name__)

# =====================================================
# AIRDROP CONFIGURATION
# =====================================================

@router.get("/config")
async def get_airdrop_config(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get current airdrop configuration"""
    
    config = db.query(AirdropConfig).first()
    if not config:
        # Return default config if none exists
        return {
            "is_active": False,
            "start_date": None,
            "end_date": None,
            "total_tokens": 50000000,  # 50M BOT
            "tokens_per_point": 10,
            "max_claim_per_user": 1000000  # 1M BOT max per user
        }
    
    return {
        "is_active": config.is_active,
        "start_date": config.start_date,
        "end_date": config.end_date,
        "total_tokens": config.total_tokens,
        "tokens_per_point": config.tokens_per_point,
        "max_claim_per_user": config.max_claim_per_user
    }

@router.get("/stats", response_model=AirdropStats)
async def get_airdrop_stats(db: Session = Depends(get_db)) -> AirdropStats:
    """Get airdrop statistics"""
    
    total_participants = db.query(AirdropClaim).count()
    total_claimed = db.query(func.sum(AirdropClaim.amount_claimed)).scalar() or 0
    total_tasks_completed = db.query(func.sum(AirdropClaim.tasks_completed)).scalar() or 0
    
    return AirdropStats(
        total_participants=total_participants,
        total_claimed=total_claimed,
        total_tasks_completed=total_tasks_completed,
        average_claim=total_claimed / total_participants if total_participants > 0 else 0
    )

# =====================================================
# TASK MANAGEMENT
# =====================================================

@router.get("/tasks", response_model=List[AirdropTaskResponse])
async def get_airdrop_tasks(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[AirdropTaskResponse]:
    """Get all available airdrop tasks"""
    
    principal = current_user.principal_id
    tasks = db.query(AirdropTask).filter(AirdropTask.is_active == True).all()
    
    # Check completion status for each task
    task_responses = []
    for task in tasks:
        # Check if user has completed this task
        claim = db.query(AirdropClaim).filter(
            AirdropClaim.principal_id == principal,
            AirdropClaim.task_id == task.id
        ).first()
        
        task_responses.append(AirdropTaskResponse(
            id=task.id,
            name=task.name,
            description=task.description,
            points=task.points,
            category=task.category,
            is_active=task.is_active,
            is_completed=claim is not None,
            completed_at=claim.created_at if claim else None
        ))
    
    return task_responses

# =====================================================
# PLATFORM USAGE VERIFICATION
# =====================================================

@router.post("/verify-bot-creation")
async def verify_bot_creation(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> VerificationResult:
    """Verify user has created a trading bot"""
    
    principal = current_user.principal_id
    bot_count = db.query(Bot).filter(
        Bot.developer_id.in_(
            db.query(UserPrincipal.user_id).filter(
                UserPrincipal.principal_id == principal
            )
        )
    ).count()
    
    if bot_count > 0:
        # Award points
        await award_points(db, principal, 'bot_creation', 100, {'bot_count': bot_count})
        return VerificationResult(verified=True, points=100, message=f"Created {bot_count} bot(s)")
    
    return VerificationResult(verified=False, points=0, message="No bots created")

@router.post("/verify-first-trade")
async def verify_first_trade(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> VerificationResult:
    """Verify user has completed their first trade"""
    
    principal = current_user.principal_id
    trade = db.query(Transaction).join(UserPrincipal).filter(
        UserPrincipal.principal_id == principal,
        Transaction.status == 'COMPLETED'
    ).first()
    
    if trade:
        await award_points(db, principal, 'first_trade', 200, {'trade_id': trade.id})
        return VerificationResult(verified=True, points=200, message="First trade completed")
    
    return VerificationResult(verified=False, points=0, message="No trades completed")

@router.post("/verify-trading-volume")
async def verify_trading_volume(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> VerificationResult:
    """Verify user's trading volume milestones"""
    
    principal = current_user.principal_id
    total_volume = db.query(func.sum(Transaction.amount_usd)).join(UserPrincipal).filter(
        UserPrincipal.principal_id == principal,
        Transaction.status == 'COMPLETED'
    ).scalar() or 0
    
    # Calculate points based on volume
    points = 0
    if total_volume >= 10000:
        points = 1000
    elif total_volume >= 1000:
        points = 200
    elif total_volume >= 100:
        points = 50
    
    if points > 0:
        await award_points(db, principal, 'trading_volume', points, {'volume': total_volume})
        return VerificationResult(verified=True, points=points, message=f"Volume: ${total_volume:,.2f}")
    
    return VerificationResult(verified=False, points=0, message=f"Volume: ${total_volume:,.2f}")

# =====================================================
# COMMUNITY ENGAGEMENT VERIFICATION
# =====================================================

@router.post("/verify-discord")
async def verify_discord(
    discord_data: DiscordVerification,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> VerificationResult:
    """Verify Discord membership"""
    
    principal = current_user.principal_id
    
    # In a real implementation, you would verify with Discord API
    # For now, we'll simulate verification
    is_member = True  # Replace with actual Discord API verification
    
    if is_member:
        await award_points(db, principal, 'discord_member', 50, {'discord_id': discord_data.discord_id})
        return VerificationResult(verified=True, points=50, message="Discord verified")
    
    return VerificationResult(verified=False, points=0, message="Discord verification failed")

@router.post("/verify-telegram")
async def verify_telegram(
    telegram_data: TelegramVerificationRequest,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> VerificationResult:
    """Verify Telegram membership using verification code"""
    
    principal = current_user.principal_id
    
    # Verify code
    verification = db.query(TelegramVerification).filter(
        TelegramVerification.code == telegram_data.code,
        TelegramVerification.used == False,
        TelegramVerification.expires_at > datetime.now()
    ).first()
    
    if verification:
        verification.used = True
        verification.used_at = datetime.now()
        verification.principal_id = principal
        db.commit()
        
        await award_points(db, principal, 'telegram_member', 30, {'telegram_id': verification.telegram_id})
        return VerificationResult(verified=True, points=30, message="Telegram verified")
    
    return VerificationResult(verified=False, points=0, message="Invalid verification code")

# =====================================================
# REFERRAL SYSTEM
# =====================================================

@router.get("/referral-code", response_model=ReferralCodeResponse)
async def get_referral_code(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ReferralCodeResponse:
    """Get or generate referral code for user"""
    
    principal = current_user.principal_id
    
    # Check if user already has a code
    existing_code = db.query(ReferralCode).filter(
        ReferralCode.referrer_principal == principal
    ).first()
    
    if existing_code:
        return ReferralCodeResponse(
            code=existing_code.code,
            referral_count=existing_code.referral_count,
            points_earned=existing_code.points_earned
        )
    
    # Generate new code
    import secrets
    import string
    code = ''.join(secrets.choices(string.ascii_uppercase + string.digits, k=8))
    
    referral_code = ReferralCode(
        referrer_principal=principal,
        code=code,
        created_at=datetime.now()
    )
    
    db.add(referral_code)
    db.commit()
    
    return ReferralCodeResponse(
        code=code,
        referral_count=0,
        points_earned=0
    )

@router.post("/use-referral")
async def use_referral_code(
    referral_code: str,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Use a referral code"""
    
    principal = current_user.principal_id
    
    # Find referral code
    code = db.query(ReferralCode).filter(
        ReferralCode.code == referral_code
    ).first()
    
    if not code:
        raise HTTPException(status_code=400, detail="Invalid referral code")
    
    if code.referrer_principal == principal:
        raise HTTPException(status_code=400, detail="Cannot use your own referral code")
    
    # Check if user already used a referral
    existing_referral = db.query(AirdropReferral).filter(
        AirdropReferral.referee_principal == principal
    ).first()
    
    if existing_referral:
        raise HTTPException(status_code=400, detail="Already used a referral code")
    
    # Create referral record
    referral = AirdropReferral(
        referrer_principal=code.referrer_principal,
        referee_principal=principal,
        referral_code_id=code.id,
        referral_code_value=referral_code
    )
    
    db.add(referral)
    db.commit()
    
    return {
        "success": True,
        "message": "Referral code used successfully",
        "referrer": code.referrer_principal
    }

# =====================================================
# CLAIMING SYSTEM
# =====================================================

@router.post("/claim", response_model=AirdropClaimResponse)
@limiter.limit("5/minute")
async def claim_airdrop(
    request: Request,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> AirdropClaimResponse:
    """Claim airdrop tokens"""
    
    principal = current_user.principal_id
    
    # Check if user already claimed
    existing_claim = db.query(AirdropClaim).filter(
        AirdropClaim.principal_id == principal
    ).first()
    
    if existing_claim:
        raise HTTPException(status_code=400, detail="Already claimed airdrop")
    
    # Calculate total points earned
    total_points = calculate_user_points(db, principal)
    
    if total_points == 0:
        raise HTTPException(status_code=400, detail="No points earned")
    
    # Calculate token amount (10 BOT per point)
    tokens_per_point = 10
    amount_claimed = total_points * tokens_per_point
    
    # Create claim record
    claim = AirdropClaim(
        principal_id=principal,
        amount_claimed=amount_claimed,
        tasks_completed=total_points // 100,  # Assuming 100 points per task
        claimed_at=datetime.now(),
        ip_address=request.client.host
    )
    
    db.add(claim)
    db.commit()
    
    return AirdropClaimResponse(
        success=True,
        amount_claimed=amount_claimed,
        tasks_completed=claim.tasks_completed,
        claimed_at=claim.claimed_at
    )

@router.get("/status", response_model=UserAirdropStatus)
async def get_user_status(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> UserAirdropStatus:
    """Get user's airdrop status"""
    
    principal = current_user.principal_id
    
    # Get user's claims
    claims = db.query(AirdropClaim).filter(
        AirdropClaim.principal_id == principal
    ).all()
    
    total_claimed = sum(claim.amount_claimed for claim in claims)
    total_tasks = sum(claim.tasks_completed for claim in claims)
    
    # Calculate current points
    current_points = calculate_user_points(db, principal)
    
    return UserAirdropStatus(
        total_claimed=total_claimed,
        total_tasks_completed=total_tasks,
        current_points=current_points,
        can_claim=len(claims) == 0 and current_points > 0
    )

# =====================================================
# HELPER FUNCTIONS
# =====================================================

async def award_points(db: Session, principal: str, task_id: str, points: int, proof: Dict[str, Any]):
    """Award points to user for completing a task"""
    
    # Check if user already earned points for this task
    existing_claim = db.query(AirdropClaim).filter(
        AirdropClaim.principal_id == principal,
        AirdropClaim.task_id == task_id
    ).first()
    
    if existing_claim:
        return  # Already awarded
    
    # Create or update claim record
    claim = AirdropClaim(
        principal_id=principal,
        task_id=task_id,
        points_earned=points,
        proof_data=proof,
        created_at=datetime.now()
    )
    
    db.add(claim)
    db.commit()

def calculate_user_points(db: Session, principal: str) -> int:
    """Calculate total points earned by user"""
    
    total_points = db.query(func.sum(AirdropClaim.points_earned)).filter(
        AirdropClaim.principal_id == principal
    ).scalar() or 0
    
    return total_points
