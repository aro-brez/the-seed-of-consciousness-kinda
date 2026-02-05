"""Encryption utilities for REALIZE-IO data protection"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64

logger = logging.getLogger(__name__)


class EncryptionManager:
    """Manages encryption for personal data in REALIZE-IO"""
    
    def __init__(self, key_path: Optional[str] = None):
        self.key_path = key_path or str(Path("~/.realize_io/master.key").expanduser())
        self.fernet = None
        self._initialize_encryption()
        
    def _initialize_encryption(self):
        """Initialize encryption with existing or new key"""
        key_file = Path(self.key_path)
        
        if key_file.exists():
            # Load existing key
            with open(key_file, 'rb') as f:
                key = f.read()
            logger.info("Loaded existing encryption key")
        else:
            # Generate new key
            key = Fernet.generate_key()
            key_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Secure key file permissions
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)  # Read/write for owner only
            logger.info("Generated new encryption key")
            
        self.fernet = Fernet(key)
        
    def encrypt_data(self, data: Union[str, Dict[str, Any]]) -> bytes:
        """Encrypt data (string or dict)"""
        if isinstance(data, dict):
            data = json.dumps(data)
        elif not isinstance(data, str):
            data = str(data)
            
        return self.fernet.encrypt(data.encode())
        
    def decrypt_data(self, encrypted_data: bytes) -> Dict[str, Any]:
        """Decrypt data and return as dict"""
        try:
            decrypted_bytes = self.fernet.decrypt(encrypted_data)
            decrypted_str = decrypted_bytes.decode()
            return json.loads(decrypted_str)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to decrypt/parse data: {e}")
            raise
            
    def decrypt_to_string(self, encrypted_data: bytes) -> str:
        """Decrypt data and return as string"""
        decrypted_bytes = self.fernet.decrypt(encrypted_data)
        return decrypted_bytes.decode()
        
    def encrypt_file(self, file_path: str, output_path: Optional[str] = None):
        """Encrypt a file"""
        input_file = Path(file_path)
        output_file = Path(output_path) if output_path else Path(f"{file_path}.encrypted")
        
        with open(input_file, 'rb') as f:
            data = f.read()
            
        encrypted_data = self.fernet.encrypt(data)
        
        with open(output_file, 'wb') as f:
            f.write(encrypted_data)
            
        # Secure permissions
        os.chmod(output_file, 0o600)
        logger.info(f"Encrypted {input_file} -> {output_file}")
        
    def decrypt_file(self, encrypted_file_path: str, output_path: Optional[str] = None):
        """Decrypt a file"""
        input_file = Path(encrypted_file_path)
        output_file = Path(output_path) if output_path else Path(str(input_file).replace('.encrypted', ''))
        
        with open(input_file, 'rb') as f:
            encrypted_data = f.read()
            
        decrypted_data = self.fernet.decrypt(encrypted_data)
        
        with open(output_file, 'wb') as f:
            f.write(decrypted_data)
            
        logger.info(f"Decrypted {input_file} -> {output_file}")
        
    @staticmethod
    def generate_derived_key(password: str, salt: bytes = None) -> Fernet:
        """Generate encryption key from password"""
        if salt is None:
            salt = os.urandom(16)
            
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return Fernet(key)


class SecureStorage:
    """Secure storage wrapper for sensitive data"""
    
    def __init__(self, storage_path: str, encryption_manager: EncryptionManager = None):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.encryption_manager = encryption_manager or EncryptionManager()
        
    def store(self, key: str, data: Dict[str, Any]):
        """Store encrypted data with key"""
        encrypted_data = self.encryption_manager.encrypt_data(data)
        
        # Create key-specific file
        key_file = self.storage_path / f"{key}.enc"
        with open(key_file, 'wb') as f:
            f.write(encrypted_data)
            
        # Secure permissions
        os.chmod(key_file, 0o600)
        logger.debug(f"Stored encrypted data for key: {key}")
        
    def retrieve(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve and decrypt data by key"""
        key_file = self.storage_path / f"{key}.enc"
        
        if not key_file.exists():
            return None
            
        try:
            with open(key_file, 'rb') as f:
                encrypted_data = f.read()
                
            return self.encryption_manager.decrypt_data(encrypted_data)
        except Exception as e:
            logger.error(f"Failed to retrieve data for key {key}: {e}")
            return None
            
    def delete(self, key: str) -> bool:
        """Delete stored data"""
        key_file = self.storage_path / f"{key}.enc"
        
        if key_file.exists():
            key_file.unlink()
            logger.info(f"Deleted encrypted data for key: {key}")
            return True
        return False
        
    def list_keys(self) -> list:
        """List all stored keys"""
        return [f.stem for f in self.storage_path.glob("*.enc")]


# Global encryption instance
encryption_manager = EncryptionManager()