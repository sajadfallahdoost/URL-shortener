# Development Guide

Local development setup and contribution guidelines for the URL Shortener project.

## Table of Contents

1. [Local Setup](#local-setup)
2. [Code Style Guide](#code-style-guide)
3. [Testing Guidelines](#testing-guidelines)
4. [Database Migrations](#database-migrations)
5. [Contribution Workflow](#contribution-workflow)
6. [Project Structure](#project-structure)
7. [Common Tasks](#common-tasks)

---

## Local Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Git

### Installation Steps

1. **Clone Repository**

```bash
git clone <repository-url>
cd URL-shortener
```

2. **Create Virtual Environment**

```bash
# Create venv
python -m venv venv

# Activate venv
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

3. **Install Dependencies**

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

4. **Setup Database**

```bash
# Start PostgreSQL
# Run setup commands from docs/database/database.sql

psql -U postgres
\i docs/database/database.sql
```

5. **Setup Redis**

```bash
# Start Redis
redis-server

# Or with Docker
docker run -d -p 6379:6379 redis:7-alpine
```

6. **Configure Environment**

```bash
cp .env.example .env
# Edit .env with your local settings
```

7. **Run Migrations**

```bash
alembic upgrade head
```

8. **Start Application**

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload

# Or
python -m app.main
```

Application runs at: http://localhost:8000

---

## Code Style Guide

### Python Style

We follow **PEP 8** with some modifications:

**Line Length:** 100 characters

```python
# Good
def create_short_url(original_url: str) -> str:
    """Create a shortened URL from original URL."""
    pass

# Bad - missing type hints and docstring
def create_short_url(original_url):
    pass
```

### Formatting Tools

**Black** - Code formatter

```bash
# Format all files
black app/ tests/

# Check formatting
black --check app/
```

**isort** - Import sorter

```bash
# Sort imports
isort app/ tests/

# Check sorting
isort --check app/
```

### Type Hints

Use type hints for all function signatures:

```python
from typing import Optional, List

def get_url_stats(short_code: str) -> Optional[dict]:
    """Get URL statistics."""
    pass

def create_multiple_urls(urls: List[str]) -> List[dict]:
    """Create multiple short URLs."""
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def shorten_url(original_url: str, custom_code: Optional[str] = None) -> dict:
    """
    Create a shortened URL.
    
    Args:
        original_url: The URL to shorten
        custom_code: Optional custom short code
        
    Returns:
        dict: Dictionary containing short_code and short_url
        
    Raises:
        InvalidURLException: If URL is invalid
        ShortCodeExistsException: If custom code already exists
        
    Example:
        >>> result = shorten_url("https://example.com")
        >>> print(result['short_code'])
        'aB3xY'
    """
    pass
```

### Naming Conventions

- **Classes**: PascalCase (`URLService`, `ShortCodeGenerator`)
- **Functions/Methods**: snake_case (`create_short_url`, `get_by_id`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_URL_LENGTH`, `BASE62_CHARS`)
- **Private**: Prefix with underscore (`_generate_code`, `_cache_url`)

### Import Organization

```python
# 1. Standard library
import os
import sys
from typing import Optional

# 2. Third-party
from fastapi import FastAPI, HTTPException
from sqlalchemy import select

# 3. Local application
from app.core.config import settings
from app.services.url_service import URLService
```

---

## Testing Guidelines

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific file
pytest tests/test_url_shortener.py

# Run specific test
pytest tests/test_url_shortener.py::test_create_short_url_success

# Run with verbose output
pytest -v

# Run and stop on first failure
pytest -x
```

### Writing Tests

**Test Structure:**

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_feature_name(test_client: AsyncClient, sample_data):
    """Test description."""
    # Arrange
    url = "https://example.com/test"
    
    # Act
    response = await test_client.post("/api/v1/urls/shorten", json={"original_url": url})
    
    # Assert
    assert response.status_code == 201
    assert "short_code" in response.json()
```

**Test Coverage Requirements:**

- Minimum 80% coverage
- 90%+ for critical paths
- All edge cases covered
- Error handling tested

**Test Categories:**

1. **Unit Tests**: Test individual functions
2. **Integration Tests**: Test component interaction
3. **API Tests**: Test HTTP endpoints
4. **Edge Cases**: Test boundary conditions

---

## Database Migrations

### Creating Migrations

```bash
# Auto-generate migration
alembic revision --autogenerate -m "Description of changes"

# Create empty migration
alembic revision -m "Description"
```

### Migration File Structure

```python
"""Description of changes

Revision ID: 002
Revises: 001
Create Date: 2024-01-15 10:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = '002'
down_revision = '001'

def upgrade() -> None:
    """Apply changes."""
    op.add_column('urls', sa.Column('new_field', sa.String(255)))

def downgrade() -> None:
    """Revert changes."""
    op.drop_column('urls', 'new_field')
```

### Migration Commands

```bash
# Show current version
alembic current

# Show migration history
alembic history

# Upgrade to latest
alembic upgrade head

# Upgrade to specific version
alembic upgrade 002

# Downgrade one version
alembic downgrade -1

# Downgrade to specific version
alembic downgrade 001
```

---

## Contribution Workflow

### 1. Create Feature Branch

```bash
# Update main
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Write code following style guide
- Add tests for new features
- Update documentation

### 3. Run Quality Checks

```bash
# Format code
black app/ tests/
isort app/ tests/

# Run linter
pylint app/

# Run type checker
mypy app/

# Run tests
pytest --cov=app
```

### 4. Commit Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: Add custom short code support

- Allow users to specify custom short codes
- Add validation for custom codes
- Update tests and documentation
"
```

**Commit Message Format:**

```
type: Short description (50 chars max)

Longer description if needed (wrap at 72 chars)

- Bullet points for details
- Reference issues: Fixes #123
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions/changes
- `refactor`: Code refactoring
- `style`: Formatting changes
- `chore`: Maintenance tasks

### 5. Push and Create PR

```bash
# Push branch
git push origin feature/your-feature-name

# Create pull request on GitHub/GitLab
```

**PR Requirements:**
- All tests passing
- Code coverage maintained
- Documentation updated
- Code review approved

---

## Project Structure

```
URL-shortener/
├── app/                      # Application code
│   ├── api/                 # API endpoints
│   │   └── v1/
│   │       ├── endpoints/   # Endpoint handlers
│   │       └── router.py    # API router
│   ├── core/                # Core configuration
│   │   ├── config.py        # Settings
│   │   ├── database.py      # DB setup
│   │   ├── redis.py         # Redis setup
│   │   ├── exceptions.py    # Custom exceptions
│   │   └── logging.py       # Logging config
│   ├── models/              # SQLAlchemy models
│   │   └── url.py
│   ├── schemas/             # Pydantic schemas
│   │   └── url.py
│   ├── repositories/        # Data access layer
│   │   └── url_repository.py
│   ├── services/            # Business logic
│   │   ├── url_service.py
│   │   └── shortener.py
│   ├── utils/               # Utilities
│   │   └── validators.py
│   └── main.py              # Application entry
├── tests/                    # Test suite
│   ├── conftest.py          # Test fixtures
│   ├── test_url_shortener.py
│   ├── test_url_redirect.py
│   └── test_api_validation.py
├── docs/                     # Documentation
│   ├── api/
│   ├── architecture/
│   ├── deployment/
│   ├── development/
│   └── database/
├── alembic/                  # Database migrations
│   ├── versions/
│   └── env.py
├── requirements.txt          # Python dependencies
├── pyproject.toml           # Project metadata
├── Dockerfile               # Docker image
├── docker-compose.yml       # Docker services
├── .gitignore
└── README.md
```

---

## Common Tasks

### Add New Endpoint

1. Create endpoint in `app/api/v1/endpoints/`
2. Add schema in `app/schemas/`
3. Include router in `app/api/v1/router.py`
4. Write tests in `tests/`

### Add Database Column

1. Update model in `app/models/`
2. Create migration: `alembic revision --autogenerate -m "Add column"`
3. Review and edit migration
4. Apply: `alembic upgrade head`

### Add New Service

1. Create service in `app/services/`
2. Add repository methods if needed
3. Write unit tests
4. Update documentation

### Debug Tips

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or with ipdb
import ipdb; ipdb.set_trace()

# Print debug info
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Debug info: {variable}")
```

---

## IDE Setup

### VS Code

**Extensions:**
- Python
- Pylance
- autoDocstring
- GitLens

**Settings (.vscode/settings.json):**

```json
{
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "editor.formatOnSave": true
}
```

### PyCharm

- Enable Black formatter
- Enable Pylint
- Set Python interpreter to venv
- Enable pytest as test runner

---

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org)
- [Pydantic Documentation](https://docs.pydantic.dev)
- [PostgreSQL Documentation](https://www.postgresql.org/docs)
- [Redis Documentation](https://redis.io/docs)

---

## Getting Help

- Check existing documentation
- Search closed issues
- Ask in discussions
- Review code examples in tests

Happy coding! 🚀

