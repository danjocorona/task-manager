# TaskFlow — Full Stack Task Manager

A full stack task management web application built from scratch with a Python/FastAPI
backend, SQLite database, JWT authentication, and a vanilla JavaScript frontend.
No frameworks. No shortcuts. Every layer of the stack written by hand.

**[▶ Live Demo](https://danjocorona.github.io/task-manager/)**

---

## Overview

TaskFlow was built as a portfolio project to demonstrate full stack engineering skills
across the entire web development stack — database modeling, REST API design,
authentication, and a dynamic frontend — without relying on frameworks to do the
heavy lifting.

---

## Features

- **JWT Authentication** — register, login, and logout with bcrypt password hashing and signed JSON Web Tokens
- **Full Task CRUD** — create, read, update, and delete tasks with title, description, due date, priority, and status
- **Dashboard Summary** — live counts of total, to-do, in-progress, done, and overdue tasks
- **Filtering** — filter tasks by status and priority via query parameters on the API
- **Overdue Detection** — tasks past their due date are flagged automatically with a warning indicator
- **Auth Guard** — unauthenticated users are redirected to login; expired tokens are detected and cleared
- **XSS Protection** — all user content is escaped before injection into the DOM
- **Responsive UI** — works on mobile, tablet, and desktop
- **Interactive Docs** — FastAPI auto-generates a live API explorer at `/docs`

---

## Tech Stack

| Layer      | Technology                                      |
|------------|-------------------------------------------------|
| Backend    | Python 3, FastAPI, Uvicorn                      |
| Database   | PostgreSQL (production), SQLite (local dev)     |
| Auth       | JWT (python-jose), bcrypt password hashing      |
| Frontend   | Vanilla HTML5, CSS3, JavaScript (ES6+)          |
| Fonts      | Google Fonts — Syne, JetBrains Mono, Inter      |
| Deployment | Railway (backend), GitHub Pages (frontend)      |

---

## Project Structure

```
task-manager/
├── backend/
│   ├── main.py            # FastAPI app — all API routes (auth + tasks)
│   ├── models.py          # SQLModel database tables and Pydantic schemas
│   ├── auth.py            # bcrypt hashing, JWT creation and decoding
│   ├── database.py        # Database engine, session management (PostgreSQL/SQLite)
│   └── requirements.txt   # Python dependencies
├── frontend/
│   ├── index.html         # Login and register page
│   ├── dashboard.html     # Main task dashboard
│   ├── css/
│   │   └── style.css      # All styles — shared across both pages
│   └── js/
│       ├── auth.js        # Login, register, token storage, tab switching
│       └── tasks.js       # Task CRUD, filters, modals, auth guard
└── README.md
```

---

## API Reference

All task endpoints require a valid JWT token in the `Authorization: Bearer <token>` header.

### Auth

| Method | Endpoint          | Auth | Description                        |
|--------|-------------------|------|------------------------------------|
| POST   | `/auth/register`  | No   | Create a new user account          |
| POST   | `/auth/login`     | No   | Login and receive a JWT token      |
| GET    | `/auth/me`        | Yes  | Get the current authenticated user |

### Tasks

| Method | Endpoint                    | Auth | Description                          |
|--------|-----------------------------|------|--------------------------------------|
| POST   | `/tasks`                    | Yes  | Create a new task                    |
| GET    | `/tasks`                    | Yes  | Get all tasks (supports filtering)   |
| GET    | `/tasks/{id}`               | Yes  | Get a single task by ID              |
| PATCH  | `/tasks/{id}`               | Yes  | Partially update a task              |
| DELETE | `/tasks/{id}`               | Yes  | Delete a task                        |
| GET    | `/tasks/summary/dashboard`  | Yes  | Get task count summary               |

**Filter parameters for `GET /tasks`:**
```
?status_filter=todo|in_progress|done
?priority_filter=low|medium|high
```

---

## How It Works

### Authentication Flow
1. User registers — password is hashed with bcrypt and stored. Plain text is never saved.
2. User logs in — credentials are verified, a signed JWT is returned with a 24-hour expiry.
3. Frontend stores the token in `localStorage` and attaches it as a `Bearer` token on every subsequent request.
4. FastAPI's `get_current_user` dependency decodes the JWT, looks up the user, and injects them into any protected route.
5. On logout, `localStorage` is cleared and the user is redirected to login.

### Database Models
Two tables — `User` and `Task` — defined with SQLModel which merges SQLAlchemy
table definitions with Pydantic validation schemas. Tasks have a foreign key to their
owner's User id, enforcing that users can only access their own tasks.

### Separation of Concerns
The backend and frontend are completely decoupled. The backend is a pure JSON API
that knows nothing about the UI. The frontend is static HTML/CSS/JS that knows nothing
about the database. They communicate only through HTTP requests and JSON responses.
This means the backend could be reused with a React or mobile frontend without any changes.

### Frontend Architecture
- **`auth.js`** handles the login page: tab switching, form validation, fetch calls to `/auth/register` and `/auth/login`, token storage, and redirecting logged-in users away from the login page.
- **`tasks.js`** handles the dashboard: an auth guard at the top redirects unauthenticated users, a shared `apiFetch()` wrapper attaches the token to every request, and separate functions handle loading, rendering, creating, editing, and deleting tasks.
- **CSS classes as state** — JavaScript adds and removes classes like `status-done`, `priority-high`, and `hidden`. CSS rules target those classes to apply visual changes. This keeps styling out of JavaScript entirely.

---

## Running Locally

**Requirements:** Python 3.10+

```bash
# Clone the repo
git clone https://github.com/danjocorona/task-manager
cd task-manager

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows

# Install dependencies
pip install -r backend/requirements.txt

# Start the backend
cd backend
uvicorn main:app --reload
```

The API will be running at `http://127.0.0.1:8000`.
Interactive API docs available at `http://127.0.0.1:8000/docs`.

Open `frontend/index.html` with VS Code Live Server or any static file server.

---

## Deployment

### Backend — Railway
The FastAPI backend is deployed on [Railway](https://railway.app) (free tier) at `https://task-manager-production-fa56.up.railway.app`

```bash
# From the backend/ folder
railway login
railway init
railway up
```

Set the start command in Railway to:
```
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Frontend — GitHub Pages
The frontend is static HTML/CSS/JS hosted on GitHub Pages.
Update the `API` constant in both `auth.js` and `tasks.js` to point to your
Railway URL before deploying:

```js
const API = 'https://task-manager-production-fa56.up.railway.app';
```

---

## Security Notes

- Passwords are hashed with bcrypt — plain text passwords are never stored or logged
- JWT tokens are signed with a secret key and expire after 24 hours
- All task endpoints verify ownership — users cannot read, edit, or delete other users' tasks
- User content is escaped with `escapeHtml()` before DOM injection to prevent XSS attacks
- CORS is configured in FastAPI — restrict `allow_origins` to your frontend URL in production

---

## License

This project is open source and available under the [MIT License](LICENSE).
