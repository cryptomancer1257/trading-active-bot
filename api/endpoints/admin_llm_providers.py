"""
Admin LLM Provider Management Endpoints
========================================

Admin-only endpoints for managing platform LLM providers.
Only users with ADMIN role can access these endpoints.

Author: AI Trading Platform
Date: 2024-10-19
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from core.database import get_db
from core import models, schemas
from core.security import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def require_admin(current_user: models.User = Depends(get_current_user)):
    """Dependency to ensure user is admin"""
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# ============================================
# PLATFORM LLM PROVIDER ENDPOINTS
# ============================================

@router.get("/", response_model=List[schemas.PlatformLLMProviderInDB])
async def get_platform_llm_providers(
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(require_admin)
):
    """Get all platform LLM providers (Admin only)"""
    try:
        providers = db.query(models.PlatformLLMProvider).all()
        return providers
    except Exception as e:
        logger.error(f"Failed to get platform LLM providers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve platform LLM providers"
        )


@router.get("/{provider_id}", response_model=schemas.PlatformLLMProviderInDB)
async def get_platform_llm_provider(
    provider_id: int,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(require_admin)
):
    """Get a specific platform LLM provider (Admin only)"""
    try:
        provider = db.query(models.PlatformLLMProvider).filter(
            models.PlatformLLMProvider.id == provider_id
        ).first()
        
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Platform LLM provider not found"
            )
        
        return provider
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get platform LLM provider {provider_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve platform LLM provider"
        )


@router.post("/", response_model=schemas.PlatformLLMProviderInDB, status_code=status.HTTP_201_CREATED)
async def create_platform_llm_provider(
    provider_data: schemas.PlatformLLMProviderCreate,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(require_admin)
):
    """Create a new platform LLM provider (Admin only)"""
    try:
        # Check if name already exists
        existing = db.query(models.PlatformLLMProvider).filter(
            models.PlatformLLMProvider.name == provider_data.name
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Platform provider with name '{provider_data.name}' already exists"
            )
        
        # If setting as default, unset other defaults
        if provider_data.is_default:
            db.query(models.PlatformLLMProvider).filter(
                models.PlatformLLMProvider.is_default == True
            ).update({"is_default": False})
        
        # Create provider
        provider = models.PlatformLLMProvider(
            provider_type=provider_data.provider_type,
            name=provider_data.name,
            api_key=provider_data.api_key,  # TODO: Encrypt this
            base_url=provider_data.base_url,
            is_active=provider_data.is_active,
            is_default=provider_data.is_default,
            created_by=admin_user.id
        )
        
        db.add(provider)
        db.flush()  # Get the provider ID
        
        # Create models if provided
        if provider_data.models:
            for model_data in provider_data.models:
                model = models.PlatformLLMModel(
                    provider_id=provider.id,
                    model_name=model_data.model_name,
                    display_name=model_data.display_name,
                    is_active=model_data.is_active,
                    max_tokens=model_data.max_tokens,
                    cost_per_1k_tokens=model_data.cost_per_1k_tokens
                )
                db.add(model)
        
        db.commit()
        db.refresh(provider)
        
        logger.info(f"✅ Admin {admin_user.email} created platform provider: {provider.name}")
        return provider
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create platform LLM provider: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create platform LLM provider: {str(e)}"
        )


@router.put("/{provider_id}", response_model=schemas.PlatformLLMProviderInDB)
async def update_platform_llm_provider(
    provider_id: int,
    provider_data: schemas.PlatformLLMProviderUpdate,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(require_admin)
):
    """Update a platform LLM provider (Admin only)"""
    try:
        provider = db.query(models.PlatformLLMProvider).filter(
            models.PlatformLLMProvider.id == provider_id
        ).first()
        
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Platform LLM provider not found"
            )
        
        # If setting as default, unset other defaults
        if provider_data.is_default and not provider.is_default:
            db.query(models.PlatformLLMProvider).filter(
                models.PlatformLLMProvider.id != provider_id,
                models.PlatformLLMProvider.is_default == True
            ).update({"is_default": False})
        
        # Update fields
        update_data = provider_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(provider, field, value)
        
        db.commit()
        db.refresh(provider)
        
        logger.info(f"✅ Admin {admin_user.email} updated platform provider: {provider.name}")
        return provider
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update platform LLM provider {provider_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update platform LLM provider"
        )


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_platform_llm_provider(
    provider_id: int,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(require_admin)
):
    """Delete a platform LLM provider (Admin only)"""
    try:
        provider = db.query(models.PlatformLLMProvider).filter(
            models.PlatformLLMProvider.id == provider_id
        ).first()
        
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Platform LLM provider not found"
            )
        
        provider_name = provider.name
        db.delete(provider)
        db.commit()
        
        logger.info(f"✅ Admin {admin_user.email} deleted platform provider: {provider_name}")
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete platform LLM provider {provider_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete platform LLM provider"
        )


# ============================================
# PLATFORM LLM MODEL ENDPOINTS
# ============================================

@router.post("/{provider_id}/models", response_model=schemas.LLMModelInDB, status_code=status.HTTP_201_CREATED)
async def create_platform_llm_model(
    provider_id: int,
    model_data: schemas.PlatformLLMModelCreate,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(require_admin)
):
    """Create a new model for a platform LLM provider (Admin only)"""
    try:
        # Check if provider exists
        provider = db.query(models.PlatformLLMProvider).filter(
            models.PlatformLLMProvider.id == provider_id
        ).first()
        
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Platform LLM provider not found"
            )
        
        # Check if model already exists for this provider
        existing = db.query(models.PlatformLLMModel).filter(
            models.PlatformLLMModel.provider_id == provider_id,
            models.PlatformLLMModel.model_name == model_data.model_name
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model '{model_data.model_name}' already exists for this provider"
            )
        
        # Create model
        model = models.PlatformLLMModel(
            provider_id=provider_id,
            model_name=model_data.model_name,
            display_name=model_data.display_name,
            is_active=model_data.is_active,
            max_tokens=model_data.max_tokens,
            cost_per_1k_tokens=model_data.cost_per_1k_tokens
        )
        
        db.add(model)
        db.commit()
        db.refresh(model)
        
        logger.info(f"✅ Admin {admin_user.email} created model {model.model_name} for provider {provider.name}")
        return model
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create platform LLM model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create platform LLM model"
        )


@router.put("/{provider_id}/models/{model_id}", response_model=schemas.LLMModelInDB)
async def update_platform_llm_model(
    provider_id: int,
    model_id: int,
    model_data: schemas.PlatformLLMModelUpdate,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(require_admin)
):
    """Update a platform LLM model (Admin only)"""
    try:
        model = db.query(models.PlatformLLMModel).filter(
            models.PlatformLLMModel.id == model_id,
            models.PlatformLLMModel.provider_id == provider_id
        ).first()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Platform LLM model not found"
            )
        
        # Update fields
        update_data = model_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(model, field, value)
        
        db.commit()
        db.refresh(model)
        
        logger.info(f"✅ Admin {admin_user.email} updated model {model.model_name}")
        return model
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update platform LLM model {model_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update platform LLM model"
        )


@router.delete("/{provider_id}/models/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_platform_llm_model(
    provider_id: int,
    model_id: int,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(require_admin)
):
    """Delete a platform LLM model (Admin only)"""
    try:
        model = db.query(models.PlatformLLMModel).filter(
            models.PlatformLLMModel.id == model_id,
            models.PlatformLLMModel.provider_id == provider_id
        ).first()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Platform LLM model not found"
            )
        
        model_name = model.model_name
        db.delete(model)
        db.commit()
        
        logger.info(f"✅ Admin {admin_user.email} deleted model {model_name}")
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete platform LLM model {model_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete platform LLM model"
        )

