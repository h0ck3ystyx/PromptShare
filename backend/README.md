# PromptShare Backend

FastAPI backend for the PromptShare internal prompt-sharing application.

## Setup

### Prerequisites

- Python 3.10+
- PostgreSQL (local or Docker)
- Redis (optional, for development)

#### Installing PostgreSQL on macOS

If you don't have PostgreSQL installed, use Homebrew:

```bash
brew install postgresql@16
brew services start postgresql@16
```

Or use Docker:

```bash
docker run --name promptshare-db -e POSTGRES_PASSWORD=password -e POSTGRES_DB=promptshare -p 5432:5432 -d postgres:16
```

### Installation

1. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

3. Create `.env` file from `.env.example`:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Initialize database migrations:
```bash
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

5. Run the development server:
```bash
uvicorn src.main:app --reload --port 7999
```

The API will be available at `http://localhost:7999`
API documentation at `http://localhost:7999/api/docs`

## Project Structure

```
backend/
├── src/
│   ├── models/          # SQLAlchemy database models
│   ├── schemas/         # Pydantic models for API
│   ├── routers/         # API route handlers
│   ├── services/        # Business logic
│   ├── config.py        # Configuration management
│   ├── constants.py     # Application constants
│   ├── database.py      # Database connection
│   ├── dependencies.py  # Dependency injection
│   └── main.py           # FastAPI app entry point
├── tests/               # Test suite
├── migrations/          # Alembic database migrations
├── requirements.txt     # Production dependencies
└── requirements-dev.txt  # Development dependencies
```

## Development

### Running Tests

```bash
pytest
pytest --cov=src --cov-report=html  # With coverage report
```

### Code Formatting

```bash
ruff check .
ruff format .
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login with LDAP/AD credentials
- `GET /api/auth/me` - Get current user information
- `POST /api/auth/logout` - Logout

## Environment Variables

See `.env.example` for all required environment variables.

## Troubleshooting

### psycopg Installation Issues

If you encounter issues installing `psycopg`, try:

1. **Install PostgreSQL development libraries** (macOS):
   ```bash
   brew install postgresql
   ```

2. **Use psycopg2-binary as fallback** (if psycopg3 doesn't work):
   Edit `requirements.txt` and change:
   ```
   psycopg[binary]==3.2.0
   ```
   to:
   ```
   psycopg2-binary==2.9.9
   ```
   Then update `database.py` to remove the URL replacement logic.

3. **For Python 3.14+ compatibility issues**, you may need to:
   - Use Python 3.11 or 3.12 (recommended for best compatibility)
   - Or ensure you're using the latest versions of packages (Pydantic >=2.9.0, FastAPI >=0.115.0)

### Database Connection Issues

If you can't connect to PostgreSQL:

1. Verify PostgreSQL is running:
   ```bash
   brew services list  # Check if postgresql is running
   # or
   docker ps  # Check if container is running
   ```

2. Test connection:
   ```bash
   psql -h localhost -U postgres -d promptshare
   ```

3. Update `.env` with correct credentials

### Pydantic/Python 3.14 Compatibility

If you encounter `pydantic-core` build errors with Python 3.14:

1. **Update to latest Pydantic** (already in requirements.txt):
   - Pydantic >=2.9.0 includes Python 3.14 support

2. **Use Python 3.11 or 3.12** (recommended):
   ```bash
   # Create new venv with Python 3.12
   python3.12 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **If issues persist**, check that all packages are up to date:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt --upgrade
   ```

## License

Internal use only.

