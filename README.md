# Constructure AI - Email Assistant

An AI-powered email assistant that helps manage your Gmail inbox using natural language commands. Chat naturally to read, reply, delete, and organize emails.

## 🌐 Live Demo

| Service | URL |
|---------|-----|
| **Frontend** | [https://constructure-ai.vercel.app](https://constructure-ai.vercel.app) |
| **Backend API** | [https://constructure-ai-backend.onrender.com](https://constructure-ai-backend.onrender.com) |

> ⚠️ **Note:** Backend is deployed on Render's free tier. Expect ~50s cold start delay on first request after inactivity.

---

## Features

- **Google OAuth2 Login** - Secure authentication with Gmail access
- **Read Emails** - Fetch and view emails with AI-generated summaries
- **Generate Replies** - Get context-aware response suggestions
- **Send Emails** - Send replies directly from the chat
- **Delete Emails** - Remove emails by sender, subject, or number
- **Smart Categorization** - AI groups emails into Work, Personal, Promotions, Urgent
- **Daily Digest** - Summarized overview of your inbox

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | Next.js 15, TypeScript, Tailwind CSS, Zustand |
| **Backend** | FastAPI, Python 3.11, Pydantic, Structlog |
| **AI Provider** | Google Gemini (free) or OpenAI GPT-4o-mini |
| **Auth** | Google OAuth 2.0, JWT (python-jose) |
| **APIs** | Gmail API, Google Generative AI |
| **Hosting** | Vercel (frontend), Render (backend) |

---

## Setup Instructions

### Prerequisites

- Node.js 18+
- Python 3.11+
- Google Cloud Project with Gmail API enabled
- Gemini API Key (free) or OpenAI API Key

### 1. Clone Repository

```bash
git clone https://github.com/Karanpal97/Constructure-AI.git
cd Constructure-AI
```

### 2. Configure Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable **Gmail API** from APIs & Services > Library
4. Configure **OAuth Consent Screen**:
   - User Type: External
   - Add test users (your Gmail addresses)
   - Add scopes:
     ```
     https://www.googleapis.com/auth/gmail.readonly
     https://www.googleapis.com/auth/gmail.send
     https://www.googleapis.com/auth/gmail.modify
     https://www.googleapis.com/auth/userinfo.email
     https://www.googleapis.com/auth/userinfo.profile
     ```
5. Create **OAuth 2.0 Client ID** (Web application):
   - Authorized redirect URIs:
     - `http://localhost:8000/auth/callback` (local)
     - `https://your-backend.onrender.com/auth/callback` (production)
6. Copy **Client ID** and **Client Secret**

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp env.example .env
```

Edit `backend/.env`:

```env
# Google OAuth (Required)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback

# Frontend URL
FRONTEND_URL=http://localhost:3000

# JWT Secret (Required - min 32 characters)
JWT_SECRET_KEY=your-super-secret-key-at-least-32-characters

# AI Provider: "gemini" (free) or "openai" (paid)
AI_PROVIDER=gemini

# Gemini API Key (Free) - Get from: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your-gemini-api-key

# OpenAI (Optional - only if AI_PROVIDER=openai)
OPENAI_API_KEY=sk-your-openai-key
```

Start backend:

```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cp env.example .env.local
```

Edit `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Start frontend:

```bash
npm run dev
```

App runs at `http://localhost:3000`

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Required |
|----------|-------------|:--------:|
| `GOOGLE_CLIENT_ID` | OAuth Client ID from Google Cloud | ✅ |
| `GOOGLE_CLIENT_SECRET` | OAuth Client Secret | ✅ |
| `GOOGLE_REDIRECT_URI` | OAuth callback URL | ✅ |
| `FRONTEND_URL` | Frontend URL for CORS/redirects | ✅ |
| `JWT_SECRET_KEY` | Secret for JWT tokens (32+ chars) | ✅ |
| `AI_PROVIDER` | `gemini` or `openai` | ✅ |
| `GEMINI_API_KEY` | Gemini API key (if using Gemini) | ✅* |
| `OPENAI_API_KEY` | OpenAI API key (if using OpenAI) | ✅* |

*One of GEMINI_API_KEY or OPENAI_API_KEY is required based on AI_PROVIDER

### Frontend (`frontend/.env.local`)

| Variable | Description | Required |
|----------|-------------|:--------:|
| `NEXT_PUBLIC_API_URL` | Backend API URL | ✅ |

---

## Deployment

### Frontend → Vercel

1. Push to GitHub
2. Import repo in [Vercel](https://vercel.com)
3. Set root directory: `frontend`
4. Add environment variable:
   - `NEXT_PUBLIC_API_URL` = `https://your-backend.onrender.com`
5. Deploy

### Backend → Render

1. Create Web Service in [Render](https://render.com)
2. Connect GitHub repo
3. Configure:
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add all environment variables from the table above
5. Update `GOOGLE_REDIRECT_URI` to use Render URL
6. Deploy

> **Important:** Add your Render backend URL to Google Cloud OAuth authorized redirect URIs.

---

## Usage Examples

| Action | Command |
|--------|---------|
| Read emails | "Show me my last 5 emails" |
| Search | "Find emails from John" |
| Reply | "Reply to email 2" |
| Send | "Send that reply" |
| Delete | "Delete email number 3" |
| Organize | "Categorize my inbox" |
| Summary | "Give me today's digest" |

---

## Assumptions & Known Limitations

1. **Cold Start Delay** - Backend on Render free tier sleeps after 15 min inactivity. First request takes ~50s.
2. **In-Memory Token Storage** - Google OAuth tokens stored in memory. Sessions lost on server restart.
3. **OAuth Testing Mode** - Google OAuth app in testing mode; only added test users can login.
4. **Gmail API Rate Limits** - Heavy usage may hit rate limits (retry logic included).
5. **Single Session** - One active session per user at a time.

---

## Project Structure

```
Constructure-AI/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app entry
│   │   ├── config.py        # Environment settings
│   │   ├── models.py        # Pydantic schemas
│   │   ├── routes/          # API endpoints
│   │   └── services/        # Business logic
│   ├── tests/               # Pytest tests
│   ├── requirements.txt
│   └── env.example
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js pages
│   │   ├── components/      # React components
│   │   ├── lib/             # API client
│   │   └── store/           # Zustand stores
│   ├── package.json
│   └── env.example
└── README.md
```

---

## Running Tests

```bash
cd backend
pytest tests/ -v
```

---

## License

Built for Constructure AI technical assessment.
