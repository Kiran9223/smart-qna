# Smart Q&A

A full-stack course discussion platform (StackOverflow-lite) where students post questions, receive answers, vote, and get notifications.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS, TanStack Query, React Router v6 |
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2 |
| Database | PostgreSQL 15 |
| Auth (local) | JWT — python-jose + passlib/bcrypt |
| Auth (AWS) | AWS Cognito JWKS validation |
| Containers | Docker, Docker Compose |

## Quick Start (Local)

### Prerequisites
- Docker & Docker Compose installed

### 1. Clone & Configure

```bash
cp backend/.env.example backend/.env
```

### 2. Start all services

```bash
docker compose up --build -d
```

### 3. Run database migrations

```bash
docker compose exec backend alembic upgrade head
```

### 4. Seed default tags

```bash
docker compose exec backend python -m app.utils.seed
```

### 5. Open the app

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Health check | http://localhost:8000/api/v1/health |

## Makefile Commands

```bash
make up           # Build & start all services
make down         # Stop all services
make logs         # Tail backend logs
make migrate      # Run Alembic migrations
make seed         # Seed default tags
make test         # Run pytest suite
```

## User Roles

| Role | Permissions |
|---|---|
| STUDENT | Post questions, answers, comments; vote |
| TA | + pin/close posts |
| ADMIN | + delete any post/answer/comment |

## API Overview

All endpoints are prefixed with `/api/v1`. See `/docs` for full Swagger UI.

### Auth
- `POST /auth/register` — Create account
- `POST /auth/login` — Get JWT tokens
- `POST /auth/refresh` — Refresh access token
- `GET /auth/me` — Get current user

### Posts
- `GET /posts` — List posts (sort, search, tag, pagination)
- `POST /posts` — Create question (auth required)
- `GET /posts/{id}` — Get post detail with answers & comments
- `PATCH /posts/{id}` — Edit post (author only)
- `POST /posts/{id}/vote` — Vote UP/DOWN (toggle logic)

### Answers
- `POST /posts/{id}/answers` — Submit answer
- `PATCH /answers/{id}/accept` — Accept answer (post author)
- `POST /answers/{id}/vote` — Vote on answer

### Tags, Notifications, Attachments
- `GET /tags` — All tags with post counts
- `GET /notifications` — My notifications
- `POST /attachments/upload` — Upload file

## Running Tests

```bash
make test
# or directly:
docker compose exec backend pytest -v
```

## AWS Deployment

See `docker-compose.prod.yml` and the `terraform/` directory for production deployment configuration. Key differences from local:

| Component | Local | AWS |
|---|---|---|
| Database | PostgreSQL in Docker | RDS db.t3.micro |
| Backend | localhost:8000 | EC2 t3.micro (port 80) |
| Frontend | Vite dev server | S3 + CloudFront |
| Auth | Local JWT | AWS Cognito |
| File uploads | `./uploads/` | S3 pre-signed URLs |
| Notifications | Direct DB insert | SQS → Lambda → SES |
