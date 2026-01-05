# VMware ESXi MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)
[![Security Scan](https://img.shields.io/badge/security-scanned-brightgreen.svg)](https://github.com/uldyssian-sh/vmware-esxi-mcp/security)

A professional Model Context Protocol (MCP) server implementation for VMware ESXi hypervisor management. This enterprise-ready solution provides secure, standardized interfaces for ESXi host operations, virtual machine lifecycle management, and infrastructure monitoring.

## Features

### Core ESXi Management
- **Host Operations**: Power management, maintenance mode, configuration
- **Virtual Machine Lifecycle**: Create, clone, migrate, snapshot management
- **Resource Monitoring**: CPU, memory, storage, network utilization
- **Security Management**: User permissions, SSL certificates, firewall rules
- **Storage Operations**: Datastore management, VMFS operations, NFS/iSCSI configuration

### MCP Integration
- **Standardized Protocol**: Full MCP specification compliance
- **Tool Discovery**: Dynamic capability advertisement
- **Resource Management**: Efficient connection pooling and caching
- **Error Handling**: Comprehensive error reporting and recovery
- **Authentication**: Secure credential management with token refresh

### Enterprise Features
- **High Availability**: Connection failover and retry mechanisms
- **Audit Logging**: Comprehensive operation tracking
- **Role-Based Access**: Granular permission controls
- **Performance Optimization**: Bulk operations and async processing
- **Exception Management**: Comprehensive error handling with custom exception classes
- **Monitoring Integration**: Prometheus metrics and health checks

## Quick Start

### Prerequisites
- Python 3.8 or higher
- VMware ESXi 6.7 or later
- Network connectivity to ESXi host
- Valid ESXi credentials with appropriate permissions

### Installation

```bash
# Clone the repository
git clone https://github.com/uldyssian-sh/vmware-esxi-mcp.git
cd vmware-esxi-mcp

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp config.example.yaml config.yaml
# Edit config.yaml with your ESXi details
```

### Configuration

Create `config.yaml`:

```yaml
esxi:
  host: "esxi-host.example.com"
  username: "root"
  password: "${ESXI_PASSWORD}"
  port: 443
  ssl_verify: true
  timeout: 30

mcp:
  server_name: "vmware-esxi-mcp"
  version: "1.7.0"
  capabilities:
    - "vm_management"
    - "host_operations"
    - "resource_monitoring"

logging:
  level: "INFO"
  file: "esxi-mcp.log"
  max_size: "10MB"
  backup_count: 5

security:
  api_key: "${MCP_API_KEY}"
  rate_limit: 100
  session_timeout: 3600
```

### Usage

```bash
# Start the MCP server
python -m vmware_esxi_mcp --config config.yaml

# Or use environment variables
export ESXI_HOST="esxi-host.example.com"
export ESXI_USERNAME="root"
export ESXI_PASSWORD="your-password"
export MCP_API_KEY="your-api-key"

python -m vmware_esxi_mcp
```

## MCP Tools

### Virtual Machine Management

#### create_vm
Create a new virtual machine with specified configuration.

```json
{
  "name": "create_vm",
  "description": "Create a new virtual machine",
  "inputSchema": {
    "type": "object",
    "properties": {
      "vm_name": {"type": "string"},
      "cpu_count": {"type": "integer", "minimum": 1},
      "memory_mb": {"type": "integer", "minimum": 512},
      "disk_size_gb": {"type": "integer", "minimum": 1},
      "network": {"type": "string"},
      "guest_os": {"type": "string"}
    },
    "required": ["vm_name", "cpu_count", "memory_mb", "disk_size_gb"]
  }
}
```

#### power_vm
Control virtual machine power state.

```json
{
  "name": "power_vm",
  "description": "Control VM power state",
  "inputSchema": {
    "type": "object",
    "properties": {
      "vm_name": {"type": "string"},
      "action": {"type": "string", "enum": ["on", "off", "reset", "suspend"]}
    },
    "required": ["vm_name", "action"]
  }
}
```

### Host Management

#### get_host_info
Retrieve comprehensive ESXi host information.

```json
{
  "name": "get_host_info",
  "description": "Get ESXi host system information",
  "inputSchema": {
    "type": "object",
    "properties": {
      "include_hardware": {"type": "boolean", "default": true},
      "include_network": {"type": "boolean", "default": true},
      "include_storage": {"type": "boolean", "default": true}
    }
  }
}
```

#### maintenance_mode
Manage host maintenance mode operations.

```json
{
  "name": "maintenance_mode",
  "description": "Enter or exit maintenance mode",
  "inputSchema": {
    "type": "object",
    "properties": {
      "action": {"type": "string", "enum": ["enter", "exit"]},
      "evacuate_vms": {"type": "boolean", "default": true},
      "timeout": {"type": "integer", "default": 300}
    },
    "required": ["action"]
  }
}
```

## Architecture

### Component Overview
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Client    │────│  ESXi MCP       │────│   VMware ESXi   │
│   Application   │    │  Server         │    │   Host          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                       ┌─────────────────┐
                       │   Configuration │
                       │   & Logging     │
                       └─────────────────┘
```

### Security Architecture
- **Authentication**: Multi-factor authentication support
- **Authorization**: Role-based access control (RBAC)
- **Encryption**: TLS 1.3 for all communications
- **Audit Trail**: Comprehensive logging of all operations
- **Input Validation**: Strict parameter validation and sanitization

## Development

### Project Structure
```
vmware-esxi-mcp/
├── src/
│   ├── vmware_esxi_mcp/
│   │   ├── __init__.py
│   │   ├── server.py
│   │   ├── tools/
│   │   ├── auth/
│   │   └── utils/
├── tests/
├── docs/
├── examples/
├── requirements.txt
└── setup.py
```

### Testing

```bash
# Run unit tests
python -m pytest tests/

# Run integration tests
python -m pytest tests/integration/ --esxi-host=test-host

# Run security tests
python -m pytest tests/security/
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Security Considerations

### Production Deployment
- Use strong, unique passwords for ESXi accounts
- Enable certificate verification in production
- Implement proper network segmentation
- Regular security updates and patches
- Monitor and audit all operations

### Best Practices
- Rotate credentials regularly
- Use least-privilege access principles
- Enable comprehensive logging
- Implement proper backup strategies
- Test disaster recovery procedures

## Troubleshooting

### Common Issues

**Connection Timeout**
```bash
# Check network connectivity
ping esxi-host.example.com

# Verify ESXi SSH/API access
curl -k https://esxi-host.example.com/sdk
```

**Authentication Failures**
- Verify credentials in configuration
- Check ESXi user permissions
- Ensure account is not locked

**SSL Certificate Issues**
- Update ESXi SSL certificates
- Configure proper certificate validation
- Check certificate expiration dates

## Performance Tuning

### Optimization Guidelines
- Use connection pooling for multiple operations
- Implement proper caching strategies
- Optimize batch operations
- Monitor resource utilization
- Configure appropriate timeouts

### Monitoring Metrics
- API response times
- Connection pool utilization
- Error rates and types
- Resource consumption
- Operation success rates

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributors

- **uldyssian-sh LT** - *Initial work and maintenance*
- **dependabot[bot]** - *Dependency updates*
- **actions-user** - *Automated workflows*

## References

- [VMware vSphere API Documentation](https://developer.vmware.com/apis/vsphere-automation/)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [VMware ESXi Security Guide](https://docs.vmware.com/en/VMware-vSphere/index.html)
- [Python VMware Libraries](https://github.com/vmware/pyvmomi)

## Support

For support and questions:
- Create an issue in this repository
- Check the [documentation](docs/)
- Review [troubleshooting guide](docs/troubleshooting.md)

---

**Maintained by: uldyssian-sh**

**Disclaimer: Use of this code is at your own risk. Author bears no responsibility for any damages caused by the code.**

⭐ Star this repository if you find it helpful!