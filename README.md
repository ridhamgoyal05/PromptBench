# PromptBench 🧠⚖️

An end-to-end evaluation platform to measure how job candidates collaborate with AI assistants to solve open-ended business problems.

---

## 📌 Product Thesis

Modern hiring evaluates not just whether candidates reach an answer, but **how they use AI to get there**:
- Do they ask targeted clarifying questions before jumping to conclusions?
- Do they critically iterate and refine their approach rather than accepting the first output?
- Do they catch AI hallucinations and verify claims against given ground-truth facts?
- Do they synthesize data into clear, actionable, and well-justified recommendations?

Unlike traditional coding interview platforms (LeetCode, HackerRank), **PromptBench** provides a standardized benchmark environment for evaluating real-time human-AI reasoning workflows.

---

## 🔒 Core Architectural Guarantee: Dual-Agent Isolation

The system maintains strict architectural isolation between two distinct AI roles:

```
Browser (React + Tailwind)
   │
   │  HTTPS (REST + JWT)
   ▼
FastAPI Backend
   │
   ├── /api/auth/*          → User registration & JWT authentication
   ├── /api/questions/*     → Fetch public case studies & contexts
   ├── /api/submissions/*   → Session lifecycle & interactive chat turns
   │       │
   │       ├──► Helper AI (Claude) ─── Public Context ONLY
   │       │                          (Zero access to rubric or ground truth)
   │       │
   │       └──► On Submit: Judge AI (Claude) ─── Rubric + Ground Truth + Full Transcript
   │
   └── /api/evaluations/*   → Dimension-level score breakdown & justifications
   │
   ▼
PostgreSQL Database (Neon / Supabase)
```

- **Helper AI (Candidate Assistant):** Scoped strictly to public case prompt and context data with zero knowledge of the hidden rubric or ground-truth solutions.
- **Judge AI (Server-Side Evaluator):** Triggered only upon final answer submission to evaluate the full transcript against the hidden rubric and ground-truth notes.

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | React (Vite) + Tailwind CSS | Interactive chat workspace, answer editor, score dashboard |
| **Backend** | Python + FastAPI + SQLAlchemy | REST APIs, session management, LLM orchestration |
| **Database** | PostgreSQL (Neon / Supabase) | Relational persistence of cases, transcripts, and scores |
| **Authentication** | JWT (`python-jose`) + bcrypt (`passlib`) | Stateless token authentication & password hashing |
| **AI Provider** | Anthropic Claude (`claude-sonnet-4-6`) | Powers Helper and Judge roles independently |
| **Deployment** | Vercel (Frontend) + Render/Railway (Backend) | Cloud deployment targets |

---

## 📊 Default Scoring Rubric & Anti-Gaming

### Weighted Evaluation Dimensions (0–10 Scale)
1. **Clarifying Questions (20%):** Assesses whether the candidate asks pertinent questions before proposing a solution.
2. **Iteration Quality (25%):** Measures prompt refinements and critical follow-ups across multiple turns.
3. **Hallucination Catching (25%):** Tests candidate detection of incorrect or distractor AI statements.
4. **Final Answer Quality (30%):** Evaluates if the recommendation is correct, data-grounded, and viable.

### Automated Anti-Gaming Heuristics
Run server-side prior to invoking the Judge LLM:
- **Near-Zero Conversation:** Flags sessions submitted with fewer than 2 conversational turns.
- **Too-Fast Submission:** Flags submissions completed in under 30 seconds from session initiation.
- **Pre-Formed Text Dump:** Flags cases where turn 1 exceeds 500 characters and mirrors the final answer.

---

## 🧪 Worked Example: "Sudden Churn Spike"

- **Problem Prompt:** "Our SaaS product's monthly churn jumped from 4% to 9% last month. Diagnose the likely cause and recommend one action using the dataset provided."
- **Context Dataset:** Synthetic dataset mixing survey responses and usage stats with a pricing complaint distractor and a feature removal signal.
- **Ground Truth:** The feature removal caused the churn; pricing complaints represent a minority vocal distractor.
- **High-Scoring Candidate Interaction:**
  1. Requests correlation breakdown between churn cohorts and plan pricing.
  2. Notices usage drops immediately following feature deprecation and asks the AI to analyze usage dates.
  3. Catches AI distractor summaries and focuses final recommendation on reinstating the removed feature.

---

## 📂 Repository Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI entrypoint
│   │   ├── db.py                 # DB connection and session setup
│   │   ├── auth_utils.py         # JWT tokens & bcrypt hashing
│   │   ├── models/models.py      # SQLAlchemy schema (5 tables)
│   │   ├── schemas/schemas.py    # Pydantic request/response schemas
│   │   ├── routers/              # Auth, Questions, Submissions, Evaluations
│   │   ├── services/             # candidate_llm.py, judge_llm.py, anti_gaming.py
│   │   └── prompts/              # Candidate and Judge system prompt templates
│   ├── requirements.txt          # Python dependencies
│   └── .env.example
│
└── frontend/
    ├── src/
    │   ├── api/client.js         # Axios client with JWT interceptor
    │   ├── pages/                # Login, Signup, QuestionList, CaseWorkspace, ScoreDashboard
    │   ├── components/           # ChatPane, ScoreBreakdown, TranscriptViewer
    │   ├── App.jsx               # React Router configuration
    │   └── main.jsx
    ├── package.json
    └── tailwind.config.js
```

---

## 🚀 Getting Started

### 1. Database Setup
Execute the table schemas in your PostgreSQL database instance:
```sql
CREATE TABLE users (id SERIAL PRIMARY KEY, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, name TEXT, created_at TIMESTAMP DEFAULT NOW());
CREATE TABLE questions (id SERIAL PRIMARY KEY, title TEXT NOT NULL, category TEXT NOT NULL, prompt_text TEXT NOT NULL, context_data TEXT NOT NULL, ground_truth_notes TEXT NOT NULL, difficulty TEXT NOT NULL, rubric_json JSONB NOT NULL, created_at TIMESTAMP DEFAULT NOW());
CREATE TABLE submissions (id SERIAL PRIMARY KEY, user_id INTEGER REFERENCES users(id), question_id INTEGER REFERENCES questions(id), status TEXT DEFAULT 'in_progress', final_answer_text TEXT, started_at TIMESTAMP DEFAULT NOW(), submitted_at TIMESTAMP);
CREATE TABLE transcript_turns (id SERIAL PRIMARY KEY, submission_id INTEGER REFERENCES submissions(id), turn_index INTEGER NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL, created_at TIMESTAMP DEFAULT NOW());
CREATE TABLE evaluations (id SERIAL PRIMARY KEY, submission_id INTEGER REFERENCES submissions(id), overall_score INTEGER, dimension_scores_json JSONB, judge_reasoning TEXT, anti_gaming_flags JSONB, created_at TIMESTAMP DEFAULT NOW());
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env`:
```env
DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<dbname>
ANTHROPIC_API_KEY=your_anthropic_api_key
JWT_SECRET=your_long_random_jwt_secret_key
```

Start backend server:
```bash
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
```

Create `frontend/.env`:
```env
VITE_API_BASE_URL=http://localhost:8000/api
```

Start development server:
```bash
npm run dev
```

---

## ⚠️ Known Limitations

- **LLM Non-Determinism:** Minor score variance across repeated runs on identical transcripts; mitigated using low temperature settings ($T \le 0.2$) and strict citation requirements.
- **Heuristic Anti-Gaming:** Heuristics serve as transparency signals rather than hard blocks.
- **Case Bank Expansion:** Ships with core seed cases with active work ongoing to expand domain scenarios.

---

