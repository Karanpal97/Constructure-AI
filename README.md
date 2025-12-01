# 🤖 Constructure AI - Email Assistant

An AI-powered email assistant that helps you manage your Gmail inbox with natural language commands. Built with FastAPI, Next.js, and OpenAI.

![Constructure AI](https://img.shields.io/badge/Constructure-AI-violet?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)

## 🌐 Live Demo

**Frontend (Vercel):** [https://constructure-ai.vercel.app](https://constructure-ai.vercel.app)

**Backend (Render):** [https://constructure-ai-backend.onrender.com](https://constructure-ai-backend.onrender.com)

## ✨ Features

### Core Features
- **🔐 Google OAuth2 Authentication** - Secure login with Gmail permissions
- **📧 Read Emails** - Fetch and view your last 5-50 emails with AI-generated summaries
- **✍️ Generate Replies** - Get context-aware, professional response suggestions
- **📤 Send Emails** - Send AI-generated or custom replies directly
- **🗑️ Delete Emails** - Delete emails by sender, subject, or reference number

### Bonus Features
- **🗣️ Natural Language Commands** - Type naturally, e.g., "Show me emails from John"
- **📊 Smart Categorization** - AI groups emails into Work, Personal, Promotions, Urgent
- **📋 Daily Digest** - Get a summarized overview of your inbox
- **🔄 Observability** - Structured logging with retry logic for resilience
- **🧪 Automated Tests** - Test suite for core functionality

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│   Next.js App   │────▶│   FastAPI API   │────▶│   Gmail API     │
│   (Vercel)      │     │   (Render)      │     │   (Google)      │
│                 │     │                 │     │                 │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │                 │
                        │   OpenAI API    │
                        │   (GPT-4o-mini) │
                        │                 │
                        └─────────────────┘
```

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Google OAuth2** - Authentication with Gmail
- **Gmail API** - Email operations (read, send, delete)
- **OpenAI GPT-4o-mini** - AI summaries and responses
- **Pydantic** - Data validation
- **Structlog** - Structured logging
- **Tenacity** - Retry logic for resilience
- **Jose (JWT)** - Token-based authentication

### Frontend
- **Next.js 15** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first styling
- **Framer Motion** - Smooth animations
- **Zustand** - State management
- **React Markdown** - Render markdown in chat
- **Lucide Icons** - Beautiful icons

## 📋 Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.11+
- **Google Cloud Project** with Gmail API enabled
- **OpenAI API Key**

## 🚀 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/constructure-ai.git
cd constructure-ai
```

### 2. Configure Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the **Gmail API**
4. Go to **APIs & Services > Credentials**
5. Click **Create Credentials > OAuth 2.0 Client IDs**
6. Configure the OAuth consent screen:
   - Add test users (e.g., `testingcheckuser1234@gmail.com`, `test@gmail.com`)
   - Add scopes:
     - `https://www.googleapis.com/auth/gmail.readonly`
     - `https://www.googleapis.com/auth/gmail.send`
     - `https://www.googleapis.com/auth/gmail.modify`
     - `https://www.googleapis.com/auth/userinfo.email`
     - `https://www.googleapis.com/auth/userinfo.profile`
7. Create OAuth 2.0 Client ID (Web application):
   - Authorized redirect URIs:
     - `http://localhost:8000/auth/callback` (development)
     - `https://your-backend-url.onrender.com/auth/callback` (production)
8. Download the credentials and note your **Client ID** and **Client Secret**

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp env.example .env
```

Edit `.env` with your values:

```env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback
FRONTEND_URL=http://localhost:3000
JWT_SECRET_KEY=your-super-secret-jwt-key-min-32-chars
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
```

Run the backend:

```bash
uvicorn app.main:app --reload
```

Backend will be available at `http://localhost:8000`

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment variables
cp env.example .env.local
```

Edit `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Run the frontend:

```bash
npm run dev
```

Frontend will be available at `http://localhost:3000`

### 5. Run Tests

```bash
cd backend
pytest tests/ -v
```

## 🚀 Deployment

### Deploy Frontend to Vercel

1. Push code to GitHub
2. Go to [Vercel](https://vercel.com)
3. Import your repository
4. Set environment variable:
   - `NEXT_PUBLIC_API_URL` = Your backend URL
5. Deploy!

### Deploy Backend to Render

1. Go to [Render](https://render.com)
2. Create a new **Web Service**
3. Connect your repository
4. Configure:
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables:
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `GOOGLE_REDIRECT_URI` (use Render URL)
   - `JWT_SECRET_KEY`
   - `OPENAI_API_KEY`
   - `FRONTEND_URL` (your Vercel URL)
6. Deploy!

**Important:** Update your Google Cloud OAuth redirect URIs to include the Render backend URL.

## 💬 Usage Examples

### Read Emails
- "Show me my last 5 emails"
- "Show emails from John"
- "Find emails about invoice"

### Reply to Emails
- "Reply to email 1"
- "Write a response to the email from Sarah"
- "Generate a professional reply"

### Delete Emails
- "Delete email number 3"
- "Delete the email from promotions"
- "Remove the latest email from newsletter"

### Organize
- "Categorize my inbox"
- "Give me today's email digest"
- "Show me urgent emails"

## 🔧 Environment Variables

### Backend

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID | ✅ |
| `GOOGLE_CLIENT_SECRET` | Google OAuth Client Secret | ✅ |
| `GOOGLE_REDIRECT_URI` | OAuth callback URL | ✅ |
| `FRONTEND_URL` | Frontend URL for CORS | ✅ |
| `JWT_SECRET_KEY` | Secret for JWT tokens (32+ chars) | ✅ |
| `OPENAI_API_KEY` | OpenAI API key | ✅ |
| `OPENAI_MODEL` | OpenAI model (default: gpt-4o-mini) | ❌ |
| `DEBUG` | Enable debug mode | ❌ |

### Frontend

| Variable | Description | Required |
|----------|-------------|----------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | ✅ |

## 📁 Project Structure

```
constructure-ai/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI application
│   │   ├── config.py         # Settings management
│   │   ├── models.py         # Pydantic models
│   │   ├── routes/
│   │   │   ├── auth.py       # Authentication endpoints
│   │   │   ├── emails.py     # Email operations
│   │   │   └── chat.py       # Chat/AI endpoints
│   │   └── services/
│   │       ├── auth.py       # OAuth service
│   │       ├── gmail.py      # Gmail API service
│   │       └── ai.py         # OpenAI service
│   ├── tests/
│   │   ├── test_auth.py
│   │   └── test_gmail.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── env.example
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx
│   │   │   ├── login/page.tsx
│   │   │   ├── dashboard/page.tsx
│   │   │   └── auth/callback/page.tsx
│   │   ├── components/
│   │   │   ├── ui/
│   │   │   ├── chat/
│   │   │   ├── auth/
│   │   │   └── layout/
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   └── utils.ts
│   │   └── store/
│   │       ├── auth.ts
│   │       └── chat.ts
│   ├── package.json
│   ├── tailwind.config.ts
│   └── env.example
└── README.md
```

## ⚠️ Known Limitations

1. **Token Storage**: Currently uses in-memory storage for Google tokens. For production, consider using Redis or a database.
2. **Single Session**: Each user can only have one active session at a time.
3. **Rate Limits**: Gmail API has rate limits; the app includes retry logic but may fail under heavy use.
4. **Test Mode**: Google OAuth app may be in "Testing" mode, limiting access to registered test users.

## 🔒 Security Considerations

- JWT tokens expire after 24 hours
- All API routes require authentication
- CORS is configured to only allow specified origins
- Sensitive data is never logged
- OAuth tokens are stored securely and refreshed automatically

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is built for the Constructure AI technical assessment.

## 🙏 Acknowledgments

- [OpenAI](https://openai.com) for the GPT API
- [Google](https://developers.google.com/gmail/api) for the Gmail API
- [Vercel](https://vercel.com) for frontend hosting
- [Render](https://render.com) for backend hosting

