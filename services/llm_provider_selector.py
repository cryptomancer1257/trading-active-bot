"""
LLM Provider Selection Service
===============================

PLATFORM-MANAGED MODEL:
- Platform provides LLM API keys (admin-managed)
- All developers use platform's providers
- Platform pays for LLM costs
- Simpler for developers (no API key management)

Author: AI Trading Platform
Date: 2025-10-19
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
    Platform-managed LLM provider selection:
    
    Logic:
    1. Get default platform provider (is_default=True)
    2. If no default, get first active platform provider
    3. Error if no platform provider available
    
    Note: User-configured providers are deprecated
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
        Get platform-managed LLM provider for developer
        
        Args:
            developer_id: Developer/user ID (for logging only)
            bot_id: Optional bot ID for logging
            preferred_provider: Optional preferred provider ("OPENAI", "ANTHROPIC", "GEMINI")
        
        Returns:
            Tuple of:
            - Source type: "PLATFORM"
            - Provider config dict with API keys and settings
        
        Raises:
            Exception: If no platform provider is available
        """
        logger.info(f"🔍 Selecting platform LLM provider for developer {developer_id}")
        
        # Check if user is on Free Plan
        user_plan = self._get_user_plan(developer_id)
        is_free_plan = user_plan and user_plan.plan_name.value == 'free'
        
        if is_free_plan:
            # Free Plan: Force use of free provider (Gemini 2.0 Flash)
            logger.info(f"👤 Developer {developer_id} is on FREE plan - auto-selecting free provider")
            platform_provider = self._get_free_provider()
            if platform_provider:
                logger.info(
                    f"✅ Using FREE platform LLM provider: {platform_provider['provider']} "
                    f"(model: {platform_provider['model']}) - Platform pays"
                )
                return ("PLATFORM", platform_provider)
            else:
                # Fallback to any available provider if free provider not configured
                logger.warning(f"⚠️ No free provider available, using default")
                platform_provider = self._get_platform_provider(None)
        else:
            # Pro Plan or higher: Use preferred provider
            logger.info(f"👤 Developer {developer_id} is on PRO plan - using preferred provider")
            platform_provider = self._get_platform_provider(preferred_provider)
        
        if platform_provider:
            logger.info(
                f"✅ Using platform LLM provider: {platform_provider['provider']} "
                f"(model: {platform_provider['model']}) - Platform pays"
            )
            return ("PLATFORM", platform_provider)
        
        # No provider available - Error (admin needs to configure)
        logger.error(f"❌ No platform LLM provider available")
        raise Exception(
            "❌ No platform LLM provider configured.\n\n"
            "Platform administrator needs to:\n\n"
            "✅ Configure platform LLM providers\n"
            "✅ Add API keys for OpenAI, Claude, or Gemini\n"
            "✅ Set one as default\n\n"
            "Contact platform administrator for assistance."
        )
    
    def _get_platform_provider(
        self, 
        preferred_provider: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get platform-managed LLM provider
        
        Priority:
        1. Preferred provider (if specified and active)
        2. Default provider (is_default=True)
        3. First active provider
        """
        # Check for preferred provider
        if preferred_provider:
            preferred = self.db.query(models.PlatformLLMProvider).filter(
                models.PlatformLLMProvider.provider_type == preferred_provider,
                models.PlatformLLMProvider.is_active == True
            ).first()
            
            if preferred:
                logger.info(f"📌 Using preferred platform provider: {preferred.provider_type}")
                return self._format_platform_provider(preferred)
        
        # Check for default provider
        default_provider = self.db.query(models.PlatformLLMProvider).filter(
            models.PlatformLLMProvider.is_default == True,
            models.PlatformLLMProvider.is_active == True
        ).first()
        
        if default_provider:
            logger.info(f"📌 Using default platform provider: {default_provider.provider_type}")
            return self._format_platform_provider(default_provider)
        
        # Fallback to first active provider
        first_active = self.db.query(models.PlatformLLMProvider).filter(
            models.PlatformLLMProvider.is_active == True
        ).order_by(
            models.PlatformLLMProvider.created_at.asc()
        ).first()
        
        if first_active:
            logger.info(f"📌 Using first active platform provider: {first_active.provider_type}")
            return self._format_platform_provider(first_active)
        
        logger.error("❌ No active platform provider found")
        return None
    
    def _format_platform_provider(self, provider: models.PlatformLLMProvider) -> Dict[str, Any]:
        """Format platform provider config"""
        # Get first active model for this provider
        model = self.db.query(models.PlatformLLMModel).filter(
            models.PlatformLLMModel.provider_id == provider.id,
            models.PlatformLLMModel.is_active == True
        ).first()
        
        if not model:
            logger.error(f"❌ No active model found for provider {provider.name}")
            # Fallback to default model
            provider_type_str = str(provider.provider_type.value).upper() if hasattr(provider.provider_type, 'value') else str(provider.provider_type).upper()
            model_map = {
                'OPENAI': 'gpt-4o-mini',
                'ANTHROPIC': 'claude-3-5-sonnet-20241022',
                'GEMINI': 'gemini-2.5-flash',
                'GROQ': 'llama-3.1-70b-versatile',
                'COHERE': 'command-r-plus'
            }
            model_name = model_map.get(provider_type_str, 'gpt-4o-mini')
        else:
            model_name = model.model_name
        
        return {
            'source': 'PLATFORM',
            'provider_id': provider.id,
            'provider': provider.provider_type,
            'model': model_name,
            'api_key': provider.api_key,  # Platform's API key
            'base_url': provider.base_url,
            'config': {},
            'is_platform_managed': True,
            'is_default': provider.is_default,
            'display_name': f"{provider.name} ({model_name})"
        }
    
    def log_usage(
        self,
        developer_id: int,
        provider_config: Dict[str, Any],
        bot_id: Optional[int],
        subscription_id: Optional[int] = None,
        request_type: str = "market_analysis",
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: float = 0.0,
        success: bool = True,
        error_message: Optional[str] = None,
        request_duration_ms: Optional[int] = None
    ):
        """
        Log LLM usage for platform providers
        
        Args:
            developer_id: Developer ID
            provider_config: Provider config from get_provider_for_developer()
            bot_id: Bot ID making the request
            subscription_id: Subscription ID for usage tracking
            request_type: Type of request (chat, analysis, signal_generation)
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cost_usd: Cost in USD (platform pays this)
            success: Whether request succeeded
            error_message: Error message if failed
            request_duration_ms: Request duration in milliseconds
        """
        total_tokens = input_tokens + output_tokens
        
        try:
            # Create usage log
            usage_log = models.LLMUsageLog(
                developer_id=developer_id,
                subscription_id=subscription_id,  # Track subscription usage
                bot_id=bot_id,
                provider=provider_config['provider'],
                model=provider_config['model'],
                request_type=request_type,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                cost_usd=cost_usd,  # Platform cost
                source_type='PLATFORM',  # Always platform now
                user_provider_id=None,  # No user provider
                success=success,
                error_message=error_message,
                request_duration_ms=request_duration_ms
            )
            self.db.add(usage_log)
            self.db.commit()
            
            logger.info(
                f"✅ Platform usage logged: {total_tokens} tokens, "
                f"cost=${cost_usd:.4f} ({request_type})"
            )
            
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


    def _get_user_plan(self, developer_id: int):
        """
        Get user's current plan
        
        Returns:
            UserPlan object or None if no plan found
        """
        from core import models
        
        user_plan = self.db.query(models.UserPlan).filter(
            models.UserPlan.user_id == developer_id,
            models.UserPlan.status == models.PlanStatus.ACTIVE
        ).first()
        
        return user_plan
    
    def _get_free_provider(self) -> Optional[Dict[str, Any]]:
        """
        Get free LLM provider (Gemini 2.0 Flash with cost = 0)
        
        Returns:
            Provider config dict or None if not available
        """
        from core import models
        
        # Try to find Gemini 2.0 Flash (free model)
        provider = self.db.query(models.PlatformLLMProvider).filter(
            models.PlatformLLMProvider.provider_type == models.LLMProviderType.GEMINI,
            models.PlatformLLMProvider.is_active == True
        ).first()
        
        if provider:
            # Get free model (gemini-2.0-flash-001 has cost = 0)
            free_model = self.db.query(models.PlatformLLMModel).filter(
                models.PlatformLLMModel.provider_id == provider.id,
                models.PlatformLLMModel.is_active == True,
                models.PlatformLLMModel.model_name.like('%2.0-flash%')
            ).first()
            
            if free_model:
                return self._format_platform_provider(provider, free_model)
            else:
                # Fallback to any active Gemini model
                any_model = self.db.query(models.PlatformLLMModel).filter(
                    models.PlatformLLMModel.provider_id == provider.id,
                    models.PlatformLLMModel.is_active == True
                ).first()
                
                if any_model:
                    return self._format_platform_provider(provider, any_model)
        
        return None


# Convenience function for quick provider selection
def get_llm_provider(db: Session, developer_id: int, bot_id: Optional[int] = None) -> Tuple[str, Dict[str, Any]]:
    """
    Quick function to get LLM provider for developer
    
    Returns:
        Tuple of (source_type, provider_config)
    """
    selector = LLMProviderSelector(db)
    return selector.get_provider_for_developer(developer_id, bot_id)

