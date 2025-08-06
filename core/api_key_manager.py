"""
Secure API Key Management System
Handles encryption/decryption and retrieval of exchange API keys by user
"""

import os
import base64
import logging
from typing import Dict, Optional, List
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy.orm import Session

from core import models, crud
from core.database import get_db

logger = logging.getLogger(__name__)

class APIKeyManager:
    """Secure API Key Manager with encryption"""
    
    def __init__(self):
        """Initialize with encryption key from environment"""
        self._encryption_key = self._get_or_create_encryption_key()
        self._fernet = Fernet(self._encryption_key)
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get encryption key from environment or generate new one"""
        import base64
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes

        # First try to get key from environment
        env_key = os.getenv('API_KEY_ENCRYPTION_KEY')
        if env_key:
            try:
                return env_key.encode()
                # return base64.urlsafe_b64decode(env_key)
            except Exception as e:
                logger.warning(f"Invalid encryption key in environment: {e}")
        
        # Generate new key from password
        password = os.getenv('API_KEY_MASTER_PASSWORD', 'default_dev_password_change_in_production').encode()
        salt = os.getenv('API_KEY_SALT', 'default_salt_change_in_production').encode()

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = kdf.derive(password)
        encoded_key = base64.urlsafe_b64encode(key)  # ✅ encode đúng format Fernet

        logger.warning("Generated encryption key from password. Set API_KEY_ENCRYPTION_KEY in environment for production!")
        return encoded_key

    
    def encrypt_api_key(self, api_key: str) -> str:
        """Encrypt API key for storage"""
        if not api_key:
            return ""
        
        try:
            encrypted = self._fernet.encrypt(api_key.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt API key: {e}")
            raise ValueError("API key encryption failed")
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """Decrypt API key for use"""
        if not encrypted_key:
            return ""
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_key.encode())
            decrypted = self._fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt API key: {e}")
            raise ValueError("API key decryption failed")
    
    def get_user_exchange_credentials(self, db: Session, user_id: int, 
                                    exchange: str = "BINANCE", 
                                    is_testnet: bool = True) -> Optional[Dict[str, str]]:
        """
        Get decrypted exchange credentials for user
        
        Args:
            db: Database session
            user_id: User ID
            exchange: Exchange name (BINANCE, COINBASE, etc.)
            is_testnet: Whether to get testnet or mainnet credentials
            
        Returns:
            Dict with decrypted api_key, api_secret, api_passphrase
        """
        try:
            # Get encrypted credentials from database
            credentials = crud.get_user_exchange_credentials(
                db, user_id=user_id, exchange=exchange, is_testnet=is_testnet
            )
            
            if not credentials:
                logger.warning(f"No {exchange} credentials found for user {user_id} (testnet={is_testnet})")
                return None
            
            cred = credentials[0]  # Get first matching credential
            
            # Decrypt credentials
            decrypted_credentials = {
                'api_key': self.decrypt_api_key(cred.api_key),
                'api_secret': self.decrypt_api_key(cred.api_secret),
                'api_passphrase': self.decrypt_api_key(cred.api_passphrase) if cred.api_passphrase else None,
                'is_testnet': cred.is_testnet,
                'exchange': cred.exchange.value,
                'validation_status': cred.validation_status,
                'last_validated': cred.last_validated
            }
            
            logger.info(f"Retrieved {exchange} credentials for user {user_id} (testnet={is_testnet})")
            return decrypted_credentials
            
        except Exception as e:
            logger.error(f"Failed to get exchange credentials: {e}")
            return None
    
    def get_user_credentials_by_principal_id(self, db: Session, 
                                           user_principal_id: str,
                                           exchange: str = "BINANCE",
                                           is_testnet: bool = True) -> Optional[Dict[str, str]]:
        """
        Get user exchange credentials directly by ICP Principal ID
        
        Args:
            db: Database session
            user_principal_id: ICP Principal ID
            exchange: Exchange name
            is_testnet: Whether to get testnet credentials
            
        Returns:
            Dict with decrypted credentials
        """
        try:
            # Query credentials directly by principal_id
            credentials = db.query(models.ExchangeCredentials).filter(
                models.ExchangeCredentials.principal_id == user_principal_id,
                models.ExchangeCredentials.exchange == exchange,
                models.ExchangeCredentials.is_testnet == is_testnet,
                models.ExchangeCredentials.is_active == True
            ).first()
            
            if not credentials:
                logger.warning(f"No credentials found for principal ID: {user_principal_id}, exchange: {exchange}, testnet: {is_testnet}")
                return None
            
            # Decrypt credentials
            decrypted_key = self.decrypt_api_key(credentials.api_key)
            decrypted_secret = self.decrypt_api_key(credentials.api_secret)
            decrypted_passphrase = self.decrypt_api_key(credentials.api_passphrase) if credentials.api_passphrase else None
            
            result = {
                'api_key': decrypted_key,
                'api_secret': decrypted_secret,
                'is_testnet': credentials.is_testnet
            }
            
            if decrypted_passphrase:
                result['api_passphrase'] = decrypted_passphrase
                
            logger.info(f"Found credentials for principal ID: {user_principal_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get credentials by principal ID: {e}")
            return None
    
    def store_user_exchange_credentials(self, db: Session, user_id: int,
                                      exchange: str, api_key: str, api_secret: str,
                                      api_passphrase: str = None, is_testnet: bool = True) -> bool:
        """
        Store encrypted exchange credentials for user
        
        Args:
            db: Database session
            user_id: User ID
            exchange: Exchange name
            api_key: Plain API key
            api_secret: Plain API secret
            api_passphrase: Plain API passphrase (optional)
            is_testnet: Whether these are testnet credentials
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Encrypt credentials
            encrypted_key = self.encrypt_api_key(api_key)
            encrypted_secret = self.encrypt_api_key(api_secret)
            encrypted_passphrase = self.encrypt_api_key(api_passphrase) if api_passphrase else None
            
            # Check if credentials already exist
            existing = crud.get_user_exchange_credentials(
                db, user_id=user_id, exchange=exchange, is_testnet=is_testnet
            )
            
            if existing:
                # Update existing credentials
                cred = existing[0]
                cred.api_key = encrypted_key
                cred.api_secret = encrypted_secret
                cred.api_passphrase = encrypted_passphrase
                cred.validation_status = "pending"
                db.commit()
                logger.info(f"Updated {exchange} credentials for user {user_id}")
            else:
                # Create new credentials
                new_cred = models.ExchangeCredentials(
                    user_id=user_id,
                    exchange=models.ExchangeType(exchange),
                    api_key=encrypted_key,
                    api_secret=encrypted_secret,
                    api_passphrase=encrypted_passphrase,
                    is_testnet=is_testnet,
                    validation_status="pending"
                )
                db.add(new_cred)
                db.commit()
                logger.info(f"Created new {exchange} credentials for user {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store exchange credentials: {e}")
            db.rollback()
            return False
    
    def validate_exchange_credentials(self, db: Session, user_id: int, 
                                    exchange: str, is_testnet: bool = True) -> bool:
        """
        Validate exchange credentials by testing API connection
        
        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            credentials = self.get_user_exchange_credentials(
                db, user_id, exchange, is_testnet
            )
            
            if not credentials:
                return False
            
            # Test credentials with exchange
            from services.exchange_factory import ExchangeFactory
            
            exchange_client = ExchangeFactory.create_exchange(
                exchange_name=exchange,
                api_key=credentials['api_key'],
                api_secret=credentials['api_secret'],
                testnet=is_testnet
            )
            
            # Test connection
            test_result = exchange_client.test_connectivity()
            
            # Update validation status
            cred_records = crud.get_user_exchange_credentials(
                db, user_id=user_id, exchange=exchange, is_testnet=is_testnet
            )
            
            if cred_records:
                cred = cred_records[0]
                cred.validation_status = "valid" if test_result else "invalid"
                cred.last_validated = models.func.now()
                db.commit()
            
            logger.info(f"Credentials validation for user {user_id}: {'valid' if test_result else 'invalid'}")
            return test_result
            
        except Exception as e:
            logger.error(f"Failed to validate credentials: {e}")
            return False
    
    def get_all_user_exchanges(self, db: Session, user_id: int) -> List[Dict[str, any]]:
        """Get all exchange credentials for a user"""
        try:
            all_credentials = db.query(models.ExchangeCredentials).filter(
                models.ExchangeCredentials.user_id == user_id,
                models.ExchangeCredentials.is_active == True
            ).all()
            
            result = []
            for cred in all_credentials:
                result.append({
                    'id': cred.id,
                    'exchange': cred.exchange.value,
                    'is_testnet': cred.is_testnet,
                    'validation_status': cred.validation_status,
                    'last_validated': cred.last_validated,
                    'created_at': cred.created_at
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get user exchanges: {e}")
            return []
    
    def store_user_exchange_credentials_by_principal_id(
        self, db: Session, principal_id: str, exchange: str, 
        api_key: str, api_secret: str, api_passphrase: str = None, 
        is_testnet: bool = True
    ) -> bool:
        """
        Store exchange credentials directly with principal ID (no user mapping required)
        
        Args:
            db: Database session
            principal_id: ICP Principal ID
            exchange: Exchange name (BINANCE, COINBASE, KRAKEN)
            api_key: Plain API key
            api_secret: Plain API secret
            api_passphrase: Plain API passphrase (optional)
            is_testnet: Whether these are testnet credentials
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Encrypt credentials
            encrypted_key = self.encrypt_api_key(api_key)
            encrypted_secret = self.encrypt_api_key(api_secret)
            encrypted_passphrase = self.encrypt_api_key(api_passphrase) if api_passphrase else None
            
            # Check if credentials already exist for this principal ID
            existing = db.query(models.ExchangeCredentials).filter(
                models.ExchangeCredentials.principal_id == principal_id,
                models.ExchangeCredentials.exchange == exchange,
                models.ExchangeCredentials.is_testnet == is_testnet
            ).first()
            
            if existing:
                # Update existing credentials
                existing.api_key = encrypted_key
                existing.api_secret = encrypted_secret
                existing.api_passphrase = encrypted_passphrase
                existing.validation_status = "pending"
                db.commit()
                logger.info(f"Updated {exchange} credentials for principal ID: {principal_id}")
            else:
                # Create new credentials
                new_cred = models.ExchangeCredentials(
                    user_id=None,  # No user mapping for marketplace users
                    principal_id=principal_id,
                    exchange=models.ExchangeType(exchange),
                    api_key=encrypted_key,
                    api_secret=encrypted_secret,
                    api_passphrase=encrypted_passphrase,
                    is_testnet=is_testnet,
                    validation_status="pending"
                )
                db.add(new_cred)
                db.commit()
                logger.info(f"Created new {exchange} credentials for principal ID: {principal_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store credentials by principal ID: {e}")
            db.rollback()
            return False

# Global instance
api_key_manager = APIKeyManager()

def get_bot_api_keys(user_principal_id: str, exchange: str = "BINANCE", 
                    is_testnet: bool = True) -> Optional[Dict[str, str]]:
    """
    Convenience function to get API keys for bot initialization
    
    Args:
        user_principal_id: ICP Principal ID
        exchange: Exchange name
        is_testnet: Whether to get testnet credentials
        
    Returns:
        Dict with api_key and api_secret for bot initialization
    """
    try:
        # Get database session
        db = next(get_db())
        
        credentials = api_key_manager.get_user_credentials_by_principal_id(
            db, user_principal_id, exchange, is_testnet
        )
        
        if credentials:
            return {
                'api_key': credentials['api_key'],
                'api_secret': credentials['api_secret'],
                'testnet': credentials['is_testnet']
            }
        
        logger.warning(f"No credentials found for principal ID: {user_principal_id}")
        return None
        
    except Exception as e:
        logger.error(f"Failed to get bot API keys: {e}")
        return None
    finally:
        db.close()