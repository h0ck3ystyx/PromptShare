# PromptShare

An internal prompt-sharing web application that allows employees to discover, submit, and collaborate on prompts for AI tools (GitHub Copilot, O365 Copilot, Cursor, Claude).

## 🚀 Features

- **Prompt Discovery**: Browse and search prompts by category, platform, or keyword
- **Collaboration**: Comment, rate, and upvote prompts
- **Authentication**: Secure LDAP/Active Directory integration
- **Role-Based Access**: Admin, moderator, and member roles
- **Analytics**: Track prompt usage and engagement
- **One-Click Copy**: Easy prompt copying for use in AI tools

## 📋 Tech Stack

### Backend
- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy
- **Authentication**: LDAP/Active Directory
- **Migrations**: Alembic
- **Testing**: pytest

### Frontend (Coming Soon)
- **Framework**: Vue.js 3
- **Styling**: Tailwind CSS
- **State Management**: Pinia
- **Build Tool**: Vite

## 🏗️ Project Structure

```
promptshare/
├── backend/          # FastAPI backend application
├── frontend/         # Vue.js frontend (coming soon)
├── requirements.md   # Project requirements
└── IMPLEMENTATION_PLAN.md  # Detailed implementation plan
```

## 🚦 Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL
- Node.js 18+ (for frontend, coming soon)

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

4. Create `.env` file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run database migrations:
```bash
alembic upgrade head
```

6. Start the development server:
```bash
uvicorn src.main:app --reload --port 7999
```

The API will be available at `http://localhost:7999`
API documentation at `http://localhost:7999/api/docs`

## 📚 Documentation

- [Implementation Plan](./IMPLEMENTATION_PLAN.md) - Detailed development plan
- [Backend README](./backend/README.md) - Backend-specific documentation
- [Requirements](./requirements.md) - Project requirements and user stories

## 🧪 Testing

Tests use a PostgreSQL database to match production and support PostgreSQL-specific features (ARRAY, UUID, enums).

### Setup Test Database

1. Start the test PostgreSQL database:
```bash
docker-compose -f docker-compose.test.yml up -d
```

2. Wait for the database to be ready (healthcheck will verify).

### Run Tests

```bash
cd backend
pytest
pytest --cov=src --cov-report=html  # With coverage
```

### Custom Test Database

You can override the test database URL:
```bash
TEST_DATABASE_URL="postgresql+psycopg://user:pass@host:port/db" pytest
```

### Cleanup

Stop the test database when done:
```bash
docker-compose -f docker-compose.test.yml down
```

## 📝 Development Status

- [x] Phase 1: Foundation (Database, Authentication)
- [x] Phase 2: Core Prompt Features
- [x] Phase 3: Search and Discovery
- [x] Phase 4: Collaboration Features (Comments, Ratings, Upvotes)
- [x] Phase 5: User Management and Permissions
- [ ] Phase 6: Notifications and Following
- [ ] Phase 7: Analytics and Reporting
- [ ] Phase 8: Onboarding and Documentation
- [ ] Phase 9: Frontend Integration
- [ ] Phase 10: Testing and Polish

## 🔒 Security

- LDAP/Active Directory authentication
- JWT token-based authorization
- Role-based access control (Admin, Moderator, Member)
- Self-protection mechanisms (admins cannot change own role/deactivate self)
- Input validation with Pydantic
- SQL injection protection via SQLAlchemy ORM
- Authorization checks on all sensitive endpoints

## 📄 License

Internal use only.

## 🤝 Contributing

This is an internal project. Please follow the coding standards defined in `.cursorrules`.

