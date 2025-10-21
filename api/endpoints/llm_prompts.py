"""
LLM Prompt Templates API Endpoints
For managing AI trading analysis prompts (NOT trading strategy templates)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from core import models, schemas, security, crud
from core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["LLM Prompts"])


@router.get("/", response_model=List[schemas.PromptTemplateInDB])
def list_llm_prompts(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List all LLM prompt templates with optional filtering"""
    try:
        prompts = crud.get_prompt_templates(
            db=db,
            skip=skip,
            limit=limit,
            category=category,
            is_active=is_active
        )
        return prompts
    except Exception as e:
        logger.error(f"Failed to list prompts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list prompts: {str(e)}"
        )


@router.get("/my", response_model=List[schemas.PromptTemplateInDB])
def list_my_llm_prompts(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
):
    """List current user's LLM prompt templates"""
    try:
        prompts = crud.get_prompt_templates_by_user(
            db=db,
            user_id=current_user.id,
            skip=skip,
            limit=limit
        )
        return prompts
    except Exception as e:
        logger.error(f"Failed to list user prompts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list user prompts: {str(e)}"
        )


@router.get("/default/{category}", response_model=schemas.PromptTemplateInDB)
def get_default_llm_prompt(
    category: str,
    db: Session = Depends(get_db)
):
    """Get default LLM prompt template for a category"""
    try:
        prompt = crud.get_default_prompt_by_category(db=db, category=category)
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No default prompt found for category '{category}'"
            )
        return prompt
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get default prompt: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get default prompt: {str(e)}"
        )


@router.get("/{prompt_id}", response_model=schemas.PromptTemplateInDB)
def get_llm_prompt(
    prompt_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific LLM prompt template by ID"""
    try:
        prompt = crud.get_prompt_template_by_id(db=db, prompt_id=prompt_id)
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt template {prompt_id} not found"
            )
        return prompt
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get prompt {prompt_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get prompt: {str(e)}"
        )


@router.post("/", response_model=schemas.PromptTemplateInDB, status_code=status.HTTP_201_CREATED)
def create_llm_prompt(
    prompt: schemas.PromptTemplateCreate,
    current_user: models.User = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new LLM prompt template"""
    try:
        # Only developers and admins can create prompts
        if current_user.role not in [models.UserRole.DEVELOPER, models.UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only developers and admins can create prompt templates"
            )
        
        new_prompt = crud.create_prompt_template(
            db=db,
            prompt=prompt,
            created_by=current_user.id
        )
        logger.info(f"Created LLM prompt template {new_prompt.id} by user {current_user.id}")
        return new_prompt
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create prompt: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create prompt: {str(e)}"
        )


@router.put("/{prompt_id}", response_model=schemas.PromptTemplateInDB)
def update_llm_prompt(
    prompt_id: int,
    prompt_update: schemas.PromptTemplateUpdate,
    current_user: models.User = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an existing LLM prompt template"""
    try:
        # Get existing prompt
        existing_prompt = crud.get_prompt_template_by_id(db=db, prompt_id=prompt_id)
        if not existing_prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt template {prompt_id} not found"
            )
        
        # Check ownership (only creator or admin can update)
        if existing_prompt.created_by != current_user.id and current_user.role != models.UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this prompt"
            )
        
        updated_prompt = crud.update_prompt_template(
            db=db,
            prompt_id=prompt_id,
            prompt_update=prompt_update
        )
        logger.info(f"Updated LLM prompt template {prompt_id} by user {current_user.id}")
        return updated_prompt
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update prompt {prompt_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update prompt: {str(e)}"
        )


@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_llm_prompt(
    prompt_id: int,
    current_user: models.User = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an LLM prompt template (soft delete by setting is_active=False)"""
    try:
        # Get existing prompt
        existing_prompt = crud.get_prompt_template_by_id(db=db, prompt_id=prompt_id)
        if not existing_prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt template {prompt_id} not found"
            )
        
        # Check ownership (only creator or admin can delete)
        if existing_prompt.created_by != current_user.id and current_user.role != models.UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this prompt"
            )
        
        # Soft delete
        crud.update_prompt_template(
            db=db,
            prompt_id=prompt_id,
            prompt_update=schemas.PromptTemplateUpdate(is_active=False)
        )
        logger.info(f"Deleted LLM prompt template {prompt_id} by user {current_user.id}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete prompt {prompt_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete prompt: {str(e)}"
        )

