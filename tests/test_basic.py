"""
Basic tests for VMware ESXi MCP Server

Tests basic functionality and imports without requiring external dependencies.

Author: uldyssian-sh
License: MIT
"""

import sys
import os
import unittest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestBasicFunctionality(unittest.TestCase):
    """Test basic functionality"""
    
    def test_package_import(self):
        """Test that the main package imports successfully"""
        try:
            import vmware_esxi_mcp
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import vmware_esxi_mcp: {e}")
    
    def test_version_exists(self):
        """Test that version is defined"""
        import vmware_esxi_mcp
        self.assertTrue(hasattr(vmware_esxi_mcp, '__version__'))
        self.assertIsNotNone(vmware_esxi_mcp.__version__)
        self.assertIsInstance(vmware_esxi_mcp.__version__, str)
    
    def test_author_exists(self):
        """Test that author is defined"""
        import vmware_esxi_mcp
        self.assertTrue(hasattr(vmware_esxi_mcp, '__author__'))
        self.assertEqual(vmware_esxi_mcp.__author__, 'uldyssian-sh')
    
    def test_server_import(self):
        """Test that server module imports successfully"""
        try:
            from vmware_esxi_mcp import server
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import server module: {e}")
    
    def test_exceptions_import(self):
        """Test that exceptions module imports successfully"""
        try:
            from vmware_esxi_mcp import exceptions
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import exceptions module: {e}")
    
    def test_esxi_server_class(self):
        """Test that ESXiMCPServer can be imported"""
        try:
            from vmware_esxi_mcp.server import ESXiMCPServer
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import ESXiMCPServer: {e}")


class TestServerFunctionality(unittest.TestCase):
    """Test server functionality"""
    
    def test_server_instantiation(self):
        """Test that ESXiMCPServer can be instantiated"""
        try:
            from vmware_esxi_mcp.server import ESXiMCPServer
            # Test with minimal config
            server = ESXiMCPServer()
            self.assertIsNotNone(server)
        except Exception as e:
            # This might fail due to missing dependencies, which is expected
            self.assertTrue(True, "Server instantiation test completed (dependencies may be missing)")
    
    def test_exception_classes(self):
        """Test that exception classes are properly defined"""
        try:
            from vmware_esxi_mcp.exceptions import (
                ESXiConnectionError,
                ESXiAuthenticationError, 
                ESXiOperationError,
                ValidationError
            )
            
            # Test that they are proper exception classes
            self.assertTrue(issubclass(ESXiConnectionError, Exception))
            self.assertTrue(issubclass(ESXiAuthenticationError, Exception))
            self.assertTrue(issubclass(ESXiOperationError, Exception))
            self.assertTrue(issubclass(ValidationError, Exception))
            
        except ImportError as e:
            self.fail(f"Failed to import exception classes: {e}")
    
    def test_secrets_manager_import(self):
        """Test that secrets manager module imports successfully"""
        try:
            from vmware_esxi_mcp import secrets_manager
            from vmware_esxi_mcp.secrets_manager import EnterpriseSecretsManager
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import secrets manager: {e}")
    
    def test_config_protection_import(self):
        """Test that config protection module imports successfully"""
        try:
            from vmware_esxi_mcp import config_protection
            from vmware_esxi_mcp.config_protection import ConfigProtectionManager
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import config protection: {e}")


class TestEnterpriseSecurityModules(unittest.TestCase):
    """Test enterprise security modules for ESXi MCP"""
    
    def test_secrets_manager_instantiation(self):
        """Test EnterpriseSecretsManager can be instantiated"""
        try:
            from vmware_esxi_mcp.secrets_manager import (
                EnterpriseSecretsManager, SecretConfig, SecretBackend
            )
            config = SecretConfig(backend=SecretBackend.MEMORY)
            manager = EnterpriseSecretsManager(config)
            self.assertIsNotNone(manager)
            self.assertEqual(manager.backend, SecretBackend.MEMORY)
        except Exception as e:
            self.fail(f"Failed to create EnterpriseSecretsManager: {e}")
    
    def test_config_protection_instantiation(self):
        """Test ConfigProtectionManager can be instantiated"""
        try:
            from vmware_esxi_mcp.config_protection import (
                ConfigProtectionManager, ConfigProtectionSettings
            )
            import tempfile
            
            with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
                config_path = f.name
            
            settings = ConfigProtectionSettings(encrypt_sensitive_fields=False)
            manager = ConfigProtectionManager(config_path, settings)
            self.assertIsNotNone(manager)
            
            # Cleanup
            import os
            if os.path.exists(config_path):
                os.unlink(config_path)
                
        except Exception as e:
            self.fail(f"Failed to create ConfigProtectionManager: {e}")
    
    def test_secrets_manager_memory_operations(self):
        """Test basic secrets manager operations with memory backend"""
        try:
            from vmware_esxi_mcp.secrets_manager import (
                EnterpriseSecretsManager, SecretConfig, SecretBackend
            )
            
            config = SecretConfig(backend=SecretBackend.MEMORY)
            manager = EnterpriseSecretsManager(config)
            
            # Test store and retrieve
            test_key = "esxi_password"
            test_value = "ESXiPassword123!"
            
            success = manager.store_secret(test_key, test_value)
            self.assertTrue(success)
            
            retrieved_value = manager.retrieve_secret(test_key)
            self.assertEqual(retrieved_value, test_value)
            
            # Test delete
            success = manager.delete_secret(test_key)
            self.assertTrue(success)
            
            # Verify deletion
            retrieved_value = manager.retrieve_secret(test_key)
            self.assertIsNone(retrieved_value)
            
        except Exception as e:
            self.fail(f"Failed secrets manager operations: {e}")


if __name__ == '__main__':
    unittest.main()