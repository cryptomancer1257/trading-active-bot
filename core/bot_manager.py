"""
Bot Management System for Trading Bot Marketplace

This module handles bot loading, validation, and execution management.
"""

import os
import sys
import importlib.util
import inspect
import ast
import json
import hashlib
import shutil
import pickle
import joblib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bots.bot_sdk import CustomBot, Action
from core import models, schemas
from core.database import SessionLocal
from services.s3_manager import get_s3_manager

logger = logging.getLogger(__name__)

class BotValidationError(Exception):
    """Exception raised when bot validation fails"""
    pass

class BotLoadingError(Exception):
    """Exception raised when bot loading fails"""
    pass

class MLModelManager:
    """Manages ML model files and operations"""
    
    def __init__(self, model_dir: str = "ml_models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        self.loaded_models: Dict[int, Any] = {}
    
    def save_model_file(self, bot_id: int, file_content: bytes, file_info: schemas.BotFileUpload) -> str:
        """Save ML model file"""
        try:
            # Create bot model directory
            bot_model_dir = self.model_dir / str(bot_id)
            bot_model_dir.mkdir(exist_ok=True)
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_hash = hashlib.sha256(file_content).hexdigest()[:8]
            
            if file_info.file_type == schemas.FileType.MODEL:
                extension = self._get_model_extension(file_info.model_framework)
                filename = f"model_{timestamp}_{file_hash}{extension}"
            elif file_info.file_type == schemas.FileType.WEIGHTS:
                extension = ".h5" if file_info.model_framework == "tensorflow" else ".pth"
                filename = f"weights_{timestamp}_{file_hash}{extension}"
            else:
                filename = f"{file_info.file_type.lower()}_{timestamp}_{file_hash}.bin"
            
            file_path = bot_model_dir / filename
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Validate model file if possible
            if file_info.file_type in [schemas.FileType.MODEL, schemas.FileType.WEIGHTS]:
                self._validate_model_file(file_path, file_info)
            
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Error saving model file: {e}")
            raise
    
    def _get_model_extension(self, framework: Optional[str]) -> str:
        """Get appropriate file extension for model framework"""
        extensions = {
            "tensorflow": ".h5",
            "pytorch": ".pth",
            "sklearn": ".pkl",
            "xgboost": ".pkl",
            "lightgbm": ".pkl",
            "onnx": ".onnx"
        }
        return extensions.get(framework, ".pkl")
    
    def _validate_model_file(self, file_path: Path, file_info: schemas.BotFileUpload):
        """Validate model file based on framework"""
        try:
            framework = file_info.model_framework
            
            if framework == "tensorflow":
                try:
                    import tensorflow as tf
                    model = tf.keras.models.load_model(file_path)
                    logger.info(f"TensorFlow model validated: {model.summary()}")
                except Exception as e:
                    raise BotValidationError(f"Invalid TensorFlow model: {e}")
            
            elif framework == "pytorch":
                try:
                    import torch
                    model = torch.load(file_path, map_location='cpu')
                    logger.info(f"PyTorch model validated")
                except Exception as e:
                    raise BotValidationError(f"Invalid PyTorch model: {e}")
            
            elif framework in ["sklearn", "xgboost", "lightgbm"]:
                try:
                    model = joblib.load(file_path)
                    logger.info(f"{framework} model validated")
                except Exception as e:
                    raise BotValidationError(f"Invalid {framework} model: {e}")
            
        except ImportError as e:
            logger.warning(f"Cannot validate {framework} model - library not installed: {e}")
        except Exception as e:
            logger.error(f"Model validation failed: {e}")
            raise
    
    def load_model(self, bot_id: int, model_path: str, framework: str) -> Any:
        """Load ML model for inference"""
        try:
            if bot_id in self.loaded_models:
                return self.loaded_models[bot_id]
            
            if not os.path.exists(model_path):
                raise BotLoadingError(f"Model file not found: {model_path}")
            
            if framework == "tensorflow":
                import tensorflow as tf
                model = tf.keras.models.load_model(model_path)
            elif framework == "pytorch":
                import torch
                model = torch.load(model_path, map_location='cpu')
                model.eval()
            elif framework in ["sklearn", "xgboost", "lightgbm"]:
                model = joblib.load(model_path)
            else:
                raise BotLoadingError(f"Unsupported framework: {framework}")
            
            # Cache the model
            self.loaded_models[bot_id] = model
            return model
            
        except Exception as e:
            logger.error(f"Error loading model for bot {bot_id}: {e}")
            raise

class BotManager:
    """Enhanced bot manager with ML support"""
    
    def __init__(self, upload_dir: str = "bot_files"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        self.loaded_bots: Dict[int, CustomBot] = {}
        self.model_manager = MLModelManager()
        self.s3_manager = get_s3_manager()
        
    def validate_bot_code(self, code_content: str) -> Dict[str, Any]:
        """
        Validate bot code for security and structure
        
        Args:
            code_content: Python code content as string
            
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "bot_class": None,
            "bot_info": {},
            "error": None  # Đảm bảo luôn có key 'error' để endpoint không bị KeyError
        }
        
        try:
            # Parse the code to AST
            tree = ast.parse(code_content)
            
            # Security checks
            security_issues = self._check_security_issues(tree)
            if security_issues:
                validation_result["errors"].extend(security_issues)
                validation_result["is_valid"] = False
                validation_result["error"] = "; ".join(security_issues)
                validation_result["valid"] = validation_result["is_valid"]
                return validation_result
            
            # Check for required imports
            required_imports = self._check_required_imports(tree)
            if not required_imports:
                msg = "Missing required imports: from bots.bot_sdk import CustomBot, Action"
                validation_result["errors"].append(msg)
                validation_result["is_valid"] = False
                validation_result["error"] = msg
                validation_result["valid"] = validation_result["is_valid"]
                return validation_result
            
            # Find bot class
            bot_class = self._find_bot_class(tree)
            if not bot_class:
                msg = "No CustomBot subclass found"
                validation_result["errors"].append(msg)
                validation_result["is_valid"] = False
                validation_result["error"] = msg
                validation_result["valid"] = validation_result["is_valid"]
                return validation_result
            
            validation_result["bot_class"] = bot_class["name"]
            validation_result["bot_info"] = bot_class["info"]
            
            # Check required methods
            missing_methods = self._check_required_methods(bot_class)
            if missing_methods:
                msg = "; ".join([f"Missing required method: {method}" for method in missing_methods])
                validation_result["errors"].extend([f"Missing required method: {method}" for method in missing_methods])
                validation_result["is_valid"] = False
                validation_result["error"] = msg
                validation_result["valid"] = validation_result["is_valid"]
                return validation_result
            
            # Additional checks
            warnings = self._check_best_practices(tree)
            validation_result["warnings"].extend(warnings)
            
        except SyntaxError as e:
            msg = f"Syntax error: {str(e)}"
            validation_result["is_valid"] = False
            validation_result["errors"].append(msg)
            validation_result["error"] = msg
        except Exception as e:
            msg = f"Validation error: {str(e)}"
            validation_result["is_valid"] = False
            validation_result["errors"].append(msg)
            validation_result["error"] = msg
        
        # Nếu có lỗi mà chưa có error, gán error là chuỗi nối các errors
        if not validation_result["valid"] and not validation_result["error"] and validation_result["errors"]:
            validation_result["error"] = "; ".join([str(e) for e in validation_result["errors"]])
        validation_result["valid"] = validation_result["is_valid"]
        return validation_result
    
    def _check_security_issues(self, tree: ast.AST) -> List[str]:
        """Check for potential security issues in the code"""
        security_issues = []
        
        # Forbidden functions/modules
        forbidden_imports = {
            'os', 'sys', 'subprocess', 'eval', 'exec', 'compile',
            'open', '__import__', 'globals', 'locals', 'vars',
            'input', 'raw_input', 'file', 'execfile', 'reload'
        }
        
        forbidden_attributes = {
            '__builtins__', '__globals__', '__locals__', '__dict__',
            '__class__', '__bases__', '__subclasses__'
        }
        
        class SecurityChecker(ast.NodeVisitor):
            def visit_Import(self, node):
                for alias in node.names:
                    if alias.name in forbidden_imports:
                        security_issues.append(f"Forbidden import: {alias.name}")
                self.generic_visit(node)
            
            def visit_ImportFrom(self, node):
                if node.module in forbidden_imports:
                    security_issues.append(f"Forbidden import: {node.module}")
                for alias in node.names:
                    if alias.name in forbidden_imports:
                        security_issues.append(f"Forbidden import: {alias.name}")
                self.generic_visit(node)
            
            def visit_Attribute(self, node):
                if node.attr in forbidden_attributes:
                    security_issues.append(f"Forbidden attribute access: {node.attr}")
                self.generic_visit(node)
            
            def visit_Call(self, node):
                if isinstance(node.func, ast.Name) and node.func.id in forbidden_imports:
                    security_issues.append(f"Forbidden function call: {node.func.id}")
                self.generic_visit(node)
        
        SecurityChecker().visit(tree)
        return security_issues
    
    def _check_required_imports(self, tree: ast.AST) -> bool:
        """Check if required imports are present"""
        required_found = False
        
        class ImportChecker(ast.NodeVisitor):
            def visit_ImportFrom(self, node):
                if (node.module == 'bots.bot_sdk' and
                    any(alias.name in ['CustomBot', 'Action'] for alias in node.names)):
                    nonlocal required_found
                    required_found = True
                self.generic_visit(node)
        
        ImportChecker().visit(tree)
        return required_found
    
    def _find_bot_class(self, tree: ast.AST) -> Optional[Dict[str, Any]]:
        """Find the CustomBot subclass in the code"""
        bot_class = None
        
        class ClassFinder(ast.NodeVisitor):
            def visit_ClassDef(self, node):
                # Check if class inherits from CustomBot
                for base in node.bases:
                    if (isinstance(base, ast.Name) and base.id == 'CustomBot'):
                        nonlocal bot_class
                        bot_class = {
                            "name": node.name,
                            "info": self._extract_class_info(node),
                            "methods": [method.name for method in node.body if isinstance(method, ast.FunctionDef)]
                        }
                        break
                self.generic_visit(node)
            
            def _extract_class_info(self, node):
                """Extract bot information from class attributes"""
                info = {}
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                if target.id == 'bot_name' and isinstance(item.value, ast.Constant):
                                    info['bot_name'] = item.value.value
                                elif target.id == 'bot_description' and isinstance(item.value, ast.Constant):
                                    info['bot_description'] = item.value.value
                return info
        
        ClassFinder().visit(tree)
        return bot_class
    
    def _check_required_methods(self, bot_class: Dict[str, Any]) -> List[str]:
        """Check if required methods are implemented"""
        required_methods = ['prepare_data', 'predict']
        missing_methods = []
        
        for method in required_methods:
            if method not in bot_class['methods']:
                missing_methods.append(method)
        
        return missing_methods
    
    def _check_best_practices(self, tree: ast.AST) -> List[str]:
        """Check for best practices and potential issues"""
        warnings = []
        
        class BestPracticeChecker(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                # Check for docstrings
                if (node.name in ['prepare_data', 'predict'] and 
                    not (node.body and isinstance(node.body[0], ast.Expr) and 
                         isinstance(node.body[0].value, ast.Constant))):
                    warnings.append(f"Method {node.name} should have a docstring")
                
                # Check for proper error handling
                has_try_except = any(isinstance(item, ast.Try) for item in node.body)
                if node.name in ['prepare_data', 'predict'] and not has_try_except:
                    warnings.append(f"Method {node.name} should include error handling")
                
                self.generic_visit(node)
        
        BestPracticeChecker().visit(tree)
        return warnings
    
    def save_bot_file(self, bot_id: int, code_content: str, filename: str) -> str:
        """
        Save bot file to filesystem
        
        Args:
            bot_id: Bot ID
            code_content: Python code content
            filename: Original filename
            
        Returns:
            Path to saved file
        """
        # Create bot directory
        bot_dir = self.upload_dir / str(bot_id)
        bot_dir.mkdir(exist_ok=True)
        
        # Generate unique filename
        content_hash = hashlib.sha256(code_content.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{content_hash}_{filename}"
        
        file_path = bot_dir / safe_filename
        
        # Save file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code_content)
        
        # Keep only latest 5 versions
        self._cleanup_old_versions(bot_dir, keep=5)
        
        return str(file_path)
    
    def _cleanup_old_versions(self, bot_dir: Path, keep: int = 5):
        """Clean up old bot versions, keeping only the latest ones"""
        try:
            python_files = list(bot_dir.glob("*.py"))
            if len(python_files) > keep:
                # Sort by modification time
                python_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                # Remove older files
                for old_file in python_files[keep:]:
                    old_file.unlink()
        except Exception as e:
            logger.warning(f"Failed to cleanup old versions: {e}")
    
    def save_bot_files(self, bot_id: int, files: List[Tuple[bytes, schemas.BotFileUpload]]) -> List[schemas.BotFileInDB]:
        """Save multiple bot files including code and ML models"""
        saved_files = []
        db = SessionLocal()
        
        try:
            for file_content, file_info in files:
                # Save file to appropriate location
                if file_info.file_type == schemas.FileType.CODE:
                    file_path = self.save_bot_file(bot_id, file_content.decode('utf-8'), "bot.py")
                else:
                    file_path = self.model_manager.save_model_file(bot_id, file_content, file_info)
                
                # Calculate file hash and size
                file_hash = hashlib.sha256(file_content).hexdigest()
                file_size = len(file_content)
                
                # Create database record
                db_file = models.BotFile(
                    bot_id=bot_id,
                    file_type=file_info.file_type,
                    file_name=getattr(file_info, 'file_name', f"{file_info.file_type.lower()}.bin"),
                    file_path=file_path,
                    file_size=file_size,
                    file_hash=file_hash,
                    description=file_info.description,
                    model_framework=file_info.model_framework,
                    model_type=file_info.model_type
                )
                
                db.add(db_file)
                db.commit()
                db.refresh(db_file)
                
                saved_files.append(schemas.BotFileInDB.from_orm(db_file))
            
            return saved_files
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving bot files: {e}")
            raise
        finally:
            db.close()
    
    def load_bot(self, bot_id: int) -> Optional[CustomBot]:
        """
        Load a bot from filesystem
        
        Args:
            bot_id: Bot ID
            
        Returns:
            Loaded bot instance or None if failed
        """
        try:
            # Check if already loaded
            if bot_id in self.loaded_bots:
                return self.loaded_bots[bot_id]
            
            # Get bot info from database
            db = SessionLocal()
            try:
                bot_record = db.query(models.Bot).filter(models.Bot.id == bot_id).first()
                if not bot_record or not bot_record.code_path:
                    return None
                
                # Load bot code
                if not os.path.exists(bot_record.code_path):
                    logger.error(f"Bot file not found: {bot_record.code_path}")
                    return None
                
                # Import module
                spec = importlib.util.spec_from_file_location(f"bot_{bot_id}", bot_record.code_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find bot class
                bot_class = None
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, CustomBot) and obj != CustomBot:
                        bot_class = obj
                        break
                
                if not bot_class:
                    logger.error(f"No CustomBot subclass found in {bot_record.code_path}")
                    return None
                
                # Create bot instance
                bot_config = bot_record.default_config or {}
                bot_instance = bot_class(bot_config, {})
                
                # Cache the bot
                self.loaded_bots[bot_id] = bot_instance
                
                return bot_instance
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error loading bot {bot_id}: {str(e)}")
            return None
    
    def load_bot_with_models(self, bot_id: int, user_config: Dict[str, Any] = None, user_api_keys: Dict[str, str] = None) -> Optional[CustomBot]:
        """Load bot with ML models if needed"""
        try:
            # Check if already loaded
            if bot_id in self.loaded_bots:
                return self.loaded_bots[bot_id]
            
            # Get bot info from database
            db = SessionLocal()
            try:
                bot_record = db.query(models.Bot).filter(models.Bot.id == bot_id).first()
                if not bot_record:
                    return None
                
                # Load bot code
                code_file = db.query(models.BotFile).filter(
                    models.BotFile.bot_id == bot_id,
                    models.BotFile.file_type == schemas.FileType.CODE,
                    models.BotFile.is_active == True
                ).first()
                
                if not code_file or not os.path.exists(code_file.file_path):
                    logger.error(f"Bot code file not found for bot {bot_id}")
                    return None
                
                # Import bot module
                spec = importlib.util.spec_from_file_location(f"bot_{bot_id}", code_file.file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find bot class
                bot_class = None
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, CustomBot) and obj != CustomBot:
                        bot_class = obj
                        break
                
                if not bot_class:
                    logger.error(f"No CustomBot subclass found for bot {bot_id}")
                    return None
                
                # Prepare configuration
                bot_config = {**(bot_record.default_config or {}), **(user_config or {})}
                
                # Load ML models if needed
                if bot_record.bot_type in [schemas.BotType.ML, schemas.BotType.DL, schemas.BotType.LLM]:
                    model_files = db.query(models.BotFile).filter(
                        models.BotFile.bot_id == bot_id,
                        models.BotFile.file_type.in_([schemas.FileType.MODEL, schemas.FileType.WEIGHTS]),
                        models.BotFile.is_active == True
                    ).all()
                    
                    models_dict = {}
                    for model_file in model_files:
                        try:
                            model = self.model_manager.load_model(
                                bot_id, model_file.file_path, model_file.model_framework
                            )
                            models_dict[model_file.file_type.value] = model
                        except Exception as e:
                            logger.warning(f"Failed to load model {model_file.file_path}: {e}")
                    
                    # Add models to bot config
                    bot_config['models'] = models_dict
                
                # Create bot instance
                api_keys = user_api_keys or {}
                bot_instance = bot_class(bot_config, api_keys)
                
                # Cache the bot
                self.loaded_bots[bot_id] = bot_instance
                
                return bot_instance
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error loading bot {bot_id}: {str(e)}")
            return None
    
    def unload_bot(self, bot_id: int):
        """Unload a bot from memory"""
        if bot_id in self.loaded_bots:
            del self.loaded_bots[bot_id]
    
    def test_bot(self, bot_id: int, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test a bot with sample data
        
        Args:
            bot_id: Bot ID
            test_data: Test data including market data
            
        Returns:
            Test results
        """
        try:
            bot = self.load_bot(bot_id)
            if not bot:
                return {"success": False, "error": "Failed to load bot"}
            
            # Create test market data
            import pandas as pd
            test_df = pd.DataFrame(test_data.get('market_data', []))
            
            if test_df.empty:
                return {"success": False, "error": "No test data provided"}
            
            # Test prepare_data method
            try:
                prepared_data = bot.prepare_data(test_df)
                if prepared_data is None or prepared_data.empty:
                    return {"success": False, "error": "prepare_data returned empty result"}
            except Exception as e:
                return {"success": False, "error": f"prepare_data failed: {str(e)}"}
            
            # Test predict method
            try:
                signal = bot.predict(prepared_data)
                if not isinstance(signal, Action):
                    return {"success": False, "error": "predict must return Action instance"}
            except Exception as e:
                return {"success": False, "error": f"predict failed: {str(e)}"}
            
            return {
                "success": True,
                "signal": {
                    "action": signal.action,
                    "type": signal.type,
                    "value": signal.value
                },
                "prepared_data_shape": prepared_data.shape,
                "prepared_data_columns": list(prepared_data.columns)
            }
            
        except Exception as e:
            return {"success": False, "error": f"Test failed: {str(e)}"}
    
    def get_bot_info(self, bot_id: int) -> Dict[str, Any]:
        """Get information about a bot"""
        try:
            bot = self.load_bot(bot_id)
            if not bot:
                return {"error": "Failed to load bot"}
            
            return {
                "bot_name": getattr(bot, 'bot_name', 'Unknown'),
                "bot_description": getattr(bot, 'bot_description', 'No description'),
                "config": getattr(bot, 'config', {}),
                "loaded": True
            }
            
        except Exception as e:
            return {"error": f"Failed to get bot info: {str(e)}"}
    
    def backup_bot(self, bot_id: int, backup_dir: str = "backups") -> str:
        """Create a backup of a bot"""
        try:
            backup_path = Path(backup_dir) / f"bot_{bot_id}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Copy bot files
            bot_dir = self.upload_dir / str(bot_id)
            if bot_dir.exists():
                shutil.copytree(bot_dir, backup_path / "files")
            
            # Export bot metadata
            db = SessionLocal()
            try:
                bot_record = db.query(models.Bot).filter(models.Bot.id == bot_id).first()
                if bot_record:
                    metadata = {
                        "id": bot_record.id,
                        "name": bot_record.name,
                        "description": bot_record.description,
                        "version": bot_record.version,
                        "created_at": bot_record.created_at.isoformat(),
                        "config_schema": bot_record.config_schema,
                        "default_config": bot_record.default_config
                    }
                    
                    with open(backup_path / "metadata.json", 'w') as f:
                        json.dump(metadata, f, indent=2)
                        
            finally:
                db.close()
            
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Error backing up bot {bot_id}: {str(e)}")
            raise
    
    def restore_bot(self, backup_path: str) -> int:
        """Restore a bot from backup"""
        try:
            backup_path = Path(backup_path)
            
            # Read metadata
            with open(backup_path / "metadata.json", 'r') as f:
                metadata = json.load(f)
            
            # Restore to database
            db = SessionLocal()
            try:
                bot_record = models.Bot(
                    name=metadata["name"],
                    description=metadata["description"],
                    version=metadata["version"],
                    config_schema=metadata["config_schema"],
                    default_config=metadata["default_config"],
                    status=models.BotStatus.PENDING
                )
                
                db.add(bot_record)
                db.commit()
                db.refresh(bot_record)
                
                # Restore files
                files_path = backup_path / "files"
                if files_path.exists():
                    bot_dir = self.upload_dir / str(bot_record.id)
                    shutil.copytree(files_path, bot_dir)
                    
                    # Update code_path
                    python_files = list(bot_dir.glob("*.py"))
                    if python_files:
                        bot_record.code_path = str(python_files[0])
                        db.commit()
                
                return bot_record.id
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error restoring bot from {backup_path}: {str(e)}")
            raise
    
    def get_bot_stats(self) -> Dict[str, Any]:
        """Get statistics about loaded bots"""
        return {
            "loaded_bots": len(self.loaded_bots),
            "bot_ids": list(self.loaded_bots.keys()),
            "upload_dir": str(self.upload_dir),
            "total_files": len(list(self.upload_dir.rglob("*.py")))
        }
    
    def validate_ml_bot_code(self, code_content: str, bot_type: schemas.BotType) -> Dict[str, Any]:
        """Validate ML bot code with additional checks"""
        validation_result = self.validate_bot_code(code_content)
        
        if not validation_result["is_valid"]:
            return validation_result
        
        # Additional ML-specific validation
        if bot_type in [schemas.BotType.ML, schemas.BotType.DL, schemas.BotType.LLM]:
            try:
                tree = ast.parse(code_content)
                ml_checks = self._check_ml_requirements(tree, bot_type)
                validation_result["ml_requirements"] = ml_checks
                
                if not ml_checks["has_model_methods"]:
                    validation_result["warnings"].append(
                        "ML bot should implement load_model() and predict_with_model() methods"
                    )
                
            except Exception as e:
                validation_result["warnings"].append(f"ML validation warning: {e}")
        
        return validation_result
    
    def _check_ml_requirements(self, tree: ast.AST, bot_type: schemas.BotType) -> Dict[str, Any]:
        """Check ML-specific requirements in bot code"""
        requirements = {
            "has_model_methods": False,
            "imports_ml_libraries": False,
            "ml_libraries": []
        }
        
        class MLChecker(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                if node.name in ["load_model", "predict_with_model", "preprocess_data"]:
                    requirements["has_model_methods"] = True
                self.generic_visit(node)
            
            def visit_Import(self, node):
                for alias in node.names:
                    if alias.name in ["tensorflow", "torch", "sklearn", "xgboost", "lightgbm", "transformers"]:
                        requirements["imports_ml_libraries"] = True
                        requirements["ml_libraries"].append(alias.name)
                self.generic_visit(node)
            
            def visit_ImportFrom(self, node):
                if node.module and any(lib in node.module for lib in ["tensorflow", "torch", "sklearn", "transformers"]):
                    requirements["imports_ml_libraries"] = True
                    requirements["ml_libraries"].append(node.module)
                self.generic_visit(node)
        
        MLChecker().visit(tree)
        return requirements
    
    def test_ml_bot(self, bot_id: int, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test ML bot with sample data"""
        try:
            bot = self.load_bot_with_models(bot_id)
            if not bot:
                return {"success": False, "error": "Failed to load bot"}
            
            # Test basic functionality
            basic_test = self.test_bot(bot_id, test_data)
            if not basic_test["success"]:
                return basic_test
            
            # Test ML-specific functionality
            if hasattr(bot, 'models') and bot.models:
                try:
                    # Test model prediction if available
                    if hasattr(bot, 'predict_with_model'):
                        sample_input = test_data.get('model_input', [])
                        if sample_input:
                            model_prediction = bot.predict_with_model(sample_input)
                            basic_test["model_prediction"] = model_prediction
                            
                except Exception as e:
                    basic_test["warnings"] = basic_test.get("warnings", [])
                    basic_test["warnings"].append(f"Model prediction test failed: {e}")
            
            return basic_test
            
        except Exception as e:
            return {"success": False, "error": f"ML bot test failed: {str(e)}"}
    
    def get_bot_files(self, bot_id: int) -> List[schemas.BotFileInDB]:
        """Get all files for a bot"""
        db = SessionLocal()
        try:
            files = db.query(models.BotFile).filter(
                models.BotFile.bot_id == bot_id,
                models.BotFile.is_active == True
            ).all()
            
            return [schemas.BotFileInDB.from_orm(file) for file in files]
            
        finally:
            db.close()
    
    def delete_bot_file(self, file_id: int) -> bool:
        """Delete a bot file"""
        db = SessionLocal()
        try:
            file_record = db.query(models.BotFile).filter(models.BotFile.id == file_id).first()
            if not file_record:
                return False
            
            # Mark as inactive instead of deleting
            file_record.is_active = False
            db.commit()
            
            # Remove from filesystem
            if os.path.exists(file_record.file_path):
                os.remove(file_record.file_path)
            
            # Remove from cache if loaded
            if file_record.bot_id in self.loaded_bots:
                del self.loaded_bots[file_record.bot_id]
            
            if file_record.bot_id in self.model_manager.loaded_models:
                del self.model_manager.loaded_models[file_record.bot_id]
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting bot file: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    # S3 Integration Methods
    def upload_bot_to_s3(self, bot_id: int, code_content: str, version: str = None) -> Dict[str, Any]:
        """Upload bot code to S3"""
        try:
            upload_result = self.s3_manager.upload_bot_code(
                bot_id=bot_id,
                code_content=code_content,
                version=version
            )
            logger.info(f"Bot {bot_id} uploaded to S3: {upload_result['s3_key']}")
            return upload_result
        except Exception as e:
            logger.error(f"Error uploading bot to S3: {e}")
            raise
    
    def upload_model_to_s3(self, bot_id: int, model_data: bytes, filename: str,
                          model_type: str, framework: str, version: str = None) -> Dict[str, Any]:
        """Upload ML model to S3"""
        try:
            upload_result = self.s3_manager.upload_ml_model(
                bot_id=bot_id,
                model_data=model_data,
                filename=filename,
                model_type=model_type,
                framework=framework,
                version=version
            )
            logger.info(f"Model {model_type} for bot {bot_id} uploaded to S3: {upload_result['s3_key']}")
            return upload_result
        except Exception as e:
            logger.error(f"Error uploading model to S3: {e}")
            raise
    
    def load_bot_from_s3(self, bot_id: int, version: Optional[str] = None, user_config: Dict[str, Any] = None,
                        user_api_keys: Dict[str, str] = None) -> Optional[CustomBot]:
        """Load bot from S3 with all dependencies"""
        try:
            # Check if already loaded
            cache_key = f"{bot_id}_{version or 'latest'}"
            if cache_key in self.loaded_bots:
                return self.loaded_bots[cache_key]
            
            # Download bot code from S3
            code_content = self.s3_manager.download_bot_code(bot_id, version)
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
            temp_file.write(code_content)
            temp_file.close()
            
            try:
                # Import bot module
                spec = importlib.util.spec_from_file_location(f"bot_{bot_id}", temp_file.name)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find bot class
                bot_class = None
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, CustomBot) and obj != CustomBot:
                        bot_class = obj
                        break
                
                if not bot_class:
                    logger.error(f"No CustomBot subclass found for bot {bot_id}")
                    return None
                
                # Prepare configuration
                config = user_config or {}
                
                # Load ML models from S3 if needed
                models_dict = self.load_models_from_s3(bot_id, version)
                if models_dict:
                    config['models'] = models_dict
                
                # Create bot instance
                api_keys = user_api_keys or {}
                bot_instance = bot_class(config, api_keys)
                
                # Cache the bot
                self.loaded_bots[cache_key] = bot_instance
                
                logger.info(f"Bot {bot_id} loaded from S3 successfully")
                return bot_instance
                
            finally:
                # Clean up temporary file
                os.unlink(temp_file.name)
                
        except Exception as e:
            logger.error(f"Error loading bot from S3: {e}")
            return None
    
    def load_models_from_s3(self, bot_id: int, version: str = None) -> Dict[str, Any]:
        """Load ML models from S3"""
        try:
            models_dict = {"models": {}, "scalers": {}}
            
            # Try to load different model types
            for model_type in ["MODEL", "WEIGHTS", "CONFIG"]:
                try:
                    model_data = self.s3_manager.download_ml_model(bot_id, model_type, version)
                    
                    # Create temporary file
                    temp_file = tempfile.NamedTemporaryFile(delete=False)
                    temp_file.write(model_data)
                    temp_file.close()
                    
                    try:
                        # Load model based on type
                        if model_type == "MODEL":
                            # Try different loading methods
                            try:
                                import tensorflow as tf
                                model = tf.keras.models.load_model(temp_file.name)
                                models_dict["models"][model_type] = model
                            except:
                                try:
                                    import torch
                                    model = torch.load(temp_file.name, map_location='cpu')
                                    models_dict["models"][model_type] = model
                                except:
                                    model = joblib.load(temp_file.name)
                                    models_dict["models"][model_type] = model
                        
                        elif model_type == "WEIGHTS":
                            # Load scaler or weights
                            try:
                                scaler = joblib.load(temp_file.name)
                                models_dict["scalers"]["SCALER"] = scaler
                            except:
                                import pickle
                                with open(temp_file.name, 'rb') as f:
                                    weights = pickle.load(f)
                                models_dict["models"]["WEIGHTS"] = weights
                        
                        elif model_type == "CONFIG":
                            # Load configuration
                            with open(temp_file.name, 'r') as f:
                                config = json.load(f)
                            models_dict["config"] = config
                    
                    finally:
                        os.unlink(temp_file.name)
                        
                except FileNotFoundError:
                    # Model type not available
                    continue
                except Exception as e:
                    logger.warning(f"Error loading {model_type} for bot {bot_id}: {e}")
                    continue
            
            return models_dict
            
        except Exception as e:
            logger.error(f"Error loading models from S3: {e}")
            return {}
    
    def list_bot_versions_s3(self, bot_id: int) -> List[str]:
        """List all versions of a bot in S3"""
        try:
            return self.s3_manager.list_versions(bot_id)
        except Exception as e:
            logger.error(f"Error listing bot versions: {e}")
            return []
    
    def get_bot_metadata_s3(self, bot_id: int, version: str) -> Dict[str, Any]:
        """Get bot metadata from S3"""
        try:
            return self.s3_manager.get_bot_metadata(bot_id, version)
        except Exception as e:
            logger.error(f"Error getting bot metadata: {e}")
            return {}
    
    def delete_bot_version_s3(self, bot_id: int, version: str) -> bool:
        """Delete a bot version from S3"""
        try:
            return self.s3_manager.delete_bot_version(bot_id, version)
        except Exception as e:
            logger.error(f"Error deleting bot version: {e}")
            return False
    
    def get_storage_stats_s3(self, bot_id: int = None) -> Dict[str, Any]:
        """Get storage statistics from S3"""
        try:
            return self.s3_manager.get_storage_stats(bot_id)
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {}

# Global instances
bot_manager = BotManager()
model_manager = bot_manager.model_manager 