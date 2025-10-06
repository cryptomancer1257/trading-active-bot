"""
LLM Provider Selection Service
===============================

Determines which LLM provider to use for a developer:
1. PRIORITY: User-configured providers (BYOK - Bring Your Own Keys) - FREE
2. FALLBACK: Platform subscription - PAID

Author: AI Trading Platform
Date: 2025-10-05
"""

from sqlalchemy.orm import Session
from core import models
from typing import Optional, Dict, Any, Tuple
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class LLMProviderSelector:
    """
    Smart LLM provider selection with cascading priority:
    
    Priority Order:
    1. User-configured Default provider (is_default=True)
    2. User-configured First Active provider
    3. Platform subscription (active, paid, within limits)
    4. Error (no provider available)
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_provider_for_developer(
        self, 
        developer_id: int,
        bot_id: Optional[int] = None,
        preferred_provider: Optional[str] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Get LLM provider for developer (BYOK only - Platform subscriptions disabled for now)
        
        Args:
            developer_id: Developer/user ID
            bot_id: Optional bot ID for logging
            preferred_provider: Optional preferred provider ("openai", "claude", "gemini")
        
        Returns:
            Tuple of:
            - Source type: "USER_CONFIGURED"
            - Provider config dict with API keys and settings
        
        Raises:
            Exception: If no provider is available
        """
        logger.info(f"🔍 Selecting LLM provider for developer {developer_id}")
        
        # Check User-Configured Providers (BYOK - FREE)
        user_provider = self._get_user_configured_provider(developer_id, preferred_provider)
        if user_provider:
            logger.info(
                f"✅ Using developer's LLM provider: {user_provider['provider']} "
                f"(model: {user_provider['model']}) - FREE"
            )
            return ("USER_CONFIGURED", user_provider)
        
        # No provider available - Error
        logger.error(f"❌ No LLM provider configured for developer {developer_id}")
        raise Exception(
            "❌ No LLM provider configured.\n\n"
            "Please add your API keys to use LLM features:\n\n"
            "✅ Go to /creator/llm-providers\n"
            "✅ Add OpenAI, Claude, or Gemini API key\n"
            "✅ Set one as default (optional)\n"
            "✅ Your bots will use your own API keys (FREE - no platform charges!)"
        )
    
    def _get_user_configured_provider(
        self, 
        developer_id: int,
        preferred_provider: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get user's own LLM provider (BYOK)
        
        Priority:
        1. Preferred provider (if specified and active)
        2. Default provider (is_default=True)
        3. First active provider (by display_order)
        
        Note: Uses 'llm_providers' table (not 'developer_llm_providers')
        """
        # Check for preferred provider
        if preferred_provider:
            preferred = self.db.query(models.LLMProvider).filter(
                models.LLMProvider.user_id == developer_id,
                models.LLMProvider.provider_type == preferred_provider,
                models.LLMProvider.is_active == True
            ).first()
            
            if preferred:
                logger.info(f"📌 Using preferred BYOK provider: {preferred.provider_type}")
                return self._format_user_provider(preferred)
        
        # Check for default provider
        default_provider = self.db.query(models.LLMProvider).filter(
            models.LLMProvider.user_id == developer_id,
            models.LLMProvider.is_default == True,
            models.LLMProvider.is_active == True
        ).first()
        
        if default_provider:
            logger.info(f"📌 Using default BYOK provider: {default_provider.provider_type}")
            return self._format_user_provider(default_provider)
        
        # Fallback to first active provider
        first_active = self.db.query(models.LLMProvider).filter(
            models.LLMProvider.user_id == developer_id,
            models.LLMProvider.is_active == True
        ).order_by(
            models.LLMProvider.display_order.asc(),
            models.LLMProvider.created_at.asc()
        ).first()
        
        if first_active:
            logger.info(f"📌 Using first active BYOK provider: {first_active.provider_type}")
            return self._format_user_provider(first_active)
        
        logger.info("ℹ️  No BYOK provider configured")
        return None
    
    def _format_user_provider(self, provider: models.LLMProvider) -> Dict[str, Any]:
        """Format user provider config with decrypted API key"""
        # Note: llm_providers table stores api_key as TEXT, not encrypted
        # If encryption is needed, wrap with decrypt_api_key()
        
        # For now, api_key is stored as plain text in llm_providers table
        # TODO: Implement encryption for llm_providers.api_key
        api_key = provider.api_key
        
        # Determine model name (llm_providers doesn't have model field)
        # Use default model based on provider_type
        # Note: provider_type is an Enum with uppercase values (OPENAI, GEMINI, etc.)
        provider_type_str = str(provider.provider_type.value).upper() if hasattr(provider.provider_type, 'value') else str(provider.provider_type).upper()
        
        model_map = {
            'OPENAI': 'gpt-4o-mini',
            'ANTHROPIC': 'claude-3-5-sonnet-20241022',
            'GEMINI': 'gemini-2.5-flash',  # Updated: Latest balanced model (Oct 2025)
            'GROQ': 'llama-3.1-70b-versatile',
            'COHERE': 'command-r-plus'
        }
        model = model_map.get(provider_type_str, 'gpt-4o-mini')
        
        return {
            'source': 'USER_CONFIGURED',
            'provider_id': provider.id,
            'provider': provider.provider_type,  # "openai", "claude", "gemini"
            'model': model,
            'api_key': api_key,
            'config': {},
            'is_free': True,  # No platform charges
            'is_default': provider.is_default,
            'display_name': f"{provider.provider_type} ({model})"
        }
    
    def _get_platform_provider(
        self, 
        developer_id: int,
        preferred_provider: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get platform LLM subscription
        
        Checks:
        1. Has active subscription
        2. Subscription is paid
        3. Not expired
        4. Within usage limits (requests & tokens)
        """
        # Get active subscription
        subscription = self.db.query(models.DeveloperLLMSubscription).filter(
            models.DeveloperLLMSubscription.developer_id == developer_id,
            models.DeveloperLLMSubscription.status == 'ACTIVE',
            models.DeveloperLLMSubscription.end_date > datetime.now(),
            models.DeveloperLLMSubscription.payment_status == 'PAID'
        ).order_by(
            models.DeveloperLLMSubscription.end_date.desc()
        ).first()
        
        if not subscription:
            logger.info("ℹ️  No active platform subscription")
            return None
        
        plan = subscription.plan
        
        # Check usage limits
        if subscription.requests_used >= plan.max_requests_per_month:
            logger.warning(
                f"⚠️  Request limit reached: "
                f"{subscription.requests_used}/{plan.max_requests_per_month}"
            )
            return None
        
        if subscription.tokens_used >= plan.max_tokens_per_month:
            logger.warning(
                f"⚠️  Token limit reached: "
                f"{subscription.tokens_used}/{plan.max_tokens_per_month}"
            )
            return None
        
        # Get available providers and models
        available_providers = plan.available_providers or []
        available_models = plan.available_models or {}
        
        if not available_providers:
            logger.error("❌ Plan has no available providers")
            return None
        
        # Select provider (prefer requested, else first available)
        if preferred_provider and preferred_provider in available_providers:
            provider = preferred_provider
        else:
            provider = available_providers[0]
        
        # Get model for provider
        models_list = available_models.get(provider, [])
        model = models_list[0] if models_list else None
        
        if not model:
            logger.error(f"❌ No model available for provider {provider}")
            return None
        
        # Get platform API key from environment
        api_key = self._get_platform_api_key(provider)
        if not api_key:
            logger.error(f"❌ Platform API key not configured for {provider}")
            return None
        
        logger.info(f"✅ Platform subscription valid: {plan.name}")
        return {
            'source': 'PLATFORM',
            'subscription_id': subscription.id,
            'plan_name': plan.name,
            'plan_id': plan.id,
            'provider': provider,
            'model': model,
            'api_key': api_key,
            'requests_remaining': plan.max_requests_per_month - subscription.requests_used,
            'tokens_remaining': plan.max_tokens_per_month - subscription.tokens_used,
            'is_free': False,  # Will be charged/counted
            'display_name': f"{provider} ({model}) - {plan.name}"
        }
    
    def _get_platform_api_key(self, provider: str) -> Optional[str]:
        """Get platform API key for specified provider"""
        api_key_map = {
            'openai': os.getenv('PLATFORM_OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY'),
            'claude': os.getenv('PLATFORM_CLAUDE_API_KEY') or os.getenv('CLAUDE_API_KEY'),
            'gemini': os.getenv('PLATFORM_GEMINI_API_KEY') or os.getenv('GEMINI_API_KEY')
        }
        return api_key_map.get(provider)
    
    def log_usage(
        self,
        developer_id: int,
        provider_config: Dict[str, Any],
        bot_id: Optional[int],
        request_type: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float = 0.0,
        success: bool = True,
        error_message: Optional[str] = None,
        request_duration_ms: Optional[int] = None
    ):
        """
        Log LLM usage and update subscription if using platform
        
        Args:
            developer_id: Developer ID
            provider_config: Provider config from get_provider_for_developer()
            bot_id: Bot ID making the request
            request_type: Type of request (chat, analysis, signal_generation)
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cost_usd: Cost in USD (for platform usage)
            success: Whether request succeeded
            error_message: Error message if failed
            request_duration_ms: Request duration in milliseconds
        """
        total_tokens = input_tokens + output_tokens
        
        try:
            # Create usage log
            usage_log = models.LLMUsageLog(
                developer_id=developer_id,
                subscription_id=provider_config.get('subscription_id'),
                bot_id=bot_id,
                provider=provider_config['provider'],
                model=provider_config['model'],
                request_type=request_type,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                cost_usd=cost_usd,
                source_type=provider_config['source'],
                user_provider_id=provider_config.get('provider_id'),
                success=success,
                error_message=error_message,
                request_duration_ms=request_duration_ms
            )
            self.db.add(usage_log)
            
            # If using platform, update subscription usage
            if provider_config['source'] == 'PLATFORM' and success:
                subscription = self.db.query(models.DeveloperLLMSubscription).get(
                    provider_config['subscription_id']
                )
                if subscription:
                    subscription.requests_used += 1
                    subscription.tokens_used += total_tokens
                    
                    # Check if approaching limits
                    plan = subscription.plan
                    requests_pct = (subscription.requests_used / plan.max_requests_per_month) * 100
                    tokens_pct = (subscription.tokens_used / plan.max_tokens_per_month) * 100
                    
                    if requests_pct >= 90 or tokens_pct >= 90:
                        logger.warning(
                            f"⚠️  Approaching limits for developer {developer_id}: "
                            f"requests={requests_pct:.1f}%, tokens={tokens_pct:.1f}%"
                        )
                    
                    logger.info(
                        f"📊 Platform usage updated: "
                        f"requests={subscription.requests_used}/{plan.max_requests_per_month}, "
                        f"tokens={subscription.tokens_used}/{plan.max_tokens_per_month}"
                    )
            
            self.db.commit()
            logger.info(f"✅ Usage logged: {total_tokens} tokens ({request_type})")
            
        except Exception as e:
            logger.error(f"❌ Failed to log usage: {e}")
            self.db.rollback()
    
    def get_usage_stats(self, developer_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Get usage statistics for developer
        
        Args:
            developer_id: Developer ID
            days: Number of days to look back
        
        Returns:
            Dict with usage stats
        """
        from datetime import timedelta
        from sqlalchemy import func
        
        start_date = datetime.now() - timedelta(days=days)
        
        # Get total usage
        usage_stats = self.db.query(
            func.count(models.LLMUsageLog.id).label('total_requests'),
            func.sum(models.LLMUsageLog.total_tokens).label('total_tokens'),
            func.sum(models.LLMUsageLog.cost_usd).label('total_cost'),
            models.LLMUsageLog.source_type
        ).filter(
            models.LLMUsageLog.developer_id == developer_id,
            models.LLMUsageLog.request_at >= start_date
        ).group_by(
            models.LLMUsageLog.source_type
        ).all()
        
        stats = {
            'period_days': days,
            'user_configured': {
                'requests': 0,
                'tokens': 0,
                'cost_usd': 0.0
            },
            'platform': {
                'requests': 0,
                'tokens': 0,
                'cost_usd': 0.0
            }
        }
        
        for stat in usage_stats:
            source_key = 'user_configured' if stat.source_type == 'USER_CONFIGURED' else 'platform'
            stats[source_key] = {
                'requests': stat.total_requests or 0,
                'tokens': int(stat.total_tokens or 0),
                'cost_usd': float(stat.total_cost or 0.0)
            }
        
        return stats


# Convenience function for quick provider selection
def get_llm_provider(db: Session, developer_id: int, bot_id: Optional[int] = None) -> Tuple[str, Dict[str, Any]]:
    """
    Quick function to get LLM provider for developer
    
    Returns:
        Tuple of (source_type, provider_config)
    """
    selector = LLMProviderSelector(db)
    return selector.get_provider_for_developer(developer_id, bot_id)

