# Local Environment Setup Guide — PromptBench

This guide walks you through setting up and running PromptBench locally on your machine.

---

## Prerequisites

- **Python**: Version 3.10, 3.11, 3.12, or 3.13+
- **Node.js**: Version 18.x or 20.x LTS + `npm`
- **PostgreSQL**: Version 14, 15, or 16 (or use the built-in Windows portable setup script)
- **Anthropic API Key**: For real AI evaluations (optional if using mock mode `RUN_LLM_TESTS=false`)

---

## 1. Quick Start (Windows)

PromptBench includes helper batch scripts located in the `scripts/` directory and project root.

1. **Start PostgreSQL**:
   ```cmd
   scripts\start_postgres.bat
   ```
   *(On first run, this automatically downloads portable PostgreSQL 16 binaries to `backend/pgsql` and initializes the cluster).*

2. **Configure Environment Variables**:
   Copy `.env.example` templates in both `backend/` and `frontend/`:
   ```cmd
   copy backend\.env.example backend\.env
   copy frontend\.env.example frontend\.env
   ```

3. **Install Dependencies & Seed Database**:
   ```cmd
   cd backend
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   python seed.py
   cd ..
   ```

4. **Install Frontend Dependencies**:
   ```cmd
   cd frontend
   npm install
   cd ..
   ```

5. **Start Application**:
   Open two terminal windows (or double-click the scripts):
   - Terminal 1: `scripts\start_backend.bat` (Starts FastAPI on `http://localhost:8000`)
   - Terminal 2: `scripts\start_frontend.bat` (Starts React/Vite on `http://localhost:5173`)

6. **Open in Browser**:
   Navigate to [http://localhost:5173](http://localhost:5173) in your browser.

---

## 2. Manual / Linux & macOS Setup

### Step 1: PostgreSQL Setup
Ensure PostgreSQL is running locally on port `5432` with a database named `postgres` (or your preferred database name):
```bash
# macOS with Homebrew
brew services start postgresql@16

# Ubuntu/Debian
sudo systemctl start postgresql
```

### Step 2: Backend Setup
```bash
cd backend

# Create & activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your DATABASE_URL, ANTHROPIC_API_KEY, and JWT_SECRET_KEY

# Seed database with the 5 business case studies
python seed.py

# Start FastAPI server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Step 3: Frontend Setup
In a separate terminal:
```bash
cd frontend

# Configure environment
cp .env.example .env

# Install packages
npm install

# Start Vite dev server
npm run dev
```

---

## 3. Environment Variables Reference

### Backend (`backend/.env`)
| Variable | Description | Example / Default |
| :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection URI | `postgresql://postgres@localhost:5432/postgres` |
| `ANTHROPIC_API_KEY` | Anthropic Claude API Key | `sk-ant-api03-...` |
| `ANTHROPIC_MODEL` | Claude model identifier | `claude-3-5-sonnet-20241022` |
| `JWT_SECRET_KEY` | Secret for signing JWT tokens | `random-secure-32-char-string` |
| `RUN_LLM_TESTS` | Toggle live LLM calls (`false` uses deterministic mock responses) | `false` |

### Frontend (`frontend/.env`)
| Variable | Description | Default |
| :--- | :--- | :--- |
| `VITE_API_BASE_URL` | Backend REST API endpoint URL | `http://localhost:8000/api` |
