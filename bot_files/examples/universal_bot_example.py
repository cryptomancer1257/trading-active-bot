"""
Universal Futures Bot - Usage Examples
Demonstrates how to use the Universal Futures Bot Template with different exchanges
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import asyncio
from bot_files.universal_futures_bot import create_universal_futures_bot, UniversalFuturesBot

# ==================== EXAMPLE 1: Basic Usage ====================

async def example_1_basic_usage():
    """Example 1: Basic trading cycle on Binance"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Usage - Binance Futures")
    print("="*70)
    
    # Create bot
    bot = create_universal_futures_bot(
        exchange='BINANCE',
        user_principal_id='demo-principal-id-123',
        config={
            'trading_pair': 'BTCUSDT',
            'leverage': 10,
            'testnet': True,
            'timeframes': ['30m', '1h', '4h'],
            'use_llm_analysis': True
        }
    )
    
    print("\n✅ Bot initialized on Binance")
    
    # Crawl data
    print("\n📊 Crawling market data...")
    data = bot.crawl_data()
    
    if not data.get('timeframes'):
        print("❌ Failed to crawl data")
        return
    
    print(f"✅ Got data for {len(data['timeframes'])} timeframes")
    
    # Analyze
    print("\n🔍 Analyzing market...")
    analysis = bot.analyze_data(data)
    
    if 'error' in analysis:
        print(f"❌ Analysis failed: {analysis['error']}")
        return
    
    print(f"✅ Analysis complete - Price: ${analysis.get('current_price', 0):.2f}")
    
    # Generate signal
    print("\n🎯 Generating trading signal...")
    signal = bot.generate_signal(analysis)
    
    print(f"\nSignal Results:")
    print(f"  Action: {signal.action}")
    print(f"  Confidence: {signal.value*100:.1f}%")
    print(f"  Reason: {signal.reason[:80]}...")
    
    # Execute if signal is not HOLD
    if signal.action != "HOLD":
        print(f"\n🚀 Would execute {signal.action} trade here")
        print("  (Set testnet=True and configure API keys to execute real trades)")
    
    print("\n✅ Example 1 completed")

# ==================== EXAMPLE 2: Multi-Exchange Comparison ====================

async def example_2_multi_exchange():
    """Example 2: Compare signals across multiple exchanges"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Multi-Exchange Signal Comparison")
    print("="*70)
    
    exchanges = ['BINANCE', 'BYBIT', 'OKX']
    principal_id = 'demo-principal-id-123'
    
    results = {}
    
    for exchange in exchanges:
        print(f"\n📊 Analyzing {exchange}...")
        
        try:
            # Create bot for each exchange
            bot = create_universal_futures_bot(
                exchange=exchange,
                user_principal_id=principal_id,
                config={
                    'trading_pair': 'BTCUSDT',
                    'timeframes': ['1h', '4h'],
                    'testnet': True
                }
            )
            
            # Quick analysis
            data = bot.crawl_data()
            analysis = bot.analyze_data(data)
            signal = bot.generate_signal(analysis)
            
            results[exchange] = {
                'action': signal.action,
                'confidence': signal.value,
                'price': analysis.get('current_price', 0)
            }
            
            print(f"  ✅ {exchange}: {signal.action} ({signal.value*100:.1f}%)")
            
        except Exception as e:
            print(f"  ❌ {exchange} failed: {e}")
            results[exchange] = {'error': str(e)}
    
    # Summary
    print("\n📊 Signal Summary:")
    print("-" * 50)
    for exchange, result in results.items():
        if 'error' not in result:
            print(f"{exchange:10} | {result['action']:6} | {result['confidence']*100:5.1f}% | ${result['price']:.2f}")
        else:
            print(f"{exchange:10} | ERROR  | {result['error']}")
    
    print("\n✅ Example 2 completed")

# ==================== EXAMPLE 3: Advanced Configuration ====================

async def example_3_advanced_config():
    """Example 3: Advanced configuration with custom settings"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Advanced Configuration")
    print("="*70)
    
    # Advanced config
    advanced_config = {
        # Trading
        'trading_pair': 'ETHUSDT',
        'leverage': 20,
        'stop_loss_pct': 0.015,       # 1.5% stop loss
        'take_profit_pct': 0.05,      # 5% take profit
        
        # Multi-timeframe
        'timeframes': ['15m', '1h', '4h', '1d'],
        'primary_timeframe': '1h',
        
        # LLM
        'use_llm_analysis': True,
        'llm_model': 'openai',
        
        # Capital Management
        'base_position_size_pct': 0.03,     # 3% base
        'max_position_size_pct': 0.15,      # 15% max
        'max_portfolio_exposure': 0.40,     # 40% total
        'sizing_method': 'llm_hybrid',
        
        # Risk Management
        'max_drawdown_threshold': 0.15,     # 15% max drawdown
        'volatility_threshold_high': 0.10,
        
        # Testing
        'testnet': True
    }
    
    bot = create_universal_futures_bot(
        exchange='BINANCE',
        user_principal_id='demo-principal-id-123',
        config=advanced_config
    )
    
    print("\n✅ Advanced bot configured:")
    print(f"  Exchange: BINANCE")
    print(f"  Pair: ETHUSDT")
    print(f"  Leverage: 20x")
    print(f"  Timeframes: {len(advanced_config['timeframes'])}")
    print(f"  Risk Management: Advanced capital allocation")
    print(f"  Position Size: 3-15% dynamic sizing")
    
    # Test data crawling
    print("\n📊 Testing data crawling...")
    data = bot.crawl_data()
    
    for tf, candles in data.get('timeframes', {}).items():
        print(f"  {tf}: {len(candles)} candles")
    
    print("\n✅ Example 3 completed")

# ==================== EXAMPLE 4: Exchange-Specific Features ====================

async def example_4_exchange_specific():
    """Example 4: Demonstrate exchange-specific features"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Exchange-Specific Features")
    print("="*70)
    
    # OKX with passphrase requirement
    print("\n📋 OKX Configuration:")
    print("  - Requires API passphrase")
    print("  - Unified trading account")
    print("  - Symbol format: BTC-USDT-SWAP")
    
    okx_config = {
        'trading_pair': 'BTC-USDT-SWAP',  # OKX format
        'leverage': 10,
        'testnet': True
    }
    
    # Kraken with fixed leverage
    print("\n📋 Kraken Configuration:")
    print("  - Fixed leverage per contract")
    print("  - US-regulated")
    print("  - Symbol format: PF_XBTUSD")
    
    kraken_config = {
        'trading_pair': 'PF_XBTUSD',      # Kraken format
        'leverage': 5,  # Note: Leverage may be fixed
        'testnet': True
    }
    
    # Huobi/HTX with integer quantities
    print("\n📋 Huobi/HTX Configuration:")
    print("  - Contract-based (integer quantities)")
    print("  - Symbol format: BTC-USDT")
    
    huobi_config = {
        'trading_pair': 'BTC-USDT',       # Huobi format
        'leverage': 10,
        'testnet': True
    }
    
    print("\n💡 Exchange-specific notes documented in config")
    print("✅ Example 4 completed")

# ==================== EXAMPLE 5: Error Handling ====================

async def example_5_error_handling():
    """Example 5: Proper error handling"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Error Handling Best Practices")
    print("="*70)
    
    try:
        # Attempt to create bot with invalid config
        print("\n🧪 Testing error handling...")
        
        bot = create_universal_futures_bot(
            exchange='BINANCE',
            user_principal_id='demo-principal-id-123',
            config={
                'trading_pair': 'BTCUSDT',
                'testnet': True
            }
        )
        
        # Try data crawling with error handling
        print("\n📊 Crawling data with error handling...")
        try:
            data = bot.crawl_data()
            
            if 'error' in data:
                print(f"  ⚠️  Crawl warning: {data['error']}")
            else:
                print(f"  ✅ Data crawled successfully")
            
        except Exception as e:
            print(f"  ❌ Crawl failed: {e}")
            print(f"  💡 Fallback to sample data or retry logic here")
        
        # Try analysis with error handling
        print("\n🔍 Analyzing with error handling...")
        try:
            analysis = bot.analyze_data(data)
            
            if 'error' in analysis:
                print(f"  ⚠️  Analysis warning: {analysis['error']}")
            else:
                print(f"  ✅ Analysis completed successfully")
                
        except Exception as e:
            print(f"  ❌ Analysis failed: {e}")
            print(f"  💡 Use technical analysis fallback")
        
        # Try signal generation with error handling
        print("\n🎯 Generating signal with error handling...")
        try:
            signal = bot.generate_signal(analysis)
            print(f"  ✅ Signal: {signal.action} ({signal.value*100:.1f}%)")
            
        except Exception as e:
            print(f"  ❌ Signal generation failed: {e}")
            print(f"  💡 Default to HOLD action")
        
    except ValueError as e:
        print(f"\n❌ Configuration error: {e}")
        print("💡 Check exchange name and API credentials")
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("💡 Review logs and configuration")
    
    print("\n✅ Example 5 completed")

# ==================== EXAMPLE 6: Portfolio Management ====================

async def example_6_portfolio():
    """Example 6: Multi-bot portfolio management"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Portfolio Management Across Exchanges")
    print("="*70)
    
    principal_id = 'demo-principal-id-123'
    
    # Define portfolio
    portfolio = {
        'BINANCE': {
            'pairs': ['BTCUSDT', 'ETHUSDT'],
            'leverage': 10,
            'allocation': 0.40  # 40% of capital
        },
        'BYBIT': {
            'pairs': ['BTCUSDT'],
            'leverage': 15,
            'allocation': 0.30  # 30% of capital
        },
        'OKX': {
            'pairs': ['BTC-USDT-SWAP'],
            'leverage': 10,
            'allocation': 0.30  # 30% of capital
        }
    }
    
    print("\n📊 Portfolio Configuration:")
    for exchange, config in portfolio.items():
        print(f"\n{exchange}:")
        print(f"  Pairs: {', '.join(config['pairs'])}")
        print(f"  Leverage: {config['leverage']}x")
        print(f"  Allocation: {config['allocation']*100:.0f}%")
    
    # Simulate portfolio tracking
    print("\n💼 Portfolio Tracking:")
    print("-" * 50)
    print(f"{'Exchange':10} | {'Pair':12} | {'Status':8} | Allocation")
    print("-" * 50)
    
    for exchange, config in portfolio.items():
        for pair in config['pairs']:
            allocation = config['allocation'] / len(config['pairs'])
            print(f"{exchange:10} | {pair:12} | Active   | {allocation*100:5.1f}%")
    
    print("\n💡 Tips for portfolio management:")
    print("  - Diversify across exchanges")
    print("  - Monitor total exposure")
    print("  - Balance risk across pairs")
    print("  - Use position limits per exchange")
    
    print("\n✅ Example 6 completed")

# ==================== MAIN RUNNER ====================

async def run_all_examples():
    """Run all examples"""
    print("\n" + "="*70)
    print("UNIVERSAL FUTURES BOT - USAGE EXAMPLES")
    print("="*70)
    print("\nThis demo shows how to use the Universal Futures Bot Template")
    print("with support for multiple exchanges (Binance, Bybit, OKX, etc.)")
    
    examples = [
        ("Basic Usage", example_1_basic_usage),
        ("Multi-Exchange Comparison", example_2_multi_exchange),
        ("Advanced Configuration", example_3_advanced_config),
        ("Exchange-Specific Features", example_4_exchange_specific),
        ("Error Handling", example_5_error_handling),
        ("Portfolio Management", example_6_portfolio),
    ]
    
    print("\nAvailable Examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print("\n" + "="*70)
    
    # Run examples
    for name, func in examples:
        try:
            await func()
        except Exception as e:
            print(f"\n❌ Example '{name}' failed: {e}")
    
    print("\n" + "="*70)
    print("✅ ALL EXAMPLES COMPLETED")
    print("="*70)
    print("\nNext Steps:")
    print("  1. Configure your API keys in database")
    print("  2. Test on testnet with real API keys")
    print("  3. Customize configuration for your strategy")
    print("  4. Monitor and optimize performance")
    print("\nDocumentation: docs/UNIVERSAL_FUTURES_BOT_GUIDE.md")
    print("="*70 + "\n")

# ==================== RUN ====================

if __name__ == "__main__":
    print("🚀 Starting Universal Futures Bot Examples...")
    
    # Note: These examples are for demonstration only
    # For real trading, you need to:
    # 1. Store API keys in database
    # 2. Configure testnet/mainnet properly
    # 3. Set up proper error handling and monitoring
    
    try:
        asyncio.run(run_all_examples())
    except KeyboardInterrupt:
        print("\n\n⚠️  Examples interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

