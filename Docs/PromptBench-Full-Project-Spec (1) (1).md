# PromptBench — Full Project Specification

**Purpose of this document:** This is a complete build specification for an app called PromptBench. It contains everything needed to build the project end-to-end — architecture, database schema, API contracts, prompts, sample data, and folder structure. Follow it as the source of truth. Where a decision isn't specified, use standard, simple, well-documented conventions for the relevant framework rather than inventing something novel.

---

## 1. What This Project Is

**PromptBench** is a web platform that helps job candidates practice a specific interview skill: using an AI assistant effectively to solve open-ended business problems. Many companies now evaluate candidates not just on right/wrong answers, but on *how they use AI* — do they ask good clarifying questions, catch AI mistakes, iterate instead of accepting the first output, and arrive at a well-justified recommendation.

There is no widely-used practice tool for this skill today, unlike the saturated market of coding-practice sites (LeetCode, HackerRank).

### 1.1 Core product loop
1. A user logs in and picks a business case study (e.g. "diagnose why churn spiked").
2. They chat with an embedded **Helper AI** to work through the problem. The Helper AI knows only the case's public context — it has no access to the correct answer.
3. When ready, the user submits a final written answer.
4. A separate **Judge AI** privately grades the entire transcript + final answer against a hidden rubric and hidden ground-truth notes, and returns structured, per-dimension scores with reasoning.
5. The user sees a score breakdown dashboard.

### 1.2 The single most important design rule
**The Helper AI and Judge AI must be architecturally isolated.** They use different system prompts, are called separately, and the Helper AI is never given the rubric, the ground-truth notes, or any scoring information — at no point, under any circumstance. This is the core integrity guarantee of the whole product and must not be weakened for convenience (e.g. don't merge them into one call "to save an API request").

---

## 2. Tech Stack

| Layer | Choice |
|---|---|
| Frontend | React (Vite) + Tailwind CSS |
| Backend | Python + FastAPI + SQLAlchemy |
| Database | PostgreSQL (Neon or Supabase, free tier) |
| Auth | JWT tokens, passwords hashed with bcrypt (via `passlib`) |
| AI provider | Anthropic Claude API, model `claude-sonnet-4-6`, used for two separate roles (Helper, Judge) |
| Frontend deploy | Vercel |
| Backend deploy | Render or Railway |

Use these exact choices. Do not substitute a different framework or database unless explicitly told to — the rest of this spec assumes them.

---

## 3. System Architecture

```
Browser (React app)
   │
   │  HTTPS requests (JSON)
   ▼
FastAPI Backend
   │
   ├── /api/auth/*          → login / signup, issues JWT
   ├── /api/questions/*     → list/fetch case studies (public fields only)
   ├── /api/submissions/*   → start a case, send chat messages, submit final answer
   │       │
   │       ├──► Helper AI call (Claude) — scoped system prompt, case context ONLY
   │       │        no rubric, no ground truth, ever
   │       │
   │       └──► on submit: Judge AI call (Claude) — rubric + full transcript +
   │                final answer + ground truth notes → structured JSON score
   │
   └── /api/evaluations/*   → fetch a submission's score breakdown
   │
   ▼
PostgreSQL (users, questions, submissions, transcript_turns, evaluations)
```

Every chat message the user sends goes to the Helper AI and is persisted. Only on final submission does the Judge AI ever get invoked, and only the backend (never the frontend, never the Helper AI) constructs the Judge's prompt.

---

## 4. Database Schema

Use PostgreSQL. Exact schema:

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE questions (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    category TEXT NOT NULL,            -- 'data_diagnosis' | 'strategy_generation' | 'customer_reasoning'
    prompt_text TEXT NOT NULL,         -- shown to candidate
    context_data TEXT NOT NULL,        -- shown to candidate AND passed to Helper AI
    ground_truth_notes TEXT NOT NULL,  -- JUDGE-ONLY. Never sent to frontend or Helper AI.
    difficulty TEXT NOT NULL,          -- 'easy' | 'medium' | 'hard'
    rubric_json JSONB NOT NULL,        -- JUDGE-ONLY. Never sent to frontend or Helper AI.
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE submissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    question_id INTEGER REFERENCES questions(id),
    status TEXT DEFAULT 'in_progress', -- 'in_progress' | 'submitted'
    final_answer_text TEXT,
    started_at TIMESTAMP DEFAULT NOW(),
    submitted_at TIMESTAMP
);

CREATE TABLE transcript_turns (
    id SERIAL PRIMARY KEY,
    submission_id INTEGER REFERENCES submissions(id),
    turn_index INTEGER NOT NULL,
    role TEXT NOT NULL,   -- 'user' | 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE evaluations (
    id SERIAL PRIMARY KEY,
    submission_id INTEGER REFERENCES submissions(id),
    overall_score INTEGER,             -- 0-100
    dimension_scores_json JSONB,       -- {"clarifying_questions": 8, ...}
    judge_reasoning TEXT,
    anti_gaming_flags JSONB,           -- array of strings, may be empty
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Critical rule:** `ground_truth_notes` and `rubric_json` on the `questions` table must never appear in any API response sent to the frontend for an in-progress submission. They are read server-side only, at grading time.

---

## 5. Environment Variables

The backend needs a `.env` file (never committed to git) with:

```
DATABASE_URL=postgresql://<connection string from Neon/Supabase>
ANTHROPIC_API_KEY=<key>
JWT_SECRET=<any long random string>
```

The frontend needs a `.env` (or Vite equivalent) with:
```
VITE_API_BASE_URL=http://localhost:8000/api   (local) or the deployed backend URL (production)
```

---

## 6. Backend — Folder Structure

```
backend/
├── app/
│   ├── main.py                        # FastAPI app entrypoint, mounts routers
│   ├── db.py                          # DB engine/session setup
│   ├── models/
│   │   └── models.py                  # SQLAlchemy ORM models for all 5 tables
│   ├── schemas/
│   │   └── schemas.py                 # Pydantic request/response models (see §8)
│   ├── routers/
│   │   ├── auth.py                    # /api/auth/*
│   │   ├── questions.py               # /api/questions/*
│   │   ├── submissions.py             # /api/submissions/*
│   │   └── evaluations.py             # /api/evaluations/*
│   ├── services/
│   │   ├── candidate_llm.py           # Helper AI call logic
│   │   ├── judge_llm.py               # Judge AI call logic
│   │   └── anti_gaming.py             # heuristic checks, run before grading
│   ├── prompts/
│   │   ├── candidate_system_prompt.py
│   │   └── judge_system_prompt.py
│   └── auth_utils.py                  # JWT creation/verification, password hashing
├── requirements.txt
└── .env                                # not committed
```

`requirements.txt`:
```
fastapi
uvicorn
sqlalchemy
psycopg2-binary
python-jose
passlib[bcrypt]
anthropic
python-dotenv
pydantic
```

---

## 7. Auth

- Passwords are hashed with bcrypt via `passlib` before storage. Never store or log plaintext passwords.
- On successful login, issue a JWT signed with `JWT_SECRET`, containing `{"user_id": <id>}`, expiring in 24 hours.
- All `/api/submissions/*` and `/api/evaluations/*` routes require a valid JWT in the `Authorization: Bearer <token>` header. `/api/questions/*` (listing/viewing case studies) can be public or also require auth — require auth, for consistency and to allow future per-user history features.
- On the backend, verify the JWT on every protected route and extract `user_id` from it — never trust a `user_id` sent directly in a request body.

---

## 8. API Contract

All request/response bodies are JSON. All protected routes require `Authorization: Bearer <jwt>`.

### 8.1 `POST /api/auth/signup`
Request: `{ "email": string, "password": string, "name": string }`
Response: `{ "message": "account created" }` (201) or 400 if email already exists.

### 8.2 `POST /api/auth/login`
Request: `{ "email": string, "password": string }`
Response: `{ "token": string }` (200) or 401 if invalid.

### 8.3 `GET /api/questions`
Response: list of questions with **only public fields**:
```json
[
  { "id": 1, "title": "Sudden Churn Spike", "category": "data_diagnosis", "difficulty": "medium" }
]
```
(No `context_data`, `rubric_json`, or `ground_truth_notes` here — those come later, scoped correctly.)

### 8.4 `GET /api/questions/{id}`
Response: `{ "id", "title", "category", "difficulty", "prompt_text", "context_data" }`
(Still no `rubric_json` or `ground_truth_notes`.)

### 8.5 `POST /api/submissions`
Starts a new attempt. Request: `{ "question_id": int }`
Response: `{ "submission_id": int }`. Sets `started_at`, `status = 'in_progress'`.

### 8.6 `POST /api/submissions/{submission_id}/message`
Sends one chat message to the Helper AI.
Request: `{ "message": string }`
Backend logic:
1. Load the submission and its question's `context_data`.
2. Load prior `transcript_turns` for this submission, ordered by `turn_index`.
3. Call the Helper AI (see §9) with the context + history + new message.
4. Persist both the user's message and the AI's reply as new `transcript_turns` rows.
Response: `{ "reply": string }`

### 8.7 `POST /api/submissions/{submission_id}/submit`
Finalizes the answer and triggers grading.
Request: `{ "final_answer_text": string }`
Backend logic:
1. Save `final_answer_text`, set `status = 'submitted'`, set `submitted_at = now()`.
2. Run anti-gaming checks (§11) on the transcript and timing.
3. Call the Judge AI (see §10) with rubric + ground truth + full transcript + final answer.
4. Save the result as a new `evaluations` row, including any anti-gaming flags.
Response: the evaluation object (see §8.8).

### 8.8 `GET /api/evaluations/{submission_id}`
Response:
```json
{
  "overall_score": 82,
  "dimension_scores": { "clarifying_questions": 8, "iteration_quality": 7, "hallucination_catching": 9, "final_answer_quality": 8 },
  "reasoning": "string",
  "anti_gaming_flags": []
}
```

---

## 9. Helper AI (Candidate Assistant)

**System prompt** (`prompts/candidate_system_prompt.py`):
```python
CANDIDATE_SYSTEM_PROMPT = """You are a helpful AI assistant available to the candidate
for this case study. You have access only to the case context provided below.
You do NOT have access to any rubric, scoring criteria, or ground-truth answer.
Respond naturally and helpfully to the candidate's questions, as a real-world AI
assistant would in a business setting.

Case Context: {context_data}
"""
```

**Service logic** (`services/candidate_llm.py`): Build the message list as `conversation_history + [{"role": "user", "content": new_message}]`. Call `client.messages.create(model="claude-sonnet-4-6", max_tokens=1000, system=system_prompt, messages=messages)`. Return `response.content[0].text`.

The Helper AI must never be constructed with the rubric or ground truth in scope, even accidentally via a shared prompt-builder function. Keep its prompt-building code entirely separate from the Judge's.

---

## 10. Judge AI

**System prompt** (`prompts/judge_system_prompt.py`):
```python
JUDGE_SYSTEM_PROMPT = """You are an expert evaluator grading a candidate's use of an AI
assistant to solve a business case study. You will receive:
1. The rubric (weighted dimensions)
2. The full transcript of the candidate's interaction with their AI assistant
3. The candidate's final submitted answer
4. Ground-truth context notes (never shown to the candidate)

Score each rubric dimension from 0-10 with a one-sentence justification grounded in
specific transcript evidence. Do not be swayed by confident tone alone -- verify claims
against the provided ground truth. Return valid JSON only, with no other text, matching
this schema:
{{
  "dimension_scores": {{ "<dimension_name>": <0-10>, ... }},
  "overall_score": <0-100>,
  "reasoning": "<concise explanation>"
}}

Rubric: {rubric_json}
Ground truth notes: {ground_truth_notes}
"""
```

**Service logic** (`services/judge_llm.py`): Format the transcript as plain text lines (`"{role}: {content}"`), build a user message containing the transcript and final answer, call Claude with the judge system prompt, and `json.loads()` the reply.

**Robustness requirement:** LLMs sometimes wrap JSON in prose or markdown fences despite instructions. Wrap the parse in a try/except; on failure, strip anything before the first `{` and after the last `}` and retry the parse once before raising an error. Never let a malformed judge reply crash the submit endpoint — log it and return a clear error to the frontend instead.

### 10.1 Rubric (default, used unless a question specifies its own)
```json
{
  "dimensions": [
    { "name": "clarifying_questions", "weight": 0.20, "description": "Did the candidate ask relevant clarifying questions before jumping to a solution?" },
    { "name": "iteration_quality", "weight": 0.25, "description": "Did the candidate refine their prompts/approach based on AI responses rather than accepting the first output?" },
    { "name": "hallucination_catching", "weight": 0.25, "description": "Did the candidate identify and correct incorrect or fabricated AI outputs?" },
    { "name": "final_answer_quality", "weight": 0.30, "description": "Is the final recommendation correct, well-justified, and grounded in the given case data?" }
  ]
}
```
Each question's `rubric_json` column can reuse this default or override it per-question.

---

## 11. Anti-Gaming Checks

Run these server-side, right before invoking the Judge, and store results in `evaluations.anti_gaming_flags`:

1. **Near-zero conversation**: fewer than 2 transcript turns before submission → flag `"near-zero conversation before submitting"`.
2. **Too-fast submission**: `submitted_at - started_at` under 30 seconds → flag `"submitted extremely fast"`.
3. **Pre-formed answer pasted as first message**: if the first user turn is over 500 characters and closely resembles the final answer text → flag `"first message looks like a pre-written answer, not a genuine question"`.

These flags do not block submission — they're surfaced to the user/evaluator as a transparency signal, and can inform future scoring adjustments.

---

## 12. Frontend — Folder Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── client.js               # axios instance, attaches JWT header
│   ├── pages/
│   │   ├── Login.jsx
│   │   ├── Signup.jsx
│   │   ├── QuestionList.jsx        # GET /api/questions
│   │   ├── CaseWorkspace.jsx       # chat pane + final answer + submit
│   │   └── ScoreDashboard.jsx      # GET /api/evaluations/{id}
│   ├── components/
│   │   ├── ChatPane.jsx
│   │   ├── ScoreBreakdown.jsx
│   │   └── TranscriptViewer.jsx
│   ├── App.jsx                     # react-router routes
│   └── main.jsx
├── index.html
├── package.json
└── tailwind.config.js
```

### 12.1 Routing (`App.jsx`)
- `/login`, `/signup` — public
- `/questions` — list of case studies (protected)
- `/case/:questionId` — starts a submission, shows `CaseWorkspace` (protected)
- `/results/:submissionId` — `ScoreDashboard` (protected)

### 12.2 API client
`client.js` should read the JWT from local component state / a simple auth context (not `localStorage` if this is ever rendered inside an artifact sandbox — for a real deployed app, `localStorage` is fine and standard), and attach it as `Authorization: Bearer <token>` on every request via an axios interceptor.

### 12.3 `CaseWorkspace.jsx` behavior
1. On mount, call `POST /api/submissions` with the question ID to get a `submission_id`.
2. Render chat history and an input box; each send calls `POST /api/submissions/{id}/message` and appends both the user message and AI reply to local state.
3. Render a textarea for the final answer.
4. On "Submit Final Answer," call `POST /api/submissions/{id}/submit`, then navigate to `/results/{submission_id}`.

---

## 13. Sample Case Studies (seed data)

Insert these directly via SQL or a seed script so the app has real content from day one.

### 13.1 "Sudden Churn Spike" (data_diagnosis, medium)
- `prompt_text`: "Our SaaS product's monthly churn jumped from 4% to 9% last month. You have access to an AI assistant and the dataset below (customer cancellation survey responses + usage log summary). Diagnose the likely cause and recommend one action."
- `context_data`: a synthetic dataset (10-15 rows) mixing survey responses and usage stats, containing one red herring (e.g. a pricing complaint mentioned by a minority of respondents) and one real signal (a spike in cancellations correlating with a recent feature removal).
- `ground_truth_notes`: "The real cause is the feature removal; the pricing complaint is a distractor mentioned by only a minority of respondents. A strong answer identifies the correlation with the feature removal and recommends either reinstating it or communicating a clear replacement."
- `rubric_json`: the default rubric from §10.1.

### 13.2 "New Market Entry" (strategy_generation, hard)
- `prompt_text`: "Our mid-size B2B SaaS company is considering expanding into either the German or Brazilian market next year. You have market size, competitor, and regulatory context below. Recommend one market and justify it."
- `context_data`: brief comparative stats for both markets (market size, number of competitors, regulatory complexity, language/localization cost) with one subtly misleading stat (e.g. a large total market size figure for a market that is actually saturated by an entrenched competitor).
- `ground_truth_notes`: "Brazil is the stronger pick due to lower competitive saturation despite Germany's larger headline market size; a strong answer catches that the German market size figure is misleading given competitive concentration."
- `rubric_json`: the default rubric from §10.1.

### 13.3 "Angry Customer Escalation" (customer_reasoning, easy)
- `prompt_text`: "A high-value customer is threatening to cancel after a billing error charged them twice. Use the AI assistant to draft a resolution plan and a response to the customer."
- `context_data`: account details, the billing error description, and this customer's account history (mostly positive, one prior minor complaint).
- `ground_truth_notes`: "A strong answer proposes an immediate refund/credit, an acknowledgment addressing the customer's specific frustration, and a concrete process fix — not just an apology."
- `rubric_json`: the default rubric from §10.1.

Build 5-7 more of these before considering the app "content complete" — vary category and difficulty.

---

## 14. Local Development

1. Backend: `cd backend`, create venv, `pip install -r requirements.txt`, create `.env`, run `uvicorn app.main:app --reload` (serves on `http://localhost:8000`).
2. Frontend: `cd frontend`, `npm install`, create `.env` with `VITE_API_BASE_URL=http://localhost:8000/api`, run `npm run dev` (serves on `http://localhost:5173`).
3. Database: create tables via the SQL in §4 against your Neon/Supabase instance, then run a seed script to insert the case studies from §13.
4. CORS: the backend must allow requests from the frontend's local origin (`http://localhost:5173`) and, later, its deployed Vercel origin.

---

## 15. Deployment

- **Frontend**: push to GitHub, connect the repo to Vercel, set `VITE_API_BASE_URL` to the deployed backend URL as a Vercel environment variable.
- **Backend**: connect the repo to Render or Railway, set `DATABASE_URL`, `ANTHROPIC_API_KEY`, and `JWT_SECRET` as environment variables in that platform's dashboard (never commit `.env`).
- **Database**: already live via Neon/Supabase; no separate deploy step.
- After both are live, update the backend's CORS allowed origins to the real Vercel domain (don't leave it wide open to `*` in production).

---

## 16. Build Order (do these in sequence)

1. Create database + run the schema in §4.
2. Backend skeleton: `db.py`, `models.py`, `main.py` with an empty router set — confirm it starts and connects to the database.
3. Auth: signup/login working end-to-end, JWT issued and verified.
4. Questions: seed the 3 sample case studies from §13, build `GET /api/questions` and `GET /api/questions/{id}`.
5. Helper AI: build `candidate_llm.py`, the `/message` endpoint, and confirm a full chat round-trip persists correctly to `transcript_turns`.
6. Judge AI: build `judge_llm.py`, the `/submit` endpoint, and test it against several fake transcripts (including a deliberately bad one and a deliberately good one) until scores feel consistent and justified.
7. Anti-gaming: implement the three checks in §11 and confirm flags populate correctly.
8. Frontend: build all pages in §12 and wire them to the real backend.
9. Content: write 5-7 more case studies beyond the 3 seeds, covering all three categories and all three difficulties.
10. Deploy both apps per §15, do an end-to-end smoke test on the live URLs, then record a short demo and write the README (architecture diagram, product thesis, one fully worked example, known limitations).

---

## 17. Known Limitations to Document (for the README)

- Judge scoring may vary slightly across repeated runs on the same transcript (LLM non-determinism) — worth demonstrating awareness of this and, if time allows, running the judge 2-3x on a test transcript to report variance.
- Small case-study bank initially (aim for 8-10 before calling it feature-complete).
- Anti-gaming checks are heuristic, not foolproof — a determined user could still game them.
