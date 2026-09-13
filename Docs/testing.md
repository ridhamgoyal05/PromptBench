# Automated Verification & Testing Suite — PromptBench

PromptBench contains a comprehensive, automated end-to-end integration and unit testing suite located in [`backend/test_flow.py`](../backend/test_flow.py).

---

## 1. Running the Test Suite

Make sure PostgreSQL is running and your Python virtual environment is activated:

```bash
# Windows
.\backend\venv\Scripts\python.exe backend/test_flow.py

# Linux / macOS
python backend/test_flow.py
```

---

## 2. Test Coverage & Verification Areas

The suite runs 7 critical test modules:

### 1. Authentication & Multi-Tenant Authorization (`test_auth_flow_and_authorization`)
- Verifies user registration (`/api/auth/signup`) and duplicate email rejection.
- Validates password hashing and JWT token issuance upon login.
- Enforces multi-tenant data boundaries: User B cannot access, send messages to, or submit answers for User A's active submission session (returns `403 Forbidden`).

### 2. Hidden Data Protection (`test_questions_data_protection`)
- Queries both `/api/questions` (list) and `/api/questions/{id}` (detail).
- Asserts that hidden evaluation data (`ground_truth_notes`, `rubric_json`) is strictly excluded from candidate-facing responses.

### 3. Submission State Transitions (`test_submission_state_transitions`)
- Walks through the full candidate lifecycle: session creation $\to$ transcript turns $\to$ final submission.
- Verifies that chat messages cannot be appended after submission (`400 Bad Request`).
- Verifies that double submission is prevented.

### 4. Judge AI JSON Validation (`test_judge_json_parsing_and_validation`)
- Tests parsing of standard JSON and Markdown-wrapped JSON (```` ```json ````).
- Validates strict Pydantic rules:
  - Overall score bound between `0` and `100`.
  - All 4 required dimension scores bound between `0` and `10`.
  - Rejection of malformed JSON or empty reasoning strings.

### 5. Evaluation Failure & Retry Semantics (`test_evaluation_failure_and_retry`)
- Simulates external AI API timeouts or network failure during submission evaluation.
- Verifies that the submission status transitions gracefully to `evaluation_failed` without losing the candidate's transcript turns or original timestamps.
- Verifies that subsequent retries successfully generate evaluation records and restore status to `submitted`.

### 6. Anti-Gaming Guardrails (`test_anti_gaming_heuristics`)
- Tests heuristic detection:
  - **Zero conversation turns**: Submitting without consulting the Helper AI.
  - **Speed threshold**: Submitting faster than 30 seconds.
  - **Pre-written copy-paste detection**: Pasting large pre-formed answers in the very first chat turn.

### 7. Attempt History Filtering (`test_attempt_history_filters`)
- Validates that `/api/evaluations/history` only returns completed, evaluated submissions and omits in-progress or failed attempts.
