# Contributing to VMware ESXi MCP Server

Thank you for your interest in contributing to the VMware ESXi MCP Server project! This document provides guidelines and information for contributors.

## Code of Conduct

This project adheres to a code of conduct that promotes a welcoming and inclusive environment for all contributors. Please read and follow our community guidelines.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- VMware ESXi environment for testing
- Basic understanding of MCP (Model Context Protocol)

### Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/vmware-esxi-mcp.git
   cd vmware-esxi-mcp
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

5. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Development Guidelines

### Code Style

- Follow PEP 8 Python style guidelines
- Use Black for code formatting
- Use type hints for all functions and methods
- Write docstrings for all public functions and classes

### Testing

- Write unit tests for all new functionality
- Maintain test coverage above 90%
- Include integration tests for ESXi interactions
- Test with multiple ESXi versions when possible

### Documentation

- Update README.md for new features
- Add docstrings to all public APIs
- Include examples for new MCP tools
- Update API documentation

## Contribution Process

### 1. Issue Creation

Before starting work:
- Check existing issues to avoid duplication
- Create a detailed issue describing the problem or feature
- Wait for maintainer feedback before starting implementation

### 2. Branch Creation

Create a feature branch from main:
```bash
git checkout -b feature/your-feature-name
```

### 3. Development

- Make small, focused commits
- Write clear commit messages
- Follow the established code patterns
- Add tests for new functionality

### 4. Testing

Run the full test suite:
```bash
# Unit tests
pytest tests/unit/

# Integration tests (requires ESXi environment)
pytest tests/integration/

# Code quality checks
flake8 src/
black --check src/
mypy src/
```

### 5. Pull Request

1. Push your branch to your fork
2. Create a pull request with:
   - Clear description of changes
   - Reference to related issues
   - Screenshots/examples if applicable
   - Updated documentation

## Types of Contributions

### Bug Fixes

- Include reproduction steps
- Add regression tests
- Update documentation if needed

### New Features

- Discuss the feature in an issue first
- Follow MCP specification guidelines
- Include comprehensive tests
- Update documentation and examples

### Documentation

- Fix typos and improve clarity
- Add examples and use cases
- Update API documentation
- Improve setup instructions

### Performance Improvements

- Include benchmarks showing improvement
- Ensure backward compatibility
- Add performance tests

## MCP Tool Development

When adding new MCP tools:

1. Follow the MCP specification
2. Use consistent naming conventions
3. Include proper input validation
4. Add comprehensive error handling
5. Write detailed documentation
6. Include usage examples

### Tool Structure

```python
@mcp_tool
async def your_tool_name(
    param1: str,
    param2: Optional[int] = None
) -> Dict[str, Any]:
    """
    Brief description of what the tool does.
    
    Args:
        param1: Description of parameter
        param2: Optional parameter description
        
    Returns:
        Dictionary containing operation results
        
    Raises:
        ESXiConnectionError: When connection fails
        ValidationError: When parameters are invalid
    """
    # Implementation here
    pass
```

## Security Guidelines

- Never commit credentials or sensitive data
- Use environment variables for configuration
- Validate all inputs thoroughly
- Follow secure coding practices
- Report security issues privately

## Release Process

Releases are managed by maintainers:

1. Version bumping follows semantic versioning
2. Changelog is updated for each release
3. Tags are created for stable releases
4. Docker images are built automatically

## Getting Help

- Create an issue for bugs or feature requests
- Join discussions in existing issues
- Check the documentation first
- Be patient and respectful

## Recognition

Contributors are recognized in:
- README.md contributors section
- Release notes
- Project documentation

Thank you for contributing to VMware ESXi MCP Server!