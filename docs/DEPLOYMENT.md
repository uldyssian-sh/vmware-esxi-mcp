# VMware ESXi MCP Server Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the VMware ESXi MCP Server in production environments. The server is designed for direct ESXi hypervisor management without vCenter dependency.

## Prerequisites

### System Requirements

#### Minimum Requirements
- **CPU**: 2 cores
- **Memory**: 4GB RAM
- **Storage**: 20GB available space
- **Network**: 1Gbps network connection
- **OS**: Linux (Ubuntu 20.04+, RHEL 8+, CentOS 8+)

#### Recommended Requirements
- **CPU**: 4 cores
- **Memory**: 8GB RAM
- **Storage**: 50GB SSD
- **Network**: 10Gbps network connection
- **OS**: Ubuntu 22.04 LTS or RHEL 9

### ESXi Environment
- **ESXi Version**: 6.7 or later (7.0+ recommended)
- **Network Access**: HTTPS (443) access to ESXi hosts
- **Credentials**: Root or administrative user account
- **SSL Certificates**: Valid SSL certificates (recommended)

### Software Dependencies
- **Python**: 3.8 or higher
- **Docker**: 20.10+ (for containerized deployment)
- **Git**: For source code management

## Installation Methods

### Method 1: Docker Deployment (Recommended)

#### Quick Start with Docker Compose

1. **Clone the repository:**
```bash
git clone https://github.com/uldyssian-sh/vmware-esxi-mcp.git
cd vmware-esxi-mcp
```

2. **Configure environment:**
```bash
cp config.example.yaml config.yaml
# Edit config.yaml with your ESXi details
```

3. **Set environment variables:**
```bash
export ESXI_HOST="esxi-host.example.com"
export ESXI_USERNAME="root"
export ESXI_PASSWORD="your-secure-password"
export MCP_API_KEY="your-api-key"
```

4. **Deploy with Docker Compose:**
```bash
docker-compose up -d
```

5. **Verify deployment:**
```bash
curl http://localhost:8080/health
```

#### Production Docker Deployment

1. **Build production image:**
```bash
docker build -t vmware-esxi-mcp:production \
  --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  --build-arg VCS_REF=$(git rev-parse --short HEAD) \
  --build-arg VERSION=1.0.0 .
```

2. **Run with production settings:**
```bash
docker run -d \
  --name vmware-esxi-mcp \
  --restart unless-stopped \
  -p 8080:8080 \
  -p 9090:9090 \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -v esxi_mcp_logs:/app/logs \
  -v esxi_mcp_data:/app/data \
  --security-opt no-new-privileges:true \
  --read-only \
  --tmpfs /tmp:noexec,nosuid,size=100m \
  vmware-esxi-mcp:production
```

### Method 2: Native Python Installation

#### System Preparation

1. **Install Python and dependencies:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev build-essential

# RHEL/CentOS
sudo dnf install python3.11 python3.11-devel gcc
```

2. **Create dedicated user:**
```bash
sudo useradd -r -s /bin/bash -d /opt/vmware-esxi-mcp esxi-mcp
sudo mkdir -p /opt/vmware-esxi-mcp
sudo chown esxi-mcp:esxi-mcp /opt/vmware-esxi-mcp
```

#### Application Installation

1. **Switch to application user:**
```bash
sudo -u esxi-mcp -i
cd /opt/vmware-esxi-mcp
```

2. **Clone and setup:**
```bash
git clone https://github.com/uldyssian-sh/vmware-esxi-mcp.git .
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

3. **Configure application:**
```bash
cp config.example.yaml config.yaml
# Edit configuration file
nano config.yaml
```

4. **Create systemd service:**
```bash
sudo tee /etc/systemd/system/vmware-esxi-mcp.service > /dev/null <<EOF
[Unit]
Description=VMware ESXi MCP Server
After=network.target
Wants=network.target

[Service]
Type=simple
User=esxi-mcp
Group=esxi-mcp
WorkingDirectory=/opt/vmware-esxi-mcp
Environment=PATH=/opt/vmware-esxi-mcp/venv/bin
ExecStart=/opt/vmware-esxi-mcp/venv/bin/python -m vmware_esxi_mcp --config /opt/vmware-esxi-mcp/config.yaml
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=vmware-esxi-mcp

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/vmware-esxi-mcp/logs /opt/vmware-esxi-mcp/data

[Install]
WantedBy=multi-user.target
EOF
```

5. **Enable and start service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable vmware-esxi-mcp
sudo systemctl start vmware-esxi-mcp
sudo systemctl status vmware-esxi-mcp
```

### Method 3: Kubernetes Deployment

#### Kubernetes Manifests

1. **Create namespace:**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: vmware-esxi-mcp
```

2. **Create ConfigMap:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: esxi-mcp-config
  namespace: vmware-esxi-mcp
data:
  config.yaml: |
    esxi:
      host: "esxi-host.example.com"
      username: "root"
      port: 443
      ssl_verify: true
      timeout: 30
    mcp:
      server_name: "vmware-esxi-mcp"
      version: "1.0.0"
      host: "0.0.0.0"
      port: 8080
    logging:
      level: "INFO"
      file: "esxi-mcp.log"
```

3. **Create Secret:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: esxi-mcp-secrets
  namespace: vmware-esxi-mcp
type: Opaque
data:
  esxi-password: <base64-encoded-password>
  api-key: <base64-encoded-api-key>
```

4. **Create Deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vmware-esxi-mcp
  namespace: vmware-esxi-mcp
spec:
  replicas: 2
  selector:
    matchLabels:
      app: vmware-esxi-mcp
  template:
    metadata:
      labels:
        app: vmware-esxi-mcp
    spec:
      containers:
      - name: vmware-esxi-mcp
        image: uldyssian-sh/vmware-esxi-mcp:1.0.0
        ports:
        - containerPort: 8080
        - containerPort: 9090
        env:
        - name: ESXI_PASSWORD
          valueFrom:
            secretKeyRef:
              name: esxi-mcp-secrets
              key: esxi-password
        - name: MCP_API_KEY
          valueFrom:
            secretKeyRef:
              name: esxi-mcp-secrets
              key: api-key
        volumeMounts:
        - name: config
          mountPath: /app/config.yaml
          subPath: config.yaml
        - name: logs
          mountPath: /app/logs
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 2
            memory: 4Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: config
        configMap:
          name: esxi-mcp-config
      - name: logs
        emptyDir: {}
```

5. **Create Service:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: vmware-esxi-mcp-service
  namespace: vmware-esxi-mcp
spec:
  selector:
    app: vmware-esxi-mcp
  ports:
  - name: http
    port: 80
    targetPort: 8080
  - name: metrics
    port: 9090
    targetPort: 9090
  type: ClusterIP
```

## Configuration

### Basic Configuration

```yaml
# ESXi Host Configuration
esxi:
  host: "esxi-host.example.com"
  username: "root"
  password: "${ESXI_PASSWORD}"
  port: 443
  ssl_verify: true
  timeout: 30
  pool_size: 5

# MCP Server Configuration
mcp:
  server_name: "vmware-esxi-mcp"
  version: "1.0.0"
  host: "0.0.0.0"
  port: 8080
  workers: 4

# Security Configuration
security:
  api_key: "${MCP_API_KEY}"
  rate_limit: 100
  session_timeout: 3600
  encryption: "AES256"

# Logging Configuration
logging:
  level: "INFO"
  file: "esxi-mcp.log"
  max_size: "10MB"
  backup_count: 5
```

### Advanced Configuration

```yaml
# Performance Configuration
performance:
  cache:
    enabled: true
    ttl: 300
    max_size: 1000
  async_operations: true
  max_concurrent: 10
  metrics:
    enabled: true
    port: 9090

# Feature Configuration
features:
  vm_operations: true
  host_management: true
  resource_monitoring: true
  snapshot_management: true
  power_operations: true

# Health Check Configuration
health:
  enabled: true
  endpoint: "/health"
  interval: 30
  timeout: 10
```

## Security Hardening

### Network Security

1. **Firewall Configuration:**
```bash
# Allow only necessary ports
sudo ufw allow 8080/tcp  # MCP API
sudo ufw allow 9090/tcp  # Metrics (if needed)
sudo ufw enable
```

2. **SSL/TLS Configuration:**
```yaml
security:
  ssl_cert: "/path/to/cert.pem"
  ssl_key: "/path/to/key.pem"
  ssl_ca: "/path/to/ca.pem"
```

### Authentication Security

1. **API Key Management:**
```bash
# Generate secure API key
openssl rand -hex 32
```

2. **ESXi Credentials:**
```bash
# Use environment variables
export ESXI_PASSWORD="$(openssl rand -base64 32)"
```

### System Security

1. **File Permissions:**
```bash
chmod 600 config.yaml
chmod 700 logs/
chown -R esxi-mcp:esxi-mcp /opt/vmware-esxi-mcp
```

2. **SELinux Configuration (RHEL/CentOS):**
```bash
sudo setsebool -P httpd_can_network_connect 1
sudo semanage port -a -t http_port_t -p tcp 8080
```

## Monitoring and Observability

### Prometheus Integration

1. **Metrics Endpoint:**
```
http://localhost:9090/metrics
```

2. **Key Metrics:**
- `esxi_mcp_requests_total`
- `esxi_mcp_request_duration_seconds`
- `esxi_mcp_active_connections`
- `esxi_mcp_vm_operations_total`
- `esxi_mcp_errors_total`

### Logging

1. **Log Locations:**
- **Docker**: `/app/logs/esxi-mcp.log`
- **Native**: `/opt/vmware-esxi-mcp/logs/esxi-mcp.log`
- **Systemd**: `journalctl -u vmware-esxi-mcp`

2. **Log Rotation:**
```bash
# Configure logrotate
sudo tee /etc/logrotate.d/vmware-esxi-mcp > /dev/null <<EOF
/opt/vmware-esxi-mcp/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 esxi-mcp esxi-mcp
    postrotate
        systemctl reload vmware-esxi-mcp
    endscript
}
EOF
```

### Health Checks

1. **Application Health:**
```bash
curl -f http://localhost:8080/health
```

2. **ESXi Connectivity:**
```bash
curl -f http://localhost:8080/health/esxi
```

## Backup and Recovery

### Configuration Backup

```bash
#!/bin/bash
# backup-config.sh
BACKUP_DIR="/backup/vmware-esxi-mcp"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" \
    config.yaml \
    logs/ \
    data/

# Keep only last 30 backups
find "$BACKUP_DIR" -name "config_*.tar.gz" -mtime +30 -delete
```

### Disaster Recovery

1. **Recovery Procedure:**
```bash
# Stop service
sudo systemctl stop vmware-esxi-mcp

# Restore configuration
tar -xzf /backup/vmware-esxi-mcp/config_latest.tar.gz

# Start service
sudo systemctl start vmware-esxi-mcp
```

## Troubleshooting

### Common Issues

#### Connection Issues
```bash
# Test ESXi connectivity
curl -k https://esxi-host.example.com/sdk

# Check DNS resolution
nslookup esxi-host.example.com

# Verify SSL certificates
openssl s_client -connect esxi-host.example.com:443
```

#### Performance Issues
```bash
# Check resource usage
htop
iostat -x 1
netstat -i

# Monitor application metrics
curl http://localhost:9090/metrics | grep esxi_mcp
```

#### Authentication Issues
```bash
# Verify credentials
python3 -c "
from pyVim.connect import SmartConnect
si = SmartConnect(host='esxi-host.example.com', user='root', pwd='password')
print('Connection successful')
"
```

### Log Analysis

```bash
# Check application logs
tail -f /opt/vmware-esxi-mcp/logs/esxi-mcp.log

# Filter error messages
grep -i error /opt/vmware-esxi-mcp/logs/esxi-mcp.log

# Monitor real-time logs
journalctl -u vmware-esxi-mcp -f
```

## Performance Tuning

### System Optimization

1. **Kernel Parameters:**
```bash
# /etc/sysctl.d/99-vmware-esxi-mcp.conf
net.core.somaxconn = 1024
net.ipv4.tcp_max_syn_backlog = 1024
vm.swappiness = 10
```

2. **File Descriptors:**
```bash
# /etc/security/limits.d/vmware-esxi-mcp.conf
esxi-mcp soft nofile 65536
esxi-mcp hard nofile 65536
```

### Application Tuning

```yaml
performance:
  # Connection pooling
  pool_size: 10
  max_retries: 3
  
  # Caching
  cache:
    enabled: true
    ttl: 300
    max_size: 5000
  
  # Async operations
  async_operations: true
  max_concurrent: 20
  
  # Worker processes
  workers: 8
```

## Maintenance

### Regular Maintenance Tasks

1. **Daily:**
   - Check service status
   - Monitor disk space
   - Review error logs

2. **Weekly:**
   - Update security patches
   - Backup configuration
   - Performance review

3. **Monthly:**
   - Update dependencies
   - Security audit
   - Capacity planning

### Update Procedure

```bash
# Backup current installation
sudo systemctl stop vmware-esxi-mcp
cp -r /opt/vmware-esxi-mcp /opt/vmware-esxi-mcp.backup

# Update application
cd /opt/vmware-esxi-mcp
git pull origin main
source venv/bin/activate
pip install --upgrade -r requirements.txt

# Test configuration
python -m vmware_esxi_mcp --config config.yaml --test

# Start service
sudo systemctl start vmware-esxi-mcp
```

## Support

### Getting Help

- **Documentation**: [GitHub Repository](https://github.com/uldyssian-sh/vmware-esxi-mcp)
- **Issues**: [GitHub Issues](https://github.com/uldyssian-sh/vmware-esxi-mcp/issues)
- **Security**: [Security Policy](https://github.com/uldyssian-sh/vmware-esxi-mcp/blob/main/SECURITY.md)

### Professional Support

For enterprise support and consulting services, please contact the maintainers through the GitHub repository.

---

**Maintained by: uldyssian-sh**

**Disclaimer: Use of this code is at your own risk. Author bears no responsibility for any damages caused by the code.**