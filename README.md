# Frederick Fire & Safety Chatbot

A memory-enabled chatbot with user authentication, conversation persistence, and Claude AI integration.

## Architecture

```
Backend (FastAPI + SQLite)     Frontend (Vite + React)
       ↓                              ↓
   /api/auth/*                   Login/Register
   /api/chat/*                   Chat Interface
       ↓                              ↓
   SQLite DB                     localStorage (token)
   - users                       
   - conversations              
   - messages                   
   - user_profiles              
```

## Quick Start

### 1. Backend Setup

```bash
cd chatbot-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run the server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd chatbot-frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

### 3. Test It

1. Open http://localhost:5173
2. Register a new account (email + password)
3. Log in
4. Start chatting!

## API Endpoints

### Auth
- `POST /api/auth/register` - Create account
- `POST /api/auth/login` - Get JWT token
- `GET /api/auth/me` - Get current user

### Chat
- `GET /api/chat/conversations` - List conversations
- `POST /api/chat/conversations` - Create conversation
- `GET /api/chat/conversations/{id}` - Get conversation with messages
- `DELETE /api/chat/conversations/{id}` - Delete conversation
- `POST /api/chat/conversations/{id}/messages` - Send message, get response
- `POST /api/chat/message` - Quick send (creates conversation if needed)

### Profile
- `GET /api/chat/profile` - Get user profile
- `PATCH /api/chat/profile` - Update profile

## Configuration

Edit `.env` in the backend:

```env
# Database (SQLite for dev, Postgres for prod)
DATABASE_URL=sqlite:///./frederick_fire.db

# Security - generate with: openssl rand -hex 32
SECRET_KEY=your_secret_key_here

# Claude API
ANTHROPIC_API_KEY=your_api_key_here
CLAUDE_MODEL=claude-sonnet-4-20250514

# Context settings
MAX_CONVERSATION_HISTORY=20
```

## Key Features

1. **Email-based auth** - No username confusion, just email + password
2. **JWT tokens** - Stateless auth, token stored in localStorage
3. **Password visibility toggle** - Show/hide password while typing
4. **Conversation persistence** - All messages saved to database
5. **Context injection** - User profile info included in Claude prompts
6. **Demo mode** - Works without API key (returns placeholder responses)

## Project Structure

```
chatbot-backend/
├── app/
│   ├── __init__.py
│   ├── auth.py          # Argon2 hashing, JWT, get_current_user
│   ├── config.py        # Settings from env
│   ├── database.py      # SQLModel + SQLite
│   ├── main.py          # FastAPI app, CORS, routers
│   ├── models.py        # User, Conversation, Message, UserProfile
│   ├── routers/
│   │   ├── auth.py      # /api/auth/* endpoints
│   │   ├── chat.py      # /api/chat/* endpoints
│   │   └── health.py    # /api/health
│   └── schemas/
│       ├── auth.py      # LoginRequest, Token
│       ├── chat.py      # Message, Conversation, Profile schemas
│       └── user.py      # UserCreate, UserRead
├── requirements.txt
└── .env.example

chatbot-frontend/
├── src/
│   ├── api.js           # Centralized API calls
│   ├── App.jsx          # Main app, auth state
│   ├── main.jsx         # Entry point
│   ├── index.css        # Global styles
│   └── components/
│       ├── LoginForm.jsx
│       ├── RegisterForm.jsx
│       └── ChatInterface.jsx
├── index.html
├── package.json
└── vite.config.js
```

## Next Steps

1. **Add pricing lookup** - Scrape or API call to find fire extinguisher prices
2. **Enhance memory** - Extract and store user preferences from conversations
3. **Move to Postgres** - Change DATABASE_URL when ready for production
4. **Add email verification** - Optional for production
5. **Plug in your HRM/RL architecture** - Replace `call_claude()` with your custom memory system

## License

MIT
