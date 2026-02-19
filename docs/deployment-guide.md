# Deployment Guide

## Local Development Setup

### Prerequisites
- Docker & Docker Compose
- Python 3.13 (via `uv`)
- Node.js 22+
- Bun 1.2.4+
- Git

### Step 1: Clone & Install

```bash
git clone <repo-url>
cd notesapp

# Install all dependencies
bun install
```

### Step 2: Environment Configuration

**Backend (.env)**
```bash
cp backend/.env.example backend/.env

# Edit backend/.env with your values
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/notesapp
JWT_SECRET=your-64-char-random-secret
JWT_EXPIRY_DAYS=7
WEBAUTHN_RP_ID=localhost
WEBAUTHN_RP_NAME=NotesApp
WEBAUTHN_ORIGIN=http://localhost:3000
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=notesapp-images
MINIO_MAX_IMAGE_SIZE=10485760
TELEGRAM_BOT_TOKEN=123456:ABC-DEF  # Optional
CORS_ORIGINS=http://localhost:3000
```

**Frontend (.env.local)**
```bash
# apps/web-svelte/.env.local
PUBLIC_API_URL=http://localhost:8000
```

### Step 3: Start Database

```bash
# Start PostgreSQL in Docker
docker-compose up -d postgres

# Verify container is running
docker-compose logs postgres
```

### Step 4: Database Migrations

```bash
cd backend

# Create virtual environment (if using uv)
uv venv

# Install dependencies
uv sync

# Run migrations
alembic upgrade head

# Check migrations applied
alembic current
```

### Step 5: Start Development Servers

```bash
# From project root
bun run dev

# This starts:
# - Frontend (SvelteKit): http://localhost:3000 (or configured port)
# - Backend: http://localhost:8000
# - Turborepo watches for changes
```

### Step 6: Verify Setup

```bash
# Test backend health
curl http://localhost:8000/api/health

# Test frontend
open http://localhost:3000

# Check API docs
open http://localhost:8000/docs
```

## Local Development Commands

```bash
# Development (using Bun)
bun run dev              # Run all services
bun run dev:web-svelte   # SvelteKit frontend only
bun run dev:desktop      # Tauri desktop app
bun run build            # Build all
bun run lint             # Lint all

# Backend specific
cd backend
uv sync               # Install deps
alembic upgrade head  # Run migrations
alembic revision --autogenerate -m "message"  # New migration

# Frontend specific (SvelteKit)
cd apps/web-svelte
bun dev              # Dev server
bun run build        # Build for production
bun run lint         # Lint code
```

## Docker Local Environment

The `docker-compose.yml` file provides PostgreSQL + backend:

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Reset database (delete volume)
docker-compose down -v
docker-compose up -d
```

Services:
- **PostgreSQL**: localhost:5432 (user: notesapp, pass: notesapp)
- **Backend**: localhost:8000 (auto-reload with uvicorn)
- **MinIO**: localhost:9000 (S3-compatible storage), localhost:9001 (console)
  - Access Key: minioadmin
  - Secret Key: minioadmin
  - Create bucket: `notesapp-images` (set public-read for image serving)

## Production Deployment

### Prerequisites
- Docker & Docker Compose installed
- Domain name with DNS configured
- Supabase project (for database + auth)
- MinIO or S3-compatible storage

### Quick Start (Docker Compose + Caddy)

This is the recommended approach - single command deployment with auto SSL.

#### Step 1: Server Setup

```bash
# SSH into VPS (DigitalOcean, Linode, Hetzner, etc.)
ssh root@your-server-ip

# Install Docker
curl -fsSL https://get.docker.com | sh

# Clone repo
cd /opt
git clone <repo-url> notesapp
cd notesapp
```

#### Step 2: Configure Environment

```bash
# Copy example and edit
cp .env.production.example .env.production

# Edit with your values
nano .env.production
```

Required variables:
| Variable | Description |
|----------|-------------|
| `DOMAIN` | Your domain (e.g., `notes.example.com`) |
| `DATABASE_URL` | Supabase pooler connection string |
| `SUPABASE_URL` | `https://[ref].supabase.co` |
| `SUPABASE_ANON_KEY` | From Supabase dashboard |
| `JWT_SECRET` | Generate: `openssl rand -hex 32` |
| `WEBAUTHN_RP_ID` | Same as domain |
| `WEBAUTHN_ORIGIN` | `https://notes.example.com` |
| `MINIO_*` | S3/MinIO credentials |
| `CORS_ORIGINS` | `https://notes.example.com` |
| `PUBLIC_API_URL` | `https://notes.example.com` |

#### Step 3: Deploy

```bash
# Load env vars
set -a && source .env.production && set +a

# Build and start with Caddy (auto SSL)
docker compose -f docker-compose.prod.yml --profile with-caddy up -d --build

# Or without Caddy (if using external reverse proxy)
docker compose -f docker-compose.prod.yml up -d --build
```

#### Step 4: Verify

```bash
# Check services
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Test API
curl https://notes.example.com/api/health
```

### Manual VPS Setup (Without Docker)

#### Step 1: Install Dependencies

```bash
# System packages
apt update && apt install -y nginx certbot python3-certbot-nginx

# Bun (for frontend)
curl -fsSL https://bun.sh/install | bash

# uv (for backend)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Step 2: Build Frontend

```bash
cd /opt/notesapp/apps/web-svelte

# Set env
echo "PUBLIC_API_URL=https://notes.example.com" > .env.production

# Build
bun install
bun run build

# The built app is in ./build
```

#### Step 3: Build Backend

```bash
cd /opt/notesapp/backend
cp .env.example .env
# Edit .env with production values

uv sync --frozen
```

#### Step 4: Create Systemd Services

**Backend** (`/etc/systemd/system/notesapp-backend.service`):
```ini
[Unit]
Description=NotesApp Backend
After=network.target

[Service]
Type=exec
User=www-data
WorkingDirectory=/opt/notesapp/backend
EnvironmentFile=/opt/notesapp/backend/.env
ExecStart=/root/.local/bin/uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

**Frontend** (`/etc/systemd/system/notesapp-frontend.service`):
```ini
[Unit]
Description=NotesApp Frontend
After=network.target

[Service]
Type=exec
User=www-data
WorkingDirectory=/opt/notesapp/apps/web-svelte
Environment=NODE_ENV=production
ExecStart=/root/.bun/bin/bun ./build
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now notesapp-backend notesapp-frontend
```

#### Step 5: Nginx + SSL

```bash
# Get SSL cert
certbot certonly --nginx -d notes.example.com
```

Create `/etc/nginx/sites-available/notesapp`:
```nginx
server {
    listen 80;
    server_name notes.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name notes.example.com;

    ssl_certificate /etc/letsencrypt/live/notes.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/notes.example.com/privkey.pem;

    # API + public shared notes
    location ~ ^/(api|pub)/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
ln -s /etc/nginx/sites-available/notesapp /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

### Cloud Platform Deployments

#### Vercel (Frontend) + Railway (Backend)

**Frontend on Vercel:**
1. Connect repo → select `apps/web-svelte`
2. Framework: SvelteKit
3. Build: `bun run build`
4. Output: `build`
5. Env: `PUBLIC_API_URL=https://api.railway.app`

**Backend on Railway:**
1. Connect repo → select `backend` directory
2. Dockerfile deployment (auto-detected)
3. Add env vars from `.env.production.example`
4. Custom domain: `api.yourdomain.com`

#### Fly.io (Full Stack)

```bash
# Backend
cd backend
fly launch --name notesapp-api
fly secrets set DATABASE_URL=... JWT_SECRET=...
fly deploy

# Frontend
cd apps/web-svelte
fly launch --name notesapp-web
fly secrets set PUBLIC_API_URL=https://notesapp-api.fly.dev
fly deploy
```

#### AWS (ECS + RDS)

1. Create RDS PostgreSQL (or use Supabase)
2. Create ECR repos for backend + frontend
3. Push Docker images
4. Deploy via ECS Fargate
5. ALB for load balancing
6. CloudFront for CDN

### Database Migrations

```bash
# Via Docker
docker compose -f docker-compose.prod.yml exec backend uv run alembic upgrade head

# Via systemd
cd /opt/notesapp/backend
uv run alembic upgrade head

# Check current migration
uv run alembic current
```

## Monitoring & Logging

### Application Logging

Backend logs to stdout (captured by Docker):
```bash
docker-compose logs -f backend
```

Frontend logs to browser console.

### Health Checks

```bash
# Backend health
curl https://yourdomain.com/api/health

# Database connectivity
curl https://yourdomain.com/api/auth/me \
  -H "Authorization: Bearer <token>"
```

### Uptime Monitoring (Future)

Configure monitoring via:
- Sentry for error tracking
- DataDog for metrics
- UptimeRobot for uptime monitoring

## Backup & Recovery

### Database Backup

```bash
# Backup PostgreSQL
docker exec notesapp-postgres-1 pg_dump -U notesapp notesapp > backup.sql

# Restore from backup
cat backup.sql | docker exec -i notesapp-postgres-1 psql -U notesapp notesapp
```

### Automated Daily Backup (Supabase)
- Supabase includes daily automated backups
- Accessible from dashboard
- Point-in-time recovery available

## Scaling Considerations

### Load Testing
```bash
# Using ab (Apache Bench)
ab -n 1000 -c 10 http://localhost:8000/api/health
```

### Horizontal Scaling
- Run multiple backend instances behind load balancer
- Frontend deployed to CDN (Vercel, Netlify, CloudFront)
- Database: upgrade Supabase plan or use managed RDS

### Vertical Scaling
- Increase VPS RAM/CPU
- Increase database instance size
- Adjust connection pool size

## Troubleshooting

### Backend won't start
```bash
# Check logs
docker-compose logs backend

# Verify database connection
docker exec notesapp-postgres-1 pg_isready -U notesapp

# Check env vars
env | grep SUPABASE
```

### Database migrations fail
```bash
# Check current migration
cd backend && alembic current

# Reset (DANGEROUS - drops data)
alembic downgrade base
alembic upgrade head
```

### Frontend can't reach API
```bash
# Check CORS
curl -H "Origin: http://localhost:3000" http://localhost:8000/api/health

# Check API URL
cat apps/web/.env.local | grep API_URL
```

## Security Checklist

- [ ] Environment variables not in .env.example
- [ ] Database password is strong (20+ chars)
- [ ] SSL/TLS certificate valid
- [ ] CORS origins restricted to domain
- [ ] No debug mode in production
- [ ] Rate limiting configured (future)
- [ ] Database backups automated
- [ ] Secrets rotation scheduled

## Performance Optimization

### Frontend
- CDN caching: 1 year for /public/*
- Gzip compression enabled
- Code splitting by route
- Image optimization

### Backend
- Connection pooling: 10-20 connections
- Query caching: 1 hour (future)
- Compression: gzip for all responses

### Database
- Index optimization
- Query analysis
- Auto-vacuum tuning

## Rollback Plan

If deployment fails:
```bash
# Rollback to previous Docker image
docker-compose down
git checkout previous-commit
docker-compose up -d
```

## References

- Supabase Docs: https://supabase.com/docs
- FastAPI Docs: https://fastapi.tiangolo.com/deployment/
- Next.js Deployment: https://nextjs.org/docs/deployment
- Docker Docs: https://docs.docker.com
