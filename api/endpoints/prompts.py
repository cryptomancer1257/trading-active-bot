"""
FastAPI endpoints for Prompt Template management
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from core import crud, models, schemas, security
from core.database import get_db

router = APIRouter()

@router.get("/", response_model=List[schemas.PromptTemplatePublic])
def get_prompt_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = Query(None, regex="^(TRADING|ANALYSIS|RISK_MANAGEMENT)$"),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Get prompt templates with optional filters"""
    prompts = crud.get_prompt_templates(
        db=db, 
        skip=skip, 
        limit=limit, 
        category=category, 
        is_active=is_active
    )
    return prompts

@router.get("/my", response_model=List[schemas.PromptTemplateInDB])
def get_my_prompt_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_developer)
):
    """Get prompt templates created by the current user"""
    prompts = crud.get_prompt_templates_by_user(
        db=db, 
        user_id=current_user.id, 
        skip=skip, 
        limit=limit
    )
    return prompts

@router.get("/default/{category}", response_model=schemas.PromptTemplatePublic)
def get_default_prompt_template(
    category: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Get the default prompt template for a category"""
    if category not in ["TRADING", "ANALYSIS", "RISK_MANAGEMENT"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid category. Must be TRADING, ANALYSIS, or RISK_MANAGEMENT"
        )
    
    prompt = crud.get_default_prompt_template(db=db, category=category)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No default prompt template found for category: {category}"
        )
    
    return prompt

@router.get("/{prompt_id}", response_model=schemas.PromptTemplateInDB)
def get_prompt_template(
    prompt_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Get a specific prompt template by ID"""
    prompt = crud.get_prompt_template_by_id(db=db, prompt_id=prompt_id)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt template not found"
        )
    
    # Check if user can access this prompt (public or own)
    if not prompt.is_active and prompt.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to inactive prompt template"
        )
    
    return prompt

@router.post("/", response_model=schemas.PromptTemplateInDB, status_code=status.HTTP_201_CREATED)
def create_prompt_template(
    prompt_data: schemas.PromptTemplateCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_developer)
):
    """Create a new prompt template"""
    try:
        prompt = crud.create_prompt_template(
            db=db, 
            prompt=prompt_data, 
            created_by=current_user.id
        )
        return prompt
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create prompt template: {str(e)}"
        )

@router.put("/{prompt_id}", response_model=schemas.PromptTemplateInDB)
def update_prompt_template(
    prompt_id: int,
    prompt_update: schemas.PromptTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_developer)
):
    """Update a prompt template"""
    # Check if prompt exists and user owns it
    existing_prompt = crud.get_prompt_template_by_id(db=db, prompt_id=prompt_id)
    if not existing_prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt template not found"
        )
    
    # Only owner or admin can update
    if existing_prompt.created_by != current_user.id and current_user.role != schemas.UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this prompt template"
        )
    
    try:
        updated_prompt = crud.update_prompt_template(
            db=db, 
            prompt_id=prompt_id, 
            prompt_update=prompt_update
        )
        return updated_prompt
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update prompt template: {str(e)}"
        )

@router.delete("/{prompt_id}", response_model=schemas.PromptTemplateInDB)
def delete_prompt_template(
    prompt_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_developer)
):
    """Delete a prompt template (soft delete if in use)"""
    # Check if prompt exists and user owns it
    existing_prompt = crud.get_prompt_template_by_id(db=db, prompt_id=prompt_id)
    if not existing_prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt template not found"
        )
    
    # Only owner or admin can delete
    if existing_prompt.created_by != current_user.id and current_user.role != schemas.UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this prompt template"
        )
    
    try:
        deleted_prompt = crud.delete_prompt_template(db=db, prompt_id=prompt_id)
        return deleted_prompt
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete prompt template: {str(e)}"
        )

@router.post("/{prompt_id}/clone", response_model=schemas.PromptTemplateInDB, status_code=status.HTTP_201_CREATED)
def clone_prompt_template(
    prompt_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_developer)
):
    """Clone an existing prompt template"""
    # Get the original prompt
    original_prompt = crud.get_prompt_template_by_id(db=db, prompt_id=prompt_id)
    if not original_prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt template not found"
        )
    
    # Check if user can access this prompt
    if not original_prompt.is_active and original_prompt.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to inactive prompt template"
        )
    
    # Create clone data
    clone_data = schemas.PromptTemplateCreate(
        name=f"{original_prompt.name} (Copy)",
        description=f"Cloned from: {original_prompt.name}",
        content=original_prompt.content,
        category=original_prompt.category,
        is_active=True,
        is_default=False  # Clones are never default
    )
    
    try:
        cloned_prompt = crud.create_prompt_template(
            db=db, 
            prompt=clone_data, 
            created_by=current_user.id
        )
        return cloned_prompt
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clone prompt template: {str(e)}"
        )
