# PromptShare Implementation Plan

## Project Overview
An internal prompt-sharing web application that allows employees to discover, submit, and collaborate on prompts for AI tools (GitHub Copilot, O365 Copilot, Cursor, Claude).

## Technology Stack

### Backend
- **Framework**: FastAPI (high performance, automatic API docs, async support)
- **Database**: PostgreSQL (with SQLAlchemy ORM)
- **Authentication**: LDAP/Active Directory integration (python-ldap or ldap3)
- **Search**: PostgreSQL full-text search (or Elasticsearch for advanced search)
- **Task Queue**: Celery with Redis (for async tasks like notifications)
- **Caching**: Redis (for session management and caching)

### Frontend
- **Framework**: Vue.js 3 (Composition API)
- **UI Library**: Tailwind CSS
- **State Management**: Pinia (Vue 3 recommended state management)
- **HTTP Client**: Axios or Fetch API
- **Build Tool**: Vite

### DevOps & Tools
- **Linting/Formatting**: Ruff (as per .cursorrules)
- **Testing**: pytest with pytest-asyncio (backend), Vitest (frontend)
- **API Documentation**: FastAPI automatic OpenAPI/Swagger
- **Containerization**: Docker & Docker Compose
- **Environment**: python-dotenv for env management
- **Python Environment**: `python -m venv venv` (standard venv)
- **AWS Deployment**: 
  - RDS PostgreSQL for database
  - ElastiCache for Redis
  - ECS/EKS or EC2 for application hosting
  - S3 for static assets (if needed)
  - CloudFront for CDN (optional)

## Project Structure

```
promptshare/
├── backend/                    # Python FastAPI backend
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── config.py               # Configuration management
│   │   ├── constants.py            # Constants (roles, statuses, etc.)
│   │   │
│   │   ├── models/                 # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── prompt.py
│   │   │   ├── comment.py
│   │   │   ├── rating.py
│   │   │   ├── tag.py
│   │   │   └── notification.py
│   │   │
│   │   ├── schemas/                # Pydantic models for API
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── prompt.py
│   │   │   ├── comment.py
│   │   │   └── common.py
│   │   │
│   │   ├── routers/                # API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             # Authentication endpoints
│   │   │   ├── prompts.py          # Prompt CRUD operations
│   │   │   ├── users.py            # User management
│   │   │   ├── comments.py         # Comments endpoints
│   │   │   ├── search.py           # Search endpoints
│   │   │   └── analytics.py        # Analytics endpoints
│   │   │
│   │   ├── services/               # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py     # LDAP/AD authentication
│   │   │   ├── prompt_service.py   # Prompt business logic
│   │   │   ├── search_service.py   # Search logic
│   │   │   ├── notification_service.py  # Notification logic
│   │   │   └── analytics_service.py     # Analytics logic
│   │   │
│   │   ├── dependencies.py         # Dependency injection
│   │   ├── database.py             # Database connection & session
│   │   └── middleware.py           # Custom middleware (auth, logging)
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py             # Pytest fixtures
│   │   ├── test_auth.py
│   │   ├── test_prompts.py
│   │   ├── test_comments.py
│   │   ├── test_search.py
│   │   └── test_services/
│   │       ├── __init__.py
│   │       ├── test_prompt_service.py
│   │       └── test_auth_service.py
│   │
│   ├── migrations/                 # Alembic migrations
│   │   └── versions/
│   │
│   ├── .env.example                # Example environment variables
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── pyproject.toml              # Ruff config, project metadata
│   ├── Dockerfile
│   └── README.md
│
├── frontend/                   # Vue.js frontend
│   ├── src/
│   │   ├── main.js                 # Vue app entry point
│   │   ├── App.vue
│   │   ├── router/                 # Vue Router
│   │   │   └── index.js
│   │   ├── stores/                 # Pinia stores
│   │   │   ├── auth.js
│   │   │   ├── prompts.js
│   │   │   └── notifications.js
│   │   ├── components/             # Vue components
│   │   │   ├── common/
│   │   │   ├── prompts/
│   │   │   ├── comments/
│   │   │   └── admin/
│   │   ├── views/                  # Page components
│   │   │   ├── Home.vue
│   │   │   ├── Login.vue
│   │   │   ├── PromptDetail.vue
│   │   │   └── AdminDashboard.vue
│   │   ├── services/               # API service layer
│   │   │   └── api.js
│   │   └── utils/                  # Utility functions
│   │       └── helpers.js
│   ├── public/
│   ├── tests/
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── README.md
│
├── .cursorrules
├── docker-compose.yml          # Local development setup
├── .env.example                # Root-level env example
└── README.md                   # Project root README
```

## Database Schema Design

### Core Tables

1. **users**
   - id (UUID, primary key)
   - email (string, unique)
   - username (string, unique)
   - full_name (string)
   - role (enum: admin, moderator, member)
   - created_at (timestamp)
   - last_login (timestamp)
   - is_active (boolean)

2. **prompts**
   - id (UUID, primary key)
   - title (string)
   - description (text)
   - content (text) - the actual prompt
   - platform_tags (array/enum: github_copilot, o365_copilot, cursor, claude)
   - use_cases (text array)
   - usage_tips (text)
   - author_id (UUID, foreign key -> users)
   - created_at (timestamp)
   - updated_at (timestamp)
   - view_count (integer)
   - is_featured (boolean)
   - status (enum: draft, published, archived)

3. **categories**
   - id (UUID, primary key)
   - name (string, unique)
   - description (text)
   - slug (string, unique)

4. **prompt_categories** (many-to-many)
   - prompt_id (UUID)
   - category_id (UUID)

5. **comments**
   - id (UUID, primary key)
   - prompt_id (UUID, foreign key)
   - user_id (UUID, foreign key)
   - content (text)
   - created_at (timestamp)
   - updated_at (timestamp)
   - parent_comment_id (UUID, nullable) - for nested comments

6. **ratings**
   - id (UUID, primary key)
   - prompt_id (UUID, foreign key)
   - user_id (UUID, foreign key)
   - rating (integer, 1-5)
   - created_at (timestamp)
   - unique constraint on (prompt_id, user_id)

7. **upvotes**
   - id (UUID, primary key)
   - prompt_id (UUID, foreign key)
   - user_id (UUID, foreign key)
   - created_at (timestamp)
   - unique constraint on (prompt_id, user_id)

8. **user_follows** (for following topics/categories)
   - id (UUID, primary key)
   - user_id (UUID, foreign key)
   - category_id (UUID, foreign key, nullable)
   - created_at (timestamp)

9. **notifications**
   - id (UUID, primary key)
   - user_id (UUID, foreign key)
   - type (enum: new_prompt, comment, update)
   - prompt_id (UUID, foreign key, nullable)
   - message (text)
   - is_read (boolean)
   - created_at (timestamp)

10. **analytics_events**
    - id (UUID, primary key)
    - event_type (enum: view, copy, search)
    - prompt_id (UUID, foreign key, nullable)
    - user_id (UUID, foreign key, nullable)
    - metadata (JSON)
    - created_at (timestamp)

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
**Goal**: Set up project structure, database, and basic authentication

- [x] Initialize Python virtual environment: `python -m venv venv`
- [x] Initialize FastAPI project structure in `backend/`
- [x] Set up PostgreSQL database with SQLAlchemy
- [x] Create database models (User, Prompt, Category)
- [x] Implement LDAP/AD authentication service
- [x] Create authentication endpoints (login, logout, current user)
- [x] Set up dependency injection for database sessions
- [x] Configure environment variables
- [x] Set up Alembic for migrations
- [x] Basic unit tests for auth service

### Phase 2: Core Prompt Features (Week 2-3)
**Goal**: Implement prompt CRUD operations

- [x] Create Pydantic schemas for prompts
- [x] Implement prompt service (create, read, update, delete)
- [x] Create prompt router endpoints
- [x] Implement category management
- [x] Add platform tagging system
- [x] Implement prompt status workflow (draft -> published)
- [x] Add one-click copy functionality (API endpoint)
- [x] Unit tests for prompt service
- [x] Integration tests for prompt endpoints

### Phase 3: Search and Discovery (Week 3-4)
**Goal**: Enable users to find prompts easily

- [x] Implement full-text search (PostgreSQL or Elasticsearch)
- [x] Create search service with filters (platform, category, keyword)
- [x] Add search endpoint with pagination
- [x] Implement prompt browsing by category
- [x] Add sorting options (newest, most viewed, highest rated)
- [x] Create featured prompts functionality
- [x] Tests for search functionality

### Phase 4: Collaboration Features (Week 4-5)
**Goal**: Enable user interaction and feedback

- [x] Implement comment system (nested comments support)
- [x] Create rating system (1-5 stars)
- [x] Implement upvote/downvote functionality
- [x] Add prompt editing (author only, with version history)
- [x] Create comment and rating endpoints
- [x] Add moderation capabilities for admins
- [x] Tests for collaboration features

### Phase 5: User Management and Permissions (Week 5)
**Goal**: Role-based access control

- [x] Implement role-based permissions (admin, moderator, member)
- [x] Create user management endpoints (admin only)
- [x] Add user profile endpoints
- [x] Implement permission decorators/middleware
- [x] Add user activity tracking
- [x] Tests for permissions

### Phase 6: Notifications and Following (Week 6)
**Goal**: Keep users engaged

- [ ] Implement follow system (categories/topics)
- [ ] Create notification service
- [ ] Add Celery tasks for async notifications
- [ ] Create notification endpoints (list, mark as read)
- [ ] Implement email notifications (optional)
- [ ] Tests for notification system

### Phase 7: Analytics and Reporting (Week 7)
**Goal**: Track usage and engagement

- [ ] Create analytics event tracking
- [ ] Implement analytics service
- [ ] Add analytics endpoints (admin only)
- [ ] Create dashboard data aggregation
- [ ] Add usage statistics (views, copies, searches)
- [ ] Tests for analytics

### Phase 8: Onboarding and Documentation (Week 8)
**Goal**: Help new users get started

- [ ] Create onboarding materials endpoint
- [ ] Implement featured collections
- [ ] Add usage tips and best practices display
- [ ] Create API documentation (FastAPI auto-generates)
- [ ] Write user documentation
- [ ] Add help/FAQ section

### Phase 9: Frontend Integration (Week 9-10)
**Goal**: Build user interface with Vue.js and Tailwind CSS

- [ ] Initialize Vue.js 3 project with Vite in `frontend/`
- [ ] Set up Tailwind CSS configuration
- [ ] Configure Vue Router for navigation
- [ ] Set up Pinia stores for state management
- [ ] Create API service layer with Axios
- [ ] Implement authentication UI (login page)
- [ ] Create prompt browsing/search interface with Tailwind styling
- [ ] Build prompt submission form with validation
- [ ] Add comment/rating UI components
- [ ] Implement one-click copy functionality with visual feedback
- [ ] Create admin dashboard with Tailwind components
- [ ] Add responsive design (mobile-first approach)
- [ ] Set up CORS configuration for API communication

### Phase 10: Testing and Polish (Week 11-12)
**Goal**: Ensure quality and performance

- [ ] Achieve >85% test coverage
- [ ] Performance testing and optimization
- [ ] Security audit (SQL injection, XSS, CSRF)
- [ ] Load testing
- [ ] UI/UX improvements
- [ ] Documentation completion
- [ ] Deployment preparation

## Key API Endpoints

### Authentication
- `POST /api/auth/login` - LDAP/AD login
- `POST /api/auth/logout` - Logout
- `GET /api/auth/me` - Get current user

### Prompts
- `GET /api/prompts` - List prompts (with filters, pagination)
- `GET /api/prompts/{id}` - Get prompt details
- `POST /api/prompts` - Create prompt (authenticated)
- `PUT /api/prompts/{id}` - Update prompt (author or admin)
- `DELETE /api/prompts/{id}` - Delete prompt (author or admin)
- `POST /api/prompts/{id}/copy` - Track copy event

### Search
- `GET /api/search` - Search prompts (query params: q, platform, category)

### Comments
- `GET /api/prompts/{id}/comments` - Get comments for prompt
- `POST /api/prompts/{id}/comments` - Add comment
- `PUT /api/comments/{id}` - Update comment
- `DELETE /api/comments/{id}` - Delete comment

### Ratings & Upvotes
- `POST /api/prompts/{id}/rate` - Rate prompt
- `POST /api/prompts/{id}/upvote` - Upvote prompt
- `DELETE /api/prompts/{id}/upvote` - Remove upvote

### Users
- `GET /api/users/{id}` - Get user profile
- `GET /api/users` - List users (admin only)
- `PUT /api/users/{id}/role` - Update user role (admin only)

### Analytics
- `GET /api/analytics/prompts/{id}` - Get prompt analytics (admin)
- `GET /api/analytics/overview` - Get overall analytics (admin)

### Notifications
- `GET /api/notifications` - Get user notifications
- `PUT /api/notifications/{id}/read` - Mark as read

## Environment Variables

### Backend (.env)
```env
# Database
DATABASE_URL=postgresql://user:password@localhost/promptshare
# For AWS RDS: postgresql://user:password@your-rds-endpoint:5432/promptshare

# LDAP/AD
LDAP_SERVER=ldap://ad.company.com
LDAP_BASE_DN=dc=company,dc=com
LDAP_USER_DN=cn=admin,dc=company,dc=com
LDAP_PASSWORD=secret

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis
REDIS_URL=redis://localhost:6379/0
# For AWS ElastiCache: redis://your-elasticache-endpoint:6379/0

# Application
APP_NAME=PromptShare
APP_ENV=development
DEBUG=True
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# AWS (for production)
AWS_REGION=us-east-1
AWS_SECRETS_MANAGER_ENABLED=False
```

### Frontend (.env)
```env
VITE_API_BASE_URL=http://localhost:7999/api
VITE_APP_NAME=PromptShare
```

### Local Development Setup

1. **Backend Setup**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
cp .env.example .env
# Edit .env with your local settings
alembic upgrade head
uvicorn src.main:app --reload --port 7999
```

2. **Frontend Setup**:
```bash
cd frontend
npm install
cp .env.example .env
# Edit .env with API URL
npm run dev
```

## Testing Strategy

1. **Unit Tests**: Test individual services and functions
   - Auth service (LDAP integration mocking)
   - Prompt service (CRUD operations)
   - Search service (query building)
   - Notification service

2. **Integration Tests**: Test API endpoints
   - Authentication flow
   - Prompt CRUD operations
   - Search functionality
   - Permission checks

3. **Test Coverage**: Maintain >85% coverage as per .cursorrules

## Security Considerations

1. **Authentication**: Secure LDAP/AD integration
2. **Authorization**: Role-based access control
3. **Input Validation**: Pydantic models for all inputs
4. **SQL Injection**: Use SQLAlchemy ORM (parameterized queries)
5. **XSS Prevention**: Sanitize user inputs
6. **CSRF Protection**: Use CSRF tokens for state-changing operations
7. **Rate Limiting**: Implement rate limiting on API endpoints
8. **Secrets Management**: Use environment variables, no hardcoded secrets

## AWS Deployment Considerations

### Infrastructure Components

1. **Database**: 
   - Amazon RDS PostgreSQL (managed database service)
   - Automated backups enabled
   - Multi-AZ deployment for high availability
   - Parameter groups for optimization

2. **Application Hosting**:
   - **Option A**: AWS ECS (Elastic Container Service) with Fargate
     - Containerized backend and frontend
     - Auto-scaling based on load
   - **Option B**: AWS EC2 instances
     - More control, requires more management
     - Use Application Load Balancer for distribution
   - **Option C**: AWS EKS (Kubernetes)
     - For larger scale deployments

3. **Caching & Session Management**:
   - Amazon ElastiCache (Redis) for session storage and caching
   - Reduces database load

4. **Static Assets**:
   - S3 bucket for frontend build artifacts
   - CloudFront CDN for global distribution (optional)

5. **Networking**:
   - VPC with public/private subnets
   - Security groups for access control
   - Application Load Balancer for traffic distribution

6. **Secrets Management**:
   - AWS Secrets Manager for database credentials, LDAP config
   - IAM roles for service authentication

7. **Monitoring & Logging**:
   - CloudWatch for application logs and metrics
   - CloudWatch Alarms for error tracking
   - X-Ray for distributed tracing (optional)

8. **CI/CD**:
   - AWS CodePipeline or GitHub Actions
   - Automated testing before deployment
   - Blue/green deployments for zero downtime

### Deployment Steps

1. **Database Setup**:
   - Create RDS PostgreSQL instance
   - Configure security groups
   - Run Alembic migrations

2. **Backend Deployment**:
   - Build Docker image for FastAPI app
   - Push to ECR (Elastic Container Registry)
   - Deploy to ECS/EC2 with environment variables from Secrets Manager

3. **Frontend Deployment**:
   - Build Vue.js app with Vite (`npm run build`)
   - Upload to S3 bucket
   - Configure CloudFront distribution (optional)

4. **Configuration**:
   - Set up environment variables in AWS Systems Manager Parameter Store or Secrets Manager
   - Configure CORS for API endpoints
   - Set up SSL certificates (ACM) for HTTPS

5. **Monitoring**:
   - Configure CloudWatch dashboards
   - Set up alerts for errors and performance issues
   - Enable database performance insights

## Development Environment Setup

### Prerequisites
- Python 3.10+ 
- Node.js 18+ and npm
- PostgreSQL (local or Docker)
- Redis (local or Docker, optional for development)

### Initial Setup Commands

```bash
# Clone repository (if applicable)
git clone <repository-url>
cd promptshare

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
cp .env.example .env
# Edit .env with your configuration

# Initialize database
alembic init migrations
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head

# Frontend setup
cd ../frontend
npm install
cp .env.example .env
# Edit .env with API URL (http://localhost:7999/api)

# Run development servers
# Terminal 1: Backend
cd backend
source venv/bin/activate
uvicorn src.main:app --reload --port 7999

# Terminal 2: Frontend
cd frontend
npm run dev
```

## Next Steps

1. Review and approve this plan
2. Set up development environment using commands above
3. Initialize Git repository (if not already done)
4. Begin Phase 1 implementation

