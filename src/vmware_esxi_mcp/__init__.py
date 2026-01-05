"""
VMware ESXi MCP Server

A professional Model Context Protocol (MCP) server implementation for VMware ESXi 
hypervisor management. This enterprise-ready solution provides secure, standardized 
interfaces for ESXi host operations, virtual machine lifecycle management, and 
infrastructure monitoring.

Author: uldyssian-sh
License: MIT
Version: 1.5.0
"""

__version__ = "1.5.0"
__author__ = "uldyssian-sh"
__license__ = "MIT"
__description__ = "VMware ESXi MCP Server - Professional ESXi management via MCP"

from .server import ESXiMCPServer
from .exceptions import (
    ESXiConnectionError,
    ESXiAuthenticationError,
    ESXiOperationError,
    ValidationError
)

__all__ = [
    "ESXiMCPServer",
    "ESXiConnectionError", 
    "ESXiAuthenticationError",
    "ESXiOperationError",
    "ValidationError",
    "__version__",
    "__author__",
    "__license__",
    "__description__"
]