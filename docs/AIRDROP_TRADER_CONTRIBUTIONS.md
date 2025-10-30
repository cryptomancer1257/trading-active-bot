# Airdrop: Trader Contributions Category

## D. Trader Contributions (10% - 5M BOT)

Thay vì focus vào GitHub contributions, category này reward traders có strategies hiệu quả và đóng góp cho community thông qua việc chia sẻ strategies.

---

## 1. Submit Strategy Template (1,000-2,000 points = 10,000-20,000 BOT)

### Mục đích
Khuyến khích traders chia sẻ strategies profitable của họ để giúp community học hỏi và sử dụng.

### Yêu cầu

Strategy phải đáp ứng các tiêu chí sau:

| Tiêu chí | Yêu cầu tối thiểu |
|----------|-------------------|
| **Running Time** | ≥ 30 ngày |
| **ROI** | ≥ 10% |
| **Total Trades** | ≥ 50 trades |
| **Win Rate** | ≥ 50% |
| **Sharpe Ratio** | ≥ 1.0 |
| **Risk Management** | Phải có Stop Loss & Take Profit |

### Verification Method

**Auto-verify** dựa trên performance metrics từ database

```python
@router.post("/submit-strategy-template")
async def submit_strategy_template(
    submission: StrategyTemplateSubmission,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Traders submit their profitable strategies as templates
    """
    
    # Get bot using this strategy
    bot = db.query(Bot).filter(
        Bot.id == submission.bot_id,
        Bot.developer_id.in_(
            db.query(UserPrincipal.user_id).filter(
                UserPrincipal.principal_id == current_user.principal_id
            )
        )
    ).first()
    
    if not bot:
        raise HTTPException(status_code=404, detail='Bot not found')
    
    # Calculate strategy performance
    performance = calculate_strategy_performance(bot.id, db)
    
    # Check eligibility
    checks = {
        'running_days': performance['days_active'] >= 30,
        'positive_roi': performance['roi'] >= 0.10,  # 10% ROI
        'trade_count': performance['total_trades'] >= 50,
        'has_risk_management': bot.stop_loss and bot.take_profit,
        'win_rate': performance['win_rate'] >= 0.50,  # 50% win rate
        'sharpe_ratio': performance['sharpe_ratio'] >= 1.0
    }
    
    if not all(checks.values()):
        return {
            'success': False,
            'error': 'Strategy does not meet requirements',
            'checks': checks,
            'performance': performance
        }
    
    # Store submission for review
    template = StrategyTemplateSubmission(
        principal_id=current_user.principal_id,
        bot_id=bot.id,
        strategy_name=submission.name,
        description=submission.description,
        strategy_config=bot.strategy_config,
        performance_metrics=performance,
        checks_passed=True,
        status='pending_review',
        submitted_at=datetime.now()
    )
    db.add(template)
    db.commit()
    
    # Calculate points based on performance
    base_points = 1000
    performance_bonus = calculate_performance_bonus(performance)
    total_points = base_points + performance_bonus
    
    return {
        'submission_id': template.id,
        'status': 'pending_review',
        'checks': checks,
        'performance': performance,
        'estimated_points': total_points
    }
```

### Performance Calculation

```python
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
            'sharpe_ratio': 0
        }
    
    total_trades = len(trades)
    winning_trades = len([t for t in trades if t.realized_pnl > 0])
    
    total_pnl = sum(t.realized_pnl for t in trades)
    total_volume = sum(t.amount_usd for t in trades)
    
    # Calculate metrics
    first_trade = min(t.created_at for t in trades)
    days_active = (datetime.now() - first_trade).days
    
    # ROI calculation
    bot_obj = db.query(Bot).filter(Bot.id == bot_id).first()
    initial_capital = bot_obj.initial_capital or 1000
    roi = total_pnl / initial_capital
    
    # Win rate
    win_rate = winning_trades / total_trades if total_trades > 0 else 0
    
    # Sharpe ratio (simplified)
    returns = [t.realized_pnl / initial_capital for t in trades]
    avg_return = sum(returns) / len(returns)
    std_return = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
    sharpe_ratio = avg_return / std_return if std_return > 0 else 0
    
    # Max drawdown
    cumulative_pnl = []
    running_total = 0
    for trade in sorted(trades, key=lambda t: t.created_at):
        running_total += trade.realized_pnl
        cumulative_pnl.append(running_total)
    
    max_drawdown = 0
    peak = cumulative_pnl[0] if cumulative_pnl else 0
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
```

### Performance Bonus

Exceptional performance gets bonus points:

```python
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
```

**Scoring Examples:**

| Performance | Base | ROI Bonus | Win Rate Bonus | Sharpe Bonus | Volume Bonus | **Total** |
|-------------|------|-----------|----------------|--------------|--------------|-----------|
| Good | 1000 | 0 | 0 | 0 | 0 | **1000** |
| Great | 1000 | 100 | 150 | 100 | 150 | **1500** |
| Excellent | 1000 | 300 | 300 | 200 | 300 | **2000** |

---

## 2. Strategy Gets Adopted (50 points = 500 BOT per adoption)

### Mục đích
Reward strategy creators khi strategies của họ được traders khác sử dụng.

### Verification Method

**Auto-verify** - tracked automatically khi user tạo bot from template

```python
@router.post("/bots/create-from-template")
async def create_bot_from_template(
    template_id: int,
    bot_config: Dict[str, Any],
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create bot using approved strategy template"""
    
    # Get template
    template = db.query(StrategyTemplateSubmission).filter(
        StrategyTemplateSubmission.id == template_id,
        StrategyTemplateSubmission.status == 'approved'
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail='Template not found')
    
    # Create bot with template strategy
    bot = Bot(
        developer_id=current_user.id,
        name=bot_config['name'],
        strategy_type=template.strategy_config['strategy_type'],
        strategy_config=template.strategy_config,
        template_id=template_id,
        initial_capital=bot_config.get('initial_capital', 1000),
        status='ACTIVE'
    )
    db.add(bot)
    db.flush()
    
    # Track adoption
    adoption = StrategyAdoption(
        template_id=template_id,
        creator_principal=template.principal_id,
        adopter_principal=current_user.principal_id,
        adopter_bot_id=bot.id,
        adopted_at=datetime.now()
    )
    db.add(adoption)
    
    # Award points to strategy creator
    await award_points(
        db,
        template.principal_id,
        f'strategy_adoption_{adoption.id}',
        50,
        {
            'template_id': template_id,
            'template_name': template.strategy_name,
            'adopter_bot_id': bot.id,
            'adopter': current_user.principal_id
        }
    )
    
    # Update template stats
    template.adoption_count = (template.adoption_count or 0) + 1
    db.commit()
    
    return {
        'bot_id': bot.id,
        'template_used': template.strategy_name,
        'creator_awarded': True,
        'creator_points': 50
    }
```

### Database Models

```python
# Add to core/models.py

class StrategyTemplateSubmission(Base):
    """Strategy templates submitted by traders"""
    __tablename__ = "strategy_template_submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    principal_id = Column(String(255), nullable=False, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False)
    
    # Template info
    strategy_name = Column(String(255), nullable=False)
    description = Column(Text)
    strategy_config = Column(JSON, nullable=False)
    
    # Performance metrics
    performance_metrics = Column(JSON)
    
    # Verification
    checks_passed = Column(Boolean, default=False)
    status = Column(String(50), default='pending_review')  # pending_review, approved, rejected
    
    # Stats
    adoption_count = Column(Integer, default=0)
    
    # Timestamps
    submitted_at = Column(DateTime, server_default=func.now())
    reviewed_at = Column(DateTime)
    approved_by = Column(Integer, ForeignKey("users.id"))
    
    # Indexes
    __table_args__ = (
        Index('idx_strategy_submissions_principal', 'principal_id'),
        Index('idx_strategy_submissions_status', 'status'),
    )


class StrategyAdoption(Base):
    """Track when strategies are adopted by other traders"""
    __tablename__ = "strategy_adoptions"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("strategy_template_submissions.id"), nullable=False)
    creator_principal = Column(String(255), nullable=False, index=True)
    adopter_principal = Column(String(255), nullable=False, index=True)
    adopter_bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False)
    
    # Timestamps
    adopted_at = Column(DateTime, server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_strategy_adoptions_template', 'template_id'),
        Index('idx_strategy_adoptions_creator', 'creator_principal'),
    )
```

---

## 3. Monthly Performance Leaderboard (200-2000 points = 2,000-20,000 BOT)

### Mục đích
Khuyến khích competitive trading và reward top performers mỗi tháng.

### Verification Method

**Auto-verify** - Calculated and awarded monthly via cron job

### Scoring Algorithm

Performance score = weighted combination of:

- **ROI** (40%): Return on investment
- **Absolute P&L** (30%): Total profit
- **Win Rate** (20%): % winning trades
- **Activity** (10%): Number of trades

```python
@router.get("/leaderboard/monthly-performance")
async def get_monthly_leaderboard(db: Session = Depends(get_db)):
    """Calculate monthly leaderboard"""
    
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
        monthly_roi = monthly_pnl / bot.initial_capital if bot.initial_capital > 0 else 0
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
```

### Award Distribution

```python
@router.post("/admin/award-monthly-rankings")
async def award_monthly_rankings(
    admin: models.User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    Award points to top performers
    Run monthly via cron job
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
        'total_points': sum(awards.values())
    }
```

### Leaderboard Display

Frontend component để hiển thị rankings:

```typescript
// frontend/components/Leaderboard.tsx
interface LeaderboardEntry {
  rank: number;
  bot_name: string;
  principal_id: string;
  monthly_roi: number;
  monthly_pnl: number;
  win_rate: number;
  trades_count: number;
  points_awarded: number;
}

export function MonthlyLeaderboard() {
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  
  useEffect(() => {
    fetch('/api/airdrop/leaderboard/monthly-performance')
      .then(res => res.json())
      .then(data => setLeaderboard(data.leaderboard));
  }, []);
  
  return (
    <div className="leaderboard">
      <h2>🏆 Monthly Performance Rankings</h2>
      <table>
        <thead>
          <tr>
            <th>Rank</th>
            <th>Bot</th>
            <th>ROI</th>
            <th>P&L</th>
            <th>Win Rate</th>
            <th>Trades</th>
            <th>Points</th>
          </tr>
        </thead>
        <tbody>
          {leaderboard.map((entry, idx) => (
            <tr key={entry.bot_id}>
              <td>{idx + 1}</td>
              <td>{entry.bot_name}</td>
              <td>{(entry.monthly_roi * 100).toFixed(2)}%</td>
              <td>${entry.monthly_pnl.toFixed(2)}</td>
              <td>{(entry.win_rate * 100).toFixed(1)}%</td>
              <td>{entry.trades_count}</td>
              <td>{getPointsForRank(idx + 1)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

---

## Summary: Trader Contributions

| Task | Points | BOT Tokens | Verification | Frequency |
|------|--------|------------|--------------|-----------|
| **Submit Strategy Template** | 1,000-2,000 | 10,000-20,000 | Auto (performance) | One-time per strategy |
| **Strategy Adoption** | 50 per adoption | 500 per adoption | Auto (on bot creation) | Ongoing |
| **Monthly Rank #1** | 2,000 | 20,000 | Auto (monthly cron) | Monthly |
| **Monthly Rank #2** | 1,500 | 15,000 | Auto (monthly cron) | Monthly |
| **Monthly Rank #3** | 1,000 | 10,000 | Auto (monthly cron) | Monthly |
| **Monthly Rank #4-5** | 700 | 7,000 | Auto (monthly cron) | Monthly |
| **Monthly Rank #6-10** | 500 | 5,000 | Auto (monthly cron) | Monthly |
| **Monthly Rank #11-20** | 200 | 2,000 | Auto (monthly cron) | Monthly |

### Total Allocation: 5M BOT (10% of airdrop)

This rewards traders based on actual performance and contribution to the community, not coding skills.

