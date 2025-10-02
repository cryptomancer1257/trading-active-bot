"""
API endpoints for managing trading prompt templates
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
import logging

from core import models, schemas, security
from core.models import TradingPromptTemplate, PromptCategory, UserFavoritePrompt, PromptUsageStats
from core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Trading Strategy Templates"])


@router.get("/templates", response_model=List[Dict[str, Any]])
def list_prompt_templates(
    category: Optional[str] = None,
    search: Optional[str] = None,
    timeframe: Optional[str] = None,
    min_win_rate: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get list of trading prompt templates with filtering options
    
    **Parameters:**
    - category: Filter by category (e.g., "Smart Money - Advanced")
    - search: Search in title and prompt text
    - timeframe: Filter by timeframe (e.g., "4H", "Daily")
    - min_win_rate: Minimum win rate percentage (e.g., 60 for 60%+)
    - skip: Pagination offset
    - limit: Maximum results to return
    """
    try:
        query = db.query(TradingPromptTemplate).filter(
            TradingPromptTemplate.is_active == True
        )
        
        # Apply filters
        if category:
            query = query.filter(TradingPromptTemplate.category == category)
        
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    TradingPromptTemplate.title.like(search_pattern),
                    TradingPromptTemplate.prompt.like(search_pattern),
                    TradingPromptTemplate.best_for.like(search_pattern)
                )
            )
        
        if timeframe:
            query = query.filter(TradingPromptTemplate.timeframe.like(f"%{timeframe}%"))
        
        if min_win_rate:
            # This is a simple filter, could be improved with regex
            query = query.filter(
                TradingPromptTemplate.win_rate_estimate.like(f"{min_win_rate}%")
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        templates = query.order_by(TradingPromptTemplate.category, TradingPromptTemplate.title)\
                        .offset(skip).limit(limit).all()
        
        # Convert to dict with additional info
        result = []
        for template in templates:
            template_dict = {
                "id": template.id,
                "template_id": template.template_id,
                "title": template.title,
                "category": template.category,
                "timeframe": template.timeframe,
                "win_rate_estimate": template.win_rate_estimate,
                "prompt": template.prompt,
                "risk_management": template.risk_management,
                "best_for": template.best_for,
                "metadata": template.template_metadata,
                "created_at": template.created_at.isoformat() if template.created_at else None
            }
            result.append(template_dict)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to list prompt templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve prompt templates"
        )


@router.get("/templates/{template_id}", response_model=Dict[str, Any])
def get_prompt_template(
    template_id: str,
    db: Session = Depends(get_db)
):
    """Get specific prompt template by ID"""
    try:
        template = db.query(TradingPromptTemplate).filter(
            TradingPromptTemplate.template_id == template_id,
            TradingPromptTemplate.is_active == True
        ).first()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt template '{template_id}' not found"
            )
        
        return {
            "id": template.id,
            "template_id": template.template_id,
            "title": template.title,
            "category": template.category,
            "timeframe": template.timeframe,
            "win_rate_estimate": template.win_rate_estimate,
            "prompt": template.prompt,
            "risk_management": template.risk_management,
            "best_for": template.best_for,
            "metadata": template.template_metadata,
            "created_at": template.created_at.isoformat() if template.created_at else None,
            "updated_at": template.updated_at.isoformat() if template.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get prompt template {template_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve prompt template"
        )


@router.get("/categories", response_model=List[Dict[str, Any]])
def list_prompt_categories(
    db: Session = Depends(get_db)
):
    """Get list of all prompt categories"""
    try:
        categories = db.query(PromptCategory).filter(
            PromptCategory.is_active == True
        ).order_by(PromptCategory.display_order).all()
        
        result = []
        for cat in categories:
            # Count templates in each category
            template_count = db.query(TradingPromptTemplate).filter(
                TradingPromptTemplate.category == cat.category_name,
                TradingPromptTemplate.is_active == True
            ).count()
            
            result.append({
                "id": cat.id,
                "category_name": cat.category_name,
                "description": cat.description,
                "parent_category": cat.parent_category,
                "template_count": template_count,
                "display_order": cat.display_order
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to list prompt categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve prompt categories"
        )


@router.post("/favorites/{template_id}")
def add_favorite_prompt(
    template_id: str,
    notes: Optional[str] = None,
    current_user: models.User = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add prompt template to user's favorites"""
    try:
        # Check if template exists
        template = db.query(TradingPromptTemplate).filter(
            TradingPromptTemplate.template_id == template_id
        ).first()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt template '{template_id}' not found"
            )
        
        # Check if already favorited
        existing = db.query(UserFavoritePrompt).filter(
            and_(
                UserFavoritePrompt.user_id == current_user.id,
                UserFavoritePrompt.template_id == template_id
            )
        ).first()
        
        if existing:
            # Update notes if provided
            if notes:
                existing.notes = notes
                db.commit()
            return {"message": "Favorite already exists", "favorite_id": existing.id}
        
        # Create new favorite
        favorite = UserFavoritePrompt(
            user_id=current_user.id,
            template_id=template_id,
            notes=notes
        )
        db.add(favorite)
        db.commit()
        db.refresh(favorite)
        
        return {
            "message": "Prompt added to favorites",
            "favorite_id": favorite.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add favorite prompt: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add favorite prompt"
        )


@router.delete("/favorites/{template_id}")
def remove_favorite_prompt(
    template_id: str,
    current_user: models.User = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove prompt template from user's favorites"""
    try:
        favorite = db.query(UserFavoritePrompt).filter(
            and_(
                UserFavoritePrompt.user_id == current_user.id,
                UserFavoritePrompt.template_id == template_id
            )
        ).first()
        
        if not favorite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Favorite not found"
            )
        
        db.delete(favorite)
        db.commit()
        
        return {"message": "Prompt removed from favorites"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove favorite prompt: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove favorite prompt"
        )


@router.get("/favorites", response_model=List[Dict[str, Any]])
def list_favorite_prompts(
    current_user: models.User = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's favorite prompt templates"""
    try:
        favorites = db.query(UserFavoritePrompt).filter(
            UserFavoritePrompt.user_id == current_user.id
        ).all()
        
        result = []
        for fav in favorites:
            template = db.query(TradingPromptTemplate).filter(
                TradingPromptTemplate.template_id == fav.template_id
            ).first()
            
            if template and template.is_active:
                result.append({
                    "favorite_id": fav.id,
                    "template_id": template.template_id,
                    "title": template.title,
                    "category": template.category,
                    "timeframe": template.timeframe,
                    "win_rate_estimate": template.win_rate_estimate,
                    "prompt": template.prompt,
                    "risk_management": template.risk_management,
                    "best_for": template.best_for,
                    "notes": fav.notes,
                    "favorited_at": fav.created_at.isoformat() if fav.created_at else None
                })
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to list favorite prompts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve favorite prompts"
        )


@router.post("/usage/{template_id}")
def record_prompt_usage(
    template_id: str,
    bot_id: Optional[int] = None,
    performance_rating: Optional[int] = None,
    notes: Optional[str] = None,
    current_user: models.User = Depends(security.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Record usage of a prompt template"""
    try:
        # Check if template exists
        template = db.query(TradingPromptTemplate).filter(
            TradingPromptTemplate.template_id == template_id
        ).first()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt template '{template_id}' not found"
            )
        
        # Create usage record
        usage = PromptUsageStats(
            template_id=template_id,
            user_id=current_user.id,
            bot_id=bot_id,
            performance_rating=performance_rating,
            notes=notes
        )
        db.add(usage)
        db.commit()
        
        return {"message": "Usage recorded successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to record prompt usage: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record usage"
        )


@router.get("/stats/{template_id}", response_model=Dict[str, Any])
def get_prompt_stats(
    template_id: str,
    db: Session = Depends(get_db)
):
    """Get usage statistics for a prompt template"""
    try:
        template = db.query(TradingPromptTemplate).filter(
            TradingPromptTemplate.template_id == template_id
        ).first()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt template '{template_id}' not found"
            )
        
        # Get usage stats
        total_usage = db.query(PromptUsageStats).filter(
            PromptUsageStats.template_id == template_id
        ).count()
        
        # Get average rating
        avg_rating = db.query(func.avg(PromptUsageStats.performance_rating)).filter(
            and_(
                PromptUsageStats.template_id == template_id,
                PromptUsageStats.performance_rating.isnot(None)
            )
        ).scalar()
        
        # Get favorite count
        favorite_count = db.query(UserFavoritePrompt).filter(
            UserFavoritePrompt.template_id == template_id
        ).count()
        
        return {
            "template_id": template_id,
            "title": template.title,
            "total_usage": total_usage,
            "average_rating": float(avg_rating) if avg_rating else None,
            "favorite_count": favorite_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get prompt stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )
