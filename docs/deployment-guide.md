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
- Docker installed on server
- Domain name configured
- SSL certificate (Let's Encrypt)
- Environment variables set

### Option 1: VPS Deployment (DigitalOcean, Linode, AWS EC2)

#### Step 1: Server Setup

```bash
# SSH into VPS
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install Docker & Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Node.js & Bun (for building frontend)
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
apt install -y nodejs
curl -fsSL https://bun.sh/install | bash

# Install Python & uv
apt install -y python3.13 python3-pip
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Step 2: Clone Repository

```bash
cd /opt
git clone <repo-url> notesapp
cd notesapp

# Create .env files
cp backend/.env.example backend/.env
# Edit backend/.env with production values

cp apps/web-svelte/.env.example apps/web-svelte/.env.production.local
# Edit frontend .env with production API URL
```

#### Step 3: Build & Deploy

```bash
# Build frontend (from root)
bun install
bun run build:web-svelte

# Build backend Docker image
cd /opt/notesapp
docker build -t notesapp-backend ./backend

# Create docker-compose for production
# (See below for production docker-compose.yml)
```

#### Step 4: Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: notesapp
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: notesapp
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "127.0.0.1:5432:5432"  # Only internal access
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U notesapp"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    image: notesapp-backend:latest
    environment:
      DATABASE_URL: postgresql+asyncpg://notesapp:${DB_PASSWORD}@postgres:5432/notesapp
      SUPABASE_URL: ${SUPABASE_URL}
      SUPABASE_ANON_KEY: ${SUPABASE_ANON_KEY}
      SUPABASE_JWT_SECRET: ${SUPABASE_JWT_SECRET}
      TELEGRAM_BOT_TOKEN: ${TELEGRAM_BOT_TOKEN}
      CORS_ORIGINS: ${CORS_ORIGINS}
    ports:
      - "127.0.0.1:8000:8000"  # Only internal access
    depends_on:
      postgres:
        condition: service_healthy
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    image: node:22-alpine
    working_dir: /app/apps/web
    command: npm run start
    volumes:
      - ./apps/web:/app/apps/web
      - /app/apps/web/.next
    environment:
      NEXT_PUBLIC_API_URL: https://api.yourdomain.com
      NEXT_PUBLIC_SUPABASE_URL: ${SUPABASE_URL}
      NEXT_PUBLIC_SUPABASE_ANON_KEY: ${SUPABASE_ANON_KEY}
    ports:
      - "127.0.0.1:3000:3000"
    restart: always

volumes:
  postgres_data:
    driver: local
```

#### Step 5: Nginx Reverse Proxy

Create `/etc/nginx/sites-available/notesapp`:

```nginx
upstream backend {
    server 127.0.0.1:8000;
}

upstream frontend {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # API routes → backend
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 30s;
    }

    # Everything else → frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Step 6: SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
apt install -y certbot python3-certbot-nginx

# Get certificate
certbot certonly --standalone -d yourdomain.com

# Enable auto-renewal
systemctl enable certbot.timer
```

#### Step 7: Start Production

```bash
cd /opt/notesapp

# Create .env with all secrets
export DB_PASSWORD="random-secure-password"
export SUPABASE_URL="https://xxx.supabase.co"
# ... set all vars

# Run migrations
docker-compose -f docker-compose.prod.yml run backend alembic upgrade head

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Verify
docker-compose -f docker-compose.prod.yml logs -f
curl https://yourdomain.com/api/health
```

### Option 2: Vercel Deployment (Recommended for Frontend)

#### Frontend on Vercel

1. Push repo to GitHub
2. Connect to Vercel at https://vercel.com
3. Set environment variables:
   ```
   NEXT_PUBLIC_API_URL=https://api.yourdomain.com
   NEXT_PUBLIC_SUPABASE_URL=<value>
   NEXT_PUBLIC_SUPABASE_ANON_KEY=<value>
   ```
4. Deploy (automatic on push)

#### Backend on Heroku/Railway

Deploy via Docker:

```bash
# Railway example
railway link
railway up -d

# Heroku example
heroku container:push web
heroku container:release web
```

### Option 3: AWS Deployment

#### Using ECS + RDS

1. Create RDS PostgreSQL instance
2. Create ECR repository
3. Build & push backend Docker image
4. Deploy via CloudFormation/Terraform
5. Use CloudFront for CDN

See AWS documentation for detailed steps.

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
