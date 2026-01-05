#!/usr/bin/env python3
"""
Basic tests for VMware ESXi MCP Server

Author: uldyssian-sh
License: MIT
"""

import unittest
import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

class TestESXiMCPBasic(unittest.TestCase):
    """Basic tests for ESXi MCP Server."""
    
    def test_import_server(self):
        """Test that server module can be imported."""
        try:
            from vmware_esxi_mcp.server import ESXiMCPServer
            self.assertTrue(True, "Server module imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import server module: {e}")
    
    def test_server_initialization(self):
        """Test server initialization."""
        try:
            from vmware_esxi_mcp.server import ESXiMCPServer
            server = ESXiMCPServer()
            self.assertIsNotNone(server)
            self.assertEqual(server.server.name, "vmware-esxi-mcp")
            self.assertEqual(server.server.version, "1.5.0")
        except Exception as e:
            self.fail(f"Server initialization failed: {e}")
    
    def test_get_available_tools(self):
        """Test that tools are properly defined."""
        try:
            from vmware_esxi_mcp.server import ESXiMCPServer
            server = ESXiMCPServer()
            tools = server.get_available_tools()
            
            self.assertIsInstance(tools, list)
            self.assertGreater(len(tools), 0)
            
            # Check that essential tools exist
            tool_names = [tool.name for tool in tools]
            essential_tools = [
                "get_host_info",
                "list_vms", 
                "create_vm",
                "power_vm"
            ]
            
            for tool_name in essential_tools:
                self.assertIn(tool_name, tool_names, f"Essential tool '{tool_name}' not found")
                
        except Exception as e:
            self.fail(f"Tool definition test failed: {e}")
    
    def test_configuration_loading(self):
        """Test configuration loading."""
        try:
            from vmware_esxi_mcp.server import ESXiMCPServer
            import os
            
            # Set test environment variables
            os.environ["ESXI_HOST"] = "test-host.example.com"
            os.environ["ESXI_USERNAME"] = "test-user"
            
            server = ESXiMCPServer()
            self.assertEqual(server.esxi_host, "test-host.example.com")
            self.assertEqual(server.esxi_username, "test-user")
            
        except Exception as e:
            self.fail(f"Configuration loading test failed: {e}")

class TestESXiMCPTools(unittest.TestCase):
    """Test individual MCP tools."""
    
    def setUp(self):
        """Set up test environment."""
        from vmware_esxi_mcp.server import ESXiMCPServer
        self.server = ESXiMCPServer()
    
    def test_host_info_structure(self):
        """Test host info returns proper structure."""
        try:
            import asyncio
            
            async def run_test():
                result = await self.server.get_host_info()
                self.assertIsInstance(result, dict)
                self.assertIn("host", result)
                self.assertIn("status", result)
                return result
            
            result = asyncio.run(run_test())
            self.assertIsNotNone(result)
            
        except Exception as e:
            self.fail(f"Host info test failed: {e}")
    
    def test_list_vms_structure(self):
        """Test VM listing returns proper structure."""
        try:
            import asyncio
            
            async def run_test():
                result = await self.server.list_vms()
                self.assertIsInstance(result, dict)
                self.assertIn("total_vms", result)
                self.assertIn("vms", result)
                return result
            
            result = asyncio.run(run_test())
            self.assertIsNotNone(result)
            
        except Exception as e:
            self.fail(f"List VMs test failed: {e}")

if __name__ == "__main__":
    # Run tests with minimal output
    unittest.main(verbosity=1)