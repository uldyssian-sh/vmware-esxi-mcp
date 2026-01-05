# VMware ESXi MCP Server API Documentation

## Overview

The VMware ESXi MCP Server provides a comprehensive Model Context Protocol (MCP) interface for managing VMware ESXi hypervisors. This API documentation covers all available tools, their parameters, and usage examples.

## Authentication

All API requests require authentication using one of the following methods:

### API Key Authentication
```http
Authorization: Bearer YOUR_API_KEY
```

### Session-based Authentication
```http
Cookie: session_id=YOUR_SESSION_ID
```

## Base URL

```
http://localhost:8080/mcp
```

## MCP Tools

### Virtual Machine Management

#### create_vm

Creates a new virtual machine on the ESXi host.

**Parameters:**
- `vm_name` (string, required): Name of the virtual machine
- `cpu_count` (integer, required): Number of CPU cores (1-64)
- `memory_mb` (integer, required): Memory in MB (512-262144)
- `disk_size_gb` (integer, required): Disk size in GB (1-2048)
- `network` (string, optional): Network name (default: "VM Network")
- `guest_os` (string, optional): Guest OS type (default: "otherGuest")
- `datastore` (string, optional): Datastore name (auto-selected if not specified)

**Example Request:**
```json
{
  "tool": "create_vm",
  "arguments": {
    "vm_name": "test-vm-001",
    "cpu_count": 2,
    "memory_mb": 4096,
    "disk_size_gb": 50,
    "network": "VM Network",
    "guest_os": "ubuntu64Guest"
  }
}
```

**Example Response:**
```json
{
  "status": "success",
  "data": {
    "vm_id": "vm-123",
    "vm_name": "test-vm-001",
    "power_state": "poweredOff",
    "cpu_count": 2,
    "memory_mb": 4096,
    "disk_size_gb": 50
  },
  "metadata": {
    "timestamp": "2026-01-05T10:30:00Z",
    "operation": "create_vm",
    "duration_ms": 15000
  }
}
```

#### clone_vm

Clones an existing virtual machine.

**Parameters:**
- `source_vm` (string, required): Name of the source VM to clone
- `clone_name` (string, required): Name for the cloned VM
- `power_on` (boolean, optional): Power on after cloning (default: false)
- `datastore` (string, optional): Target datastore (default: same as source)

**Example Request:**
```json
{
  "tool": "clone_vm",
  "arguments": {
    "source_vm": "template-vm",
    "clone_name": "cloned-vm-001",
    "power_on": true
  }
}
```

#### delete_vm

Deletes a virtual machine and its associated files.

**Parameters:**
- `vm_name` (string, required): Name of the VM to delete
- `force` (boolean, optional): Force deletion even if powered on (default: false)

**Example Request:**
```json
{
  "tool": "delete_vm",
  "arguments": {
    "vm_name": "old-vm-001",
    "force": false
  }
}
```

#### power_vm

Controls the power state of a virtual machine.

**Parameters:**
- `vm_name` (string, required): Name of the virtual machine
- `action` (string, required): Power action ("on", "off", "reset", "suspend")
- `force` (boolean, optional): Force the action (default: false)

**Example Request:**
```json
{
  "tool": "power_vm",
  "arguments": {
    "vm_name": "test-vm-001",
    "action": "on"
  }
}
```

#### get_vm_info

Retrieves detailed information about a virtual machine.

**Parameters:**
- `vm_name` (string, required): Name of the virtual machine
- `include_performance` (boolean, optional): Include performance metrics (default: false)

**Example Response:**
```json
{
  "status": "success",
  "data": {
    "vm_name": "test-vm-001",
    "vm_id": "vm-123",
    "power_state": "poweredOn",
    "guest_os": "Ubuntu Linux (64-bit)",
    "cpu_count": 2,
    "memory_mb": 4096,
    "disk_usage_gb": 25.5,
    "network_adapters": [
      {
        "name": "Network adapter 1",
        "network": "VM Network",
        "mac_address": "00:50:56:12:34:56"
      }
    ],
    "tools_status": "toolsOk",
    "uptime_seconds": 86400
  }
}
```

### Host Management

#### get_host_info

Retrieves comprehensive ESXi host information.

**Parameters:**
- `include_hardware` (boolean, optional): Include hardware details (default: true)
- `include_network` (boolean, optional): Include network configuration (default: true)
- `include_storage` (boolean, optional): Include storage information (default: true)
- `include_performance` (boolean, optional): Include performance metrics (default: false)

**Example Response:**
```json
{
  "status": "success",
  "data": {
    "host_name": "esxi-host-01.example.com",
    "version": "7.0.3",
    "build": "19193900",
    "hardware": {
      "vendor": "Dell Inc.",
      "model": "PowerEdge R740",
      "cpu_model": "Intel Xeon Gold 6248R",
      "cpu_cores": 48,
      "memory_gb": 256
    },
    "network": {
      "management_ip": "192.168.1.100",
      "vswitch_count": 2,
      "portgroup_count": 5
    },
    "storage": {
      "datastore_count": 3,
      "total_capacity_gb": 2048,
      "free_space_gb": 1024
    }
  }
}
```

#### maintenance_mode

Manages ESXi host maintenance mode.

**Parameters:**
- `action` (string, required): Action to perform ("enter", "exit")
- `evacuate_vms` (boolean, optional): Evacuate VMs when entering (default: true)
- `timeout` (integer, optional): Timeout in seconds (default: 300)

**Example Request:**
```json
{
  "tool": "maintenance_mode",
  "arguments": {
    "action": "enter",
    "evacuate_vms": true,
    "timeout": 600
  }
}
```

#### reboot_host

Reboots the ESXi host.

**Parameters:**
- `force` (boolean, optional): Force reboot (default: false)
- `delay` (integer, optional): Delay in seconds before reboot (default: 0)

### Resource Monitoring

#### get_performance_metrics

Retrieves performance metrics for the ESXi host or VMs.

**Parameters:**
- `target` (string, required): Target type ("host" or "vm")
- `target_name` (string, optional): VM name (required if target is "vm")
- `metrics` (array, optional): Specific metrics to retrieve
- `interval` (integer, optional): Sampling interval in seconds (default: 20)
- `duration` (integer, optional): Duration in seconds (default: 300)

**Available Metrics:**
- `cpu.usage.average`
- `mem.usage.average`
- `disk.usage.average`
- `net.usage.average`

**Example Request:**
```json
{
  "tool": "get_performance_metrics",
  "arguments": {
    "target": "host",
    "metrics": ["cpu.usage.average", "mem.usage.average"],
    "interval": 20,
    "duration": 300
  }
}
```

#### get_resource_usage

Gets current resource usage summary.

**Parameters:**
- `include_vms` (boolean, optional): Include per-VM breakdown (default: false)

**Example Response:**
```json
{
  "status": "success",
  "data": {
    "host": {
      "cpu_usage_percent": 45.2,
      "memory_usage_percent": 67.8,
      "storage_usage_percent": 52.1,
      "network_usage_mbps": 125.5
    },
    "vms": [
      {
        "name": "test-vm-001",
        "cpu_usage_percent": 12.5,
        "memory_usage_mb": 2048,
        "disk_usage_gb": 25.5
      }
    ]
  }
}
```

### Snapshot Management

#### create_snapshot

Creates a snapshot of a virtual machine.

**Parameters:**
- `vm_name` (string, required): Name of the virtual machine
- `snapshot_name` (string, required): Name for the snapshot
- `description` (string, optional): Snapshot description
- `memory` (boolean, optional): Include memory state (default: false)
- `quiesce` (boolean, optional): Quiesce guest file system (default: true)

#### delete_snapshot

Deletes a VM snapshot.

**Parameters:**
- `vm_name` (string, required): Name of the virtual machine
- `snapshot_name` (string, required): Name of the snapshot to delete
- `consolidate` (boolean, optional): Consolidate disk files (default: true)

#### revert_snapshot

Reverts a VM to a specific snapshot.

**Parameters:**
- `vm_name` (string, required): Name of the virtual machine
- `snapshot_name` (string, required): Name of the snapshot to revert to
- `power_on` (boolean, optional): Power on after revert (default: false)

## Error Handling

All API responses follow a consistent error format:

```json
{
  "status": "error",
  "error": {
    "code": "ESXI_CONNECTION_ERROR",
    "message": "Failed to connect to ESXi host",
    "details": {
      "host": "esxi-host.example.com",
      "port": 443,
      "timeout": 30
    }
  },
  "metadata": {
    "timestamp": "2026-01-05T10:30:00Z",
    "request_id": "req-12345"
  }
}
```

### Common Error Codes

- `ESXI_CONNECTION_ERROR`: Cannot connect to ESXi host
- `AUTHENTICATION_ERROR`: Invalid credentials
- `VM_NOT_FOUND`: Virtual machine not found
- `INSUFFICIENT_RESOURCES`: Not enough resources available
- `OPERATION_TIMEOUT`: Operation timed out
- `PERMISSION_DENIED`: Insufficient permissions
- `INVALID_PARAMETER`: Invalid parameter value

## Rate Limiting

API requests are rate-limited to prevent abuse:

- **Default Limit**: 100 requests per minute per API key
- **Burst Limit**: 20 requests per 10 seconds
- **Headers**: Rate limit information is included in response headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1641398400
```

## Webhooks

The server supports webhooks for real-time event notifications:

### Supported Events
- `vm.created`
- `vm.deleted`
- `vm.power.changed`
- `host.maintenance.entered`
- `host.maintenance.exited`
- `performance.threshold.exceeded`

### Webhook Configuration
```json
{
  "url": "https://your-app.com/webhooks/esxi",
  "events": ["vm.created", "vm.power.changed"],
  "secret": "your-webhook-secret"
}
```

## SDK Examples

### Python SDK
```python
from vmware_esxi_mcp import ESXiMCPClient

client = ESXiMCPClient(
    host="localhost:8080",
    api_key="your-api-key"
)

# Create a VM
result = await client.create_vm(
    vm_name="test-vm",
    cpu_count=2,
    memory_mb=4096,
    disk_size_gb=50
)

print(f"VM created: {result['data']['vm_id']}")
```

### JavaScript SDK
```javascript
const { ESXiMCPClient } = require('vmware-esxi-mcp-js');

const client = new ESXiMCPClient({
  host: 'localhost:8080',
  apiKey: 'your-api-key'
});

// Get host information
const hostInfo = await client.getHostInfo({
  includeHardware: true,
  includePerformance: true
});

console.log('Host:', hostInfo.data.host_name);
```

## Best Practices

### Performance Optimization
1. Use batch operations when possible
2. Cache frequently accessed data
3. Implement proper retry logic
4. Monitor API usage and performance

### Security
1. Use HTTPS in production
2. Rotate API keys regularly
3. Implement proper access controls
4. Monitor for suspicious activity

### Error Handling
1. Implement exponential backoff for retries
2. Handle rate limiting gracefully
3. Log errors for debugging
4. Provide meaningful error messages to users

## Support

For API support and questions:
- Create an issue: https://github.com/uldyssian-sh/vmware-esxi-mcp/issues
- Documentation: https://github.com/uldyssian-sh/vmware-esxi-mcp/blob/main/README.md
- Security issues: https://github.com/uldyssian-sh/vmware-esxi-mcp/blob/main/SECURITY.md