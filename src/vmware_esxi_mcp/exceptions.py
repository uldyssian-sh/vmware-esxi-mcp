#!/usr/bin/env python3
"""
VMware ESXi MCP Server - Exception Classes

Custom exception classes for VMware ESXi MCP Server operations.
Provides comprehensive error handling and debugging capabilities.

Author: uldyssian-sh
License: MIT
"""

from typing import Optional, Dict, Any


class ESXiMCPError(Exception):
    """Base exception class for all ESXi MCP Server errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """
        Initialize ESXi MCP error.
        
        Args:
            message: Human-readable error message
            error_code: Optional error code for programmatic handling
            details: Optional additional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary representation."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details
        }


class ESXiConnectionError(ESXiMCPError):
    """Exception raised when connection to ESXi host fails."""
    
    def __init__(self, host: str, message: str = "Failed to connect to ESXi host", **kwargs):
        """
        Initialize ESXi connection error.
        
        Args:
            host: ESXi host address
            message: Error message
            **kwargs: Additional arguments for base class
        """
        super().__init__(message, **kwargs)
        self.host = host
        self.details.update({"host": host})


class ESXiAuthenticationError(ESXiMCPError):
    """Exception raised when authentication to ESXi host fails."""
    
    def __init__(self, username: str, message: str = "Authentication failed", **kwargs):
        """
        Initialize ESXi authentication error.
        
        Args:
            username: Username that failed authentication
            message: Error message
            **kwargs: Additional arguments for base class
        """
        super().__init__(message, **kwargs)
        self.username = username
        self.details.update({"username": username})


class ESXiOperationError(ESXiMCPError):
    """Exception raised when ESXi operation fails."""
    
    def __init__(self, operation: str, message: str = "ESXi operation failed", **kwargs):
        """
        Initialize ESXi operation error.
        
        Args:
            operation: Name of the failed operation
            message: Error message
            **kwargs: Additional arguments for base class
        """
        super().__init__(message, **kwargs)
        self.operation = operation
        self.details.update({"operation": operation})


class ValidationError(ESXiMCPError):
    """Exception raised when input validation fails."""
    
    def __init__(self, field: str, value: Any, message: str = "Validation failed", **kwargs):
        """
        Initialize validation error.
        
        Args:
            field: Name of the field that failed validation
            value: Value that failed validation
            message: Error message
            **kwargs: Additional arguments for base class
        """
        super().__init__(message, **kwargs)
        self.field = field
        self.value = value
        self.details.update({"field": field, "value": str(value)})


class VMOperationError(ESXiOperationError):
    """Exception raised when virtual machine operation fails."""
    
    def __init__(self, vm_name: str, operation: str, message: str = "VM operation failed", **kwargs):
        """
        Initialize VM operation error.
        
        Args:
            vm_name: Name of the virtual machine
            operation: Name of the failed operation
            message: Error message
            **kwargs: Additional arguments for base class
        """
        super().__init__(operation, message, **kwargs)
        self.vm_name = vm_name
        self.details.update({"vm_name": vm_name})


class HostOperationError(ESXiOperationError):
    """Exception raised when host operation fails."""
    
    def __init__(self, host: str, operation: str, message: str = "Host operation failed", **kwargs):
        """
        Initialize host operation error.
        
        Args:
            host: ESXi host address
            operation: Name of the failed operation
            message: Error message
            **kwargs: Additional arguments for base class
        """
        super().__init__(operation, message, **kwargs)
        self.host = host
        self.details.update({"host": host})


class DatastoreOperationError(ESXiOperationError):
    """Exception raised when datastore operation fails."""
    
    def __init__(self, datastore: str, operation: str, message: str = "Datastore operation failed", **kwargs):
        """
        Initialize datastore operation error.
        
        Args:
            datastore: Name of the datastore
            operation: Name of the failed operation
            message: Error message
            **kwargs: Additional arguments for base class
        """
        super().__init__(operation, message, **kwargs)
        self.datastore = datastore
        self.details.update({"datastore": datastore})


class NetworkOperationError(ESXiOperationError):
    """Exception raised when network operation fails."""
    
    def __init__(self, network: str, operation: str, message: str = "Network operation failed", **kwargs):
        """
        Initialize network operation error.
        
        Args:
            network: Name of the network
            operation: Name of the failed operation
            message: Error message
            **kwargs: Additional arguments for base class
        """
        super().__init__(operation, message, **kwargs)
        self.network = network
        self.details.update({"network": network})


class SnapshotOperationError(ESXiOperationError):
    """Exception raised when snapshot operation fails."""
    
    def __init__(self, vm_name: str, snapshot_name: str, operation: str, 
                 message: str = "Snapshot operation failed", **kwargs):
        """
        Initialize snapshot operation error.
        
        Args:
            vm_name: Name of the virtual machine
            snapshot_name: Name of the snapshot
            operation: Name of the failed operation
            message: Error message
            **kwargs: Additional arguments for base class
        """
        super().__init__(operation, message, **kwargs)
        self.vm_name = vm_name
        self.snapshot_name = snapshot_name
        self.details.update({
            "vm_name": vm_name,
            "snapshot_name": snapshot_name
        })


class ConfigurationError(ESXiMCPError):
    """Exception raised when configuration is invalid."""
    
    def __init__(self, config_key: str, message: str = "Configuration error", **kwargs):
        """
        Initialize configuration error.
        
        Args:
            config_key: Configuration key that caused the error
            message: Error message
            **kwargs: Additional arguments for base class
        """
        super().__init__(message, **kwargs)
        self.config_key = config_key
        self.details.update({"config_key": config_key})


class TimeoutError(ESXiMCPError):
    """Exception raised when operation times out."""
    
    def __init__(self, operation: str, timeout: int, message: str = "Operation timed out", **kwargs):
        """
        Initialize timeout error.
        
        Args:
            operation: Name of the operation that timed out
            timeout: Timeout value in seconds
            message: Error message
            **kwargs: Additional arguments for base class
        """
        super().__init__(message, **kwargs)
        self.operation = operation
        self.timeout = timeout
        self.details.update({
            "operation": operation,
            "timeout": timeout
        })


class ResourceNotFoundError(ESXiMCPError):
    """Exception raised when requested resource is not found."""
    
    def __init__(self, resource_type: str, resource_name: str, 
                 message: str = "Resource not found", **kwargs):
        """
        Initialize resource not found error.
        
        Args:
            resource_type: Type of resource (VM, datastore, network, etc.)
            resource_name: Name of the resource
            message: Error message
            **kwargs: Additional arguments for base class
        """
        super().__init__(message, **kwargs)
        self.resource_type = resource_type
        self.resource_name = resource_name
        self.details.update({
            "resource_type": resource_type,
            "resource_name": resource_name
        })


class InsufficientPermissionsError(ESXiMCPError):
    """Exception raised when user lacks required permissions."""
    
    def __init__(self, operation: str, required_permission: str, 
                 message: str = "Insufficient permissions", **kwargs):
        """
        Initialize insufficient permissions error.
        
        Args:
            operation: Name of the operation requiring permissions
            required_permission: Required permission for the operation
            message: Error message
            **kwargs: Additional arguments for base class
        """
        super().__init__(message, **kwargs)
        self.operation = operation
        self.required_permission = required_permission
        self.details.update({
            "operation": operation,
            "required_permission": required_permission
        })


# Exception mapping for common error scenarios
EXCEPTION_MAP = {
    "connection_failed": ESXiConnectionError,
    "authentication_failed": ESXiAuthenticationError,
    "operation_failed": ESXiOperationError,
    "validation_failed": ValidationError,
    "vm_operation_failed": VMOperationError,
    "host_operation_failed": HostOperationError,
    "datastore_operation_failed": DatastoreOperationError,
    "network_operation_failed": NetworkOperationError,
    "snapshot_operation_failed": SnapshotOperationError,
    "configuration_error": ConfigurationError,
    "timeout_error": TimeoutError,
    "resource_not_found": ResourceNotFoundError,
    "insufficient_permissions": InsufficientPermissionsError,
}


def create_exception(error_type: str, *args, **kwargs) -> ESXiMCPError:
    """
    Create exception instance based on error type.
    
    Args:
        error_type: Type of error to create
        *args: Positional arguments for exception
        **kwargs: Keyword arguments for exception
        
    Returns:
        Exception instance
        
    Raises:
        ValueError: If error_type is not recognized
    """
    if error_type not in EXCEPTION_MAP:
        raise ValueError(f"Unknown error type: {error_type}")
    
    exception_class = EXCEPTION_MAP[error_type]
    return exception_class(*args, **kwargs)