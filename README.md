# ChatGepeto

Assistente educacional inteligente usando Flask (backend) e Next.js (frontend), com deploy na AWS via ECS Fargate.

## Arquitetura

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   GitHub    │─────▶│GitHub Actions│─────▶│  AWS ECR    │
│   (Code)    │      │   (CI/CD)    │      │  (Images)   │
└─────────────┘      └──────────────┘      └──────┬──────┘
                            │                     │
                            ▼                     ▼
                     ┌──────────────┐      ┌─────────────┐
                     │ CodeCommit   │      │ ECS Fargate │
                     │   (Mirror)   │      │  (Deploy)   │
                     └──────────────┘      └──────┬──────┘
                                                  │
                                                  ▼
                                           ┌─────────────┐
                                           │     ALB     │
                                           │ (Public IP) │
                                           └─────────────┘
```

Ver [docs/architecture.md](docs/architecture.md) para diagrama completo.

## Estrutura

```
chatgepeto/
├── backend/                    # Flask backend
│   ├── app/
│   │   ├── __init__.py        # App factory
│   │   ├── config.py          # Configurações
│   │   ├── models/            # SQLAlchemy models
│   │   ├── routes/            # Blueprints (API)
│   │   ├── schemas/           # Marshmallow schemas
│   │   └── services/          # LLM providers
│   ├── tests/
│   └── requirements.txt
├── frontend/                   # Next.js frontend
│   ├── app/                   # App router
│   └── package.json
├── terraform/                  # AWS Infrastructure
│   ├── main.tf
│   ├── vpc.tf
│   ├── ecr.tf
│   ├── ecs.tf
│   ├── alb.tf
│   ├── iam.tf
│   └── cloudwatch.tf
├── .github/workflows/
│   ├── ci.yml                 # Lint, test, build
│   └── deploy.yml             # Deploy to AWS
├── docker-compose.yml
├── Dockerfile.backend         # Multi-stage build
└── Dockerfile.frontend        # Multi-stage build
```

## Quick Start (Docker)

```bash
# Copiar env
cp .env.example .env

# Subir serviços
docker-compose up --build

# Criar superuser
docker-compose exec backend python manage.py create-superuser
```

**Acesso:**
- Frontend: http://localhost:3000
- API: http://localhost:8000/api
- Admin: http://localhost:8000/admin

**Credenciais:** `gepetobot` / `cesariscool`

## API Endpoints

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/health/` | GET | Health check |
| `/api/auth/login/` | POST | Login |
| `/api/auth/logout/` | POST | Logout |
| `/api/auth/me/` | GET | Usuário atual |
| `/api/conversations/` | GET, POST | Listar/criar conversas |
| `/api/conversations/<id>/` | GET, PATCH, DELETE | Detalhe conversa |
| `/api/conversations/<id>/messages/` | POST | Enviar mensagem |
| `/api/conversations/<id>/messages/stream/` | POST | Streaming (SSE) |

## Deploy AWS

### 1. Infraestrutura (Terraform)

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Editar terraform.tfvars com suas configs

terraform init
terraform plan
terraform apply
```

### 2. Secrets GitHub

Adicionar no GitHub (Settings > Secrets):
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

### 3. Deploy

Push para `main` dispara deploy automático via GitHub Actions.

## Stack

**Backend:**
- Flask 3.0 + SQLAlchemy + Marshmallow
- Groq API (LLM) + Ollama (local)
- Gunicorn + Docker

**Frontend:**
- Next.js 14 + TypeScript + Tailwind

**AWS:**
- ECS Fargate + ALB + ECR
- CloudWatch + SSM
- CodeCommit (mirror)

**CI/CD:**
- GitHub Actions (lint, test, build, deploy)

## Testes

```bash
# Backend
cd backend && pytest --cov=app

# Frontend
cd frontend && npm run test

# Lint
ruff check backend/
npm run lint --prefix frontend
```

## Licença

MIT
