from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from core.database import get_db
from core import models, schemas
from core.security import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=List[schemas.LLMProviderInDB])
async def get_llm_providers(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all LLM providers for the current user"""
    try:
        providers = db.query(models.LLMProvider).filter(
            models.LLMProvider.user_id == current_user.id
        ).all()
        return providers
    except Exception as e:
        logger.error(f"Failed to get LLM providers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve LLM providers"
        )

@router.get("/{provider_id}", response_model=schemas.LLMProviderInDB)
async def get_llm_provider(
    provider_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get a specific LLM provider"""
    try:
        provider = db.query(models.LLMProvider).filter(
            models.LLMProvider.id == provider_id,
            models.LLMProvider.user_id == current_user.id
        ).first()
        
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="LLM provider not found"
            )
        
        return provider
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get LLM provider {provider_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve LLM provider"
        )

@router.post("/", response_model=schemas.LLMProviderInDB, status_code=status.HTTP_201_CREATED)
async def create_llm_provider(
    provider_data: schemas.LLMProviderCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new LLM provider"""
    try:
        # If setting as default, unset other defaults
        if provider_data.is_default:
            db.query(models.LLMProvider).filter(
                models.LLMProvider.user_id == current_user.id,
                models.LLMProvider.is_default == True
            ).update({"is_default": False})
        
        # Create provider
        provider = models.LLMProvider(
            user_id=current_user.id,
            provider_type=provider_data.provider_type,
            name=provider_data.name,
            api_key=provider_data.api_key,  # TODO: Encrypt this
            base_url=provider_data.base_url,
            is_active=provider_data.is_active,
            is_default=provider_data.is_default
        )
        
        db.add(provider)
        db.flush()  # Get the provider ID
        
        # Create models if provided
        if provider_data.models:
            for model_data in provider_data.models:
                model = models.LLMModel(
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
        
        logger.info(f"Created LLM provider {provider.id} for user {current_user.id}")
        return provider
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create LLM provider: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create LLM provider"
        )

@router.put("/{provider_id}", response_model=schemas.LLMProviderInDB)
async def update_llm_provider(
    provider_id: int,
    provider_data: schemas.LLMProviderUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update an LLM provider"""
    try:
        provider = db.query(models.LLMProvider).filter(
            models.LLMProvider.id == provider_id,
            models.LLMProvider.user_id == current_user.id
        ).first()
        
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="LLM provider not found"
            )
        
        # If setting as default, unset other defaults
        if provider_data.is_default:
            db.query(models.LLMProvider).filter(
                models.LLMProvider.user_id == current_user.id,
                models.LLMProvider.id != provider_id,
                models.LLMProvider.is_default == True
            ).update({"is_default": False})
        
        # Update provider fields
        update_data = provider_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(provider, field, value)
        
        db.commit()
        db.refresh(provider)
        
        logger.info(f"Updated LLM provider {provider_id} for user {current_user.id}")
        return provider
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update LLM provider {provider_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update LLM provider"
        )

@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_llm_provider(
    provider_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete an LLM provider"""
    try:
        provider = db.query(models.LLMProvider).filter(
            models.LLMProvider.id == provider_id,
            models.LLMProvider.user_id == current_user.id
        ).first()
        
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="LLM provider not found"
            )
        
        db.delete(provider)
        db.commit()
        
        logger.info(f"Deleted LLM provider {provider_id} for user {current_user.id}")
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete LLM provider {provider_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete LLM provider"
        )

# Model endpoints
@router.get("/{provider_id}/models", response_model=List[schemas.LLMModelInDB])
async def get_llm_models(
    provider_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all models for a specific LLM provider"""
    try:
        # Verify provider ownership
        provider = db.query(models.LLMProvider).filter(
            models.LLMProvider.id == provider_id,
            models.LLMProvider.user_id == current_user.id
        ).first()
        
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="LLM provider not found"
            )
        
        models_list = db.query(models.LLMModel).filter(
            models.LLMModel.provider_id == provider_id
        ).all()
        
        return models_list
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get LLM models for provider {provider_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve LLM models"
        )

@router.post("/{provider_id}/models", response_model=schemas.LLMModelInDB, status_code=status.HTTP_201_CREATED)
async def create_llm_model(
    provider_id: int,
    model_data: schemas.LLMModelCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new LLM model for a provider"""
    try:
        # Verify provider ownership
        provider = db.query(models.LLMProvider).filter(
            models.LLMProvider.id == provider_id,
            models.LLMProvider.user_id == current_user.id
        ).first()
        
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="LLM provider not found"
            )
        
        # Create model
        model = models.LLMModel(
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
        
        logger.info(f"Created LLM model {model.id} for provider {provider_id}")
        return model
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create LLM model for provider {provider_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create LLM model"
        )

@router.put("/{provider_id}/models/{model_id}", response_model=schemas.LLMModelInDB)
async def update_llm_model(
    provider_id: int,
    model_id: int,
    model_data: schemas.LLMModelUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update an LLM model"""
    try:
        # Verify provider ownership
        provider = db.query(models.LLMProvider).filter(
            models.LLMProvider.id == provider_id,
            models.LLMProvider.user_id == current_user.id
        ).first()
        
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="LLM provider not found"
            )
        
        # Get model
        model = db.query(models.LLMModel).filter(
            models.LLMModel.id == model_id,
            models.LLMModel.provider_id == provider_id
        ).first()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="LLM model not found"
            )
        
        # Update model fields
        update_data = model_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(model, field, value)
        
        db.commit()
        db.refresh(model)
        
        logger.info(f"Updated LLM model {model_id} for provider {provider_id}")
        return model
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update LLM model {model_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update LLM model"
        )

@router.delete("/{provider_id}/models/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_llm_model(
    provider_id: int,
    model_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete an LLM model"""
    try:
        # Verify provider ownership
        provider = db.query(models.LLMProvider).filter(
            models.LLMProvider.id == provider_id,
            models.LLMProvider.user_id == current_user.id
        ).first()
        
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="LLM provider not found"
            )
        
        # Get model
        model = db.query(models.LLMModel).filter(
            models.LLMModel.id == model_id,
            models.LLMModel.provider_id == provider_id
        ).first()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="LLM model not found"
            )
        
        db.delete(model)
        db.commit()
        
        logger.info(f"Deleted LLM model {model_id} for provider {provider_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete LLM model {model_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete LLM model"
        )
