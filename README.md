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
python -m venv venv
venv\\Scripts\\activate
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
```

## Data
The recommender reads:
```
backend/data/books_manga_comics_catalog.csv
```

## Notes
- If recommendations are empty, restart the backend to rebuild embeddings.
- Ensure you are logged in before using library endpoints.
