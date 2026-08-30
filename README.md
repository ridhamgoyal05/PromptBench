# PromptBench
A dual-agent interview preparation platform that evaluates how candidates leverage AI assistants to solve open-ended business cases, featuring architecturally isolated Helper and Judge LLMs.    
An end-to-end evaluation and interview preparation platform designed to measure how job candidates collaborate with AI assistants to solve open-ended, unstructured business problems.

---

## 📌 Product Thesis

Modern hiring evaluates not just whether candidates reach an answer, but **how they use AI to get there**:
- Do they ask targeted clarifying questions before jumping to conclusions?
- Do they critically iterate and refine their approach rather than accepting the first output?
- Do they catch AI hallucinations and verify claims against given ground-truth facts?
- Do they synthesize data into clear, actionable, and well-justified recommendations?

Unlike traditional coding interview platforms (LeetCode, HackerRank), **PromptBench** provides a standardized benchmark environment for evaluating real-time human-AI reasoning workflows.

---

## 🔒 Core Architectural Guarantee: Air-Gapped Dual-Agent Isolation

The system maintains strict architectural isolation between two distinct AI roles:

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
* **Helper AI (Candidate Assistant):** Scoped strictly to public case prompt and context data. It operates with zero knowledge of the hidden rubric or ground-truth solutions, eliminating prompt injection risks.
* **Judge AI (Server-Side Evaluator):** Triggered only upon final answer submission. It ingests the complete interaction transcript, final response, hidden rubric, and ground-truth notes to return structured, evidence-grounded JSON evaluations.

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
3. **Hallucination Catching (25%):** Tests the candidate’s ability to detect and rectify incorrect or distractor AI statements[cite: 1].
4. **Final Answer Quality (30%):** Evaluates whether the final recommendation is correct, grounded in case data, and operationally viable[cite: 1].

### Automated Anti-Gaming Heuristics[cite: 1]
Run server-side prior to invoking the Judge LLM[cite: 1]:
* ⚠️ **Near-Zero Conversation:** Flags sessions submitted with fewer than 2 conversational turns[cite: 1].
* ⚠️ **Too-Fast Submission:** Flags submissions completed in under 30 seconds from session initiation[cite: 1].
* ⚠️ **Pre-Formed Text Dump:** Flags cases where turn 1 exceeds 500 characters and mirrors the final answer[cite: 1].

---

## 🧪 Worked Example: "Sudden Churn Spike"

* **Problem Prompt:** "Our SaaS product's monthly churn jumped from 4% to 9% last month. Diagnose the likely cause and recommend one action using the dataset provided."[cite: 1]
* **Context Dataset:** Contains a mix of survey responses and usage stats with a pricing complaint distractor and a correlation with a recent feature removal[cite: 1].
* **Ground Truth:** The feature removal caused the churn; the pricing complaints represent a minority vocal distractor[cite: 1].
* **High-Scoring Candidate Interaction:**
  1. Requests correlation breakdown between churn cohorts and plan pricing (tests pricing hypothesis)[cite: 1].
  2. Notices usage drops immediately following the feature deprecation and asks the AI to analyze usage dates[cite: 1].
  3. Catches AI distractor summaries and focuses final recommendation on reinstating the removed feature or deploying an immediate migration tool[cite: 1].

---

## 📂 Repository Structure

.
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI entrypoint[cite: 1]
│   │   ├── db.py                 # DB connection and session setup[cite: 1]
│   │   ├── auth_utils.py         # JWT tokens & bcrypt hashing[cite: 1]
│   │   ├── models/models.py      # SQLAlchemy schema (5 tables)[cite: 1]
│   │   ├── schemas/schemas.py    # Pydantic request/response schemas[cite: 1]
│   │   ├── routers/              # Auth, Questions, Submissions, Evaluations[cite: 1]
│   │   ├── services/             # candidate_llm.py, judge_llm.py, anti_gaming.py[cite: 1]
│   │   └── prompts/              # Candidate and Judge system prompt templates[cite: 1]
│   ├── requirements.txt          # Python dependencies[cite: 1]
│   └── .env.example
│
└── frontend/
├── src/
│   ├── api/client.js         # Axios client with JWT interceptor[cite: 1]
│   ├── pages/                # Login, Signup, QuestionList, CaseWorkspace, ScoreDashboard[cite: 1]
│   ├── components/           # ChatPane, ScoreBreakdown, TranscriptViewer[cite: 1]
│   ├── App.jsx               # React Router configuration[cite: 1]
│   └── main.jsx
├── package.json
└── tailwind.config.js[cite: 1]

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL database instance (local or hosted via Neon/Supabase)[cite: 1]
- Anthropic API Key[cite: 1]

### 1. Database Setup
Execute the table schemas in your PostgreSQL database instance[cite: 1]:
```sql
CREATE TABLE users (id SERIAL PRIMARY KEY, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, name TEXT, created_at TIMESTAMP DEFAULT NOW());
CREATE TABLE questions (id SERIAL PRIMARY KEY, title TEXT NOT NULL, category TEXT NOT NULL, prompt_text TEXT NOT NULL, context_data TEXT NOT NULL, ground_truth_notes TEXT NOT NULL, difficulty TEXT NOT NULL, rubric_json JSONB NOT NULL, created_at TIMESTAMP DEFAULT NOW());
CREATE TABLE submissions (id SERIAL PRIMARY KEY, user_id INTEGER REFERENCES users(id), question_id INTEGER REFERENCES questions(id), status TEXT DEFAULT 'in_progress', final_answer_text TEXT, started_at TIMESTAMP DEFAULT NOW(), submitted_at TIMESTAMP);
CREATE TABLE transcript_turns (id SERIAL PRIMARY KEY, submission_id INTEGER REFERENCES submissions(id), turn_index INTEGER NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL, created_at TIMESTAMP DEFAULT NOW());
CREATE TABLE evaluations (id SERIAL PRIMARY KEY, submission_id INTEGER REFERENCES submissions(id), overall_score INTEGER, dimension_scores_json JSONB, judge_reasoning TEXT, anti_gaming_flags JSONB, created_at TIMESTAMP DEFAULT NOW());
[cite: 1]2. Backend SetupBashcd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
[cite: 1]Create backend/.env[cite: 1]:Code snippetDATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<dbname>
ANTHROPIC_API_KEY=your_anthropic_api_key
JWT_SECRET=your_long_random_jwt_secret_key
[cite: 1]Start backend server[cite: 1]:Bashuvicorn app.main:app --reload --port 8000
[cite: 1]3. Frontend SetupBashcd frontend
npm install
[cite: 1]Create frontend/.env[cite: 1]:Code snippetVITE_API_BASE_URL=http://localhost:8000/api
[cite: 1]Start development server[cite: 1]:Bashnpm run dev
[cite: 1]⚠️ Known LimitationsLLM Non-Determinism: Minor score variance may occur across repeated runs on identical transcripts; mitigated using low temperature settings ($T \le 0.2$) and strict citation requirements[cite: 1].Heuristic Anti-Gaming: Heuristics serve as transparency signals rather than hard blocks[cite: 1].Case Bank Expansion: Currently ships with core seed cases; active work is underway to expand domain scenarios across data diagnosis, strategy, and customer reasoning[cite: 1].
