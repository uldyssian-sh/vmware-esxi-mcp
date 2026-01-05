"""
Unit tests for ESXi connection management.

Tests the core ESXi connection functionality, authentication,
and connection pooling specific to ESXi hypervisor management.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from vmware_esxi_mcp.connection import ESXiConnection
from vmware_esxi_mcp.exceptions import ESXiConnectionError, ESXiAuthenticationError


class TestESXiConnection:
    """Test ESXi connection management."""

    @pytest.fixture
    def esxi_config(self):
        """ESXi connection configuration fixture."""
        return {
            "host": "esxi-test.example.com",
            "username": "root",
            "password": "test-password",
            "port": 443,
            "ssl_verify": True,
            "timeout": 30
        }

    @pytest.fixture
    def mock_service_instance(self):
        """Mock vSphere service instance."""
        mock_si = Mock()
        mock_si.content = Mock()
        mock_si.content.rootFolder = Mock()
        mock_si.content.viewManager = Mock()
        return mock_si

    @patch('vmware_esxi_mcp.connection.SmartConnect')
    def test_connect_success(self, mock_connect, esxi_config, mock_service_instance):
        """Test successful ESXi connection."""
        mock_connect.return_value = mock_service_instance
        
        connection = ESXiConnection(esxi_config)
        result = connection.connect()
        
        assert result is True
        assert connection.service_instance == mock_service_instance
        mock_connect.assert_called_once_with(
            host=esxi_config["host"],
            user=esxi_config["username"],
            pwd=esxi_config["password"],
            port=esxi_config["port"],
            sslContext=None if esxi_config["ssl_verify"] else Mock()
        )

    @patch('vmware_esxi_mcp.connection.SmartConnect')
    def test_connect_authentication_failure(self, mock_connect, esxi_config):
        """Test ESXi authentication failure."""
        mock_connect.side_effect = Exception("Login failure")
        
        connection = ESXiConnection(esxi_config)
        
        with pytest.raises(ESXiAuthenticationError):
            connection.connect()

    @patch('vmware_esxi_mcp.connection.SmartConnect')
    def test_connect_network_failure(self, mock_connect, esxi_config):
        """Test ESXi network connection failure."""
        mock_connect.side_effect = ConnectionError("Network unreachable")
        
        connection = ESXiConnection(esxi_config)
        
        with pytest.raises(ESXiConnectionError):
            connection.connect()

    def test_get_host_system(self, mock_service_instance):
        """Test retrieving ESXi host system object."""
        mock_host = Mock()
        mock_host.name = "esxi-test.example.com"
        mock_service_instance.content.rootFolder.childEntity = [mock_host]
        
        connection = ESXiConnection({})
        connection.service_instance = mock_service_instance
        
        host = connection.get_host_system()
        assert host == mock_host

    def test_get_virtual_machines(self, mock_service_instance):
        """Test retrieving virtual machines from ESXi host."""
        mock_vm1 = Mock()
        mock_vm1.name = "test-vm-1"
        mock_vm2 = Mock()
        mock_vm2.name = "test-vm-2"
        
        mock_host = Mock()
        mock_host.vm = [mock_vm1, mock_vm2]
        
        connection = ESXiConnection({})
        connection.service_instance = mock_service_instance
        
        with patch.object(connection, 'get_host_system', return_value=mock_host):
            vms = connection.get_virtual_machines()
            assert len(vms) == 2
            assert mock_vm1 in vms
            assert mock_vm2 in vms

    def test_connection_pooling(self, esxi_config):
        """Test ESXi connection pooling functionality."""
        connection = ESXiConnection(esxi_config)
        
        # Test pool initialization
        assert connection.pool_size == esxi_config.get("pool_size", 5)
        assert len(connection.connection_pool) == 0
        
        # Test pool management
        with patch.object(connection, 'connect', return_value=True):
            connection.get_pooled_connection()
            assert len(connection.connection_pool) <= connection.pool_size

    @pytest.mark.asyncio
    async def test_async_operations(self, esxi_config, mock_service_instance):
        """Test asynchronous ESXi operations."""
        connection = ESXiConnection(esxi_config)
        connection.service_instance = mock_service_instance
        
        # Mock async VM operations
        with patch.object(connection, 'power_on_vm_async', new_callable=AsyncMock) as mock_power_on:
            mock_power_on.return_value = {"status": "success"}
            
            result = await connection.power_on_vm_async("test-vm")
            assert result["status"] == "success"
            mock_power_on.assert_called_once_with("test-vm")

    def test_esxi_specific_features(self, mock_service_instance):
        """Test ESXi-specific features not available in vCenter."""
        connection = ESXiConnection({})
        connection.service_instance = mock_service_instance
        
        # Test direct host management
        mock_host = Mock()
        mock_host.configManager = Mock()
        mock_host.configManager.storageSystem = Mock()
        
        with patch.object(connection, 'get_host_system', return_value=mock_host):
            # Test direct datastore access
            storage_system = connection.get_storage_system()
            assert storage_system == mock_host.configManager.storageSystem
            
            # Test host configuration access
            config_manager = connection.get_config_manager()
            assert config_manager == mock_host.configManager

    def test_maintenance_mode_operations(self, mock_service_instance):
        """Test ESXi maintenance mode operations."""
        connection = ESXiConnection({})
        connection.service_instance = mock_service_instance
        
        mock_host = Mock()
        mock_host.runtime = Mock()
        mock_host.runtime.inMaintenanceMode = False
        
        with patch.object(connection, 'get_host_system', return_value=mock_host):
            # Test entering maintenance mode
            with patch.object(mock_host, 'EnterMaintenanceMode_Task') as mock_enter:
                mock_task = Mock()
                mock_enter.return_value = mock_task
                
                result = connection.enter_maintenance_mode()
                assert result == mock_task
                mock_enter.assert_called_once()

    def test_performance_monitoring(self, mock_service_instance):
        """Test ESXi performance monitoring capabilities."""
        connection = ESXiConnection({})
        connection.service_instance = mock_service_instance
        
        mock_perf_manager = Mock()
        mock_service_instance.content.perfManager = mock_perf_manager
        
        # Test performance counter retrieval
        mock_counters = [
            Mock(key=1, nameInfo=Mock(key="cpu.usage.average")),
            Mock(key=2, nameInfo=Mock(key="mem.usage.average"))
        ]
        mock_perf_manager.perfCounter = mock_counters
        
        counters = connection.get_performance_counters()
        assert len(counters) == 2
        assert any(c.nameInfo.key == "cpu.usage.average" for c in counters)

    def test_error_handling(self, esxi_config):
        """Test comprehensive error handling."""
        connection = ESXiConnection(esxi_config)
        
        # Test invalid configuration
        with pytest.raises(ValueError):
            ESXiConnection({})  # Empty config
        
        # Test connection timeout
        with patch('vmware_esxi_mcp.connection.SmartConnect') as mock_connect:
            mock_connect.side_effect = TimeoutError("Connection timeout")
            
            with pytest.raises(ESXiConnectionError) as exc_info:
                connection.connect()
            assert "timeout" in str(exc_info.value).lower()

    def test_ssl_certificate_handling(self, esxi_config):
        """Test SSL certificate validation."""
        # Test with SSL verification disabled
        esxi_config["ssl_verify"] = False
        connection = ESXiConnection(esxi_config)
        
        with patch('vmware_esxi_mcp.connection.SmartConnect') as mock_connect:
            with patch('ssl.create_default_context') as mock_ssl_context:
                connection.connect()
                mock_ssl_context.assert_called_once()

    def test_connection_cleanup(self, mock_service_instance):
        """Test proper connection cleanup."""
        connection = ESXiConnection({})
        connection.service_instance = mock_service_instance
        
        with patch.object(mock_service_instance, 'Disconnect') as mock_disconnect:
            connection.disconnect()
            mock_disconnect.assert_called_once()
            assert connection.service_instance is None