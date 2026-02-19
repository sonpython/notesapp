# Deployment Guide

## Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Caddy     │────▶│   Backend   │────▶│  PostgreSQL │
│  (SSL/LB)   │     │  (FastAPI)  │     │  (Database) │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │
       ▼                   ▼
┌─────────────┐     ┌─────────────┐
│  Frontend   │     │    MinIO    │
│ (SvelteKit) │     │  (Storage)  │
└─────────────┘     └─────────────┘
```

**Stack:**
- Backend: FastAPI + SQLAlchemy + asyncpg
- Frontend: SvelteKit + Bun
- Auth: WebAuthn/Passkey (self-hosted, no external auth)
- Database: PostgreSQL (self-hosted or managed)
- Storage: MinIO (S3-compatible)
- Reverse Proxy: Caddy (auto SSL)

---

## VPS Deployment (Recommended)

### Prerequisites
- VPS with 1GB+ RAM (DigitalOcean, Hetzner, Linode)
- Domain pointing to VPS IP
- SSH access

### Step 1: Server Setup

```bash
# SSH into VPS
ssh root@your-server-ip

# Install Docker
curl -fsSL https://get.docker.com | sh

# Clone repo
git clone https://github.com/your/notesapp.git /opt/notesapp
cd /opt/notesapp
```

### Step 2: Environment Configuration

```bash
# Create production env file
cat > .env.production << 'EOF'
# Domain
DOMAIN=notes.yourdomain.com

# Database (PostgreSQL)
DATABASE_URL=postgresql+asyncpg://notesapp:YOUR_DB_PASSWORD@postgres:5432/notesapp
DB_PASSWORD=YOUR_DB_PASSWORD

# Auth (WebAuthn)
JWT_SECRET=$(openssl rand -hex 32)
JWT_EXPIRY_DAYS=7
WEBAUTHN_RP_ID=notes.yourdomain.com
WEBAUTHN_RP_NAME=NotesApp
WEBAUTHN_ORIGIN=https://notes.yourdomain.com

# Storage (MinIO)
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=notesapp
MINIO_SECRET_KEY=YOUR_MINIO_SECRET
MINIO_BUCKET=notesapp-images
MINIO_SECURE=false

# CORS
CORS_ORIGINS=https://notes.yourdomain.com

# Frontend
PUBLIC_API_URL=https://notes.yourdomain.com
EOF

# Generate secrets
sed -i "s/YOUR_DB_PASSWORD/$(openssl rand -hex 16)/g" .env.production
sed -i "s/YOUR_MINIO_SECRET/$(openssl rand -hex 16)/g" .env.production

# Review and edit
nano .env.production
```

### Step 3: Create Production Docker Compose

```bash
cat > docker-compose.production.yml << 'EOF'
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: notesapp
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: notesapp
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U notesapp"]
      interval: 10s
      timeout: 5s
      retries: 5

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ACCESS_KEY}
      MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY}
    volumes:
      - minio_data:/data
    restart: always

  backend:
    build: ./backend
    environment:
      DATABASE_URL: ${DATABASE_URL}
      JWT_SECRET: ${JWT_SECRET}
      JWT_EXPIRY_DAYS: ${JWT_EXPIRY_DAYS}
      WEBAUTHN_RP_ID: ${WEBAUTHN_RP_ID}
      WEBAUTHN_RP_NAME: ${WEBAUTHN_RP_NAME}
      WEBAUTHN_ORIGIN: ${WEBAUTHN_ORIGIN}
      MINIO_ENDPOINT: ${MINIO_ENDPOINT}
      MINIO_ACCESS_KEY: ${MINIO_ACCESS_KEY}
      MINIO_SECRET_KEY: ${MINIO_SECRET_KEY}
      MINIO_BUCKET: ${MINIO_BUCKET}
      MINIO_SECURE: ${MINIO_SECURE}
      CORS_ORIGINS: ${CORS_ORIGINS}
    depends_on:
      postgres:
        condition: service_healthy
    restart: always

  frontend:
    build:
      context: ./apps/web-svelte
      args:
        PUBLIC_API_URL: ${PUBLIC_API_URL}
    depends_on:
      - backend
    restart: always

  caddy:
    image: caddy:2-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    environment:
      DOMAIN: ${DOMAIN}
    depends_on:
      - frontend
      - backend
    restart: always

volumes:
  postgres_data:
  minio_data:
  caddy_data:
  caddy_config:
EOF
```

### Step 4: Deploy

```bash
# Load env vars
set -a && source .env.production && set +a

# Build and start
docker compose -f docker-compose.production.yml up -d --build

# Check status
docker compose -f docker-compose.production.yml ps

# View logs
docker compose -f docker-compose.production.yml logs -f

# Run migrations
docker compose -f docker-compose.production.yml exec backend uv run alembic upgrade head
```

### Step 5: Create MinIO Bucket

```bash
# Access MinIO console at https://your-domain:9001
# Or via CLI:
docker compose -f docker-compose.production.yml exec minio \
  mc alias set local http://localhost:9000 $MINIO_ACCESS_KEY $MINIO_SECRET_KEY

docker compose -f docker-compose.production.yml exec minio \
  mc mb local/notesapp-images
```

### Step 6: Verify

```bash
curl https://notes.yourdomain.com/api/health
```

---

## CI/CD with GitHub Actions

### Setup Deploy Keys

```bash
# On VPS: Generate SSH key for deployments
ssh-keygen -t ed25519 -f ~/.ssh/deploy_key -N ""

# Add to authorized_keys
cat ~/.ssh/deploy_key.pub >> ~/.ssh/authorized_keys

# Copy private key (add to GitHub Secrets as DEPLOY_KEY)
cat ~/.ssh/deploy_key
```

### GitHub Secrets Required

Add these in GitHub → Settings → Secrets → Actions:

| Secret | Value |
|--------|-------|
| `DEPLOY_HOST` | Your VPS IP |
| `DEPLOY_USER` | `root` or deploy user |
| `DEPLOY_KEY` | SSH private key |
| `DEPLOY_PATH` | `/opt/notesapp` |

### Create CD Workflow

The workflow is at `.github/workflows/cd.yml` - it will:
1. Run on push to `main` (after CI passes)
2. SSH to VPS
3. Pull latest code
4. Rebuild and restart containers

---

## Database Management

### Run Migrations

```bash
# Production
docker compose -f docker-compose.production.yml exec backend uv run alembic upgrade head

# Check current
docker compose -f docker-compose.production.yml exec backend uv run alembic current
```

### Backup Database

```bash
# Backup
docker compose -f docker-compose.production.yml exec postgres \
  pg_dump -U notesapp notesapp > backup_$(date +%Y%m%d).sql

# Restore
cat backup.sql | docker compose -f docker-compose.production.yml exec -T postgres \
  psql -U notesapp notesapp
```

### Automated Backups

```bash
# Add to crontab
crontab -e

# Daily backup at 2am
0 2 * * * cd /opt/notesapp && docker compose -f docker-compose.production.yml exec -T postgres pg_dump -U notesapp notesapp | gzip > /backups/notesapp_$(date +\%Y\%m\%d).sql.gz
```

---

## Updating Production

### Manual Update

```bash
cd /opt/notesapp
git pull origin main
docker compose -f docker-compose.production.yml up -d --build
docker compose -f docker-compose.production.yml exec backend uv run alembic upgrade head
```

### Via CI/CD

Push to `main` branch → GitHub Actions auto-deploys

---

## Troubleshooting

### Check Logs

```bash
# All services
docker compose -f docker-compose.production.yml logs -f

# Specific service
docker compose -f docker-compose.production.yml logs -f backend
```

### Backend Won't Start

```bash
# Check database connection
docker compose -f docker-compose.production.yml exec backend \
  python -c "from app.database import engine; print('OK')"

# Check migrations
docker compose -f docker-compose.production.yml exec backend uv run alembic current
```

### SSL Issues

```bash
# Check Caddy logs
docker compose -f docker-compose.production.yml logs caddy

# Verify domain DNS
dig +short notes.yourdomain.com
```

### Reset Everything

```bash
# WARNING: Destroys all data
docker compose -f docker-compose.production.yml down -v
docker compose -f docker-compose.production.yml up -d --build
```

---

## Security Checklist

- [ ] Strong passwords in .env.production
- [ ] Firewall enabled (only 80, 443, 22)
- [ ] SSH key auth only (disable password)
- [ ] Regular backups configured
- [ ] Secrets not committed to git
- [ ] CORS restricted to your domain

---

## Local Development

See [README.md](../README.md) for local development setup.

```bash
# Quick start
docker-compose up -d postgres minio
cd backend && uv sync && uv run uvicorn app.main:app --reload
cd apps/web-svelte && bun dev
```
