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

### Backend
```
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

### Frontend
```
cd frontend
npm install
npm run dev
```

## Environment
Create `backend/.env`:
```
JWT_SECRET_KEY=your-32-char-or-longer-secret
SECRET_KEY=your-32-char-or-longer-secret
FLASK_DEBUG=true
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
- Ensure you are logged in before using library endpoints.
- Password reset endpoints are implemented. In debug you can set `RETURN_RESET_TOKEN=true` to get the reset token back in the response (production should email it instead).
