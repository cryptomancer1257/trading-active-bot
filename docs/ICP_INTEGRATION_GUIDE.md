# 🌐 ICP Marketplace Integration Guide

## Overview

This guide provides comprehensive instructions for integrating an Internet Computer Protocol (ICP) marketplace with the Bot Trading System. The integration enables seamless bot rental, user management, and trading execution across both platforms.

## 🏗️ Integration Architecture

### System Flow
```
┌─────────────────┐    HTTP Outcalls    ┌─────────────────┐
│  ICP Marketplace │ ◄─────────────────► │ Bot Trading API │
│   (Canisters)    │                     │   (FastAPI)     │
└─────────────────┘                     └─────────────────┘
         │                                       │
         ▼                                       ▼
┌─────────────────┐                     ┌─────────────────┐
│  ICP Frontend   │                     │     MySQL       │
│ (React/Svelte)  │                     │   Database      │
└─────────────────┘                     └─────────────────┘
```

### Data Synchronization
- **User Identity**: ICP Principal ID ↔ Bot System User Mapping
- **Bot Registrations**: Marketplace Listings ↔ Bot System Subscriptions
- **Trading Status**: Real-time sync via API calls
- **Payment Processing**: ICP Tokens → Bot Service Activation

---

## 🔐 Authentication Setup

### 1. Marketplace API Key Configuration

Register your ICP marketplace with the Bot Trading System:

```typescript
// ICP Canister Configuration
const BOT_TRADING_API = {
  base_url: "https://api.bot-marketplace.com",
  api_key: "marketplace_dev_api_key_12345", // Provided by Bot Trading team
  timeout: 30000 // 30 seconds
};
```

### 2. HTTP Outcall Setup

Configure HTTP outcalls in your ICP canister:

```rust
// Rust Canister Example
use ic_cdk::api::management_canister::http_request::{
    CanisterHttpRequestArgument, HttpHeader, HttpMethod, HttpResponse,
};

#[update]
async fn call_bot_api(
    method: String,
    url: String,
    headers: Vec<(String, String)>,
    body: Option<Vec<u8>>,
) -> Result<HttpResponse, String> {
    let request_headers: Vec<HttpHeader> = headers
        .into_iter()
        .map(|(k, v)| HttpHeader { name: k, value: v })
        .collect();

    let request = CanisterHttpRequestArgument {
        url,
        method: match method.as_str() {
            "GET" => HttpMethod::GET,
            "POST" => HttpMethod::POST,
            "PUT" => HttpMethod::PUT,
            _ => return Err("Unsupported HTTP method".to_string()),
        },
        body,
        max_response_bytes: Some(2048),
        transform: None,
        headers: request_headers,
    };

    ic_cdk::api::management_canister::http_request::http_request(request)
        .await
        .map_err(|e| format!("HTTP request failed: {:?}", e.1))
        .map(|(response,)| response)
}
```

---

## 🚀 Implementation Phases

### Phase 1: Bot Registration

#### Step 1: Register Bot Templates

When adding new bots to your marketplace, register them with the Bot Trading System:

```typescript
// TypeScript/JavaScript Frontend
interface BotRegistrationRequest {
  user_principal_id: string;
  bot_id: number;
  marketplace_name: string;
  marketplace_description: string;
  price_on_marketplace: string;
}

const registerBotTemplate = async (botData: BotRegistrationRequest) => {
  const response = await fetch(`${BOT_TRADING_API.base_url}/bots/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': BOT_TRADING_API.api_key,
    },
    body: JSON.stringify(botData),
  });

  if (!response.ok) {
    throw new Error(`Bot registration failed: ${response.statusText}`);
  }

  return await response.json();
};

// Usage Example
const newBot = await registerBotTemplate({
  user_principal_id: "marketplace-system",
  bot_id: 1,
  marketplace_name: "Advanced Futures Trading Bot",
  marketplace_description: "AI-powered bot with LLM integration",
  price_on_marketplace: "50.00"
});
```

#### Step 2: Store Bot Information on ICP

```rust
// Rust Canister - Store bot data
#[derive(Clone, Debug, CandidType, Deserialize)]
struct MarketplaceBot {
    id: u64,
    name: String,
    description: String,
    price: u64, // Price in ICP tokens (scaled by 1e8)
    bot_system_id: u64,
    bot_api_key: String,
    is_active: bool,
    created_at: u64,
}

thread_local! {
    static MARKETPLACE_BOTS: RefCell<BTreeMap<u64, MarketplaceBot>> = RefCell::new(BTreeMap::new());
}

#[update]
async fn add_marketplace_bot(
    name: String,
    description: String,
    price: u64,
    bot_system_id: u64,
) -> Result<u64, String> {
    // Register with Bot Trading System
    let registration_response = call_bot_api(
        "POST".to_string(),
        format!("{}/bots/register", BOT_TRADING_API.base_url),
        vec![
            ("Content-Type".to_string(), "application/json".to_string()),
            ("X-API-Key".to_string(), BOT_TRADING_API.api_key.clone()),
        ],
        Some(serde_json::to_vec(&json!({
            "user_principal_id": "marketplace-system",
            "bot_id": bot_system_id,
            "marketplace_name": name,
            "marketplace_description": description,
            "price_on_marketplace": (price as f64 / 1e8).to_string()
        })).unwrap()),
    ).await?;

    let bot_data: serde_json::Value = serde_json::from_slice(&registration_response.body)
        .map_err(|e| format!("Failed to parse response: {}", e))?;

    // Store in ICP
    let bot_id = MARKETPLACE_BOTS.with(|bots| {
        let mut bots = bots.borrow_mut();
        let id = bots.len() as u64 + 1;
        bots.insert(id, MarketplaceBot {
            id,
            name,
            description,
            price,
            bot_system_id,
            bot_api_key: bot_data["api_key"].as_str().unwrap_or("").to_string(),
            is_active: true,
            created_at: ic_cdk::api::time(),
        });
        id
    });

    Ok(bot_id)
}
```

### Phase 2: User Bot Rental

#### Step 3: User Payment Processing

```rust
// Handle ICP token payments for bot rentals
#[update]
async fn rent_bot(
    bot_id: u64,
    duration_days: u64,
    payment_amount: u64,
) -> Result<String, String> {
    let caller = ic_cdk::caller();
    
    // Verify payment (implement ICRC-1 token transfer verification)
    let payment_verified = verify_payment(caller, payment_amount).await?;
    
    if !payment_verified {
        return Err("Payment verification failed".to_string());
    }

    // Get bot details
    let bot = MARKETPLACE_BOTS.with(|bots| {
        bots.borrow().get(&bot_id).cloned()
    }).ok_or("Bot not found")?;

    // Register user with Bot Trading System
    let registration_response = call_bot_api(
        "POST".to_string(),
        format!("{}/bots/register", BOT_TRADING_API.base_url),
        vec![
            ("Content-Type".to_string(), "application/json".to_string()),
            ("X-API-Key".to_string(), BOT_TRADING_API.api_key.clone()),
        ],
        Some(serde_json::to_vec(&json!({
            "user_principal_id": caller.to_string(),
            "bot_id": bot.bot_system_id,
            "marketplace_name": format!("User Bot - {}", bot.name),
            "marketplace_description": "Personal bot instance"
        })).unwrap()),
    ).await?;

    let response_data: serde_json::Value = serde_json::from_slice(&registration_response.body)
        .map_err(|e| format!("Failed to parse response: {}", e))?;

    // Store rental record
    let rental_id = store_user_rental(
        caller,
        bot_id,
        duration_days,
        response_data["api_key"].as_str().unwrap_or("").to_string(),
    );

    Ok(rental_id)
}
```

#### Step 4: Exchange Credentials Management

```typescript
// Frontend - User enters exchange credentials
interface ExchangeCredentials {
  exchange: 'BINANCE' | 'COINBASE' | 'KRAKEN';
  api_key: string;
  api_secret: string;
  api_passphrase?: string;
  is_testnet: boolean;
}

const storeUserCredentials = async (
  userPrincipal: string,
  credentials: ExchangeCredentials
) => {
  // First, encrypt credentials locally (optional extra security)
  const encryptedCredentials = await encryptCredentials(credentials);
  
  // Store on ICP (encrypted)
  await marketplaceActor.store_user_credentials(
    userPrincipal,
    encryptedCredentials
  );
  
  // Send to Bot Trading System
  const response = await fetch(`${BOT_TRADING_API.base_url}/exchange-credentials/store-by-principal`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': BOT_TRADING_API.api_key,
    },
    body: JSON.stringify({
      principal_id: userPrincipal,
      exchange: credentials.exchange,
      api_key: credentials.api_key,
      api_secret: credentials.api_secret,
      api_passphrase: credentials.api_passphrase,
      is_testnet: credentials.is_testnet,
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to store credentials');
  }

  return await response.json();
};
```

### Phase 3: Trading Execution

#### Step 5: Start Bot Trading

```rust
// Canister function to start trading
#[update]
async fn start_trading(
    user_principal: Principal,
    config: TradingConfig,
) -> Result<String, String> {
    // Verify user has active rental
    let rental = get_user_active_rental(user_principal)?;
    
    // Call Bot Trading System
    let response = call_bot_api(
        "POST".to_string(),
        format!("{}/api/futures-bot/execute", BOT_TRADING_API.base_url),
        vec![
            ("Content-Type".to_string(), "application/json".to_string()),
        ],
        Some(serde_json::to_vec(&json!({
            "user_principal_id": user_principal.to_string(),
            "config": config
        })).unwrap()),
    ).await?;

    let result: serde_json::Value = serde_json::from_slice(&response.body)
        .map_err(|e| format!("Failed to parse response: {}", e))?;

    // Store task ID for monitoring
    let task_id = result["task_id"].as_str().unwrap_or("").to_string();
    store_trading_task(user_principal, task_id.clone());

    Ok(task_id)
}

#[derive(Clone, Debug, CandidType, Deserialize)]
struct TradingConfig {
    trading_pair: String,
    leverage: u8,
    timeframes: Vec<String>,
    use_llm_analysis: bool,
    auto_confirm: bool,
    stop_loss_pct: f64,
    take_profit_pct: f64,
    position_size_pct: f64,
}
```

#### Step 6: Monitor Trading Status

```typescript
// Frontend monitoring component
const TradingMonitor: React.FC<{ userPrincipal: string }> = ({ userPrincipal }) => {
  const [tradingStatus, setTradingStatus] = useState(null);
  const [activeTasks, setActiveTasks] = useState([]);

  useEffect(() => {
    const monitorTrading = async () => {
      try {
        // Get user's bot status
        const response = await fetch(
          `${BOT_TRADING_API.base_url}/api/futures-bot/status?user_principal_id=${userPrincipal}`
        );
        
        if (response.ok) {
          const status = await response.json();
          setTradingStatus(status);
        }

        // Get active task statuses
        const tasks = await Promise.all(
          activeTasks.map(async (taskId) => {
            const taskResponse = await fetch(
              `${BOT_TRADING_API.base_url}/api/futures-bot/task-status/${taskId}`
            );
            return taskResponse.ok ? await taskResponse.json() : null;
          })
        );

        setActiveTasks(tasks.filter(Boolean));
      } catch (error) {
        console.error('Monitoring error:', error);
      }
    };

    const interval = setInterval(monitorTrading, 10000); // Every 10 seconds
    return () => clearInterval(interval);
  }, [userPrincipal, activeTasks]);

  return (
    <div className="trading-monitor">
      <h3>Trading Status</h3>
      {tradingStatus && (
        <div>
          <p>Active Tasks: {tradingStatus.active_tasks}</p>
          <p>Total Trades: {tradingStatus.total_trades}</p>
          <p>Win Rate: {tradingStatus.win_rate}%</p>
          <p>Total P&L: {tradingStatus.total_pnl}</p>
        </div>
      )}
      
      <h4>Recent Tasks</h4>
      {activeTasks.map((task) => (
        <div key={task.task_id} className="task-status">
          <p>Status: {task.status}</p>
          <p>Progress: {task.progress}%</p>
          {task.result && (
            <p>Result: {task.result.action} - {task.result.pnl}</p>
          )}
        </div>
      ))}
    </div>
  );
};
```

---

## 🔄 Real-time Updates

### Webhook Integration

Configure webhooks to receive real-time trading updates:

```rust
// Canister webhook handler
#[update]
async fn handle_trading_webhook(
    event_type: String,
    user_principal_id: String,
    data: serde_json::Value,
) -> Result<(), String> {
    match event_type.as_str() {
        "trade.executed" => {
            // Update user's trading statistics
            update_user_trade_stats(
                Principal::from_text(&user_principal_id).unwrap(),
                data,
            );
        },
        "bot.stopped" => {
            // Handle bot stopping
            handle_bot_stopped(
                Principal::from_text(&user_principal_id).unwrap(),
                data,
            );
        },
        "error.occurred" => {
            // Handle trading errors
            handle_trading_error(
                Principal::from_text(&user_principal_id).unwrap(),
                data,
            );
        },
        _ => return Err("Unknown event type".to_string()),
    }
    
    Ok(())
}
```

### WebSocket Alternative

For real-time updates without webhooks:

```typescript
// Frontend polling strategy
const useRealTimeUpdates = (userPrincipal: string) => {
  const [updates, setUpdates] = useState([]);

  useEffect(() => {
    let eventSource: EventSource;

    const connectToUpdates = () => {
      // Use Server-Sent Events or polling
      eventSource = new EventSource(
        `${BOT_TRADING_API.base_url}/stream/trading-updates?user_principal_id=${userPrincipal}`
      );

      eventSource.onmessage = (event) => {
        const update = JSON.parse(event.data);
        setUpdates(prev => [update, ...prev.slice(0, 99)]); // Keep last 100 updates
      };

      eventSource.onerror = () => {
        setTimeout(connectToUpdates, 5000); // Reconnect after 5 seconds
      };
    };

    connectToUpdates();

    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [userPrincipal]);

  return updates;
};
```

---

## 🛠️ Development Setup

### Local Development Environment

1. **Bot Trading System Setup**:
```bash
git clone <bot-trading-repo>
cd trade-bot-marketplace
docker-compose up -d
```

2. **ICP Local Replica**:
```bash
dfx start --clean --background
dfx deploy
```

3. **Frontend Development**:
```bash
npm install
npm run dev
```

### Environment Configuration

```bash
# .env.local
NEXT_PUBLIC_BOT_TRADING_API=http://localhost:8000
NEXT_PUBLIC_BOT_API_KEY=marketplace_dev_api_key_12345
NEXT_PUBLIC_IC_HOST=http://localhost:4943
```

---

## 🧪 Testing Strategy

### Unit Tests

```typescript
// Jest tests for API integration
describe('Bot Trading API Integration', () => {
  test('should register bot successfully', async () => {
    const mockResponse = {
      registration_id: 1,
      api_key: 'test_key',
      status: 'approved'
    };

    fetchMock.mockResponseOnce(JSON.stringify(mockResponse));

    const result = await registerBotTemplate({
      user_principal_id: 'test-principal',
      bot_id: 1,
      marketplace_name: 'Test Bot',
      marketplace_description: 'Test Description',
      price_on_marketplace: '10.00'
    });

    expect(result.status).toBe('approved');
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/bots/register'),
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          'X-API-Key': 'marketplace_dev_api_key_12345'
        })
      })
    );
  });
});
```

### Integration Tests

```rust
// Canister integration tests
#[cfg(test)]
mod tests {
    use super::*;
    
    #[tokio::test]
    async fn test_bot_rental_flow() {
        // Test complete bot rental flow
        let user_principal = Principal::anonymous();
        let bot_id = 1u64;
        let duration = 30u64;
        let payment = 1000u64;

        // Mock payment verification
        // ... test implementation
        
        let result = rent_bot(bot_id, duration, payment).await;
        assert!(result.is_ok());
    }
}
```

---

## 🚀 Production Deployment

### Canister Deployment

```bash
# Deploy to IC mainnet
dfx deploy --network ic

# Update canister with production endpoints
dfx canister call marketplace_backend update_config '(
  record {
    bot_trading_api_url = "https://api.bot-marketplace.com";
    api_key = "prod_marketplace_api_key_xyz";
  }
)'
```

### Frontend Deployment

```bash
# Build for production
npm run build

# Deploy to Vercel/Netlify
vercel deploy --prod
```

### Monitoring Setup

```typescript
// Error monitoring
const setupErrorMonitoring = () => {
  window.addEventListener('error', (event) => {
    // Send to monitoring service
    console.error('Frontend error:', event.error);
  });

  // API error tracking
  const originalFetch = window.fetch;
  window.fetch = async (...args) => {
    try {
      const response = await originalFetch(...args);
      if (!response.ok) {
        console.error('API error:', response.status, response.statusText);
      }
      return response;
    } catch (error) {
      console.error('Network error:', error);
      throw error;
    }
  };
};
```

---

## 📋 Checklist

### Pre-Launch Checklist

- [ ] Bot Trading API endpoints configured
- [ ] Authentication setup verified
- [ ] Payment processing implemented
- [ ] Exchange credentials storage working
- [ ] Trading execution tested
- [ ] Real-time monitoring implemented
- [ ] Error handling comprehensive
- [ ] Security audit completed
- [ ] Performance testing passed
- [ ] Documentation updated

### Production Monitoring

- [ ] API response times < 1s
- [ ] Error rate < 1%
- [ ] Trading execution success rate > 95%
- [ ] User data encrypted and secure
- [ ] Backup systems operational
- [ ] Monitoring alerts configured

---

## 🆘 Troubleshooting

### Common Issues

1. **API Authentication Failures**
   - Verify API key is correct
   - Check header format: `X-API-Key: your_key`
   - Ensure marketplace is registered

2. **Trading Execution Errors**
   - Verify user has exchange credentials stored
   - Check principal ID mapping exists
   - Validate trading configuration parameters

3. **Real-time Update Issues**
   - Check webhook URL configuration
   - Verify network connectivity
   - Implement fallback polling mechanism

### Support Resources

- **Technical Documentation**: [docs.bot-marketplace.com](https://docs.bot-marketplace.com)
- **API Status Page**: [status.bot-marketplace.com](https://status.bot-marketplace.com)
- **Developer Discord**: [discord.gg/bot-marketplace](https://discord.gg/bot-marketplace)
- **Email Support**: dev-support@bot-marketplace.com

---

*This integration guide ensures seamless connectivity between ICP marketplaces and the Bot Trading System, providing users with a unified experience across both platforms.*