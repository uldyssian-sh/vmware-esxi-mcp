"""
Enterprise Secrets Management for VMware ESXi MCP Server

Provides secure storage and retrieval of sensitive configuration data using
multiple backends including Python Keyring and HashiCorp Vault integration.

Author: uldyssian-sh
License: MIT
"""

import os
import json
import base64
import hashlib
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import warnings

# Optional imports with graceful fallback
try:
    import keyring
    from keyring.backends import SecretService, macOS, Windows
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    warnings.warn("Python keyring not available. Using fallback storage.", ImportWarning)

try:
    import hvac  # HashiCorp Vault client
    VAULT_AVAILABLE = True
except ImportError:
    VAULT_AVAILABLE = False
    warnings.warn("HashiCorp Vault client not available. Vault integration disabled.", ImportWarning)

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    warnings.warn("Cryptography library not available. Local encryption disabled.", ImportWarning)

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class SecretBackend(Enum):
    """Available secret storage backends"""
    KEYRING = "keyring"
    VAULT = "vault"
    ENCRYPTED_FILE = "encrypted_file"
    ENVIRONMENT = "environment"
    MEMORY = "memory"  # Fallback for development


@dataclass
class VaultConfig:
    """HashiCorp Vault configuration"""
    url: str
    token: Optional[str] = None
    mount_point: str = "secret"
    namespace: Optional[str] = None
    verify_ssl: bool = True
    timeout: int = 30


@dataclass
class SecretConfig:
    """Secret storage configuration"""
    backend: SecretBackend
    service_name: str = "vmware-vcenter-mcp"
    vault_config: Optional[VaultConfig] = None
    encryption_key: Optional[str] = None
    file_path: Optional[str] = None


class EnterpriseSecretsManager:
    """Enterprise-grade secrets management with multiple backends"""
    
    def __init__(self, config: SecretConfig):
        self.config = config
        self.backend = config.backend
        self.service_name = config.service_name
        
        # Initialize backend-specific clients
        self.vault_client = None
        self.fernet = None
        self._memory_store = {}  # Fallback storage
        
        self._initialize_backend()
        
        logger.info("Secrets manager initialized",
                   extra={"backend": self.backend.value, "service_name": self.service_name})
    
    def _initialize_backend(self):
        """Initialize the selected backend"""
        
        if self.backend == SecretBackend.KEYRING:
            if not KEYRING_AVAILABLE:
                logger.warning("Keyring not available, falling back to memory storage")
                self.backend = SecretBackend.MEMORY
                return
            
            # Configure keyring backend priority
            self._configure_keyring()
            
        elif self.backend == SecretBackend.VAULT:
            if not VAULT_AVAILABLE:
                logger.warning("Vault client not available, falling back to keyring")
                self.backend = SecretBackend.KEYRING
                self._initialize_backend()
                return
            
            self._initialize_vault()
            
        elif self.backend == SecretBackend.ENCRYPTED_FILE:
            if not CRYPTO_AVAILABLE:
                logger.warning("Cryptography not available, falling back to keyring")
                self.backend = SecretBackend.KEYRING
                self._initialize_backend()
                return
            
            self._initialize_encryption()
    
    def _configure_keyring(self):
        """Configure keyring backend priority"""
        if not KEYRING_AVAILABLE:
            return
        
        # Set preferred backends based on platform
        import platform
        system = platform.system().lower()
        
        if system == "darwin":  # macOS
            keyring.set_keyring(macOS.Keyring())
        elif system == "windows":
            keyring.set_keyring(Windows.WinVaultKeyring())
        else:  # Linux
            try:
                keyring.set_keyring(SecretService.Keyring())
            except Exception:
                logger.warning("SecretService not available, using default keyring")
    
    def _initialize_vault(self):
        """Initialize HashiCorp Vault client"""
        if not self.config.vault_config:
            raise ValueError("Vault configuration required for Vault backend")
        
        vault_config = self.config.vault_config
        
        try:
            self.vault_client = hvac.Client(
                url=vault_config.url,
                token=vault_config.token,
                namespace=vault_config.namespace,
                verify=vault_config.verify_ssl,
                timeout=vault_config.timeout
            )
            
            # Verify connection
            if not self.vault_client.is_authenticated():
                raise ValueError("Vault authentication failed")
            
            logger.info("Vault client initialized successfully",
                       url=vault_config.url,
                       namespace=vault_config.namespace)
            
        except Exception as e:
            logger.error("Failed to initialize Vault client", error=str(e))
            raise
    
    def _initialize_encryption(self):
        """Initialize local file encryption"""
        if not self.config.encryption_key:
            # Generate key from service name and system info
            key_material = f"{self.service_name}-{os.getenv('USER', 'default')}"
            key_bytes = key_material.encode()
            
            # Derive encryption key using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'vmware-mcp-salt',  # In production, use random salt
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(key_bytes))
        else:
            key = self.config.encryption_key.encode()
        
        self.fernet = Fernet(key)
        logger.info("Local encryption initialized")
    
    def store_secret(self, key: str, value: Union[str, Dict[str, Any]]) -> bool:
        """Store a secret using the configured backend"""
        
        # Convert dict to JSON string
        if isinstance(value, dict):
            value = json.dumps(value)
        
        try:
            if self.backend == SecretBackend.KEYRING:
                return self._store_keyring(key, value)
            elif self.backend == SecretBackend.VAULT:
                return self._store_vault(key, value)
            elif self.backend == SecretBackend.ENCRYPTED_FILE:
                return self._store_encrypted_file(key, value)
            elif self.backend == SecretBackend.ENVIRONMENT:
                return self._store_environment(key, value)
            else:  # MEMORY fallback
                return self._store_memory(key, value)
                
        except Exception as e:
            logger.error("Failed to store secret", key=key, error=str(e))
            return False
    
    def retrieve_secret(self, key: str) -> Optional[Union[str, Dict[str, Any]]]:
        """Retrieve a secret using the configured backend"""
        
        try:
            if self.backend == SecretBackend.KEYRING:
                value = self._retrieve_keyring(key)
            elif self.backend == SecretBackend.VAULT:
                value = self._retrieve_vault(key)
            elif self.backend == SecretBackend.ENCRYPTED_FILE:
                value = self._retrieve_encrypted_file(key)
            elif self.backend == SecretBackend.ENVIRONMENT:
                value = self._retrieve_environment(key)
            else:  # MEMORY fallback
                value = self._retrieve_memory(key)
            
            if value is None:
                return None
            
            # Try to parse as JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logger.error("Failed to retrieve secret", key=key, error=str(e))
            return None
    
    def delete_secret(self, key: str) -> bool:
        """Delete a secret using the configured backend"""
        
        try:
            if self.backend == SecretBackend.KEYRING:
                return self._delete_keyring(key)
            elif self.backend == SecretBackend.VAULT:
                return self._delete_vault(key)
            elif self.backend == SecretBackend.ENCRYPTED_FILE:
                return self._delete_encrypted_file(key)
            elif self.backend == SecretBackend.ENVIRONMENT:
                return self._delete_environment(key)
            else:  # MEMORY fallback
                return self._delete_memory(key)
                
        except Exception as e:
            logger.error("Failed to delete secret", key=key, error=str(e))
            return False
    
    # Keyring backend methods
    def _store_keyring(self, key: str, value: str) -> bool:
        """Store secret in system keyring"""
        keyring.set_password(self.service_name, key, value)
        logger.debug("Secret stored in keyring", key=key)
        return True
    
    def _retrieve_keyring(self, key: str) -> Optional[str]:
        """Retrieve secret from system keyring"""
        value = keyring.get_password(self.service_name, key)
        if value:
            logger.debug("Secret retrieved from keyring", key=key)
        return value
    
    def _delete_keyring(self, key: str) -> bool:
        """Delete secret from system keyring"""
        try:
            keyring.delete_password(self.service_name, key)
            logger.debug("Secret deleted from keyring", key=key)
            return True
        except keyring.errors.PasswordDeleteError:
            return False
    
    # Vault backend methods
    def _store_vault(self, key: str, value: str) -> bool:
        """Store secret in HashiCorp Vault"""
        path = f"{self.service_name}/{key}"
        
        response = self.vault_client.secrets.kv.v2.create_or_update_secret(
            path=path,
            secret={"value": value},
            mount_point=self.config.vault_config.mount_point
        )
        
        logger.debug("Secret stored in Vault", key=key, path=path)
        return response is not None
    
    def _retrieve_vault(self, key: str) -> Optional[str]:
        """Retrieve secret from HashiCorp Vault"""
        path = f"{self.service_name}/{key}"
        
        try:
            response = self.vault_client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=self.config.vault_config.mount_point
            )
            
            if response and 'data' in response and 'data' in response['data']:
                value = response['data']['data'].get('value')
                if value:
                    logger.debug("Secret retrieved from Vault", key=key, path=path)
                return value
                
        except hvac.exceptions.InvalidPath:
            pass  # Secret doesn't exist
        
        return None
    
    def _delete_vault(self, key: str) -> bool:
        """Delete secret from HashiCorp Vault"""
        path = f"{self.service_name}/{key}"
        
        try:
            self.vault_client.secrets.kv.v2.delete_metadata_and_all_versions(
                path=path,
                mount_point=self.config.vault_config.mount_point
            )
            logger.debug("Secret deleted from Vault", key=key, path=path)
            return True
        except Exception:
            return False
    
    # Encrypted file backend methods
    def _store_encrypted_file(self, key: str, value: str) -> bool:
        """Store secret in encrypted file"""
        file_path = self.config.file_path or f"{self.service_name}_secrets.enc"
        
        # Load existing secrets
        secrets = self._load_encrypted_file()
        secrets[key] = value
        
        # Encrypt and save
        encrypted_data = self.fernet.encrypt(json.dumps(secrets).encode())
        
        with open(file_path, 'wb') as f:
            f.write(encrypted_data)
        
        logger.debug("Secret stored in encrypted file", key=key, file=file_path)
        return True
    
    def _retrieve_encrypted_file(self, key: str) -> Optional[str]:
        """Retrieve secret from encrypted file"""
        secrets = self._load_encrypted_file()
        value = secrets.get(key)
        
        if value:
            logger.debug("Secret retrieved from encrypted file", key=key)
        
        return value
    
    def _delete_encrypted_file(self, key: str) -> bool:
        """Delete secret from encrypted file"""
        file_path = self.config.file_path or f"{self.service_name}_secrets.enc"
        
        secrets = self._load_encrypted_file()
        if key in secrets:
            del secrets[key]
            
            # Re-encrypt and save
            encrypted_data = self.fernet.encrypt(json.dumps(secrets).encode())
            
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)
            
            logger.debug("Secret deleted from encrypted file", key=key)
            return True
        
        return False
    
    def _load_encrypted_file(self) -> Dict[str, str]:
        """Load and decrypt secrets file"""
        file_path = self.config.file_path or f"{self.service_name}_secrets.enc"
        
        if not os.path.exists(file_path):
            return {}
        
        try:
            with open(file_path, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
            
        except Exception as e:
            logger.error("Failed to load encrypted file", error=str(e))
            return {}
    
    # Environment backend methods
    def _store_environment(self, key: str, value: str) -> bool:
        """Store secret in environment variable"""
        env_key = f"{self.service_name.upper().replace('-', '_')}_{key.upper()}"
        os.environ[env_key] = value
        logger.debug("Secret stored in environment", key=key, env_key=env_key)
        return True
    
    def _retrieve_environment(self, key: str) -> Optional[str]:
        """Retrieve secret from environment variable"""
        env_key = f"{self.service_name.upper().replace('-', '_')}_{key.upper()}"
        value = os.getenv(env_key)
        
        if value:
            logger.debug("Secret retrieved from environment", key=key, env_key=env_key)
        
        return value
    
    def _delete_environment(self, key: str) -> bool:
        """Delete secret from environment variable"""
        env_key = f"{self.service_name.upper().replace('-', '_')}_{key.upper()}"
        
        if env_key in os.environ:
            del os.environ[env_key]
            logger.debug("Secret deleted from environment", key=key, env_key=env_key)
            return True
        
        return False
    
    # Memory backend methods (fallback)
    def _store_memory(self, key: str, value: str) -> bool:
        """Store secret in memory (fallback)"""
        self._memory_store[key] = value
        logger.debug("Secret stored in memory (fallback)", key=key)
        return True
    
    def _retrieve_memory(self, key: str) -> Optional[str]:
        """Retrieve secret from memory (fallback)"""
        value = self._memory_store.get(key)
        
        if value:
            logger.debug("Secret retrieved from memory (fallback)", key=key)
        
        return value
    
    def _delete_memory(self, key: str) -> bool:
        """Delete secret from memory (fallback)"""
        if key in self._memory_store:
            del self._memory_store[key]
            logger.debug("Secret deleted from memory (fallback)", key=key)
            return True
        
        return False
    
    def list_secrets(self) -> list:
        """List all stored secret keys"""
        try:
            if self.backend == SecretBackend.KEYRING:
                # Keyring doesn't support listing, return empty list
                return []
            elif self.backend == SecretBackend.VAULT:
                return self._list_vault_secrets()
            elif self.backend == SecretBackend.ENCRYPTED_FILE:
                secrets = self._load_encrypted_file()
                return list(secrets.keys())
            elif self.backend == SecretBackend.ENVIRONMENT:
                prefix = f"{self.service_name.upper().replace('-', '_')}_"
                return [key[len(prefix):].lower() for key in os.environ.keys() 
                       if key.startswith(prefix)]
            else:  # MEMORY fallback
                return list(self._memory_store.keys())
                
        except Exception as e:
            logger.error("Failed to list secrets", error=str(e))
            return []
    
    def _list_vault_secrets(self) -> list:
        """List secrets from Vault"""
        try:
            response = self.vault_client.secrets.kv.v2.list_secrets(
                path=self.service_name,
                mount_point=self.config.vault_config.mount_point
            )
            
            if response and 'data' in response and 'keys' in response['data']:
                return response['data']['keys']
                
        except hvac.exceptions.InvalidPath:
            pass  # No secrets exist
        
        return []
    
    def get_backend_info(self) -> Dict[str, Any]:
        """Get information about the current backend"""
        info = {
            "backend": self.backend.value,
            "service_name": self.service_name,
            "available_backends": []
        }
        
        # Check available backends
        if KEYRING_AVAILABLE:
            info["available_backends"].append("keyring")
        if VAULT_AVAILABLE:
            info["available_backends"].append("vault")
        if CRYPTO_AVAILABLE:
            info["available_backends"].append("encrypted_file")
        
        info["available_backends"].extend(["environment", "memory"])
        
        return info


# Convenience functions for common use cases
def create_keyring_manager(service_name: str = "vmware-esxi-mcp") -> EnterpriseSecretsManager:
    """Create a secrets manager using system keyring"""
    config = SecretConfig(
        backend=SecretBackend.KEYRING,
        service_name=service_name
    )
    return EnterpriseSecretsManager(config)


def create_vault_manager(vault_url: str, vault_token: str, 
                        service_name: str = "vmware-esxi-mcp") -> EnterpriseSecretsManager:
    """Create a secrets manager using HashiCorp Vault"""
    vault_config = VaultConfig(
        url=vault_url,
        token=vault_token
    )
    
    config = SecretConfig(
        backend=SecretBackend.VAULT,
        service_name=service_name,
        vault_config=vault_config
    )
    
    return EnterpriseSecretsManager(config)


def create_encrypted_file_manager(file_path: str = None, 
                                 service_name: str = "vmware-esxi-mcp") -> EnterpriseSecretsManager:
    """Create a secrets manager using encrypted file storage"""
    config = SecretConfig(
        backend=SecretBackend.ENCRYPTED_FILE,
        service_name=service_name,
        file_path=file_path
    )
    
    return EnterpriseSecretsManager(config)