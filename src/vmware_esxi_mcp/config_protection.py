"""
Enterprise Configuration Protection for VMware ESXi MCP Server

Provides secure configuration file handling with encryption, integrity checking,
and access control for sensitive configuration data.

Author: uldyssian-sh
License: MIT
"""

import os
import json
import hashlib
import stat
import tempfile
import shutil
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from pathlib import Path
import warnings

# Optional imports with graceful fallback
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    warnings.warn("PyYAML not available. YAML configuration files not supported.", ImportWarning)

# Optional imports with graceful fallback
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    import base64
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    warnings.warn("Cryptography library not available. Configuration encryption disabled.", ImportWarning)

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from .secrets_manager import EnterpriseSecretsManager, SecretBackend, SecretConfig


@dataclass
class ConfigProtectionSettings:
    """Configuration protection settings for ESXi MCP"""
    encrypt_sensitive_fields: bool = True
    use_file_permissions: bool = True
    create_backup: bool = True
    validate_integrity: bool = True
    sensitive_field_patterns: List[str] = field(default_factory=lambda: [
        "*password*", "*secret*", "*key*", "*token*", "*credential*",
        "*auth*", "*cert*", "*private*", "*api_key*", "*access_key*",
        "*esxi_password*", "*root_password*", "*ssl_key*"
    ])
    file_permissions: int = 0o600  # Owner read/write only
    backup_retention: int = 5  # Keep 5 backup versions


class ConfigProtectionManager:
    """Enterprise configuration protection manager for ESXi MCP"""
    
    def __init__(self, config_path: str, settings: ConfigProtectionSettings = None,
                 secrets_manager: EnterpriseSecretsManager = None):
        self.config_path = Path(config_path)
        self.settings = settings or ConfigProtectionSettings()
        self.secrets_manager = secrets_manager
        
        # Initialize encryption if available
        self.fernet = None
        
        if CRYPTO_AVAILABLE and self.settings.encrypt_sensitive_fields:
            self._initialize_encryption()
        
        logger.info("ESXi MCP configuration protection manager initialized - config_path: %s, encryption_enabled: %s",
                   str(self.config_path), self.fernet is not None)
    
    def _initialize_encryption(self):
        """Initialize encryption keys"""
        try:
            # Try to load existing keys from secrets manager
            if self.secrets_manager:
                symmetric_key = self.secrets_manager.retrieve_secret("config_encryption_key")
                if symmetric_key:
                    self.fernet = Fernet(symmetric_key.encode())
                    logger.debug("Loaded existing encryption key from secrets manager")
                    return
            
            # Generate new symmetric key
            key = Fernet.generate_key()
            self.fernet = Fernet(key)
            
            # Store key in secrets manager if available
            if self.secrets_manager:
                self.secrets_manager.store_secret("config_encryption_key", key.decode())
                logger.debug("Generated and stored new encryption key")
            else:
                logger.warning("No secrets manager available, encryption key not persisted")
                
        except Exception as e:
            logger.error("Failed to initialize encryption", error=str(e))
            self.fernet = None
    
    def load_config(self) -> Dict[str, Any]:
        """Load and decrypt configuration file"""
        if not self.config_path.exists():
            logger.warning("Configuration file does not exist", path=str(self.config_path))
            return {}
        
        try:
            # Check file permissions
            if self.settings.use_file_permissions:
                self._check_file_permissions()
            
            # Load configuration
            with open(self.config_path, 'r', encoding='utf-8') as f:
                if self.config_path.suffix.lower() == '.yaml' or self.config_path.suffix.lower() == '.yml':
                    if YAML_AVAILABLE:
                        config = yaml.safe_load(f) or {}
                    else:
                        raise ValueError("YAML configuration files not supported (PyYAML not installed)")
                else:
                    config = json.load(f)
            
            # Validate integrity if enabled
            if self.settings.validate_integrity:
                if not self._validate_integrity(config):
                    logger.error("Configuration integrity validation failed")
                    return {}
            
            # Decrypt sensitive fields
            if self.fernet and self.settings.encrypt_sensitive_fields:
                config = self._decrypt_sensitive_fields(config)
            
            logger.info("ESXi MCP configuration loaded successfully - fields_count: %d, encrypted_fields: %d", 
                       len(config), self._count_encrypted_fields(config))
            
            return config
            
        except Exception as e:
            logger.error("Failed to load configuration", error=str(e))
            return {}
    
    def save_config(self, config: Dict[str, Any], create_backup: bool = None) -> bool:
        """Encrypt and save configuration file"""
        create_backup = create_backup if create_backup is not None else self.settings.create_backup
        
        try:
            # Create backup if requested
            if create_backup and self.config_path.exists():
                self._create_backup()
            
            # Make a copy for encryption
            config_to_save = config.copy()
            
            # Encrypt sensitive fields
            if self.fernet and self.settings.encrypt_sensitive_fields:
                config_to_save = self._encrypt_sensitive_fields(config_to_save)
            
            # Add integrity hash
            if self.settings.validate_integrity:
                config_to_save = self._add_integrity_hash(config_to_save)
            
            # Write to temporary file first
            temp_path = self.config_path.with_suffix(self.config_path.suffix + '.tmp')
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                if self.config_path.suffix.lower() == '.yaml' or self.config_path.suffix.lower() == '.yml':
                    if YAML_AVAILABLE:
                        yaml.dump(config_to_save, f, default_flow_style=False, indent=2)
                    else:
                        raise ValueError("YAML configuration files not supported (PyYAML not installed)")
                else:
                    json.dump(config_to_save, f, indent=2)
            
            # Set file permissions before moving
            if self.settings.use_file_permissions:
                os.chmod(temp_path, self.settings.file_permissions)
            
            # Atomic move
            shutil.move(str(temp_path), str(self.config_path))
            
            logger.info("ESXi MCP configuration saved successfully - path: %s, encrypted_fields: %d",
                       str(self.config_path), self._count_encrypted_fields(config_to_save))
            
            return True
            
        except Exception as e:
            logger.error("Failed to save configuration", error=str(e))
            return False
    
    def _check_file_permissions(self):
        """Check and fix file permissions"""
        current_permissions = stat.S_IMODE(self.config_path.stat().st_mode)
        
        if current_permissions != self.settings.file_permissions:
            logger.warning("Configuration file has incorrect permissions - current: %s, expected: %s",
                          oct(current_permissions), oct(self.settings.file_permissions))
            
            try:
                os.chmod(self.config_path, self.settings.file_permissions)
                logger.info("Fixed configuration file permissions")
            except Exception as e:
                logger.error("Failed to fix file permissions", error=str(e))
    
    def _is_sensitive_field(self, field_path: str) -> bool:
        """Check if a field path matches sensitive field patterns"""
        field_lower = field_path.lower()
        
        for pattern in self.settings.sensitive_field_patterns:
            pattern_lower = pattern.lower().replace('*', '')
            if pattern_lower in field_lower:
                return True
        
        return False
    
    def _encrypt_sensitive_fields(self, config: Dict[str, Any], path: str = "") -> Dict[str, Any]:
        """Recursively encrypt sensitive fields in configuration"""
        if not self.fernet:
            return config
        
        result = {}
        
        for key, value in config.items():
            current_path = f"{path}.{key}" if path else key
            
            if isinstance(value, dict):
                result[key] = self._encrypt_sensitive_fields(value, current_path)
            elif isinstance(value, str) and self._is_sensitive_field(current_path):
                # Check if already encrypted
                if not value.startswith("encrypted:"):
                    try:
                        encrypted_value = self.fernet.encrypt(value.encode()).decode()
                        result[key] = f"encrypted:{encrypted_value}"
                        logger.debug("Encrypted sensitive field: %s", current_path)
                    except Exception as e:
                        logger.error("Failed to encrypt field %s: %s", current_path, str(e))
                        result[key] = value
                else:
                    result[key] = value  # Already encrypted
            else:
                result[key] = value
        
        return result
    
    def _decrypt_sensitive_fields(self, config: Dict[str, Any], path: str = "") -> Dict[str, Any]:
        """Recursively decrypt sensitive fields in configuration"""
        if not self.fernet:
            return config
        
        result = {}
        
        for key, value in config.items():
            current_path = f"{path}.{key}" if path else key
            
            if isinstance(value, dict):
                result[key] = self._decrypt_sensitive_fields(value, current_path)
            elif isinstance(value, str) and value.startswith("encrypted:"):
                try:
                    encrypted_value = value[10:]  # Remove "encrypted:" prefix
                    decrypted_value = self.fernet.decrypt(encrypted_value.encode()).decode()
                    result[key] = decrypted_value
                    logger.debug("Decrypted sensitive field: %s", current_path)
                except Exception as e:
                    logger.error("Failed to decrypt field %s: %s", current_path, str(e))
                    result[key] = value  # Return encrypted value if decryption fails
            else:
                result[key] = value
        
        return result
    
    def _count_encrypted_fields(self, config: Dict[str, Any]) -> int:
        """Count encrypted fields in configuration"""
        count = 0
        
        def count_recursive(obj):
            nonlocal count
            if isinstance(obj, dict):
                for value in obj.values():
                    count_recursive(value)
            elif isinstance(obj, str) and obj.startswith("encrypted:"):
                count += 1
        
        count_recursive(config)
        return count
    
    def _add_integrity_hash(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Add integrity hash to configuration"""
        # Create a copy without existing hash
        config_copy = config.copy()
        config_copy.pop('_integrity_hash', None)
        
        # Calculate hash
        config_str = json.dumps(config_copy, sort_keys=True)
        integrity_hash = hashlib.sha256(config_str.encode()).hexdigest()
        
        # Add hash to config
        config['_integrity_hash'] = integrity_hash
        return config
    
    def _validate_integrity(self, config: Dict[str, Any]) -> bool:
        """Validate configuration integrity"""
        if '_integrity_hash' not in config:
            logger.warning("No integrity hash found in configuration")
            return True  # Allow configs without hash
        
        stored_hash = config.pop('_integrity_hash')
        
        # Calculate current hash
        config_str = json.dumps(config, sort_keys=True)
        current_hash = hashlib.sha256(config_str.encode()).hexdigest()
        
        # Restore hash
        config['_integrity_hash'] = stored_hash
        
        if current_hash != stored_hash:
            logger.error("Configuration integrity check failed - expected: %s, actual: %s",
                        stored_hash, current_hash)
            return False
        
        logger.debug("Configuration integrity validated successfully")
        return True
    
    def _create_backup(self):
        """Create backup of current configuration"""
        if not self.config_path.exists():
            return
        
        try:
            # Create backup directory
            backup_dir = self.config_path.parent / 'backups'
            backup_dir.mkdir(exist_ok=True)
            
            # Generate backup filename with timestamp
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{self.config_path.stem}_{timestamp}{self.config_path.suffix}"
            backup_path = backup_dir / backup_name
            
            # Copy file
            shutil.copy2(self.config_path, backup_path)
            
            # Set permissions
            if self.settings.use_file_permissions:
                os.chmod(backup_path, self.settings.file_permissions)
            
            logger.info("Configuration backup created: %s", str(backup_path))
            
            # Clean old backups
            self._cleanup_old_backups(backup_dir)
            
        except Exception as e:
            logger.error("Failed to create backup", error=str(e))
    
    def _cleanup_old_backups(self, backup_dir: Path):
        """Clean up old backup files"""
        try:
            # Get all backup files for this config
            pattern = f"{self.config_path.stem}_*{self.config_path.suffix}"
            backup_files = list(backup_dir.glob(pattern))
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Remove old backups
            for backup_file in backup_files[self.settings.backup_retention:]:
                backup_file.unlink()
                logger.debug("Removed old backup: %s", str(backup_file))
                
        except Exception as e:
            logger.error("Failed to cleanup old backups", error=str(e))
    
    def rotate_encryption_key(self) -> bool:
        """Rotate encryption key and re-encrypt configuration"""
        if not self.fernet or not CRYPTO_AVAILABLE:
            logger.warning("Encryption not available, cannot rotate key")
            return False
        
        try:
            # Load current config (decrypted)
            config = self.load_config()
            
            # Generate new key
            new_key = Fernet.generate_key()
            old_fernet = self.fernet
            self.fernet = Fernet(new_key)
            
            # Save config with new key
            success = self.save_config(config)
            
            if success:
                # Update key in secrets manager
                if self.secrets_manager:
                    self.secrets_manager.store_secret("config_encryption_key", new_key.decode())
                
                logger.info("Encryption key rotated successfully")
                return True
            else:
                # Restore old key on failure
                self.fernet = old_fernet
                logger.error("Failed to save config with new key, restored old key")
                return False
                
        except Exception as e:
            logger.error("Failed to rotate encryption key", error=str(e))
            return False
    
    def export_config_template(self, output_path: str, include_sensitive: bool = False) -> bool:
        """Export configuration template with example values"""
        try:
            config = self.load_config()
            template = self._create_template(config, include_sensitive)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                if output_path.endswith('.yaml') or output_path.endswith('.yml'):
                    if YAML_AVAILABLE:
                        yaml.dump(template, f, default_flow_style=False, indent=2)
                    else:
                        raise ValueError("YAML export not supported (PyYAML not installed)")
                else:
                    json.dump(template, f, indent=2)
            
            logger.info("ESXi MCP configuration template exported: %s", output_path)
            return True
            
        except Exception as e:
            logger.error("Failed to export template", error=str(e))
            return False
    
    def _create_template(self, config: Dict[str, Any], include_sensitive: bool) -> Dict[str, Any]:
        """Create configuration template with example values"""
        template = {}
        
        for key, value in config.items():
            if key.startswith('_'):  # Skip internal fields
                continue
            
            if isinstance(value, dict):
                template[key] = self._create_template(value, include_sensitive)
            elif self._is_sensitive_field(key):
                if include_sensitive:
                    template[key] = "CHANGE_ME_SENSITIVE_VALUE"
                else:
                    template[key] = "*** SENSITIVE - CONFIGURE SEPARATELY ***"
            else:
                # Create example value based on type
                if isinstance(value, str):
                    template[key] = "example_string_value"
                elif isinstance(value, int):
                    template[key] = 12345
                elif isinstance(value, bool):
                    template[key] = True
                elif isinstance(value, list):
                    template[key] = ["example_item"]
                else:
                    template[key] = value
        
        return template
    
    def get_protection_status(self) -> Dict[str, Any]:
        """Get current protection status"""
        status = {
            "config_path": str(self.config_path),
            "config_exists": self.config_path.exists(),
            "encryption_available": CRYPTO_AVAILABLE,
            "encryption_enabled": self.fernet is not None,
            "settings": {
                "encrypt_sensitive_fields": self.settings.encrypt_sensitive_fields,
                "use_file_permissions": self.settings.use_file_permissions,
                "create_backup": self.settings.create_backup,
                "validate_integrity": self.settings.validate_integrity,
                "file_permissions": oct(self.settings.file_permissions),
                "backup_retention": self.settings.backup_retention
            }
        }
        
        if self.config_path.exists():
            stat_info = self.config_path.stat()
            status["file_info"] = {
                "size": stat_info.st_size,
                "permissions": oct(stat.S_IMODE(stat_info.st_mode)),
                "modified": stat_info.st_mtime
            }
            
            # Count encrypted fields
            try:
                config = self.load_config()
                status["encrypted_fields_count"] = self._count_encrypted_fields(config)
                status["total_fields_count"] = len(config)
            except Exception:
                status["encrypted_fields_count"] = "unknown"
                status["total_fields_count"] = "unknown"
        
        return status


# Convenience functions
def create_protected_config_manager(config_path: str, 
                                   use_keyring: bool = True,
                                   use_vault: bool = False,
                                   vault_url: str = None,
                                   vault_token: str = None) -> ConfigProtectionManager:
    """Create a configuration protection manager with secrets integration"""
    
    secrets_manager = None
    
    if use_vault and vault_url and vault_token:
        from .secrets_manager import create_vault_manager
        secrets_manager = create_vault_manager(vault_url, vault_token)
    elif use_keyring:
        from .secrets_manager import create_keyring_manager
        secrets_manager = create_keyring_manager()
    
    return ConfigProtectionManager(
        config_path=config_path,
        secrets_manager=secrets_manager
    )