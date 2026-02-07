# ComicAI Recommendation System

A full-stack comic/manga recommendation system with authentication, chat-based prompts, and personal library management.

## Features
- JWT authentication (register, login, logout)
- Chat-style recommendations
- Personal library with favorites, in-progress, completed, and trash
- Drag & drop between library columns
- Trash search (server-side)

## Tech Stack
**Frontend**
- React + Vite
- Tailwind CSS
- React Router
- Axios

**Backend**
- Flask
- Flask-SQLAlchemy
- Flask-JWT-Extended
- Flask-CORS
- SentenceTransformers (semantic similarity)

## Project Structure
```
frontend/
backend/
```

## Setup

### Quick Start (Backend Only)
```
python3 scripts/dev.py
```
This will create `backend/.venv`, install backend dependencies, ensure `backend/.env` has strong secrets, and start the backend server.

### Backend
```
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```
Notes:
- Backend defaults to port `5001` (or whatever `PORT` is in `backend/.env`). If the port is taken it will pick the next free port and print it.
- The chosen port is written to `backend/.runtime-port` for the frontend dev proxy.

### Frontend
```
cd frontend
npm install
npm run dev
```
Notes:
- In dev, the frontend calls the API at `/api` and Vite proxies it to the backend (no CORS needed).
- For non-dev environments, set `VITE_API_BASE_URL` to something like `http://localhost:5001/api`.

## Environment
Create `backend/.env`:
```
JWT_SECRET_KEY=your-32-char-or-longer-secret
SECRET_KEY=your-32-char-or-longer-secret
FLASK_DEBUG=true
PORT=5001
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```
You can start from `backend/.env.example`.

## Data
The recommender reads:
```
backend/data/books_manga_comics_catalog.csv
```

## Notes
- The backend will build a vector index on first request (and rebuild automatically if the catalog or embedding model changes).
- Index artifacts are stored under `backend/data/` (see `.gitignore` for filenames).
- Ensure you are logged in before using library endpoints.
- Password reset endpoints are implemented. In debug you can set `RETURN_RESET_TOKEN=true` to get the reset token back in the response (production should email it instead).

## Troubleshooting
- Library endpoints returning 401: you are not logged in (expected). Log in/register and retry.
- Library endpoints returning 422: invalid `Authorization` header or malformed token. Clear local storage key `comicai_auth` and retry.
- Recommender errors on first request: check backend dependencies and the configured `EMBEDDING_MODEL` in `backend/.env`.
