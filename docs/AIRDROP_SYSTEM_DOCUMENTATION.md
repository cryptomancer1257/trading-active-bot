# BOT Token Airdrop System Documentation

## Overview

The BOT Token Airdrop System is a comprehensive platform for distributing BOT tokens to users who complete various tasks across different categories. The system includes automated verification, manual review processes, and anti-sybil measures to ensure fair distribution.

## System Architecture

### Components

1. **Database Models** (`core/models.py`)
   - `AirdropTask`: Task definitions and configurations
   - `AirdropClaim`: Individual user claims and verification status
   - `UserActivity`: Activity tracking for daily streaks
   - `ReferralCode`: Referral code management
   - `AirdropReferral`: Referral tracking
   - `TelegramVerification`: Telegram verification codes
   - `AirdropContentSubmission`: Content submissions for review
   - `BotTemplateSubmission`: Bot template submissions
   - `AirdropConfig`: System configuration

2. **API Endpoints** (`api/endpoints/airdrop.py`)
   - Task verification endpoints
   - User status and statistics
   - Admin review endpoints
   - Configuration management

3. **Verification Services** (`services/airdrop_verification.py`)
   - Platform usage verification
   - Community engagement verification
   - SNS participation verification
   - Developer contributions verification

4. **Frontend Components**
   - `AirdropPage.tsx`: Main airdrop interface
   - `DiscordVerification.tsx`: Discord verification modal
   - `TelegramVerification.tsx`: Telegram verification modal
   - `ReferralComponent.tsx`: Referral system interface

5. **Telegram Bot** (`services/telegram_bot.py`)
   - Automated verification code generation
   - Channel membership verification

## Task Categories

### 1. Platform Usage (40% - 20M BOT)

#### Create Trading Bot (100 points = 1,000 BOT)
- **Verification**: Automatic database query
- **Trigger**: When user creates first bot
- **Data Source**: `bots` table

#### Complete First Trade (200 points = 2,000 BOT)
- **Verification**: Automatic transaction query
- **Trigger**: On first completed trade
- **Data Source**: `transactions` table

#### Trading Volume Milestones (50-1000 points)
- **Verification**: Aggregated transaction data
- **Tiers**: $100 (50 pts), $1K (200 pts), $10K (1000 pts)
- **Data Source**: `transactions` table aggregation

#### Profitable Bot Bonus (500 points = 5,000 BOT)
- **Verification**: P&L calculation
- **Trigger**: Daily calculation
- **Data Source**: `transactions` table P&L aggregation

#### Daily Active Streak (10 points/day)
- **Verification**: Activity log tracking
- **Trigger**: On login/activity
- **Data Source**: `user_activity` table

### 2. Community Engagement (30% - 15M BOT)

#### Discord Verified Member (50 points = 500 BOT)
- **Verification**: OAuth + Discord API
- **Method**: Check server membership via Discord API
- **Fallback**: Manual verification

#### Telegram Member (30 points = 300 BOT)
- **Verification**: Bot verification code
- **Method**: Telegram bot generates codes for channel members
- **Process**: User gets code from bot, enters on website

#### Twitter Follow + Retweet (20 points = 200 BOT)
- **Verification**: Twitter API v2
- **Method**: OAuth flow + API calls to check follow/retweet status

#### Content Creation (Variable points)
- **Verification**: Manual review + community voting
- **Tiers**: Blog post (50-200), Video (100-500), Guide (200-1000)
- **Process**: Submit content → Admin review → Points awarded

#### Referral Program (50 points = 500 BOT per referral)
- **Verification**: Referral code tracking
- **Method**: Generate unique codes, track usage
- **Process**: Referrer gets code → Referee uses code → Both get points

### 3. SNS Participation (20% - 10M BOT)

#### Participated in SNS Sale (100 points = 1,000 BOT)
- **Verification**: On-chain transaction query
- **Method**: Query IC blockchain for SNS swap participation
- **Bonus**: 1 point per 100 ICP committed (max 500 bonus)

#### Vote on Governance Proposals (50 points = 500 BOT per vote)
- **Verification**: SNS governance query
- **Method**: Query SNS governance canister for votes cast

### 4. Developer Contributions (10% - 5M BOT)

#### Submit Bot Template (1,000 points = 10,000 BOT)
- **Verification**: GitHub integration + code review
- **Requirements**: README, tests, documentation, proper structure
- **Process**: Submit GitHub repo → Automated checks → Admin review

#### Merged PR (500 points = 5,000 BOT)
- **Verification**: GitHub webhooks
- **Method**: Webhook triggers when PR is merged

#### Bug Report (100 points = 1,000 BOT)
- **Verification**: GitHub issues tracking
- **Method**: Webhook triggers when issue labeled as 'confirmed-bug'

## Verification Methods

### Automatic Verification
- **Platform Usage**: Database queries, transaction analysis
- **Discord**: OAuth + Discord API calls
- **Twitter**: OAuth + Twitter API calls
- **SNS Participation**: Blockchain queries
- **GitHub**: Webhook integration

### Semi-Automatic Verification
- **Telegram**: Bot generates codes, user enters on website
- **Referrals**: Code tracking system

### Manual Verification
- **Content Creation**: Admin review process
- **Bot Templates**: Admin review after automated checks

## Anti-Sybil Measures

### Rate Limiting
- 10 verification attempts per minute per IP
- 5 claims per IP address maximum

### Identity Verification
- KYC required for claims > 10,000 BOT tokens
- IP address tracking
- User agent logging

### Verification Validation
- Multiple verification methods for high-value tasks
- Cross-reference with existing user data
- Audit trails for all claims

## Configuration

### Environment Variables
```bash
# Discord
DISCORD_SERVER_ID=your_server_id
DISCORD_BOT_TOKEN=your_bot_token

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHANNEL_ID=your_channel_id

# Twitter
TWITTER_BEARER_TOKEN=your_bearer_token
OUR_TWITTER_ACCOUNT_ID=your_account_id
AIRDROP_ANNOUNCEMENT_TWEET_ID=tweet_id

# SNS
SNS_SWAP_CANISTER_ID=canister_id
SNS_GOVERNANCE_CANISTER_ID=canister_id
IC_MAINNET_URL=https://ic0.app

# GitHub
GITHUB_TOKEN=your_github_token
```

### Database Configuration
- Airdrop start/end dates
- Points to tokens conversion ratio
- Maximum claims per IP
- KYC threshold

## API Endpoints

### Public Endpoints
- `GET /api/airdrop/tasks` - Get available tasks
- `GET /api/airdrop/status/{principal_id}` - Get user status
- `GET /api/airdrop/stats` - Get campaign statistics

### Verification Endpoints
- `POST /api/airdrop/verify-bot-creation`
- `POST /api/airdrop/verify-first-trade`
- `POST /api/airdrop/verify-trading-volume`
- `POST /api/airdrop/verify-profitable-bot`
- `POST /api/airdrop/verify-daily-streak`
- `POST /api/airdrop/verify-discord`
- `POST /api/airdrop/verify-telegram`
- `POST /api/airdrop/verify-twitter`
- `POST /api/airdrop/verify-sns-participation`
- `POST /api/airdrop/verify-governance-votes`

### Submission Endpoints
- `POST /api/airdrop/submit-content`
- `POST /api/airdrop/submit-bot-template`
- `GET /api/airdrop/generate-referral-code`
- `POST /api/airdrop/track-referral`

### Admin Endpoints
- `POST /api/airdrop/admin/review-content/{submission_id}`
- `POST /api/airdrop/admin/review-template/{submission_id}`

## Frontend Integration

### Main Components
1. **AirdropPage**: Main interface with task list, user status, and statistics
2. **DiscordVerification**: Modal for Discord verification
3. **TelegramVerification**: Modal for Telegram verification
4. **ReferralComponent**: Referral code management

### Service Layer
- `airdropService.ts`: API client for all airdrop operations
- Type definitions for all data structures
- Error handling and loading states

## Setup Instructions

### 1. Database Setup
```bash
# Run the migration script
python scripts/init_airdrop_system.py
```

### 2. Configuration
Set up environment variables for all external services:
- Discord bot and server
- Telegram bot and channel
- Twitter API credentials
- SNS canister IDs
- GitHub token

### 3. Telegram Bot Setup
```bash
# Start the Telegram verification bot
python services/telegram_bot.py
```

### 4. Frontend Integration
Add the AirdropPage to your routing system:
```tsx
import AirdropPage from './pages/AirdropPage';

// Add to your router
<Route path="/airdrop" component={AirdropPage} />
```

### 5. API Integration
The airdrop router is already included in `main.py`:
```python
app.include_router(airdrop.router, prefix="/api/airdrop", tags=["Airdrop"])
```

## Monitoring and Analytics

### Key Metrics
- Total participants
- Points awarded
- Tokens distributed
- Verification success rates
- Task completion rates

### Admin Dashboard
- Pending content submissions
- Bot template reviews
- Claim verification status
- System statistics

## Security Considerations

### Data Protection
- All sensitive data encrypted
- API keys stored securely
- User data anonymized where possible

### Access Control
- Admin endpoints protected
- Rate limiting implemented
- Input validation on all endpoints

### Audit Trail
- All claims logged with timestamps
- Verification data stored
- IP addresses and user agents tracked

## Troubleshooting

### Common Issues

1. **Discord Verification Fails**
   - Check bot permissions
   - Verify server ID
   - Ensure bot is in server

2. **Telegram Bot Not Responding**
   - Check bot token
   - Verify channel ID
   - Ensure bot is added to channel

3. **Twitter Verification Issues**
   - Check API credentials
   - Verify account IDs
   - Check API rate limits

4. **Database Errors**
   - Check connection string
   - Verify table creation
   - Check migration status

### Debug Mode
Enable debug logging:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

### Planned Features
- Mobile app integration
- Advanced analytics dashboard
- Automated KYC integration
- Multi-language support
- Social media integration expansion

### Scalability Improvements
- Redis caching for verification results
- Background job processing
- Microservices architecture
- CDN integration for static assets

## Support

For technical support or questions about the airdrop system:
- Check the logs for error messages
- Verify all configuration settings
- Test individual verification methods
- Contact the development team

## License

This airdrop system is part of the BOT Token project and follows the same licensing terms.
