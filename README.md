# Smart Q&A

A full-stack course discussion platform (StackOverflow-lite) where students post questions, receive answers, vote, and get notifications. Includes AI-powered semantic duplicate detection using Amazon Bedrock and a serverless notification pipeline via AWS SQS + Lambda.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS, TanStack Query, React Router v6 |
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2 |
| Database | PostgreSQL 15 + pgvector extension |
| Auth (local) | JWT — python-jose + passlib/bcrypt |
| Auth (AWS) | AWS Cognito JWKS validation |
| AI / Embeddings | Amazon Bedrock — Titan Embeddings G1 (1536-dim vectors) |
| Vector Search | pgvector — cosine similarity via IVFFlat index |
| File Uploads | S3 (production) / local `uploads/` dir (development) |
| Notifications | SQS → Lambda → RDS + SES (production) / direct DB write (development) |
| Containers | Docker, Docker Compose |
| IaC | Terraform (EC2, RDS, S3, CloudFront, Cognito, SQS, Lambda, ECR) |
| CI/CD | GitHub Actions (backend CI, frontend CI, Terraform apply) |

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
- `POST /posts/similar` — Find semantically similar posts (AI)

### Answers
- `POST /posts/{id}/answers` — Submit answer
- `PATCH /answers/{id}` — Edit answer (author only)
- `PATCH /answers/{id}/accept` — Accept answer (post author)
- `POST /answers/{id}/vote` — Vote on answer
- `DELETE /answers/{id}` — Delete answer (author or ADMIN)

### Tags, Notifications, Attachments
- `GET /tags` — All tags with post counts
- `GET /notifications` — My notifications
- `POST /attachments/upload` — Upload file (S3 or local)

## AI Similarity Search

When a user types a new question title, the frontend automatically checks for semantically similar existing posts using Amazon Bedrock + pgvector.

**How it works:**
1. After a 600 ms debounce, the frontend calls `POST /api/v1/posts/similar`
2. The backend calls Amazon Bedrock Titan Embeddings to generate a 1536-dim vector for the query text
3. pgvector finds the closest posts in the database using cosine distance
4. Posts with ≥ 75% similarity are returned and displayed in a warning panel

**Configuration:**

| Variable | Default | Description |
|---|---|---|
| `BEDROCK_MODEL_ID` | `amazon.titan-embed-text-v2:0` | Bedrock embedding model |
| `AWS_REGION` | `us-east-1` | AWS region for Bedrock |
| `BEDROCK_REGION` | `us-east-1` | Override region for Bedrock only |

Bedrock is optional — if credentials are absent or the model is unreachable, similarity search is silently skipped and the app continues to work normally.

See `docs/ai-similarity-search-guide.md` for the full implementation guide.

## Notifications

Notifications are delivered through two modes, controlled by `NOTIFICATION_DELIVERY_MODE`:

| Mode | Behavior |
|---|---|
| `sqs` | Publishes events to the SQS queue; Lambda writes to RDS and optionally sends SES email |
| `direct` | Writes directly to the `notifications` table (local dev) |
| `auto` (default) | Uses SQS if `SQS_NOTIFICATION_QUEUE_URL` is set, otherwise direct |

**Triggered on:**
- New answer submitted on a post you authored
- Your answer is accepted

**AWS components (production):**
- SQS queue: `smartqna-prod-notifications-events`
- Lambda function (`lambda/notification_worker/`) — triggered by SQS, writes to RDS, sends SES email
- Lambda function (`lambda/notification_api/`) — HTTP API for reading/marking notifications

See `docs/notifications-microservice-guide.md` and `docs/notifications-microservice-contract.md` for details.

## File Uploads

Attachments support two backends, selected automatically:

| Condition | Storage |
|---|---|
| `S3_BUCKET_ATTACHMENTS` is set | Uploaded to S3; URL returned as `https://<bucket>.s3.<region>.amazonaws.com/attachments/<file>` |
| Not set | Saved to `./uploads/` directory; URL returned as `/uploads/<file>` |

**Allowed types:** JPEG, PNG, GIF, WebP, PDF, plain text, ZIP  
**Max size:** 10 MB

## Running Tests

```bash
make test
# or directly:
docker compose exec backend pytest -v
```

## AWS Deployment

See `docker-compose.prod.yml` and the `terraform/` directory for production deployment configuration.

| Component | Local | AWS |
|---|---|---|
| Database | PostgreSQL in Docker | RDS db.t3.micro + pgvector |
| Backend | localhost:8000 | EC2 t3.micro (port 80) via ECR image |
| Frontend | Vite dev server | S3 + CloudFront |
| Auth | Local JWT | AWS Cognito |
| File uploads | `./uploads/` | S3 pre-signed URLs |
| Notifications | Direct DB insert | SQS → Lambda → RDS + SES |
| AI embeddings | Skipped (no creds) | Bedrock Titan Embeddings (us-east-1) |

### Terraform Modules

```
terraform/
├── main.tf            # Root config — provider, backend
├── networking.tf      # VPC, subnets, security groups
├── compute.tf         # EC2 instance, key pair
├── storage.tf         # RDS PostgreSQL, S3 buckets
├── cdn.tf             # CloudFront distribution
├── ecr.tf             # ECR repository for backend image
├── iam.tf             # IAM roles and policies
└── modules/
    └── notification_service/   # SQS queue + Lambda worker + SES
```

### CI/CD Pipelines

| Workflow | Trigger | What it does |
|---|---|---|
| `backend-ci.yml` | Push to `main`, manual | Runs pytest, builds & pushes Docker image to ECR, deploys to EC2 |
| `frontend-ci.yml` | Push to `main`, manual | Builds React app, syncs to S3, invalidates CloudFront |
| `terraform.yml` | Push to `main`, manual | `terraform plan` + `terraform apply` |

See `docs/cicd-and-infrastructure.md` and `docs/github-actions-reference.md` for full pipeline documentation.
