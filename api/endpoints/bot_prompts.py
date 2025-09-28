from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from core.database import get_db
from core import models, schemas, security
import core.crud as crud

router = APIRouter()

# BotPrompt schemas
class BotPromptBase(schemas.BaseModel):
    bot_id: int
    prompt_id: int
    is_active: bool = True
    priority: int = 0
    custom_override: Optional[str] = None

class BotPromptCreate(BotPromptBase):
    pass

class BotPromptUpdate(schemas.BaseModel):
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    custom_override: Optional[str] = None

class BotPromptInDB(BotPromptBase):
    id: int
    attached_at: str
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True

class BotPromptWithDetails(BotPromptInDB):
    prompt_template: schemas.PromptTemplateInDB
    bot: schemas.BotInDB

# Bot-Prompt Management Endpoints

@router.get("/bots/{bot_id}/prompts")
async def get_bot_prompts(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Get all prompts attached to a specific bot"""
    # Verify bot ownership
    bot = db.query(models.Bot).filter(models.Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    if bot.developer_id != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to access this bot")
    
    try:
        # Get bot prompts with prompt template info
        bot_prompts = db.query(models.BotPrompt).filter(
            models.BotPrompt.bot_id == bot_id
        ).all()
        
        # Convert to format with prompt template info
        result = []
        for bp in bot_prompts:
            # Get prompt template info
            prompt_template = db.query(models.PromptTemplate).filter(
                models.PromptTemplate.id == bp.prompt_id
            ).first()
            
            result.append({
                "id": bp.id,
                "bot_id": bp.bot_id,
                "prompt_id": bp.prompt_id,
                "is_active": bp.is_active,
                "priority": bp.priority,
                "custom_override": bp.custom_override,
                "attached_at": bp.attached_at.isoformat() if bp.attached_at else None,
                "created_at": bp.created_at.isoformat() if bp.created_at else None,
                "updated_at": bp.updated_at.isoformat() if bp.updated_at else None,
                "prompt_template": {
                    "id": prompt_template.id if prompt_template else bp.prompt_id,
                    "name": prompt_template.name if prompt_template else "Unknown Prompt",
                    "description": prompt_template.description if prompt_template else None,
                    "content": prompt_template.content if prompt_template else None,
                    "category": prompt_template.category if prompt_template else "UNKNOWN",
                    "is_active": prompt_template.is_active if prompt_template else True,
                    "is_default": prompt_template.is_default if prompt_template else False,
                    "created_at": prompt_template.created_at.isoformat() if prompt_template and prompt_template.created_at else None,
                    "updated_at": prompt_template.updated_at.isoformat() if prompt_template and prompt_template.updated_at else None
                }
            })
        
        return result
    except Exception as e:
        print(f"Error in get_bot_prompts: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/prompts/{prompt_id}/bots", response_model=List[BotPromptWithDetails])
async def get_prompt_bots(
    prompt_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Get all bots using a specific prompt"""
    # Verify prompt access
    prompt = db.query(models.PromptTemplate).filter(models.PromptTemplate.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    if prompt.created_by != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to access this prompt")
    
    return crud.get_prompt_bots(db, prompt_id=prompt_id)

@router.post("/bots/{bot_id}/prompts/{prompt_id}")
async def attach_prompt_to_bot(
    bot_id: int,
    prompt_id: int,
    priority: int = Query(0, description="Priority level (higher = more important)"),
    custom_override: Optional[str] = Query(None, description="Bot-specific prompt customization"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Attach a prompt to a bot"""
    # Verify bot ownership
    bot = db.query(models.Bot).filter(models.Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    if bot.developer_id != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to access this bot")
    
    # Verify prompt exists
    prompt = db.query(models.PromptTemplate).filter(models.PromptTemplate.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    # Check if bot already has a prompt attached
    existing = db.query(models.BotPrompt).filter(
        models.BotPrompt.bot_id == bot_id
    ).first()
    
    if existing:
        # Update existing attachment instead of creating new one
        existing.prompt_id = prompt_id
        existing.priority = priority
        existing.custom_override = custom_override
        existing.updated_at = func.now()
        db.commit()
        db.refresh(existing)
        
        # Return the updated attachment
        return {
            "id": existing.id,
            "bot_id": existing.bot_id,
            "prompt_id": existing.prompt_id,
            "is_active": existing.is_active,
            "priority": existing.priority,
            "custom_override": existing.custom_override,
            "attached_at": existing.attached_at.isoformat() if existing.attached_at else "",
            "created_at": existing.created_at.isoformat() if existing.created_at else "",
            "updated_at": existing.updated_at.isoformat() if existing.updated_at else ""
        }
    
    try:
        bot_prompt = crud.attach_prompt_to_bot(
            db, 
            bot_id=bot_id, 
            prompt_id=prompt_id, 
            priority=priority,
            custom_override=custom_override
        )
        
        # Return simple format to avoid validation errors
        return {
            "id": bot_prompt.id,
            "bot_id": bot_prompt.bot_id,
            "prompt_id": bot_prompt.prompt_id,
            "is_active": bot_prompt.is_active,
            "priority": bot_prompt.priority,
            "custom_override": bot_prompt.custom_override,
            "attached_at": bot_prompt.attached_at.isoformat() if bot_prompt.attached_at else "",
            "created_at": bot_prompt.created_at.isoformat() if bot_prompt.created_at else "",
            "updated_at": bot_prompt.updated_at.isoformat() if bot_prompt.updated_at else ""
        }
    except Exception as e:
        print(f"Error in attach_prompt_to_bot: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/bots/{bot_id}/prompts/{prompt_id}")
async def detach_prompt_from_bot(
    bot_id: int,
    prompt_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Detach a prompt from a bot"""
    # Verify bot ownership
    bot = db.query(models.Bot).filter(models.Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    if bot.developer_id != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to access this bot")
    
    # Find the attachment
    bot_prompt = db.query(models.BotPrompt).filter(
        models.BotPrompt.bot_id == bot_id,
        models.BotPrompt.prompt_id == prompt_id
    ).first()
    
    if not bot_prompt:
        raise HTTPException(status_code=404, detail="Prompt not attached to this bot")
    
    crud.detach_prompt_from_bot(db, bot_prompt_id=bot_prompt.id)
    return {"message": "Prompt detached successfully"}

@router.put("/bots/{bot_id}/prompts/{prompt_id}", response_model=BotPromptInDB)
async def update_bot_prompt(
    bot_id: int,
    prompt_id: int,
    update_data: BotPromptUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Update bot-prompt relationship settings"""
    # Verify bot ownership
    bot = db.query(models.Bot).filter(models.Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    if bot.developer_id != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to access this bot")
    
    # Find the attachment
    bot_prompt = db.query(models.BotPrompt).filter(
        models.BotPrompt.bot_id == bot_id,
        models.BotPrompt.prompt_id == prompt_id
    ).first()
    
    if not bot_prompt:
        raise HTTPException(status_code=404, detail="Prompt not attached to this bot")
    
    return crud.update_bot_prompt(db, bot_prompt_id=bot_prompt.id, update_data=update_data)

@router.get("/bots/{bot_id}/suggested-prompts", response_model=List[schemas.PromptTemplateInDB])
async def get_suggested_prompts(
    bot_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Get suggested prompts for a bot based on bot type and category"""
    # Verify bot ownership
    bot = db.query(models.Bot).filter(models.Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    if bot.developer_id != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to access this bot")
    
    return crud.get_suggested_prompts(db, bot_id=bot_id, limit=limit)

@router.get("/prompts/{prompt_id}/suggested-bots", response_model=List[schemas.BotInDB])
async def get_suggested_bots(
    prompt_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_active_user)
):
    """Get suggested bots for a prompt"""
    # Verify prompt access
    prompt = db.query(models.PromptTemplate).filter(models.PromptTemplate.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    if prompt.created_by != current_user.id and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to access this prompt")
    
    return crud.get_suggested_bots(db, prompt_id=prompt_id, limit=limit)
