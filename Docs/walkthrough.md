# User Journey & Walkthrough Guide — PromptBench

This document walks through the complete end-to-end user experience in PromptBench, from onboarding to evaluation review.

---

## 1. Candidate Onboarding

1. **Registration & Sign In**:
   - Access the platform at [http://localhost:5173](http://localhost:5173).
   - Click **Sign Up** to create an account with your name, email, and password.
   - Upon successful signup, log in to receive an authenticated JWT session.

---

## 2. Selecting a Business Case Study

After logging in, the **Case Catalog** displays the available benchmarking scenarios:

1. **Sudden Churn Spike** (`Data Diagnosis` | Medium)
   - *Scenario*: A B2B SaaS platform experiences an unexpected 28% jump in churn after a major redesign.
   - *Challenge*: Disentangle conflicting metrics, ask the Helper AI for cohort and log breakdowns, and identify root causes.

2. **New Market Entry** (`Strategy / Market Sizing` | Hard)
   - *Scenario*: An electric vehicle charging provider evaluates expanding into Southeast Asia.
   - *Challenge*: Filter assumptions, request regulatory context, and synthesize an actionable market entry strategy.

3. **Angry Customer Escalation** (`Operations / Incident Response` | Hard)
   - *Scenario*: A critical payment outage affects top enterprise customers during peak hours.
   - *Challenge*: Coordinate mitigation, prioritize customer communications, and construct a comprehensive post-mortem.

4. **Sales Decline Diagnosis** (`Business Analytics` | Medium)
   - *Scenario*: Q3 pipeline velocity dropped across mid-market accounts.
   - *Challenge*: Probe sales cycle stages, identify bottleneck conversion drop-offs, and suggest pipeline remedies.

5. **Product Launch Strategy** (`Product Strategy` | Easy)
   - *Scenario*: Prioritizing features for a new collaborative AI workspace tool.
   - *Challenge*: Evaluate user persona feedback, trade off speed-to-market versus feature depth, and present a launch roadmap.

---

## 3. Interactive Case Workspace

Clicking **Start Case** opens the two-pane workspace:

- **Left Pane (Context & Helper AI)**:
  - Displays the problem statement, context data, and constraints.
  - Interactive chat panel with the **Helper AI**.
  - Candidate can ask questions, request data splits, brainstorm hypotheses, and test assumptions.
- **Right Pane (Final Recommendation Editor)**:
  - Scratchpad for structuring the final deliverable.
  - Rich text area where the candidate writes their executive synthesis, data justifications, and action plan.

---

## 4. Submitting for Evaluation

When the candidate completes their analysis:
1. Click **Submit Final Answer**.
2. PromptBench packages the full conversation transcript and final answer.
3. The server invokes the **Judge AI** with the hidden ground truth and rubric schemas.
4. The system validates the evaluation JSON and stores the result in PostgreSQL.
5. The UI automatically redirects the candidate to the **Score Dashboard**.

---

## 5. Score Dashboard & Feedback

The evaluation report includes:
- **Overall Score (0-100)**: Weighted performance grade.
- **Dimensional Breakdown (0-10)**:
  - *Clarifying Questions*: Thoroughness in framing the problem.
  - *Iteration Quality*: Depth of follow-up inquiry with AI.
  - *Hallucination Catching*: Critical verification of AI claims.
  - *Final Answer Quality*: Structure, clarity, and analytical rigor.
- **Judge Reasoning**: Detailed qualitative feedback highlighting strengths and opportunities for improvement.
- **Anti-Gaming Status**: Verification flags ensuring authentic candidate effort.
- **Full Transcript Review**: Turn-by-turn recap of the conversation.

---

## 6. Troubleshooting

### "No cases found on dashboard"
- **Cause**: The database tables were created but the seed script has not been run.
- **Fix**: Run `python backend/seed.py` (or `.\backend\venv\Scripts\python.exe backend/seed.py`).

### "Could not connect to database" / "Connection refused on port 5432"
- **Cause**: PostgreSQL service is not running.
- **Fix**: Run `scripts\start_postgres.bat` or verify local PostgreSQL is listening on port 5432.

### "Helper AI API call failed" / "Anthropic API Error"
- **Cause**: Invalid or missing `ANTHROPIC_API_KEY`.
- **Fix**: Set a valid key in `backend/.env` or set `RUN_LLM_TESTS=false` to use deterministic mock responses for local testing.
