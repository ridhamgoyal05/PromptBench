# REST API Reference — PromptBench

PromptBench exposes a RESTful API built with FastAPI. All endpoints return JSON and use standard HTTP status codes.

---

## 1. Authentication Endpoints (`/api/auth`)

### Register User
- **Method / Path**: `POST /api/auth/signup`
- **Auth Required**: No
- **Request Body**:
  ```json
  {
    "email": "candidate@example.com",
    "password": "SecurePassword123!",
    "name": "Alex Candidate"
  }
  ```
- **Success Response (`201 Created`)**:
  ```json
  {
    "message": "account created"
  }
  ```
- **Errors**: `400 Bad Request` if email already exists.

### Login User
- **Method / Path**: `POST /api/auth/login`
- **Auth Required**: No
- **Request Body**:
  ```json
  {
    "email": "candidate@example.com",
    "password": "SecurePassword123!"
  }
  ```
- **Success Response (`200 OK`)**:
  ```json
  {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```
- **Errors**: `401 Unauthorized` for invalid credentials.

---

## 2. Case Studies Endpoints (`/api/questions`)

### List Available Cases
- **Method / Path**: `GET /api/questions`
- **Auth Required**: Bearer Token
- **Success Response (`200 OK`)**:
  ```json
  [
    {
      "id": 1,
      "title": "Sudden Churn Spike",
      "category": "data_diagnosis",
      "difficulty": "medium",
      "prompt_text": "A SaaS company experienced an unexpected 28% jump in churn...",
      "created_at": "2026-09-13T10:00:00Z"
    }
  ]
  ```
  *(Note: `ground_truth_notes` and `rubric_json` are never returned.)*

### Get Case Study Details
- **Method / Path**: `GET /api/questions/{question_id}`
- **Auth Required**: Bearer Token
- **Success Response (`200 OK`)**:
  ```json
  {
    "id": 1,
    "title": "Sudden Churn Spike",
    "category": "data_diagnosis",
    "difficulty": "medium",
    "prompt_text": "...",
    "context_data": "...",
    "created_at": "2026-09-13T10:00:00Z"
  }
  ```
- **Errors**: `404 Not Found`.

---

## 3. Submission & Helper AI Endpoints (`/api/submissions`)

### Start Case Workspace Session
- **Method / Path**: `POST /api/submissions`
- **Auth Required**: Bearer Token
- **Request Body**:
  ```json
  {
    "question_id": 1
  }
  ```
- **Success Response (`201 Created`)**:
  ```json
  {
    "submission_id": 12,
    "question_id": 1,
    "title": "Sudden Churn Spike",
    "difficulty": "medium",
    "category": "data_diagnosis",
    "prompt_text": "...",
    "context_data": "...",
    "started_at": "2026-09-13T12:00:00Z",
    "transcript": []
  }
  ```

### Chat with Helper AI
- **Method / Path**: `POST /api/submissions/{submission_id}/message`
- **Auth Required**: Bearer Token
- **Request Body**:
  ```json
  {
    "message": "Can you break down churn by user tier over the last 3 months?"
  }
  ```
- **Success Response (`200 OK`)**:
  ```json
  {
    "reply": "Looking at the tier data, the churn increase is concentrated in Enterprise accounts...",
    "turn_index": 2
  }
  ```
- **Errors**:
  - `403 Forbidden` if the user is not the submission owner.
  - `400 Bad Request` if the submission is already submitted.

### Final Submission & Trigger Judge AI
- **Method / Path**: `POST /api/submissions/{submission_id}/submit`
- **Auth Required**: Bearer Token
- **Request Body**:
  ```json
  {
    "final_answer_text": "Executive Recommendation: Re-introduce custom reporting feature..."
  }
  ```
- **Success Response (`200 OK`)**:
  ```json
  {
    "id": 5,
    "submission_id": 12,
    "overall_score": 88,
    "dimension_scores_json": {
      "clarifying_questions": 9,
      "iteration_quality": 9,
      "hallucination_catching": 8,
      "final_answer_quality": 9
    },
    "judge_reasoning": "Candidate identified root cause...",
    "anti_gaming_flags": [],
    "created_at": "2026-09-13T12:35:00Z"
  }
  ```
- **Errors**:
  - `403 Forbidden` if unauthorized.
  - `400 Bad Request` if already submitted.
  - `500 Internal Server Error` with graceful state `evaluation_failed` if Judge API times out (allows retry).

---

## 4. Evaluations & History (`/api/evaluations`)

### Get Attempt History
- **Method / Path**: `GET /api/evaluations/history`
- **Auth Required**: Bearer Token
- **Success Response (`200 OK`)**:
  ```json
  [
    {
      "submission_id": 12,
      "question_title": "Sudden Churn Spike",
      "overall_score": 88,
      "submitted_at": "2026-09-13T12:35:00Z"
    }
  ]
  ```

### Get Detailed Evaluation & Transcript
- **Method / Path**: `GET /api/evaluations/{submission_id}`
- **Auth Required**: Bearer Token
- **Success Response (`200 OK`)**:
  Returns comprehensive scoring report, dimension breakdown, judge reasoning, anti-gaming check results, and the complete turn-by-turn conversation transcript.
