#!/usr/bin/env python3
"""
Setup configuration for VMware ESXi MCP Server.

This setup script provides professional packaging and installation
capabilities for the VMware ESXi MCP Server project.
"""

from setuptools import setup, find_packages
import os
import re

# Read version from __init__.py
def get_version():
    with open(os.path.join("src", "vmware_esxi_mcp", "__init__.py"), "r") as f:
        content = f.read()
        match = re.search(r'__version__ = ["\']([^"\']+)["\']', content)
        if match:
            return match.group(1)
        raise RuntimeError("Unable to find version string")

# Read long description from README
def get_long_description():
    with open("README.md", "r", encoding="utf-8") as f:
        return f.read()

# Read requirements
def get_requirements():
    with open("requirements.txt", "r") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="vmware-esxi-mcp",
    version=get_version(),
    author="uldyssian-sh",
    author_email="25517637+uldyssian-sh@users.noreply.github.com",
    description="Professional Model Context Protocol (MCP) server for VMware ESXi hypervisor management",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/uldyssian-sh/vmware-esxi-mcp",
    project_urls={
        "Bug Reports": "https://github.com/uldyssian-sh/vmware-esxi-mcp/issues",
        "Source": "https://github.com/uldyssian-sh/vmware-esxi-mcp",
        "Documentation": "https://github.com/uldyssian-sh/vmware-esxi-mcp/blob/main/README.md",
        "Changelog": "https://github.com/uldyssian-sh/vmware-esxi-mcp/blob/main/CHANGELOG.md",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Developers",
        "Topic :: System :: Systems Administration",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Environment :: Web Environment",
    ],
    python_requires=">=3.8",
    install_requires=get_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "bandit>=1.7.0",
            "safety>=2.0.0",
        ],
        "docs": [
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.2.0",
            "myst-parser>=1.0.0",
        ],
        "monitoring": [
            "prometheus-client>=0.16.0",
            "grafana-api>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "vmware-esxi-mcp=vmware_esxi_mcp.cli:main",
            "esxi-mcp-server=vmware_esxi_mcp.server:main",
        ],
    },
    include_package_data=True,
    package_data={
        "vmware_esxi_mcp": [
            "config/*.yaml",
            "templates/*.json",
            "schemas/*.json",
        ],
    },
    zip_safe=False,
    keywords=[
        "vmware", "esxi", "mcp", "model-context-protocol", 
        "virtualization", "hypervisor", "infrastructure", 
        "automation", "enterprise", "api"
    ],
)