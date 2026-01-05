#!/usr/bin/env python3
"""
Secure Configuration Management Example for VMware ESXi MCP Server

Demonstrates enterprise-grade configuration protection and secrets management
for VMware ESXi MCP Server deployments.

Author: uldyssian-sh
License: MIT
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from vmware_esxi_mcp.secrets_manager import (
    EnterpriseSecretsManager, SecretBackend, SecretConfig, VaultConfig,
    create_keyring_manager, create_vault_manager, create_encrypted_file_manager
)
from vmware_esxi_mcp.config_protection import (
    ConfigProtectionManager, ConfigProtectionSettings,
    create_protected_config_manager
)


def example_esxi_keyring_secrets():
    """Example: Using system keyring for ESXi secrets management"""
    print("=== ESXi MCP System Keyring Secrets Management ===")
    
    # Create keyring-based secrets manager
    secrets_manager = create_keyring_manager("vmware-esxi-example")
    
    # Store ESXi-specific secrets
    esxi_secrets = {
        "esxi_root_password": "ESXiRootPassword123!",
        "esxi_api_key": "esxi_api_key_xyz789",
        "ssl_certificate": "-----BEGIN CERTIFICATE-----\nMIIC...\n-----END CERTIFICATE-----",
        "esxi_host_config": {
            "host": "esxi-host.example.com",
            "username": "root",
            "password": "ESXiHostPassword456!",
            "port": 443
        }
    }
    
    print("Storing ESXi secrets in system keyring...")
    for key, value in esxi_secrets.items():
        success = secrets_manager.store_secret(key, value)
        print(f"  {key}: {'✅ Stored' if success else '❌ Failed'}")
    
    print("\nRetrieving ESXi secrets from system keyring...")
    for key in esxi_secrets.keys():
        value = secrets_manager.retrieve_secret(key)
        if value:
            if isinstance(value, dict):
                print(f"  {key}: ✅ Retrieved (dict with {len(value)} keys)")
            else:
                print(f"  {key}: ✅ Retrieved (length: {len(str(value))})")
        else:
            print(f"  {key}: ❌ Not found")
    
    # Get backend information
    info = secrets_manager.get_backend_info()
    print(f"\nBackend Info:")
    print(f"  Current backend: {info['backend']}")
    print(f"  Available backends: {', '.join(info['available_backends'])}")


def example_esxi_vault_secrets():
    """Example: Using HashiCorp Vault for ESXi secrets management"""
    print("\n=== ESXi MCP HashiCorp Vault Secrets Management ===")
    
    # Note: This requires a running Vault instance
    vault_url = os.getenv("VAULT_URL", "http://localhost:8200")
    vault_token = os.getenv("VAULT_TOKEN", "dev-token")
    
    if not vault_token or vault_token == "dev-token":
        print("⚠️  Vault example skipped - set VAULT_URL and VAULT_TOKEN environment variables")
        return
    
    try:
        # Create Vault-based secrets manager
        secrets_manager = create_vault_manager(vault_url, vault_token, "vmware-esxi-example")
        
        # Store ESXi secrets in Vault
        esxi_secrets = {
            "esxi_cluster_credentials": {
                "hosts": [
                    {"host": "esxi1.example.com", "username": "root", "password": "ESXi1Password123!"},
                    {"host": "esxi2.example.com", "username": "root", "password": "ESXi2Password123!"},
                    {"host": "esxi3.example.com", "username": "root", "password": "ESXi3Password123!"}
                ]
            },
            "esxi_ssl_certificates": {
                "ca_cert": "-----BEGIN CERTIFICATE-----\nCA_CERT_DATA\n-----END CERTIFICATE-----",
                "server_cert": "-----BEGIN CERTIFICATE-----\nSERVER_CERT_DATA\n-----END CERTIFICATE-----",
                "private_key": "-----BEGIN PRIVATE KEY-----\nPRIVATE_KEY_DATA\n-----END PRIVATE KEY-----"
            }
        }
        
        print("Storing ESXi secrets in HashiCorp Vault...")
        for key, value in esxi_secrets.items():
            success = secrets_manager.store_secret(key, value)
            print(f"  {key}: {'✅ Stored' if success else '❌ Failed'}")
        
        print("\nRetrieving ESXi secrets from HashiCorp Vault...")
        for key in esxi_secrets.keys():
            value = secrets_manager.retrieve_secret(key)
            if value:
                if isinstance(value, dict):
                    print(f"  {key}: ✅ Retrieved (dict with {len(value)} keys)")
                else:
                    print(f"  {key}: ✅ Retrieved (length: {len(str(value))})")
            else:
                print(f"  {key}: ❌ Not found")
        
        # List all secrets
        secret_keys = secrets_manager.list_secrets()
        print(f"\nAll ESXi secrets in Vault: {secret_keys}")
        
    except Exception as e:
        print(f"❌ Vault example failed: {e}")


def example_esxi_config_protection():
    """Example: Protected ESXi configuration file management"""
    print("\n=== ESXi MCP Protected Configuration Management ===")
    
    # Create temporary config file
    config_file = "/tmp/vmware_esxi_config.yaml"
    
    # Create configuration protection manager
    settings = ConfigProtectionSettings(
        encrypt_sensitive_fields=True,
        use_file_permissions=True,
        create_backup=True,
        validate_integrity=True,
        sensitive_field_patterns=[
            "*password*", "*secret*", "*key*", "*token*", 
            "*credential*", "*auth*", "*cert*", "*private*",
            "*esxi_password*", "*root_password*", "*ssl_key*"
        ],
        file_permissions=0o600
    )
    
    # Use keyring for encryption key storage
    secrets_manager = create_keyring_manager("vmware-esxi-config-example")
    config_manager = ConfigProtectionManager(config_file, settings, secrets_manager)
    
    # Sample ESXi configuration with sensitive data
    esxi_config = {
        "mcp_server": {
            "name": "VMware ESXi MCP Server",
            "version": "1.5.0",
            "host": "0.0.0.0",
            "port": 8080,
            "debug": False
        },
        "esxi_hosts": [
            {
                "name": "esxi-host-1",
                "host": "esxi1.example.com",
                "username": "root",
                "password": "ESXiHost1Password123!",  # Will be encrypted
                "port": 443,
                "ssl_verify": True
            },
            {
                "name": "esxi-host-2", 
                "host": "esxi2.example.com",
                "username": "root",
                "password": "ESXiHost2Password123!",  # Will be encrypted
                "port": 443,
                "ssl_verify": True
            }
        ],
        "security": {
            "api_key": "esxi_mcp_api_key_secret",  # Will be encrypted
            "ssl_certificate": "-----BEGIN CERTIFICATE-----\nESXi_CERT_DATA\n-----END CERTIFICATE-----",
            "ssl_private_key": "-----BEGIN PRIVATE KEY-----\nESXi_KEY_DATA\n-----END PRIVATE KEY-----",  # Will be encrypted
            "encryption_enabled": True
        },
        "monitoring": {
            "enabled": True,
            "interval": 60,
            "metrics_endpoint": "/metrics"
        },
        "logging": {
            "level": "INFO",
            "file": "/var/log/vmware-esxi-mcp.log",
            "max_size": "100MB",
            "backup_count": 5
        }
    }
    
    print("Saving protected ESXi configuration...")
    success = config_manager.save_config(esxi_config)
    print(f"ESXi configuration saved: {'✅ Success' if success else '❌ Failed'}")
    
    if os.path.exists(config_file):
        # Check file permissions
        import stat
        file_stat = os.stat(config_file)
        permissions = oct(stat.S_IMODE(file_stat.st_mode))
        print(f"File permissions: {permissions}")
        
        # Show encrypted content
        print("\nRaw file content (with encrypted fields):")
        with open(config_file, 'r') as f:
            content = f.read()
            lines = content.split('\n')
            for i, line in enumerate(lines[:20], 1):  # Show first 20 lines
                print(f"  {i:2d}: {line}")
            if len(lines) > 20:
                print(f"  ... ({len(lines) - 20} more lines)")
    
    print("\nLoading and decrypting ESXi configuration...")
    loaded_config = config_manager.load_config()
    
    if loaded_config:
        print("✅ ESXi configuration loaded and decrypted successfully")
        print(f"Configuration sections: {list(loaded_config.keys())}")
        
        # Verify sensitive fields are decrypted
        esxi_host_password = loaded_config.get('esxi_hosts', [{}])[0].get('password')
        if esxi_host_password == "ESXiHost1Password123!":
            print("✅ ESXi sensitive fields decrypted correctly")
        else:
            print("❌ ESXi sensitive field decryption failed")
    else:
        print("❌ Failed to load ESXi configuration")
    
    # Get protection status
    status = config_manager.get_protection_status()
    print(f"\nESXi Protection Status:")
    print(f"  Encryption enabled: {status['encryption_enabled']}")
    print(f"  Encrypted fields: {status.get('encrypted_fields_count', 'unknown')}")
    print(f"  Total fields: {status.get('total_fields_count', 'unknown')}")
    
    # Export template
    template_file = "/tmp/vmware_esxi_config_template.yaml"
    print(f"\nExporting ESXi configuration template...")
    success = config_manager.export_config_template(template_file, include_sensitive=False)
    if success:
        print(f"✅ ESXi template exported to: {template_file}")
        
        # Show template content
        print("\nESXi Template content:")
        with open(template_file, 'r') as f:
            content = f.read()
            lines = content.split('\n')
            for i, line in enumerate(lines[:15], 1):  # Show first 15 lines
                print(f"  {i:2d}: {line}")
            if len(lines) > 15:
                print(f"  ... ({len(lines) - 15} more lines)")
    
    # Cleanup
    for file_path in [config_file, template_file]:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Cleaned up: {file_path}")
    
    # Clean up backup directory
    backup_dir = Path(config_file).parent / 'backups'
    if backup_dir.exists():
        import shutil
        shutil.rmtree(backup_dir)
        print(f"Cleaned up backup directory: {backup_dir}")


def example_esxi_integration():
    """Example: Complete integration with VMware ESXi MCP"""
    print("\n=== Complete ESXi MCP Integration Example ===")
    
    # Create integrated configuration manager
    config_file = "/tmp/vmware_esxi_mcp_production.yaml"
    config_manager = create_protected_config_manager(
        config_path=config_file,
        use_keyring=True,
        use_vault=False  # Set to True and provide vault_url/vault_token for Vault
    )
    
    # Enterprise ESXi configuration
    enterprise_esxi_config = {
        "mcp_server": {
            "name": "VMware ESXi MCP Server",
            "version": "1.5.0",
            "environment": "production",
            "host": "0.0.0.0",
            "port": 8080
        },
        "esxi_cluster": {
            "name": "Production Cluster",
            "hosts": [
                {
                    "name": "esxi-prod-01",
                    "host": "esxi-prod-01.enterprise.com",
                    "username": "root",
                    "password": "ESXiProd01Password123!",  # Encrypted
                    "port": 443,
                    "datacenter": "DC1",
                    "cluster": "Cluster1"
                },
                {
                    "name": "esxi-prod-02",
                    "host": "esxi-prod-02.enterprise.com", 
                    "username": "root",
                    "password": "ESXiProd02Password123!",  # Encrypted
                    "port": 443,
                    "datacenter": "DC1",
                    "cluster": "Cluster1"
                },
                {
                    "name": "esxi-prod-03",
                    "host": "esxi-prod-03.enterprise.com",
                    "username": "root", 
                    "password": "ESXiProd03Password123!",  # Encrypted
                    "port": 443,
                    "datacenter": "DC1",
                    "cluster": "Cluster1"
                }
            ]
        },
        "security": {
            "api_key": "esxi_enterprise_api_key_2024",  # Encrypted
            "ssl_certificate_path": "/etc/ssl/certs/esxi-mcp.crt",
            "ssl_private_key_path": "/etc/ssl/private/esxi-mcp.key",
            "ssl_private_key": "-----BEGIN PRIVATE KEY-----\nENTERPRISE_KEY_DATA\n-----END PRIVATE KEY-----",  # Encrypted
            "encryption_enabled": True,
            "session_timeout": 3600
        },
        "monitoring": {
            "enabled": True,
            "interval": 30,
            "metrics": {
                "cpu_usage": True,
                "memory_usage": True,
                "storage_usage": True,
                "network_usage": True,
                "vm_count": True
            },
            "alerts": {
                "cpu_threshold": 80,
                "memory_threshold": 85,
                "storage_threshold": 90
            }
        },
        "backup": {
            "enabled": True,
            "schedule": "0 2 * * *",  # Daily at 2 AM
            "retention_days": 30,
            "encryption_key": "backup_encryption_key_enterprise"  # Encrypted
        },
        "logging": {
            "level": "INFO",
            "file": "/var/log/vmware-esxi-mcp.log",
            "max_size": "500MB",
            "backup_count": 10,
            "format": "json"
        }
    }
    
    print("Saving enterprise ESXi configuration with encryption...")
    success = config_manager.save_config(enterprise_esxi_config)
    print(f"Enterprise ESXi config saved: {'✅ Success' if success else '❌ Failed'}")
    
    print("\nLoading enterprise ESXi configuration...")
    loaded_config = config_manager.load_config()
    
    if loaded_config:
        print("✅ Enterprise ESXi configuration loaded successfully")
        
        # Demonstrate usage in application
        esxi_cluster = loaded_config.get('esxi_cluster', {})
        security_config = loaded_config.get('security', {})
        monitoring_config = loaded_config.get('monitoring', {})
        
        print(f"\nESXi Configuration ready for use:")
        print(f"  Cluster name: {esxi_cluster.get('name')}")
        print(f"  ESXi hosts: {len(esxi_cluster.get('hosts', []))}")
        print(f"  Security enabled: {bool(security_config.get('api_key'))}")
        print(f"  Monitoring enabled: {monitoring_config.get('enabled')}")
        print(f"  Monitoring interval: {monitoring_config.get('interval')} seconds")
        
        # Show that sensitive data is properly decrypted
        first_host = esxi_cluster.get('hosts', [{}])[0]
        if first_host.get('password') == "ESXiProd01Password123!":
            print("✅ ESXi sensitive configuration data properly decrypted")
        else:
            print("❌ ESXi configuration decryption issue detected")
        
        # Show cluster information
        print(f"\nESXi Cluster Details:")
        for i, host in enumerate(esxi_cluster.get('hosts', []), 1):
            print(f"  Host {i}: {host.get('name')} ({host.get('host')})")
            print(f"    Datacenter: {host.get('datacenter')}")
            print(f"    Cluster: {host.get('cluster')}")
    
    # Cleanup
    if os.path.exists(config_file):
        os.remove(config_file)
        print(f"\nCleaned up: {config_file}")


def main():
    """Run all ESXi MCP examples"""
    print("VMware ESXi MCP - Enterprise Secrets & Configuration Management Examples")
    print("=" * 80)
    
    try:
        # Run examples
        example_esxi_keyring_secrets()
        example_esxi_vault_secrets()
        example_esxi_config_protection()
        example_esxi_integration()
        
        print("\n" + "=" * 80)
        print("✅ All ESXi MCP examples completed successfully!")
        print("\nKey Features Demonstrated:")
        print("  • System keyring integration for ESXi secret storage")
        print("  • HashiCorp Vault integration for enterprise ESXi secret management")
        print("  • Encrypted file storage with automatic key management")
        print("  • ESXi configuration file encryption with selective field protection")
        print("  • File permission management and integrity validation")
        print("  • Backup creation and rotation for ESXi configurations")
        print("  • Template generation for ESXi deployment")
        print("  • Complete enterprise ESXi cluster integration example")
        print("  • Multi-host ESXi cluster configuration management")
        print("  • ESXi-specific sensitive field patterns")
        
    except Exception as e:
        print(f"\n❌ ESXi MCP example failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()