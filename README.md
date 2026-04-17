# Peakquiz v2

A timed mountain peak identification quiz. View a photo, pick the correct peak from four options, and score as many points as possible before the 60-second timer runs out.

## Stack

| Layer | Tech |
|-------|------|
| Frontend | React 18 + TypeScript + Vite 5 |
| Backend | FastAPI + SQLAlchemy 2 + SQLite |
| Auth | Google OAuth2 + HTTP-only JWT cookies |
| Styling | CSS Modules + custom design token system |
| Package managers | `uv` (Python), `npm` (Node) |
| Task runner | [Task](https://taskfile.dev) (`go-task`) |

## Prerequisites

- Python 3.12+
- Node.js 20+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [Task](https://taskfile.dev/installation/) (`brew install go-task`)

## Setup

### 1. Install dependencies

```bash
task install
```

### 2. Configure the backend

Copy the example env file and fill in your values:

```bash
cp backend/.env.example backend/.env
```

Required variables:

```
GOOGLE_CLIENT_ID=<your-google-oauth-client-id>
GOOGLE_CLIENT_SECRET=<your-google-oauth-client-secret>
SECRET_KEY=<any-random-string-for-jwt-signing>
FRONTEND_URL=http://localhost:5173
DATABASE_URL=sqlite:///./peakquiz.db
```

To get Google OAuth credentials: create a project in [Google Cloud Console](https://console.cloud.google.com), enable the Google+ API, and create an OAuth 2.0 Client ID with `http://localhost:8000/api/auth/google/callback` as an authorized redirect URI.

### 3. Populate the database

The app expects a `peakquiz.db` SQLite database in `backend/` with `peaks` and `pictures` tables. Pictures must have a `cdn_url` to appear in the quiz.

## Running

Start both servers with one command:

```bash
task
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

Or run them separately:

```bash
task backend    # FastAPI on :8000
task frontend   # Vite dev server on :5173
```

## Project structure

```
peakquiz_v2/
├── Taskfile.yaml
├── backend/
│   ├── pyproject.toml        # Python dependencies
│   ├── peakquiz.db           # SQLite database
│   └── app/
│       ├── main.py           # FastAPI app, CORS, middleware
│       ├── core/
│       │   ├── config.py     # Settings from .env
│       │   └── security.py   # JWT creation/decoding
│       ├── db/
│       │   ├── database.py   # SQLAlchemy engine + session
│       │   └── models.py     # User, Peak, Picture models
│       ├── api/routes/
│       │   ├── auth.py       # Google OAuth, /me, /logout
│       │   ├── quiz.py       # Quiz session logic
│       │   └── rankings.py   # Global leaderboard
│       └── schemas/          # Pydantic request/response models
└── frontend/
    ├── vite.config.ts        # Dev proxy: /api → localhost:8000
    └── src/
        ├── App.tsx           # Root component, route state
        ├── types/            # Shared TypeScript types
        ├── components/       # AnswerOption, Timer, Navigation, LeaderboardTable
        ├── pages/            # LandingPage, QuizPage, LeaderboardPage
        ├── hooks/
        │   ├── useAuth.ts    # Auth state + Google login
        │   └── useQuiz.ts    # Quiz state machine + timer
        ├── services/api.ts   # Fetch wrapper for all endpoints
        └── styles/
            ├── tokens.css    # Design system variables
            └── global.css    # Base styles
```

## Game mechanics

- **60 seconds** to identify as many peaks as possible
- **100 points** per correct answer
- **+5 bonus seconds** for a correct answer in the final 10 seconds
- Wrong answer: all options lock, advance to next question after 600ms
- Correct answer: advance after 400ms
- Questions are drawn from the full peak pool — no hard limit on how many you can answer in a session
- Final score is saved to the global leaderboard if you're logged in

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/auth/google/login` | Redirect to Google OAuth |
| GET | `/api/auth/google/callback` | OAuth callback |
| GET | `/api/auth/me` | Current user info |
| POST | `/api/auth/logout` | Clear auth cookie |
| POST | `/api/quiz/start` | Start session, return first 10 questions |
| GET | `/api/quiz/next/{session_id}` | Fetch next unseen question |
| POST | `/api/quiz/answer` | Submit answer, get result + score |
| POST | `/api/quiz/finish` | End session, save best score, return rank |
| GET | `/api/rankings?limit=50` | Global leaderboard |

## Other tasks

```bash
task backend:lint     # mypy type-check
task frontend:build   # production build (tsc + vite)
```
