# KIP Platform — Setup & Run Guide
# ===================================
# Kwacha Intelligence Platform v1.0
# React + FastAPI + PostgreSQL + ChromaDB

## QUICK START (Development)

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL 16 (or Docker)
- Git

---

## STEP 1: Project Structure Setup

Place your existing KIP files in the right locations:

```
kip-platform/
├── backend/
│   └── kip_corpus/       ← Copy your chroma_db and supplements here
├── ml_models/
│   ├── gdp_growth_lstm_model.h5        ← YOUR LSTM MODEL
│   └── inflation_lstm_model.h5         ← YOUR LSTM MODEL
└── data/
    └── consumer-price_index.csv        ← YOUR ZAMSTATS CSV
```

---

## STEP 2: Backend Setup

```bash
cd kip-platform/backend

# Copy your env file
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate       # Windows
source .venv/bin/activate    # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Start the backend
uvicorn main:app --reload --port 8000
```

Backend runs at: http://localhost:8000
API docs at:     http://localhost:8000/docs

---

## STEP 3: Database Setup

Option A — Local PostgreSQL:
```bash
# Create database (PostgreSQL must be running)
createdb kip_db
createuser kip --pwprompt   # password: kip_password

# Tables auto-created on first backend start
```

Option B — Docker PostgreSQL only:
```bash
docker run -d \
  --name kip_postgres \
  -e POSTGRES_DB=kip_db \
  -e POSTGRES_USER=kip \
  -e POSTGRES_PASSWORD=kip_password \
  -p 5432:5432 \
  postgres:16-alpine
```

---

## STEP 4: Frontend Setup

```bash
cd kip-platform/frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Frontend runs at: http://localhost:5173

---

## STEP 5: ngrok Testing (for WhatsApp + sharing with testers)

```bash
# Install ngrok: https://ngrok.com/download

# Expose your backend (in a new terminal)
ngrok http 8000

# You'll get a URL like: https://abc123.ngrok.io
# Use this as your Twilio webhook URL:
# https://abc123.ngrok.io/api/whatsapp/webhook
```

### Twilio WhatsApp Setup:
1. Go to twilio.com → Messaging → Try it Out → WhatsApp
2. Set webhook URL to: https://YOUR-NGROK-URL/api/whatsapp/webhook
3. Add to .env: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
4. Restart backend

---

## STEP 6: Link ChromaDB Knowledge Base

Copy your existing ChromaDB:
```bash
cp -r /path/to/your/kip_corpus ./backend/kip_corpus
```

Or run the existing KIP knowledge base builder:
```bash
cd backend
python kip_vector_db.py        # from your existing scripts
python kip_add_supplements.py  # from your existing scripts
```

---

## STEP 7: Add LSTM Models

```bash
# Copy your trained models
cp /path/to/gdp_growth_lstm_model.h5    ./ml_models/
cp /path/to/inflation_lstm_model.h5     ./ml_models/

# Install TensorFlow for actual LSTM inference
pip install tensorflow==2.15.0

# Without TF, KIP uses statistical fallback forecasts (still works)
```

---

## FULL DOCKER DEPLOYMENT

```bash
# Set environment variables
export ANTHROPIC_API_KEY=sk-ant-your-key

# Build and run everything
docker-compose up --build

# Access at:
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# API Docs: http://localhost:8000/docs
```

---

## RAILWAY CLOUD DEPLOYMENT

1. Push to GitHub
2. Go to railway.app → New Project → Deploy from GitHub
3. Add services: PostgreSQL (one click), Backend, Frontend
4. Set environment variables in Railway dashboard:
   - ANTHROPIC_API_KEY
   - DATABASE_URL (Railway auto-fills this)
   - TWILIO_* (when ready)

---

## ENVIRONMENT VARIABLES REFERENCE

| Variable | Required | Description |
|----------|----------|-------------|
| ANTHROPIC_API_KEY | ✅ | Your Claude API key |
| DATABASE_URL | ✅ | PostgreSQL connection string |
| CLAUDE_MODEL | Optional | Default: claude-haiku-4-5-20251001 |
| CHROMA_DB_PATH | Optional | Path to ChromaDB directory |
| LSTM_GDP_MODEL_PATH | Optional | Path to GDP LSTM .h5 file |
| LSTM_INFLATION_MODEL_PATH | Optional | Path to Inflation LSTM .h5 file |
| CPI_CSV_PATH | Optional | Path to ZamStats CPI CSV |
| TWILIO_ACCOUNT_SID | Optional | For WhatsApp bot |
| TWILIO_AUTH_TOKEN | Optional | For WhatsApp bot |

---

## ARCHITECTURE OVERVIEW

```
User (Web)          User (WhatsApp)
    │                     │
    ▼                     ▼
React Frontend       Twilio Webhook
(Vite + Tailwind)   (POST /api/whatsapp/webhook)
    │                     │
    └──────┬──────────────┘
           │
           ▼
    FastAPI Backend (Python)
    ├── Intent Classifier → detects response type
    ├── KIP Brain (RAG) → ChromaDB + Claude API
    ├── LSTM Service → GDP + Inflation forecasts
    ├── CPI Service → ZamStats commodity prices
    └── Business Journey → logs + KIP analysis
           │
    ┌──────┴──────────────┐
    │                     │
    ▼                     ▼
PostgreSQL            ChromaDB
(users, messages,    (KIP knowledge base:
 business logs)       supplements, textbooks,
                       business plans)
```

---

## ADDING MORE KNOWLEDGE TO KIP

```bash
# Add new business plans (from your existing scripts)
python kip_bizplan_adapter.py --pdf-dir ./downloaded_pdfs/

# Add new ZamStats data
python kip_cpi_predictor.py --csv new_data.csv

# Rebuild vector DB after adding supplements
python kip_add_supplements.py
python kip_vector_db.py
```

---

## WHATSAPP COMMANDS REFERENCE

Users can message KIP via WhatsApp with:
- Any business question → KIP responds with formatted advice
- "LOG [update]" → starts business journey log (future)
- "DASHBOARD" → KIP sends key economic indicators (future)

---

*KIP — Built for Zambia. Powered by AI.*
