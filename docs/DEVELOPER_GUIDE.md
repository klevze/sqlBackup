# sqlBackup Developer Guide

## Getting Started

This guide helps developers get started with the sqlBackup codebase, understand the architecture, and contribute to the project.

## Development Setup

### Prerequisites

- Python 3.6 or higher
- MySQL/MariaDB server for testing
- Git for version control

### Installation for Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/klevze/sqlBackup.git
   cd sqlBackup
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install in development mode:**
   ```bash
   pip install -e .
   ```

4. **Install development dependencies:**
   ```bash
   pip install pytest pytest-cov flake8 black mypy
   ```

## Project Architecture

### Core Components

```
sqlBackup/
├── src/                    # Main source code
│   ├── backup.py          # Backup orchestration
│   ├── config.py          # Configuration management
│   ├── config_validator.py # Configuration validation
│   ├── logger.py          # Logging system
│   ├── notifications.py   # Notification system
│   └── remote_upload.py   # Remote upload system
├── tests/                 # Test suite
├── docs/                  # Documentation
└── examples/              # Usage examples
```

### Data Flow

```
Config Load → Validation → Backup Creation → Compression → Upload → Notification
     ↓              ↓            ↓             ↓          ↓         ↓
Logger Setup → Error Check → MySQL Dump → Archive → SFTP/FTP → Email/SMS/etc
```

## Development Workflow

### Code Style

We follow PEP 8 with some modifications:

- Line length: 88 characters (Black default)
- Use type hints where possible
- Docstrings in Google style

### Formatting and Linting

```bash
# Format code with Black
black src/ tests/

# Check with flake8
flake8 src/ tests/

# Type checking with mypy
mypy src/
```

### Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_backup.py

# Run specific test
pytest tests/test_backup.py::TestMySQLBackup::test_create_backup
```

### Adding New Features

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Write tests first (TDD approach):**
   ```python
   # tests/test_your_feature.py
   import pytest
   from sql_backup.your_module import YourClass

   class TestYourFeature:
       def test_your_functionality(self):
           # Arrange
           instance = YourClass()
           
           # Act
           result = instance.your_method()
           
           # Assert
           assert result == expected_value
   ```

3. **Implement the feature:**
   ```python
   # src/your_module.py
   from sql_backup.logger import get_logger

   logger = get_logger(__name__)

   class YourClass:
       def your_method(self):
           logger.info("Executing your method")
           # Implementation here
           return result
   ```

4. **Update documentation:**
   - Add docstrings to new functions/classes
   - Update API.md if adding public APIs
   - Add examples if relevant

5. **Test your changes:**
   ```bash
   pytest
   black src/ tests/
   flake8 src/ tests/
   ```

## Code Patterns

### Error Handling Pattern

```python
from sql_backup.logger import get_logger

logger = get_logger(__name__)

def your_function():
    try:
        # Your code here
        result = risky_operation()
        logger.info("Operation completed successfully")
        return result
    except SpecificException as e:
        logger.error(f"Specific error occurred: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in your_function: {str(e)}")
        raise
```

### Configuration Access Pattern

```python
from sql_backup.config import Config

class YourClass:
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(__name__)
        
    def your_method(self):
        # Get configuration values with defaults
        setting = self.config.get('section', 'key', 'default_value')
        enabled = self.config.getboolean('section', 'enabled', False)
        port = self.config.getint('section', 'port', 8080)
```

### Logging Pattern

```python
from sql_backup.logger import get_logger

logger = get_logger(__name__)

class YourClass:
    def your_method(self):
        logger.debug("Starting your_method")
        
        try:
            # Your code
            logger.info("Operation completed successfully")
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}")
            raise
        finally:
            logger.debug("Finished your_method")
```

## Testing Guidelines

### Test Structure

```python
import pytest
from unittest.mock import Mock, patch, MagicMock
from sql_backup.your_module import YourClass

class TestYourClass:
    @pytest.fixture
    def mock_config(self):
        """Fixture providing a mock configuration."""
        config = Mock()
        config.get.return_value = "test_value"
        config.getboolean.return_value = True
        return config
    
    @pytest.fixture
    def your_instance(self, mock_config):
        """Fixture providing an instance of your class."""
        return YourClass(mock_config)
    
    def test_successful_operation(self, your_instance):
        """Test successful operation."""
        # Arrange
        expected_result = "success"
        
        # Act
        result = your_instance.your_method()
        
        # Assert
        assert result == expected_result
    
    def test_error_handling(self, your_instance):
        """Test error handling."""
        # Arrange
        with patch('src.your_module.risky_operation') as mock_op:
            mock_op.side_effect = Exception("Test error")
            
            # Act & Assert
            with pytest.raises(Exception):
                your_instance.your_method()
```

### Mocking External Dependencies

```python
# Mock database connections
@patch('src.backup.subprocess.run')
def test_mysqldump(self, mock_subprocess):
    mock_subprocess.return_value.returncode = 0
    # Test your code

# Mock file operations
@patch('src.backup.os.path.exists')
@patch('builtins.open', new_callable=mock_open)
def test_file_operations(self, mock_file, mock_exists):
    mock_exists.return_value = True
    # Test your code

# Mock network requests
@patch('src.notifications.requests.post')
def test_notification_sending(self, mock_post):
    mock_post.return_value.status_code = 200
    # Test your code
```

## Debugging

### Debug Configuration

Create a debug configuration file (`debug_config.ini`):

```ini
[backup]
backup_dir = /tmp/debug_backups
keep_days = 1
archive_type = none

[mysql]
user = test_user
password = test_password
host = localhost
port = 3306
database = test_db

[logging]
level = DEBUG
file = logs/debug.log

[notification]
channels = 
```

### Debug Script

```python
# debug.py
import sys
from sql_backup.logger import setup_logging, get_logger
from sql_backup.config import Config
from sql_backup.backup import MySQLBackup

def main():
    # Setup debug logging
    setup_logging(log_level='DEBUG', console_output=True)
    logger = get_logger(__name__)
    
    try:
        # Load debug configuration
        config = Config('debug_config.ini')
        config.load_config()
        
        # Create backup with debug config
        backup = MySQLBackup('debug_config.ini')
        
        # Add breakpoints as needed
        import pdb; pdb.set_trace()
        
        success = backup.create_backup()
        logger.info(f"Debug backup result: {success}")
        
    except Exception as e:
        logger.error(f"Debug session failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
```

## Contributing

### Submitting Changes

1. **Ensure all tests pass:**
   ```bash
   pytest
   ```

2. **Check code quality:**
   ```bash
   black src/ tests/
   flake8 src/ tests/
   mypy src/
   ```

3. **Update documentation if needed**

4. **Create a pull request with:**
   - Clear description of changes
   - Test results
   - Documentation updates

### Issue Reporting

When reporting issues, include:

- Python version
- Operating system
- Configuration file (remove sensitive data)
- Full error traceback
- Steps to reproduce

### Feature Requests

For new features, provide:

- Use case description
- Proposed API design
- Implementation considerations
- Backward compatibility notes

## Performance Considerations

### Database Operations

- Use connection pooling for multiple backups
- Consider streaming for large databases
- Implement timeout handling

### File Operations

- Use temporary files for intermediate steps
- Clean up resources in finally blocks
- Consider disk space requirements

### Network Operations

- Implement retry logic with exponential backoff
- Use connection timeouts
- Handle network interruptions gracefully

## Security Guidelines

### Sensitive Data

- Never log passwords or tokens
- Use environment variables for secrets
- Validate all external inputs

### File Permissions

- Set appropriate permissions on backup files
- Secure temporary files
- Clean up sensitive data

### Network Security

- Use TLS/SSL for remote connections
- Validate server certificates
- Implement proper authentication

## Deployment

### Production Checklist

- [ ] Configuration validated
- [ ] Log rotation configured
- [ ] Monitoring set up
- [ ] Backup retention policy
- [ ] Security review completed
- [ ] Performance tested

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY config.ini.default ./config.ini

CMD ["python", "-m", "src.backup"]
```

### Systemd Service

```ini
[Unit]
Description=SQL Backup Service
After=network.target

[Service]
Type=oneshot
User=backup
WorkingDirectory=/opt/sqlbackup
ExecStart=/opt/sqlbackup/venv/bin/python -m src.backup
Environment=PYTHONPATH=/opt/sqlbackup

[Install]
WantedBy=multi-user.target
```

This developer guide provides comprehensive information for developers working on the sqlBackup project, covering setup, architecture, workflows, and best practices.
