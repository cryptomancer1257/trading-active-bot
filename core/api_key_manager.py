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
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
        Get decrypted exchange credentials for user (legacy - use principal_id version)
        
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
            logger.info(f"Found credentials for user {user_id} (testnet={is_testnet}): {cred.api_key}")
            
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
                'passphrase': decrypted_passphrase or '',  # Consistent key name for OKX/Bitget
                'is_testnet': credentials.is_testnet
            }
            
            logger.info(f"Found credentials for principal ID: {user_principal_id} (passphrase: {'✅' if decrypted_passphrase else '❌'})")
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
        is_testnet: bool = True, credential_type: str = 'SPOT'
    ) -> bool:
        """
        Store exchange credentials directly with principal ID (no user mapping required)
        
        Args:
            db: Database session
            principal_id: ICP Principal ID
            exchange: Exchange name (BINANCE, BYBIT, OKX, etc.)
            api_key: Plain API key
            api_secret: Plain API secret
            api_passphrase: Plain API passphrase (optional)
            is_testnet: Whether these are testnet credentials
            credential_type: Trading mode (SPOT, FUTURES, MARGIN)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Normalize credential_type
            cred_type_upper = str(credential_type).upper() if credential_type else 'SPOT'
            cred_type_enum = models.CredentialType(cred_type_upper)
            
            # Encrypt credentials
            encrypted_key = self.encrypt_api_key(api_key)
            encrypted_secret = self.encrypt_api_key(api_secret)
            encrypted_passphrase = self.encrypt_api_key(api_passphrase) if api_passphrase else None
            
            # Check if credentials already exist for this principal ID + exchange + testnet + credential_type
            existing = db.query(models.ExchangeCredentials).filter(
                models.ExchangeCredentials.principal_id == principal_id,
                models.ExchangeCredentials.exchange == exchange,
                models.ExchangeCredentials.is_testnet == is_testnet,
                models.ExchangeCredentials.credential_type == cred_type_enum
            ).first()
            
            if existing:
                # Update existing credentials
                existing.api_key = encrypted_key
                existing.api_secret = encrypted_secret
                existing.api_passphrase = encrypted_passphrase
                existing.validation_status = "pending"
                db.commit()
                logger.info(f"Updated {exchange} {cred_type_upper} credentials for principal ID: {principal_id}")
            else:
                # Create new credentials
                new_cred = models.ExchangeCredentials(
                    user_id=None,  # No user mapping for marketplace users
                    principal_id=principal_id,
                    exchange=models.ExchangeType(exchange),
                    credential_type=cred_type_enum,
                    api_key=encrypted_key,
                    api_secret=encrypted_secret,
                    api_passphrase=encrypted_passphrase,
                    is_testnet=is_testnet,
                    validation_status="pending"
                )
                db.add(new_cred)
                db.commit()
                logger.info(f"Created new {exchange} {cred_type_upper} credentials for principal ID: {principal_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store credentials by principal ID: {e}")
            db.rollback()
            return False

# Global instance
api_key_manager = APIKeyManager()

def get_bot_api_keys(user_principal_id: str, exchange: str = "BINANCE", 
                    is_testnet: bool = True, subscription_id: int = None) -> Optional[Dict[str, str]]:
    """
    Convenience function to get API keys for bot initialization
    
    Args:
        user_principal_id: ICP Principal ID
        exchange: Exchange name
        is_testnet: Whether to get testnet credentials
        subscription_id: Subscription ID to check payment method
        
    Returns:
        Dict with api_key and api_secret for bot initialization
    """
    try:
        # Get database session
        db = next(get_db())
        
        # Check if this is a TRIAL subscription
        is_trial_payment = False
        if subscription_id:
            subscription = db.query(models.Subscription).filter(
                models.Subscription.id == subscription_id
            ).first()
            
            if subscription:
                logger.info(f"Found subscription {subscription_id}: payment_method={subscription.payment_method}, bot_id={subscription.bot_id}")
                if subscription.payment_method == models.PaymentMethod.TRIAL:
                    is_trial_payment = True
                    logger.info(f"TRIAL subscription detected for {user_principal_id}, using developer credentials")
            else:
                logger.warning(f"No subscription found with ID {subscription_id}")
        
        # For TRIAL payments, use developer credentials from developer_exchange_credentials table
        if is_trial_payment:
            # Get the bot's developer credentials
            if subscription and subscription.bot:
                developer_id = subscription.bot.developer_id
                logger.info(f"Looking for developer credentials: developer_id={developer_id}, exchange={exchange}, is_testnet={is_testnet}")
                
                # Query developer_exchange_credentials table
                # Convert string exchange to ExchangeType enum
                exchange_enum = getattr(models.ExchangeType, exchange, None)
                if not exchange_enum:
                    logger.error(f"Invalid exchange type: {exchange}")
                    return None
                
                # Special handling for exchanges without testnet
                # Bitget doesn't have testnet - always use mainnet
                if exchange == 'BITGET' and is_testnet:
                    logger.warning(f"⚠️ {exchange} does not have testnet! Using MAINNET credentials instead.")
                    logger.warning(f"   All trades will be REAL (real money). Use small amounts!")
                    network_type = models.NetworkType.MAINNET  # Force mainnet for Bitget
                else:
                    network_type = models.NetworkType.TESTNET if is_testnet else models.NetworkType.MAINNET
                dev_credentials = db.query(models.DeveloperExchangeCredentials).filter(
                    models.DeveloperExchangeCredentials.user_id == developer_id,
                    models.DeveloperExchangeCredentials.exchange_type == exchange_enum,
                    models.DeveloperExchangeCredentials.network_type == network_type,
                    models.DeveloperExchangeCredentials.is_active == True
                ).first()
                
                if dev_credentials:
                    logger.info(f"Found developer credentials: id={dev_credentials.id}, name={dev_credentials.name}")
                    # Decrypt developer credentials using Security module
                    from core.security import decrypt_sensitive_data
                    
                    # Decrypt developer credentials using Security module
                    decrypted_key = decrypt_sensitive_data(dev_credentials.api_key)
                    decrypted_secret = decrypt_sensitive_data(dev_credentials.api_secret)
                    
                    # Check if still encrypted (only if it looks like encrypted data AND is very long)
                    if decrypted_key.startswith('Z0FBQUFBQm8z') and len(decrypted_key) > 200:
                        logger.info("Detected double encryption, decrypting again...")
                        decrypted_key = decrypt_sensitive_data(decrypted_key)
                        decrypted_secret = decrypt_sensitive_data(decrypted_secret)
                        logger.info("Double decryption completed")
                    
                    logger.info(f"Using developer credentials for TRIAL subscription {subscription_id}")
                    
                    # Decrypt passphrase if exists (required for OKX, Bitget)
                    passphrase = ""
                    if dev_credentials.passphrase:
                        logger.info(f"🔐 Decrypting passphrase for {exchange} (length: {len(dev_credentials.passphrase)})")
                        passphrase = decrypt_sensitive_data(dev_credentials.passphrase)
                        if passphrase.startswith('Z0FBQUFBQm8z') and len(passphrase) > 200:
                            logger.info("   Double encryption detected, decrypting again...")
                            passphrase = decrypt_sensitive_data(passphrase)
                        logger.info(f"✅ Passphrase decrypted for {exchange} (length: {len(passphrase)})")
                    else:
                        # Only warn if passphrase is actually required for this exchange
                        if exchange in ['OKX', 'BITGET']:
                            logger.warning(f"❌ No passphrase found in database for {exchange} (REQUIRED!)")
                        else:
                            logger.info(f"ℹ️  No passphrase for {exchange} (not required)")
                    
                    # For Bitget, always return testnet=False since they don't have testnet
                    actual_testnet = dev_credentials.network_type == models.NetworkType.TESTNET
                    if exchange == 'BITGET':
                        actual_testnet = False  # Bitget always uses mainnet
                    
                    return {
                        'api_key': decrypted_key,
                        'api_secret': decrypted_secret,
                        'passphrase': passphrase,
                        'testnet': actual_testnet
                    }
                else:
                    logger.warning(f"No developer credentials found for developer {developer_id}, exchange: {exchange}, network: {'TESTNET' if is_testnet else 'MAINNET'}")
                    # Let's also check what credentials exist for this developer
                    all_dev_creds = db.query(models.DeveloperExchangeCredentials).filter(
                        models.DeveloperExchangeCredentials.user_id == developer_id,
                        models.DeveloperExchangeCredentials.is_active == True
                    ).all()
                    logger.info(f"Available developer credentials for developer {developer_id}: {[(c.exchange_type, c.network_type, c.name) for c in all_dev_creds]}")
            else:
                logger.warning(f"No bot found for subscription {subscription_id} or bot has no developer_id")
        
        # For non-TRIAL payments, use user credentials as before
        credentials = api_key_manager.get_user_credentials_by_principal_id(
            db, user_principal_id, exchange, is_testnet
        )
        
        if credentials:
            return {
                'api_key': credentials['api_key'],
                'api_secret': credentials['api_secret'],
                'passphrase': credentials.get('passphrase', ''),  # Include passphrase for OKX, Bitget
                'testnet': credentials['is_testnet']
            }
        
        logger.warning(f"No credentials found for principal ID: {user_principal_id}")
        return None
        
    except Exception as e:
        logger.error(f"Failed to get bot API keys: {e}")
        return None
    finally:
        db.close()