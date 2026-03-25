# GitHub Actions — CI/CD Reference

This document explains the GitHub Actions CI/CD setup for the Smart Q&A project: what it does, how each workflow works step by step, and why it is beneficial for a team.

---

## What Is GitHub Actions?

GitHub Actions is a CI/CD (Continuous Integration / Continuous Deployment) system built directly into GitHub. It listens for events in your repository (like a `git push`) and automatically runs a series of steps you define in `.yml` files inside `.github/workflows/`.

No extra server or third-party service is needed — GitHub provides the runner (a temporary Ubuntu virtual machine) for free.

---

## Why We Use It

### Without GitHub Actions (Manual Deployment)

Every time any teammate pushes a change, someone would have to manually:

1. Run the test suite locally and hope it passes
2. Build the Docker image on their machine
3. Authenticate to AWS and push the image to ECR
4. SSH into the EC2 server
5. Pull the new Docker image and restart the containers
6. Build the React app (`npm run build`)
7. Upload the production files to S3
8. Invalidate the CloudFront cache so users see the new version

That is 8 steps every single time — easy to forget one, easy to skip the tests, and only one person typically knows how to do it all.

### With GitHub Actions (Automated)

Every teammate just does:

```bash
git push origin main
```

GitHub automatically executes all the steps above, in the correct order, every time, without human error.

---

## Our Workflows

We have two workflow files, each responsible for a different part of the application:

| File | Triggers When | Responsibility |
|---|---|---|
| `.github/workflows/backend-ci.yml` | Push to `main` with changes in `backend/` | Test the API, build Docker image, deploy to EC2 |
| `.github/workflows/frontend-ci.yml` | Push to `main` with changes in `frontend/` | Build React app, upload to S3, refresh CloudFront |

The `paths:` filter means the workflows are smart — pushing only a frontend change will not trigger the backend pipeline, and vice versa.

---

## Workflow 1: Backend CI/CD (`backend-ci.yml`)

### Trigger

```yaml
on:
  push:
    branches: [main]
    paths: [backend/**]
```

Fires only when a push to `main` includes changes inside the `backend/` directory.

---

### Job 1: `test`

This job runs first and acts as a quality gate. The deploy job cannot run unless this passes.

```yaml
services:
  postgres:
    image: postgres:15
    env:
      POSTGRES_DB: test_smartqna
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
    ports: ["5432:5432"]
    options: >-
      --health-cmd pg_isready
      --health-interval 5s
      --health-timeout 5s
      --health-retries 5
```

GitHub spins up a **real PostgreSQL 15 container** alongside the job. The health check ensures the database is fully ready before any steps try to connect to it.

| Step | Command | What It Does |
|---|---|---|
| Checkout | `actions/checkout@v4` | Pulls your repository code onto the runner |
| Setup Python | `actions/setup-python@v5` | Installs Python 3.11 |
| Install dependencies | `pip install -r backend/requirements.txt` | Installs all Python packages |
| Run migrations | `alembic upgrade head` | Creates all database tables in the test DB |
| Run tests | `pytest -v` | Executes the full test suite |

If any test fails, the workflow stops here. The broken code is never deployed.

---

### Job 2: `deploy`

```yaml
deploy:
  needs: test
  if: github.ref == 'refs/heads/main'
```

`needs: test` means this job only starts after `test` succeeds. The `if:` condition is a double-check that we are on `main`.

| Step | What It Does |
|---|---|
| `aws-actions/configure-aws-credentials@v4` | Authenticates the runner to AWS using secrets stored in GitHub |
| `aws-actions/amazon-ecr-login@v2` | Logs into Amazon ECR (AWS's private Docker registry) |
| `docker build` + `docker push` | Builds the backend Docker image and pushes it to ECR |
| SSH into EC2 | Connects to the production server and pulls the new image, then restarts containers using `docker-compose.prod.yml` |

The full deploy step on EC2:
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ECR_REPO>
docker pull <ECR_REPO>:latest
cd /home/ec2-user/smartqna && docker compose -f docker-compose.prod.yml up -d
```

---

### Backend Flow Diagram

```
Push to main (backend change)
        │
        ▼
  [test job]
  ├── Start Postgres container
  ├── Install Python 3.11 + dependencies
  ├── Run Alembic migrations
  └── Run pytest
        │
   All pass? ──No──► Workflow fails. Deploy blocked.
        │ Yes
        ▼
  [deploy job]
  ├── Authenticate to AWS
  ├── Login to ECR
  ├── docker build + docker push to ECR
  └── SSH into EC2 → pull image → docker compose up
        │
        ▼
  EC2 is now running the latest backend
```

---

## Workflow 2: Frontend CI/CD (`frontend-ci.yml`)

### Trigger

```yaml
on:
  push:
    branches: [main]
    paths: [frontend/**]
```

Fires only when a push to `main` includes changes inside the `frontend/` directory.

---

### Job: `deploy`

There is no separate test job for the frontend — the build itself acts as a validation step (if the React app fails to compile, the workflow stops).

| Step | Command | What It Does |
|---|---|---|
| Checkout | `actions/checkout@v4` | Pulls repository code onto the runner |
| Setup Node | `actions/setup-node@v4` | Installs Node.js 20 |
| Install & build | `npm ci && npm run build` | Installs exact dependencies and produces production bundle in `frontend/dist/` |
| Configure AWS | `aws-actions/configure-aws-credentials@v4` | Authenticates to AWS |
| Sync to S3 | `aws s3 sync frontend/dist s3://<bucket> --delete` | Uploads all built files to S3; `--delete` removes files that no longer exist |
| Invalidate CloudFront | `aws cloudfront create-invalidation --paths "/*"` | Clears the CDN cache so all users immediately get the new version |

The `VITE_API_URL` environment variable is injected at build time so the React app knows the production backend address:

```yaml
env:
  VITE_API_URL: https://${{ secrets.EC2_HOST }}/api/v1
```

---

### Frontend Flow Diagram

```
Push to main (frontend change)
        │
        ▼
  [deploy job]
  ├── Install Node 20
  ├── npm ci + npm run build → produces frontend/dist/
  ├── Authenticate to AWS
  ├── aws s3 sync → upload dist/ to S3
  └── CloudFront invalidation → CDN cache cleared
        │
        ▼
  Users see the updated frontend immediately
```

---

## GitHub Secrets

Both workflows use `${{ secrets.* }}` placeholders instead of hardcoded values. These are encrypted variables stored in GitHub and never visible in logs or to anyone without admin access to the repo.

Go to: **GitHub repo → Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Description | Where to Find It |
|---|---|---|
| `AWS_ACCESS_KEY_ID` | IAM user access key ID | AWS Console → IAM → Users → Security credentials |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret access key | Same as above (only shown once at creation) |
| `ECR_REPO` | Full ECR repository URI | AWS Console → ECR → your repository → URI |
| `EC2_HOST` | Public IP or DNS of EC2 instance | AWS Console → EC2 → Instances → Public IPv4 |
| `EC2_SSH_KEY` | Private SSH key for EC2 access | The `.pem` file from your EC2 key pair |
| `S3_FRONTEND_BUCKET` | S3 bucket name for frontend files | AWS Console → S3 → your bucket name |
| `CF_DISTRIBUTION_ID` | CloudFront distribution ID | AWS Console → CloudFront → your distribution → ID |

---

## One-Time Setup Checklist

Before the workflows can run successfully, the following AWS infrastructure must exist:

- [ ] ECR repository named `smartqna-backend`
- [ ] EC2 instance (Amazon Linux 2023, t3.micro) with Docker installed
- [ ] S3 bucket for frontend static files
- [ ] CloudFront distribution pointing to the S3 bucket
- [ ] All 7 GitHub secrets added to the repository
- [ ] EC2 SSH key (`EC2_SSH_KEY`) added as a GitHub secret and the public key added to EC2's `~/.ssh/authorized_keys`
- [ ] Project pushed to GitHub with the `main` branch

EC2 Docker setup (run once after launching the instance):
```bash
ssh ec2-user@<your-ec2-ip>
sudo yum update -y
sudo yum install docker -y
sudo service docker start
sudo usermod -aG docker ec2-user
```

---

## Key Benefits for the Team

| Benefit | Explanation |
|---|---|
| **Tests are enforced** | No one can accidentally deploy broken code. If `pytest` fails, the deploy job is blocked automatically. |
| **Anyone can deploy** | Teammates do not need to know AWS CLI, Docker, or SSH. A `git push` is all it takes. |
| **Consistent deployments** | Every deploy runs the exact same steps regardless of who pushed, eliminating "works on my machine" issues. |
| **Full visibility** | The GitHub Actions tab shows a complete history of every deploy — who triggered it, whether tests passed, and whether the deploy succeeded. |
| **Secrets are centralized** | AWS credentials are stored once in GitHub secrets. No teammate needs to manage or share `.env` files with production values. |
| **Independent pipelines** | Frontend and backend are deployed separately. A frontend change does not re-deploy the backend, and vice versa. |
