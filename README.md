# ChatGepeto

NotebookLM-like chatbot built with Django and Next.js.

## Project Structure

```
chatgepeto/
├── backend/                    # Django backend
│   ├── chatgepeto/            # Django settings
│   ├── chat/                  # Chat conversations
│   ├── documents/             # Document management
│   ├── users/                 # User management
│   ├── api/                   # API endpoints
│   ├── embeddings/            # Vector embeddings
│   ├── sources/               # Citation tracking
│   └── requirements.txt
├── frontend/                   # Next.js frontend
│   ├── app/                   # App router pages
│   ├── components/            # React components
│   └── package.json
├── nginx/                      # Nginx configuration
├── docker-compose.yml
├── Dockerfile.backend
└── Dockerfile.frontend
```

## Quick Start

### Docker Setup (Recommended)

1. Copy environment file:
```bash
cp .env.example .env
```

2. Start everything with Docker:
```bash
docker-compose up --build
```

This automatically:
- Builds backend & frontend containers
- Runs database migrations
- Collects static files
- Starts development servers

3. Create the superuser (in a new terminal):
```bash
docker-compose exec backend python manage.py create_superuser_gepeto
```

4. Access:
- Frontend: http://localhost:3000
- Login page: http://localhost:3000/login
- Backend API: http://localhost:8000/api
- Django Admin: http://localhost:8000/admin

### Local Development (without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py create_superuser_gepeto  # Creates gepetobot user
python manage.py runserver
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Authentication

**Test Credentials:**
- Username: `gepetobot`
- Password: `cesariscool`

**API Endpoints:**
- `POST /api/auth/login/` - Login with username/password
- `POST /api/auth/logout/` - Logout (requires authentication)
- `GET /api/auth/me/` - Get current user (requires authentication)

**Creating the test superuser:**

With Docker:
```bash
docker-compose exec backend python manage.py create_superuser_gepeto
```

Without Docker:
```bash
cd backend
python manage.py create_superuser_gepeto
```

## Django Apps

- **users**: Custom user model
- **chat**: Conversations and messages
- **documents**: File uploads and chunking
- **embeddings**: Vector storage for RAG
- **sources**: Citation tracking
- **api**: REST API endpoints

## Next Steps

1. ✅ Authentication system (login/logout)
2. Implement chat API endpoints
3. Build frontend chat interface
4. Add document upload functionality
5. Implement RAG with embeddings
6. Add citations and source tracking
