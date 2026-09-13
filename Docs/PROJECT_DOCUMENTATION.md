# PromptBench — Practice AI Collaborating Skills

**Project Documentation**

---

## 1. Introduction

PromptBench is a full-stack web application designed to train and benchmark a user's ability to collaborate effectively with an AI assistant while solving open-ended business problems. Unlike traditional coding-assessment platforms that grade a candidate's ability to write algorithms, PromptBench evaluates a different and increasingly relevant skill set: how well a person *works with* an AI system to reach a well-reasoned, well-justified conclusion.

The platform presents candidates with realistic business case studies (e.g., diagnosing a sales decline, planning a market entry) and asks them to investigate the problem through conversation with a "Helper AI." Once satisfied, the candidate submits a final recommendation, which is graded automatically by a separate "Judge AI" against a hidden rubric and ground-truth notes.

## 2. Objectives

- Provide realistic, open-ended business case studies for practicing AI-assisted problem solving.
- Evaluate candidates on four measurable dimensions: asking clarifying questions, iterative refinement, catching AI hallucinations, and the quality of the final answer.
- Maintain a strict separation between the AI a candidate talks to and the AI that grades them, so that grading criteria can never leak into the conversation.
- Detect and flag attempts to game the evaluation (e.g., submitting a pre-written answer without any real interaction).
- Give users a persistent history of past attempts and scores for self-review.

## 3. Key Architectural Principle: Helper vs. Judge Isolation

The system is built around one core security boundary:

| | Helper AI | Judge AI |
|---|---|---|
| **Audience** | Candidate (client-facing) | System only (server-side) |
| **Trigger** | Every chat message during the case | Once, when the candidate submits a final answer |
| **Has access to** | Case prompt and public context data only | Full conversation transcript, final answer, hidden ground-truth notes, and the scoring rubric |
| **Purpose** | Acts as a normal, helpful assistant | Produces a structured, rubric-based grading report |

The Helper AI never receives the rubric, the ground-truth notes, or any scoring information — it behaves exactly like a real-world AI assistant a candidate might use on the job. The Judge AI is invoked only after submission and is the only component with visibility into what "correct" looks like. This isolation protects the integrity of the evaluation and prevents the candidate's assistant from accidentally (or deliberately) revealing answers.

## 4. Technology Stack

| Layer | Technology |
|---|---|
| Backend framework | Python, FastAPI |
| ORM | SQLAlchemy |
| Database | PostgreSQL 16.2 |
| Data validation | Pydantic |
| Authentication | JWT (python-jose), Bcrypt password hashing |
| AI provider | Anthropic API (Claude) |
| Frontend framework | React 18 (Vite) |
| Styling | Tailwind CSS |
| HTTP client | Axios |
| Routing | React Router |

## 5. System Architecture

```
┌────────────┐      HTTPS/JSON       ┌──────────────────┐
│   React    │ ────────────────────► │   FastAPI         │
│  Frontend  │ ◄──────────────────── │   Backend          │
└────────────┘                       └────────┬──────────┘
                                               │
                     ┌─────────────────────────┼─────────────────────────┐
                     ▼                         ▼                         ▼
             ┌───────────────┐        ┌────────────────┐        ┌────────────────┐
             │  PostgreSQL    │        │  Helper AI Call │        │  Judge AI Call  │
             │  (SQLAlchemy)  │        │  (candidate_llm) │        │  (judge_llm)     │
             └───────────────┘        └────────────────┘        └────────────────┘
```

The backend is organized as a set of FastAPI routers, each responsible for one concern:

- `auth.py` — signup, login, JWT issuance, and the `get_current_user` dependency used to protect routes.
- `questions.py` — listing and retrieving business case studies.
- `submissions.py` — starting a case attempt, exchanging chat messages with the Helper AI, and submitting the final answer for grading.
- `evaluations.py` — retrieving past evaluation results and attempt history.
- `candidate_llm.py` — wraps the Anthropic API call for the Helper AI, scoped only to public case context.
- `judge_llm.py` — wraps the Anthropic API call for the Judge AI, including strict Pydantic validation of the returned JSON grading report.
- `anti_gaming.py` — heuristic checks run at submission time (see Section 8).
- `config.py` — centralized environment variable loading and startup validation.

## 6. Database Design

The application uses PostgreSQL with SQLAlchemy models. There are five core tables:

### `users`
Stores registered accounts.
| Column | Type | Notes |
|---|---|---|
| id | Integer (PK) | |
| email | String | Unique |
| password_hash | String | Bcrypt hash |
| name | String | |
| created_at | DateTime | |

### `questions`
Stores the business case studies.
| Column | Type | Notes |
|---|---|---|
| id | Integer (PK) | |
| title | String | |
| category | String | `data_diagnosis` \| `strategy_generation` \| `customer_reasoning` |
| prompt_text | Text | Shown to the candidate |
| context_data | Text | Public case data, shown to candidate and Helper AI |
| ground_truth_notes | Text | Hidden; visible only to Judge AI |
| difficulty | String | `easy` \| `medium` \| `hard` |
| rubric_json | JSONB | Hidden scoring rubric, visible only to Judge AI |

### `submissions`
Tracks one attempt by one user at one question.
| Column | Type | Notes |
|---|---|---|
| id | Integer (PK) | |
| user_id | FK → users.id | |
| question_id | FK → questions.id | |
| status | String | `in_progress` \| `submitted` \| `evaluation_failed` |
| final_answer_text | Text | |
| started_at / submitted_at | DateTime | |

### `transcript_turns`
Stores every message exchanged with the Helper AI for a submission.
| Column | Type | Notes |
|---|---|---|
| id | Integer (PK) | |
| submission_id | FK → submissions.id | |
| turn_index | Integer | Ordering |
| role | String | `user` \| `assistant` |
| content | Text | |

### `evaluations`
Stores the Judge AI's grading report for a submitted attempt.
| Column | Type | Notes |
|---|---|---|
| id | Integer (PK) | |
| submission_id | FK → submissions.id | |
| overall_score | Integer | 0–100 |
| dimension_scores_json | JSONB | Per-dimension 0–10 scores |
| judge_reasoning | Text | |
| anti_gaming_flags | JSONB | List of warning strings |

**Relationships:** `users → submissions → (transcript_turns, evaluations)`, and `questions → submissions`, all with cascading deletes.

## 7. API Reference

All endpoints are mounted under the `/api` prefix and (except signup/login) require a `Bearer` JWT.

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/signup` | Create a new account |
| POST | `/api/auth/login` | Authenticate and receive a JWT |
| GET | `/api/questions` | List all available case studies |
| GET | `/api/questions/{id}` | Get details of one case study |
| POST | `/api/submissions` | Start a new attempt on a question |
| GET | `/api/submissions/{id}` | Get a submission's current state and transcript |
| POST | `/api/submissions/{id}/message` | Send a message to the Helper AI and store the reply |
| POST | `/api/submissions/{id}/submit` | Submit final answer and trigger Judge AI grading |
| GET | `/api/evaluations/history` | List the current user's past graded attempts |
| GET | `/api/evaluations/{submission_id}` | Get the full evaluation report for one submission |
| GET | `/api/health` | Health check |

## 8. Anti-Gaming Checks

To discourage candidates from bypassing genuine engagement with the Helper AI, the system runs three heuristic checks at submission time (`anti_gaming.py`):

1. **Near-zero conversation** — flags submissions with fewer than two transcript turns.
2. **Extremely fast submission** — flags attempts submitted within 30 seconds of starting.
3. **Pre-written answer detection** — computes Jaccard similarity between a candidate's first message and their final answer; a long first message (>500 characters) that closely matches the final answer is flagged as likely pre-written rather than a genuine investigative question.

Flags are stored alongside the evaluation and surfaced to the user, but do not currently block submission — they are informational signals for the reviewer.

## 9. Frontend Structure

| Page | Route | Purpose |
|---|---|---|
| Login | `/login` | User authentication |
| Signup | `/signup` | New account registration |
| QuestionList | `/questions` | Browse available case studies (protected) |
| CaseWorkspace | `/case/:submissionId` | Chat with Helper AI and draft/submit a final answer (protected) |
| ScoreDashboard | `/results/:submissionId` | View a graded submission's score breakdown (protected) |
| MyAttempts | `/attempts` | View history of past attempts (protected) |

Protected routes are wrapped in a `ProtectedRoute` component that redirects unauthenticated users to `/login`.

## 10. Setup & Running Locally

1. **Database**: Start a local PostgreSQL 16.2 instance on `localhost:5432` (convenience scripts `start_postgres.bat` / `stop_postgres.bat` / `status_postgres.bat` are provided for Windows).
2. **Environment variables**: Populate `backend/.env` (`DATABASE_URL`, `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, `JWT_SECRET_KEY`, `RUN_LLM_TESTS`) and `frontend/.env` (`VITE_API_BASE_URL`) from the provided `.env.example` templates.
3. **Seed the database**: `python backend/seed.py` — populates 5 case studies spanning `data_diagnosis`, `strategy_generation`, and `customer_reasoning` categories.
4. **Run backend tests**: `python backend/test_flow.py` — an end-to-end verification suite (7 test cases) covering the signup-to-evaluation flow.
5. **Start servers**: `start_backend.bat` (FastAPI on port 8000, docs at `/docs`) and `start_frontend.bat` (Vite dev server on port 5173).

## 11. Testing

The backend includes `test_flow.py`, an integration test script that exercises the complete candidate journey — signup, login, listing questions, creating a submission, exchanging messages, submitting a final answer, and retrieving the evaluation — asserting correct status transitions and response shapes at each step. When `RUN_LLM_TESTS=false`, both the Helper and Judge AI calls fall back to deterministic mocked responses, allowing the full flow to be tested without consuming API credits or requiring network access.

## 12. Security Considerations

- Passwords are hashed with bcrypt before storage; plaintext passwords are never persisted.
- Authentication uses signed JWTs; protected routes validate the token and re-fetch the user on every request.
- Ownership checks are enforced on all submission and evaluation endpoints — a user cannot view or modify another user's data.
- Secrets (`ANTHROPIC_API_KEY`, `JWT_SECRET_KEY`, `DATABASE_URL`) are loaded from environment variables via `.env`, which is excluded from version control by `.gitignore`.

## 13. Limitations & Future Enhancements

- Anti-gaming flags are currently advisory only; a future version could weight them into the final score or require manual review.
- The rubric structure is fixed to four dimensions; a configurable rubric schema per question category could allow richer case types.
- No admin interface currently exists for adding or editing case studies outside of the seed script.
- Deployment configuration (e.g., Docker, cloud hosting) is not yet included; the project currently targets local development only.

## 14. Conclusion

PromptBench demonstrates a complete, working full-stack application with a clear separation of concerns between its presentation layer, business logic, and AI integration points. Its central design contribution — strictly isolating the candidate-facing Helper AI from the grading Judge AI — addresses a real integrity concern in AI-assisted assessment and is implemented consistently across the schema, API, and prompt design.
