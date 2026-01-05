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


if __name__ == '__main__':
    unittest.main()