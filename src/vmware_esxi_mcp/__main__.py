#!/usr/bin/env python3
"""
VMware ESXi MCP Server - Main Entry Point

Command-line interface for the VMware ESXi MCP Server.

Author: uldyssian-sh
License: MIT
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent))

from vmware_esxi_mcp.server import ESXiMCPServer

def setup_logging(level: str = "INFO"):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('esxi-mcp.log')
        ]
    )

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="VMware ESXi MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m vmware_esxi_mcp
  python -m vmware_esxi_mcp --host esxi-host.example.com --username root
  python -m vmware_esxi_mcp --config config.yaml --log-level DEBUG
        """
    )
    
    parser.add_argument(
        "--host",
        default=os.getenv("ESXI_HOST", "esxi-host.example.com"),
        help="ESXi host address (default: %(default)s)"
    )
    
    parser.add_argument(
        "--username", 
        default=os.getenv("ESXI_USERNAME", "root"),
        help="ESXi username (default: %(default)s)"
    )
    
    parser.add_argument(
        "--password",
        default=os.getenv("ESXI_PASSWORD", ""),
        help="ESXi password (use ESXI_PASSWORD env var)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=443,
        help="ESXi API port (default: %(default)s)"
    )
    
    parser.add_argument(
        "--config",
        type=Path,
        help="Configuration file path"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: %(default)s)"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="VMware ESXi MCP Server 1.5.0"
    )
    
    return parser.parse_args()

def load_config(config_path: Path) -> dict:
    """Load configuration from file."""
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        import yaml
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except ImportError:
        # Fallback to basic parsing if PyYAML not available
        config = {}
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and ':' in line:
                    key, value = line.split(':', 1)
                    config[key.strip()] = value.strip()
        return config

async def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration if provided
        config = {}
        if args.config:
            config = load_config(args.config)
            logger.info(f"Loaded configuration from: {args.config}")
        
        # Set environment variables from args/config
        os.environ["ESXI_HOST"] = config.get("esxi_host", args.host)
        os.environ["ESXI_USERNAME"] = config.get("esxi_username", args.username)
        if args.password:
            os.environ["ESXI_PASSWORD"] = args.password
        elif config.get("esxi_password"):
            os.environ["ESXI_PASSWORD"] = config["esxi_password"]
        
        # Validate required configuration
        if not os.environ.get("ESXI_PASSWORD"):
            logger.warning("ESXi password not provided - some operations may fail")
        
        logger.info("Starting VMware ESXi MCP Server...")
        logger.info(f"ESXi Host: {os.environ.get('ESXI_HOST')}")
        logger.info(f"Username: {os.environ.get('ESXI_USERNAME')}")
        
        # Create and run server
        server = ESXiMCPServer()
        await server.run()
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())