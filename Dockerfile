# VMware ESXi MCP Server - Enterprise Docker Image
# Multi-stage build for optimized production deployment

# Build stage
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# Add metadata labels
LABEL org.opencontainers.image.title="VMware ESXi MCP Server"
LABEL org.opencontainers.image.description="Professional Model Context Protocol server for VMware ESXi management"
LABEL org.opencontainers.image.authors="uldyssian-sh"
LABEL org.opencontainers.image.vendor="uldyssian-sh"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${VCS_REF}"
LABEL org.opencontainers.image.source="https://github.com/uldyssian-sh/vmware-esxi-mcp"
LABEL org.opencontainers.image.url="https://github.com/uldyssian-sh/vmware-esxi-mcp"
LABEL org.opencontainers.image.documentation="https://github.com/uldyssian-sh/vmware-esxi-mcp/blob/main/README.md"
LABEL org.opencontainers.image.licenses="MIT"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r mcp && useradd -r -g mcp -d /app -s /bin/bash mcp

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ ./src/
COPY config.example.yaml ./config.yaml
COPY setup.py .
COPY README.md .
COPY LICENSE .

# Install the application
RUN pip install -e .

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/backup && \
    chown -R mcp:mcp /app

# Switch to non-root user
USER mcp

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV MCP_CONFIG_FILE=/app/config.yaml
ENV MCP_LOG_LEVEL=INFO
ENV MCP_LOG_FILE=/app/logs/esxi-mcp.log

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Default command
CMD ["python", "-m", "vmware_esxi_mcp", "--config", "/app/config.yaml"]