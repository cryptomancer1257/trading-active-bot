# file: api/endpoints/trader_contributions.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging

from core import models
from core.database import get_db
from core.security import get_current_active_user, get_current_active_admin
from core.models import (
    Bot, Transaction, UserPrincipal, StrategyTemplateSubmission, 
    StrategyAdoption, AirdropClaim
)

router = APIRouter(prefix="/trader-contributions", tags=["trader-contributions"])

logger = logging.getLogger(__name__)

# =====================================================
# PYDANTIC SCHEMAS
# =====================================================

class StrategyTemplateSubmissionRequest(BaseModel):
    bot_id: int
    name: str
    description: str

class StrategyTemplateResponse(BaseModel):
    id: int
    strategy_name: str
    description: str
    performance_metrics: Dict[str, Any]
    status: str
    adoption_count: int
    submitted_at: datetime

class CreateBotFromTemplateRequest(BaseModel):
    template_id: int
    name: str
    initial_capital: float = 1000

# =====================================================
# STRATEGY PERFORMANCE CALCULATION
# =====================================================

def calculate_strategy_performance(bot_id: int, db: Session) -> Dict[str, Any]:
    """Calculate comprehensive strategy performance metrics"""
    
    # Get all trades for this bot
    trades = db.query(Transaction).filter(
        Transaction.bot_id == bot_id,
        Transaction.status == 'COMPLETED'
    ).all()
    
    if not trades:
        return {
            'days_active': 0,
            'total_trades': 0,
            'roi': 0,
            'win_rate': 0,
            'sharpe_ratio': 0,
            'total_pnl': 0,
            'total_volume': 0,
            'max_drawdown': 0
        }
    
    total_trades = len(trades)
    winning_trades = len([t for t in trades if (t.realized_pnl or 0) > 0])
    
    total_pnl = sum(t.realized_pnl or 0 for t in trades)
    total_volume = sum(t.amount_usd or 0 for t in trades)
    
    # Calculate metrics
    first_trade = min(t.created_at for t in trades)
    days_active = (datetime.now() - first_trade).days
    
    # ROI calculation
    bot_obj = db.query(Bot).filter(Bot.id == bot_id).first()
    initial_capital = getattr(bot_obj, 'initial_capital', None) or 1000
    roi = total_pnl / initial_capital if initial_capital > 0 else 0
    
    # Win rate
    win_rate = winning_trades / total_trades if total_trades > 0 else 0
    
    # Sharpe ratio (simplified)
    returns = [(t.realized_pnl or 0) / initial_capital for t in trades]
    avg_return = sum(returns) / len(returns) if returns else 0
    
    variance = sum((r - avg_return) ** 2 for r in returns) / len(returns) if returns else 0
    std_return = variance ** 0.5
    sharpe_ratio = avg_return / std_return if std_return > 0 else 0
    
    # Max drawdown
    cumulative_pnl = []
    running_total = 0
    for trade in sorted(trades, key=lambda t: t.created_at):
        running_total += (trade.realized_pnl or 0)
        cumulative_pnl.append(running_total)
    
    max_drawdown = 0
    if cumulative_pnl:
        peak = cumulative_pnl[0]
        for pnl in cumulative_pnl:
            if pnl > peak:
                peak = pnl
            drawdown = (peak - pnl) / peak if peak > 0 else 0
            max_drawdown = max(max_drawdown, drawdown)
    
    return {
        'days_active': days_active,
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': total_trades - winning_trades,
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'roi': roi,
        'total_volume': total_volume,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'avg_trade_pnl': total_pnl / total_trades if total_trades > 0 else 0
    }

def calculate_performance_bonus(performance: Dict[str, Any]) -> int:
    """Calculate bonus points based on exceptional performance"""
    bonus = 0
    
    # ROI bonuses
    if performance['roi'] > 0.50:      # 50%+ ROI
        bonus += 500
    elif performance['roi'] > 0.30:    # 30%+ ROI
        bonus += 300
    elif performance['roi'] > 0.20:    # 20%+ ROI
        bonus += 100
    
    # Win rate bonuses
    if performance['win_rate'] > 0.70:     # 70%+ win rate
        bonus += 300
    elif performance['win_rate'] > 0.60:   # 60%+ win rate
        bonus += 150
    
    # Sharpe ratio bonuses (risk-adjusted returns)
    if performance['sharpe_ratio'] > 2.0:
        bonus += 200
    elif performance['sharpe_ratio'] > 1.5:
        bonus += 100
    
    # Volume bonuses
    if performance['total_volume'] > 100000:    # $100k+
        bonus += 300
    elif performance['total_volume'] > 50000:   # $50k+
        bonus += 150
    
    return min(bonus, 1000)  # Max 1000 bonus points

async def award_points(
    db: Session, 
    principal: str, 
    task_id: str, 
    points: int, 
    proof: Dict[str, Any]
):
    """Award points to user for completing a task"""
    
    # Check if user already earned points for this task
    existing_claim = db.query(AirdropClaim).filter(
        AirdropClaim.principal_id == principal,
        AirdropClaim.task_id == task_id
    ).first()
    
    if existing_claim:
        return  # Already awarded
    
    # Create claim record
    claim = AirdropClaim(
        principal_id=principal,
        task_id=task_id,
        points_earned=points,
        proof_data=proof,
        created_at=datetime.now()
    )
    
    db.add(claim)
    db.commit()

# =====================================================
# STRATEGY TEMPLATE SUBMISSION
# =====================================================

@router.post("/submit-strategy-template")
async def submit_strategy_template(
    submission: StrategyTemplateSubmissionRequest,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Submit a strategy template for review
    Requirements:
    - Strategy must have been running for at least 30 days
    - Must have positive ROI (>10%)
    - Must have completed at least 50 trades
    - Must have risk management parameters
    """
    
    principal = current_user.principal_id
    
    # Get bot and verify ownership
    bot = db.query(Bot).filter(
        Bot.id == submission.bot_id,
        Bot.developer_id.in_(
            db.query(UserPrincipal.user_id).filter(
                UserPrincipal.principal_id == principal
            )
        )
    ).first()
    
    if not bot:
        raise HTTPException(status_code=404, detail='Bot not found or not owned by user')
    
    # Check if already submitted
    existing = db.query(StrategyTemplateSubmission).filter(
        StrategyTemplateSubmission.bot_id == submission.bot_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail='Strategy already submitted for this bot')
    
    # Calculate strategy performance
    performance = calculate_strategy_performance(bot.id, db)
    
    # Check eligibility
    checks = {
        'running_days': performance['days_active'] >= 30,
        'positive_roi': performance['roi'] >= 0.10,  # 10% ROI
        'trade_count': performance['total_trades'] >= 50,
        'has_risk_management': hasattr(bot, 'stop_loss') and hasattr(bot, 'take_profit'),
        'win_rate': performance['win_rate'] >= 0.50,  # 50% win rate
        'sharpe_ratio': performance['sharpe_ratio'] >= 1.0
    }
    
    if not all(checks.values()):
        return {
            'success': False,
            'error': 'Strategy does not meet requirements',
            'checks': checks,
            'performance': performance,
            'requirements': {
                'min_days': 30,
                'min_roi': 0.10,
                'min_trades': 50,
                'min_win_rate': 0.50,
                'min_sharpe_ratio': 1.0
            }
        }
    
    # Store submission for review
    template = StrategyTemplateSubmission(
        principal_id=principal,
        bot_id=bot.id,
        strategy_name=submission.name,
        description=submission.description,
        strategy_config=bot.strategy_config or {},
        performance_metrics=performance,
        checks_passed=True,
        status='pending_review',
        submitted_at=datetime.now()
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    
    # Calculate points
    base_points = 1000
    performance_bonus = calculate_performance_bonus(performance)
    total_points = base_points + performance_bonus
    
    return {
        'success': True,
        'submission_id': template.id,
        'status': 'pending_review',
        'checks': checks,
        'performance': performance,
        'estimated_points': total_points,
        'message': 'Strategy submitted for review. You will receive points once approved.'
    }

@router.get("/my-strategy-templates", response_model=List[StrategyTemplateResponse])
async def get_my_strategy_templates(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[StrategyTemplateResponse]:
    """Get user's submitted strategy templates"""
    
    principal = current_user.principal_id
    
    templates = db.query(StrategyTemplateSubmission).filter(
        StrategyTemplateSubmission.principal_id == principal
    ).all()
    
    return [
        StrategyTemplateResponse(
            id=t.id,
            strategy_name=t.strategy_name,
            description=t.description or "",
            performance_metrics=t.performance_metrics or {},
            status=t.status,
            adoption_count=t.adoption_count or 0,
            submitted_at=t.submitted_at
        )
        for t in templates
    ]

@router.get("/strategy-templates", response_model=List[StrategyTemplateResponse])
async def get_approved_strategy_templates(
    db: Session = Depends(get_db)
) -> List[StrategyTemplateResponse]:
    """Get all approved strategy templates"""
    
    templates = db.query(StrategyTemplateSubmission).filter(
        StrategyTemplateSubmission.status == 'approved'
    ).order_by(StrategyTemplateSubmission.adoption_count.desc()).all()
    
    return [
        StrategyTemplateResponse(
            id=t.id,
            strategy_name=t.strategy_name,
            description=t.description or "",
            performance_metrics=t.performance_metrics or {},
            status=t.status,
            adoption_count=t.adoption_count or 0,
            submitted_at=t.submitted_at
        )
        for t in templates
    ]

# =====================================================
# STRATEGY ADOPTION
# =====================================================

@router.post("/create-bot-from-template")
async def create_bot_from_template(
    request: CreateBotFromTemplateRequest,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Create bot using approved strategy template"""
    
    principal = current_user.principal_id
    
    # Get template
    template = db.query(StrategyTemplateSubmission).filter(
        StrategyTemplateSubmission.id == request.template_id,
        StrategyTemplateSubmission.status == 'approved'
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail='Template not found or not approved')
    
    # Don't allow using own template
    if template.principal_id == principal:
        raise HTTPException(status_code=400, detail='Cannot use your own template')
    
    # Create bot with template strategy
    bot = Bot(
        developer_id=current_user.id,
        name=request.name,
        strategy_config=template.strategy_config,
        template_id=template.id,
        initial_capital=request.initial_capital,
        status='ACTIVE'
    )
    db.add(bot)
    db.flush()
    
    # Track adoption
    adoption = StrategyAdoption(
        template_id=template.id,
        creator_principal=template.principal_id,
        adopter_principal=principal,
        adopter_bot_id=bot.id,
        adopted_at=datetime.now()
    )
    db.add(adoption)
    
    # Award points to strategy creator (50 points = 500 BOT)
    await award_points(
        db,
        template.principal_id,
        f'strategy_adoption_{adoption.id}',
        50,
        {
            'template_id': template.id,
            'template_name': template.strategy_name,
            'adopter_bot_id': bot.id,
            'adopter': principal
        }
    )
    
    # Update template stats
    template.adoption_count = (template.adoption_count or 0) + 1
    db.commit()
    
    return {
        'success': True,
        'bot_id': bot.id,
        'template_used': template.strategy_name,
        'creator_awarded': True,
        'creator_points': 50,
        'message': f'Bot created using {template.strategy_name}. Creator received 50 points!'
    }

# =====================================================
# MONTHLY LEADERBOARD
# =====================================================

@router.get("/leaderboard/monthly-performance")
async def get_monthly_leaderboard(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Calculate monthly leaderboard based on bot performance"""
    
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0)
    
    # Get all active bots with trades this month
    bots_performance = []
    
    active_bots = db.query(Bot).filter(
        Bot.status == 'ACTIVE'
    ).all()
    
    for bot in active_bots:
        monthly_trades = db.query(Transaction).filter(
            Transaction.bot_id == bot.id,
            Transaction.created_at >= start_of_month,
            Transaction.status == 'COMPLETED'
        ).all()
        
        if not monthly_trades:
            continue
        
        # Calculate monthly metrics
        monthly_pnl = sum(t.realized_pnl or 0 for t in monthly_trades)
        initial_capital = getattr(bot, 'initial_capital', None) or 1000
        monthly_roi = monthly_pnl / initial_capital if initial_capital > 0 else 0
        winning_trades = len([t for t in monthly_trades if (t.realized_pnl or 0) > 0])
        win_rate = winning_trades / len(monthly_trades) if monthly_trades else 0
        
        # Calculate weighted score
        score = (
            monthly_roi * 40 +                  # 40% weight on ROI
            (monthly_pnl / 1000) * 30 +         # 30% weight on absolute P&L
            win_rate * 20 +                     # 20% weight on win rate
            len(monthly_trades) * 0.1           # 10% weight on activity
        )
        
        # Get owner principal
        owner = db.query(UserPrincipal).filter(
            UserPrincipal.user_id == bot.developer_id
        ).first()
        
        bots_performance.append({
            'bot_id': bot.id,
            'bot_name': bot.name,
            'principal_id': owner.principal_id if owner else None,
            'monthly_roi': monthly_roi,
            'monthly_pnl': monthly_pnl,
            'win_rate': win_rate,
            'trades_count': len(monthly_trades),
            'score': score
        })
    
    # Rank by score
    ranked = sorted(bots_performance, key=lambda x: x['score'], reverse=True)
    
    return {
        'month': start_of_month.strftime('%Y-%m'),
        'total_participants': len(ranked),
        'leaderboard': ranked[:50]  # Top 50
    }

@router.post("/admin/award-monthly-rankings")
async def award_monthly_rankings(
    admin: models.User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Award points to top performers (run monthly via cron)
    """
    
    leaderboard_data = await get_monthly_leaderboard(db)
    leaderboard = leaderboard_data['leaderboard']
    
    # Award tiers
    awards = {
        1: 2000,    # 1st place: 20,000 BOT
        2: 1500,    # 2nd place: 15,000 BOT
        3: 1000,    # 3rd place: 10,000 BOT
        4: 700,     # 4th place: 7,000 BOT
        5: 700,     # 5th place: 7,000 BOT
        6: 500,     # 6th-10th place: 5,000 BOT each
        7: 500,
        8: 500,
        9: 500,
        10: 500,
    }
    
    # 11-20th get 200 points each (2,000 BOT)
    for i in range(11, 21):
        awards[i] = 200
    
    month_str = datetime.now().strftime('%Y%m')
    awarded_count = 0
    
    for rank, entry in enumerate(leaderboard[:20], 1):
        if not entry['principal_id']:
            continue
        
        points = awards.get(rank, 0)
        
        if points > 0:
            await award_points(
                db,
                entry['principal_id'],
                f'monthly_ranking_{month_str}_rank{rank}',
                points,
                {
                    'rank': rank,
                    'month': month_str,
                    'score': entry['score'],
                    'monthly_roi': entry['monthly_roi'],
                    'monthly_pnl': entry['monthly_pnl'],
                    'win_rate': entry['win_rate'],
                    'bot_id': entry['bot_id']
                }
            )
            awarded_count += 1
    
    # Log event
    logger.info(f"Monthly rankings awarded for {month_str}: {awarded_count} traders")
    
    return {
        'success': True,
        'month': month_str,
        'awarded_count': awarded_count,
        'total_points_distributed': sum(awards.values()),
        'leaderboard': leaderboard[:20]
    }

