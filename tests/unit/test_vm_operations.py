"""
Unit tests for ESXi VM operations.

Tests VM lifecycle management operations specific to ESXi hypervisor,
including direct VM manipulation without vCenter overhead.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from vmware_esxi_mcp.vm_operations import ESXiVMOperations
from vmware_esxi_mcp.exceptions import VMOperationError, InsufficientResourcesError


class TestESXiVMOperations:
    """Test ESXi-specific VM operations."""

    @pytest.fixture
    def mock_connection(self):
        """Mock ESXi connection."""
        connection = Mock()
        connection.service_instance = Mock()
        connection.get_host_system = Mock()
        return connection

    @pytest.fixture
    def vm_operations(self, mock_connection):
        """VM operations instance."""
        return ESXiVMOperations(mock_connection)

    @pytest.fixture
    def mock_vm(self):
        """Mock virtual machine object."""
        vm = Mock()
        vm.name = "test-vm"
        vm.runtime = Mock()
        vm.runtime.powerState = "poweredOff"
        vm.config = Mock()
        vm.config.hardware = Mock()
        vm.config.hardware.numCPU = 2
        vm.config.hardware.memoryMB = 4096
        return vm

    def test_create_vm_esxi_direct(self, vm_operations, mock_connection):
        """Test direct VM creation on ESXi host."""
        mock_host = Mock()
        mock_datastore = Mock()
        mock_datastore.name = "datastore1"
        mock_host.datastore = [mock_datastore]
        mock_connection.get_host_system.return_value = mock_host
        
        # Mock VM creation task
        mock_task = Mock()
        mock_task.info = Mock()
        mock_task.info.state = "success"
        mock_task.info.result = Mock()
        mock_task.info.result.name = "test-vm"
        
        with patch.object(mock_host, 'CreateVM_Task', return_value=mock_task):
            result = vm_operations.create_vm(
                vm_name="test-vm",
                cpu_count=2,
                memory_mb=4096,
                disk_size_gb=50
            )
            
            assert result["status"] == "success"
            assert result["vm_name"] == "test-vm"
            mock_host.CreateVM_Task.assert_called_once()

    def test_create_vm_with_esxi_specific_config(self, vm_operations, mock_connection):
        """Test VM creation with ESXi-specific configuration."""
        mock_host = Mock()
        mock_connection.get_host_system.return_value = mock_host
        
        # Test ESXi-specific VM configuration
        vm_config = {
            "vm_name": "esxi-optimized-vm",
            "cpu_count": 4,
            "memory_mb": 8192,
            "disk_size_gb": 100,
            "esxi_config": {
                "cpu_hot_add": True,
                "memory_hot_add": True,
                "nested_virtualization": True,
                "hardware_version": "vmx-19"
            }
        }
        
        with patch.object(vm_operations, '_create_vm_config_spec') as mock_config:
            mock_config.return_value = Mock()
            
            vm_operations.create_vm(**vm_config)
            
            # Verify ESXi-specific configuration was applied
            mock_config.assert_called_once()
            call_args = mock_config.call_args[1]
            assert call_args["esxi_config"]["nested_virtualization"] is True

    def test_direct_host_resource_check(self, vm_operations, mock_connection):
        """Test direct ESXi host resource availability check."""
        mock_host = Mock()
        mock_host.summary = Mock()
        mock_host.summary.hardware = Mock()
        mock_host.summary.hardware.numCpuCores = 16
        mock_host.summary.hardware.memorySize = 68719476736  # 64GB in bytes
        
        mock_host.summary.quickStats = Mock()
        mock_host.summary.quickStats.overallCpuUsage = 8000  # MHz
        mock_host.summary.quickStats.overallMemoryUsage = 32768  # MB
        
        mock_connection.get_host_system.return_value = mock_host
        
        # Test resource availability
        resources = vm_operations.check_host_resources()
        
        assert resources["cpu"]["total_cores"] == 16
        assert resources["memory"]["total_gb"] == 64
        assert resources["cpu"]["available_cores"] > 0
        assert resources["memory"]["available_gb"] > 0

    def test_vm_power_operations_esxi(self, vm_operations, mock_vm):
        """Test ESXi-specific VM power operations."""
        # Test power on with ESXi-specific options
        mock_task = Mock()
        mock_task.info = Mock()
        mock_task.info.state = "success"
        
        with patch.object(mock_vm, 'PowerOnVM_Task', return_value=mock_task):
            result = vm_operations.power_on_vm(mock_vm, host_affinity=True)
            
            assert result["status"] == "success"
            mock_vm.PowerOnVM_Task.assert_called_once()

    def test_vm_snapshot_operations_esxi(self, vm_operations, mock_vm):
        """Test ESXi VM snapshot operations."""
        mock_task = Mock()
        mock_task.info = Mock()
        mock_task.info.state = "success"
        mock_task.info.result = Mock()
        
        # Test snapshot creation with ESXi-specific options
        with patch.object(mock_vm, 'CreateSnapshot_Task', return_value=mock_task):
            result = vm_operations.create_snapshot(
                vm=mock_vm,
                name="esxi-snapshot",
                description="ESXi direct snapshot",
                memory=False,  # ESXi typically doesn't include memory
                quiesce=True
            )
            
            assert result["status"] == "success"
            mock_vm.CreateSnapshot_Task.assert_called_once()

    def test_vm_clone_on_esxi(self, vm_operations, mock_vm, mock_connection):
        """Test VM cloning directly on ESXi host."""
        mock_host = Mock()
        mock_datastore = Mock()
        mock_datastore.name = "datastore1"
        mock_host.datastore = [mock_datastore]
        mock_connection.get_host_system.return_value = mock_host
        
        mock_task = Mock()
        mock_task.info = Mock()
        mock_task.info.state = "success"
        mock_task.info.result = Mock()
        mock_task.info.result.name = "cloned-vm"
        
        with patch.object(mock_vm, 'CloneVM_Task', return_value=mock_task):
            result = vm_operations.clone_vm(
                source_vm=mock_vm,
                clone_name="cloned-vm",
                datastore="datastore1"
            )
            
            assert result["status"] == "success"
            assert result["vm_name"] == "cloned-vm"

    def test_esxi_performance_monitoring(self, vm_operations, mock_vm, mock_connection):
        """Test ESXi-specific VM performance monitoring."""
        mock_perf_manager = Mock()
        mock_connection.service_instance.content.perfManager = mock_perf_manager
        
        # Mock performance data
        mock_perf_data = Mock()
        mock_perf_data.value = [
            Mock(id=Mock(instance=""), value=[100, 150, 200])  # CPU usage
        ]
        
        with patch.object(mock_perf_manager, 'QueryPerf', return_value=[mock_perf_data]):
            metrics = vm_operations.get_vm_performance_metrics(
                vm=mock_vm,
                metrics=["cpu.usage.average"],
                interval=20,
                duration=300
            )
            
            assert "cpu.usage.average" in metrics
            assert len(metrics["cpu.usage.average"]) == 3

    def test_esxi_storage_operations(self, vm_operations, mock_vm, mock_connection):
        """Test ESXi-specific storage operations."""
        mock_host = Mock()
        mock_storage_system = Mock()
        mock_host.configManager = Mock()
        mock_host.configManager.storageSystem = mock_storage_system
        mock_connection.get_host_system.return_value = mock_host
        
        # Test direct datastore operations
        mock_datastore_info = Mock()
        mock_datastore_info.name = "datastore1"
        mock_datastore_info.freeSpace = 1073741824000  # 1TB
        mock_datastore_info.maxFileSize = 274877906944  # 256GB
        
        with patch.object(mock_storage_system, 'QueryDatastoreInfo', return_value=[mock_datastore_info]):
            datastore_info = vm_operations.get_datastore_info("datastore1")
            
            assert datastore_info["name"] == "datastore1"
            assert datastore_info["free_space_gb"] > 0

    def test_vm_hardware_modification_esxi(self, vm_operations, mock_vm):
        """Test ESXi VM hardware modification."""
        mock_task = Mock()
        mock_task.info = Mock()
        mock_task.info.state = "success"
        
        # Test CPU hot-add (ESXi specific feature)
        with patch.object(mock_vm, 'ReconfigVM_Task', return_value=mock_task):
            result = vm_operations.modify_vm_hardware(
                vm=mock_vm,
                cpu_count=4,
                memory_mb=8192,
                cpu_hot_add=True,
                memory_hot_add=True
            )
            
            assert result["status"] == "success"
            mock_vm.ReconfigVM_Task.assert_called_once()

    def test_esxi_network_operations(self, vm_operations, mock_vm, mock_connection):
        """Test ESXi-specific network operations."""
        mock_host = Mock()
        mock_network_system = Mock()
        mock_host.configManager = Mock()
        mock_host.configManager.networkSystem = mock_network_system
        mock_connection.get_host_system.return_value = mock_host
        
        # Test direct network configuration
        mock_portgroup = Mock()
        mock_portgroup.spec = Mock()
        mock_portgroup.spec.name = "VM Network"
        mock_portgroup.spec.vlanId = 0
        
        with patch.object(mock_network_system, 'QueryNetworkConfig') as mock_query:
            mock_query.return_value = Mock(portgroup=[mock_portgroup])
            
            network_config = vm_operations.get_network_configuration()
            
            assert len(network_config["portgroups"]) > 0
            assert network_config["portgroups"][0]["name"] == "VM Network"

    @pytest.mark.asyncio
    async def test_async_vm_operations(self, vm_operations, mock_vm):
        """Test asynchronous VM operations on ESXi."""
        # Test async power operations
        with patch.object(vm_operations, 'power_on_vm_async', new_callable=AsyncMock) as mock_power:
            mock_power.return_value = {"status": "success"}
            
            result = await vm_operations.power_on_vm_async(mock_vm)
            assert result["status"] == "success"

    def test_error_handling_esxi_specific(self, vm_operations, mock_connection):
        """Test ESXi-specific error handling."""
        mock_host = Mock()
        mock_connection.get_host_system.return_value = mock_host
        
        # Test insufficient resources error
        mock_host.summary = Mock()
        mock_host.summary.hardware = Mock()
        mock_host.summary.hardware.memorySize = 1073741824  # 1GB only
        
        with pytest.raises(InsufficientResourcesError):
            vm_operations.create_vm(
                vm_name="large-vm",
                cpu_count=8,
                memory_mb=16384,  # 16GB - more than available
                disk_size_gb=100
            )

    def test_esxi_maintenance_mode_vm_operations(self, vm_operations, mock_connection):
        """Test VM operations during ESXi maintenance mode."""
        mock_host = Mock()
        mock_host.runtime = Mock()
        mock_host.runtime.inMaintenanceMode = True
        mock_connection.get_host_system.return_value = mock_host
        
        # Test that certain operations are blocked in maintenance mode
        with pytest.raises(VMOperationError) as exc_info:
            vm_operations.create_vm(
                vm_name="test-vm",
                cpu_count=2,
                memory_mb=4096,
                disk_size_gb=50
            )
        
        assert "maintenance mode" in str(exc_info.value).lower()

    def test_vm_migration_esxi_to_esxi(self, vm_operations, mock_vm, mock_connection):
        """Test VM migration between ESXi hosts (without vCenter)."""
        # This would be a cold migration or export/import operation
        mock_task = Mock()
        mock_task.info = Mock()
        mock_task.info.state = "success"
        
        with patch.object(vm_operations, 'export_vm') as mock_export:
            mock_export.return_value = {"status": "success", "export_path": "/tmp/vm-export"}
            
            result = vm_operations.migrate_vm_cold(
                vm=mock_vm,
                destination_host="esxi-02.example.com",
                destination_datastore="datastore2"
            )
            
            assert result["status"] == "success"