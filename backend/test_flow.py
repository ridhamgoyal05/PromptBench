import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import warnings

# Suppress deprecation and runtime warnings for clean test runner output
warnings.filterwarnings("ignore")

# Load env variables
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(env_path)
load_dotenv()

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set test environment flags
os.environ["ENV"] = "testing"
# If no DATABASE_URL is set, we will use a dummy test URL to pass import checks,
# but we tell the user they must supply one.
if not os.getenv("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "postgresql://dummy:dummy@localhost:5432/dummy"
if not os.getenv("ANTHROPIC_MODEL"):
    os.environ["ANTHROPIC_MODEL"] = "claude-3-5-sonnet-20241022"
if not os.getenv("JWT_SECRET_KEY"):
    os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-must-be-long"
if not os.getenv("ANTHROPIC_API_KEY"):
    os.environ["ANTHROPIC_API_KEY"] = "dummy-api-key"

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.db import engine, Base, SessionLocal
from backend.app.models import User, Question, Submission, TranscriptTurn, Evaluation
from backend.app.judge_llm import parse_and_validate_judge_response
from backend.app.anti_gaming import run_anti_gaming_checks

class PromptBenchTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Only attempt database operations if a real DATABASE_URL is provided (not the dummy one)
        cls.has_real_db = "dummy" not in os.getenv("DATABASE_URL")
        
        if cls.has_real_db:
            print("Connecting to test PostgreSQL database and initializing tables...")
            Base.metadata.create_all(bind=engine)
            cls.db = SessionLocal()
            
            # Setup seed question for testing
            cls.test_question = Question(
                title="Test Case Study",
                category="data_diagnosis",
                difficulty="medium",
                prompt_text="Solve this test case study.",
                context_data="Test context data.",
                ground_truth_notes="Test hidden ground truth.",
                rubric_json={
                    "dimensions": [
                        {"name": "clarifying_questions", "weight": 0.25, "description": "Clarifying questions"},
                        {"name": "iteration_quality", "weight": 0.25, "description": "Iteration"},
                        {"name": "hallucination_catching", "weight": 0.25, "description": "Hallucination"},
                        {"name": "final_answer_quality", "weight": 0.25, "description": "Final answer"}
                    ]
                }
            )
            cls.db.add(cls.test_question)
            cls.db.commit()
            cls.db.refresh(cls.test_question)
            cls.question_id = cls.test_question.id
        else:
            print("Warning: Real PostgreSQL DATABASE_URL is not set. Database integration tests will be skipped.")
            cls.question_id = 1

        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        if cls.has_real_db:
            cls.db.query(Evaluation).delete()
            cls.db.query(TranscriptTurn).delete()
            cls.db.query(Submission).delete()
            cls.db.query(Question).delete()
            cls.db.query(User).delete()
            cls.db.commit()
            cls.db.close()

    def setUp(self):
        pass

    def get_token_for_user(self, email, password, name):
        login_res = self.client.post("/api/auth/login", json={"email": email, "password": password})
        if login_res.status_code == 200:
            return login_res.json()["token"]
        self.client.post("/api/auth/signup", json={"email": email, "password": password, "name": name})
        login_res = self.client.post("/api/auth/login", json={"email": email, "password": password})
        return login_res.json()["token"]

    # ==========================================
    # 1. AUTHENTICATION & AUTHORIZATION TESTS
    # ==========================================
    def test_auth_flow_and_authorization(self):
        if not self.has_real_db:
            self.skipTest("Skipping DB integration test.")
        email_a = "user_auth_a@example.com"
        email_b = "user_auth_b@example.com"
        password = "testpassword123"

        # Signup A
        signup_res = self.client.post("/api/auth/signup", json={
            "email": email_a, "password": password, "name": "User A"
        })
        self.assertEqual(signup_res.status_code, 201)
        self.assertEqual(signup_res.json()["message"], "account created")

        # Signup A duplicate (should fail)
        signup_dup = self.client.post("/api/auth/signup", json={
            "email": email_a, "password": password, "name": "User A Dup"
        })
        self.assertEqual(signup_dup.status_code, 400)

        # Signup B
        signup_b = self.client.post("/api/auth/signup", json={
            "email": email_b, "password": password, "name": "User B"
        })
        self.assertEqual(signup_b.status_code, 201)

        # Login A
        login_res_a = self.client.post("/api/auth/login", json={
            "email": email_a, "password": password
        })
        self.assertEqual(login_res_a.status_code, 200)
        token_a = login_res_a.json()["token"]

        # Login B
        login_res_b = self.client.post("/api/auth/login", json={
            "email": email_b, "password": password
        })
        self.assertEqual(login_res_b.status_code, 200)
        token_b = login_res_b.json()["token"]

        # Request with invalid token
        questions_res = self.client.get("/api/questions", headers={"Authorization": "Bearer invalidtoken"})
        self.assertEqual(questions_res.status_code, 401)

        # User A starts submission
        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}

        sub_res = self.client.post("/api/submissions", json={"question_id": self.question_id}, headers=headers_a)
        self.assertEqual(sub_res.status_code, 201)
        submission_id = sub_res.json()["submission_id"]

        # User B tries to view/modify/submit User A's submission (should fail)
        msg_res = self.client.post(
            f"/api/submissions/{submission_id}/message", 
            json={"message": "Hello"}, 
            headers=headers_b
        )
        self.assertEqual(msg_res.status_code, 403)

        submit_res = self.client.post(
            f"/api/submissions/{submission_id}/submit", 
            json={"final_answer_text": "My final recommendation."}, 
            headers=headers_b
        )
        self.assertEqual(submit_res.status_code, 403)

        eval_res = self.client.get(f"/api/evaluations/{submission_id}", headers=headers_b)
        self.assertEqual(eval_res.status_code, 403)

    # ==========================================
    # 2. QUESTIONS DATA PROTECTION
    # ==========================================
    def test_questions_data_protection(self):
        if not self.has_real_db:
            self.skipTest("Skipping DB integration test.")
        token = self.get_token_for_user("user_a@example.com", "testpassword123", "User A")
        headers = {"Authorization": f"Bearer {token}"}

        # Check question list
        questions_res = self.client.get("/api/questions", headers=headers)
        self.assertEqual(questions_res.status_code, 200)
        q_list = questions_res.json()
        self.assertTrue(len(q_list) > 0)
        
        # Verify hidden fields ground_truth_notes and rubric_json are NOT present in list
        for q in q_list:
            self.assertNotIn("ground_truth_notes", q)
            self.assertNotIn("rubric_json", q)

        # Check question detail
        q_detail_res = self.client.get(f"/api/questions/{self.question_id}", headers=headers)
        self.assertEqual(q_detail_res.status_code, 200)
        q_detail = q_detail_res.json()
        self.assertEqual(q_detail["id"], self.question_id)
        
        # Verify hidden fields are NOT present in detail
        self.assertNotIn("ground_truth_notes", q_detail)
        self.assertNotIn("rubric_json", q_detail)

    # ==========================================
    # 3. SUBMISSION STATE TRANSITIONS
    # ==========================================
    def test_submission_state_transitions(self):
        if not self.has_real_db:
            self.skipTest("Skipping DB integration test.")
        token = self.get_token_for_user("user_a@example.com", "testpassword123", "User A")
        headers = {"Authorization": f"Bearer {token}"}

        # Start submission
        sub_res = self.client.post("/api/submissions", json={"question_id": self.question_id}, headers=headers)
        sub_id = sub_res.json()["submission_id"]

        # Send chat message (changes state turns)
        msg_res1 = self.client.post(f"/api/submissions/{sub_id}/message", json={"message": "First query"}, headers=headers)
        self.assertEqual(msg_res1.status_code, 200)
        self.assertIn("reply", msg_res1.json())

        msg_res2 = self.client.post(f"/api/submissions/{sub_id}/message", json={"message": "Second query"}, headers=headers)
        self.assertEqual(msg_res2.status_code, 200)

        # Submit answer (success evaluation mocked by default)
        submit_res = self.client.post(f"/api/submissions/{sub_id}/submit", json={"final_answer_text": "Good recommendation."}, headers=headers)
        self.assertEqual(submit_res.status_code, 200)
        self.assertEqual(submit_res.json()["overall_score"], 82)

        # Sending message to submitted submission must fail
        msg_fail = self.client.post(f"/api/submissions/{sub_id}/message", json={"message": "Post-submit query"}, headers=headers)
        self.assertEqual(msg_fail.status_code, 400)

        # Re-submitting submitted submission must fail
        submit_fail = self.client.post(f"/api/submissions/{sub_id}/submit", json={"final_answer_text": "Another recommendation."}, headers=headers)
        self.assertEqual(submit_fail.status_code, 400)

    # ==========================================
    # 4. JUDGE JSON PARSING & VALIDATION
    # ==========================================
    def test_judge_json_parsing_and_validation(self):
        # Valid JSON
        valid_input = """
        {
          "overall_score": 85,
          "dimension_scores": {
            "clarifying_questions": 8,
            "iteration_quality": 9,
            "hallucination_catching": 7,
            "final_answer_quality": 9
          },
          "reasoning": "Strong work."
        }
        """
        validated = parse_and_validate_judge_response(valid_input)
        self.assertEqual(validated["overall_score"], 85)
        self.assertEqual(validated["dimension_scores"]["clarifying_questions"], 8)
        self.assertEqual(validated["reasoning"], "Strong work.")

        # Markdown wrapped JSON
        markdown_input = f"```json\n{valid_input}\n```"
        validated_md = parse_and_validate_judge_response(markdown_input)
        self.assertEqual(validated_md["overall_score"], 85)

        # Malformed JSON (should raise ValueError)
        with self.assertRaises(ValueError):
            parse_and_validate_judge_response("{malformed_json_here")

        # Invalid overall score (> 100)
        invalid_score_input = valid_input.replace('"overall_score": 85', '"overall_score": 105')
        with self.assertRaises(ValueError):
            parse_and_validate_judge_response(invalid_score_input)

        # Invalid dimension score (> 10)
        invalid_dim_input = valid_input.replace('"clarifying_questions": 8', '"clarifying_questions": 12')
        with self.assertRaises(ValueError):
            parse_and_validate_judge_response(invalid_dim_input)

        # Missing required dimension
        missing_dim_input = """
        {
          "overall_score": 85,
          "dimension_scores": {
            "clarifying_questions": 8,
            "iteration_quality": 9,
            "final_answer_quality": 9
          },
          "reasoning": "Missing hallucination catching."
        }
        """
        with self.assertRaises(ValueError):
            parse_and_validate_judge_response(missing_dim_input)

        # Missing reasoning
        missing_reasoning = """
        {
          "overall_score": 85,
          "dimension_scores": {
            "clarifying_questions": 8,
            "iteration_quality": 9,
            "hallucination_catching": 7,
            "final_answer_quality": 9
          },
          "reasoning": ""
        }
        """
        with self.assertRaises(ValueError):
            parse_and_validate_judge_response(missing_reasoning)

    # ==========================================
    # 5. EVALUATION FAILURE & RETRY SEMANTICS
    # ==========================================
    @patch("backend.app.submissions.call_judge_ai")
    def test_evaluation_failure_and_retry(self, mock_judge_call):
        if not self.has_real_db:
            self.skipTest("Skipping DB integration test.")
        token = self.get_token_for_user("user_a@example.com", "testpassword123", "User A")
        headers = {"Authorization": f"Bearer {token}"}

        # Start submission
        sub_res = self.client.post("/api/submissions", json={"question_id": self.question_id}, headers=headers)
        sub_id = sub_res.json()["submission_id"]

        # Setup Judge failure
        mock_judge_call.side_effect = Exception("Anthropic API Error")

        # Submit answer (should fail)
        submit_res = self.client.post(
            f"/api/submissions/{sub_id}/submit", 
            json={"final_answer_text": "Attempt 1 Final Answer"}, 
            headers=headers
        )
        self.assertEqual(submit_res.status_code, 500)
        self.assertIn("We couldn't evaluate your response right now", submit_res.json()["detail"])

        # DB Submission status should be "evaluation_failed"
        db_sub = self.db.query(Submission).filter(Submission.id == sub_id).first()
        self.assertEqual(db_sub.status, "evaluation_failed")
        self.assertEqual(db_sub.final_answer_text, "Attempt 1 Final Answer")
        
        # Save original submission timing
        orig_submitted_at = db_sub.submitted_at
        orig_started_at = db_sub.started_at

        # Verify no Evaluation is stored in DB
        db_eval = self.db.query(Evaluation).filter(Evaluation.submission_id == sub_id).first()
        self.assertIsNone(db_eval)

        # Retry evaluation (Setup mock success)
        mock_judge_call.side_effect = None
        mock_judge_call.return_value = {
            "overall_score": 90,
            "dimension_scores": {
                "clarifying_questions": 9,
                "iteration_quality": 9,
                "hallucination_catching": 9,
                "final_answer_quality": 9
            },
            "reasoning": "Excellent work."
        }

        # Submit retry
        retry_res = self.client.post(
            f"/api/submissions/{sub_id}/submit", 
            json={"final_answer_text": "This should not overwrite or add transcript turns"}, 
            headers=headers
        )
        self.assertEqual(retry_res.status_code, 200)
        self.assertEqual(retry_res.json()["overall_score"], 90)

        # Verify DB updates
        self.db.refresh(db_sub)
        self.assertEqual(db_sub.status, "submitted")
        self.assertEqual(db_sub.final_answer_text, "Attempt 1 Final Answer") # Should keep original final answer text
        self.assertEqual(db_sub.started_at, orig_started_at) # Should keep original started_at
        self.assertEqual(db_sub.submitted_at, orig_submitted_at) # Should keep original submitted_at

        # Verify exactly one evaluation created
        db_evals = self.db.query(Evaluation).filter(Evaluation.submission_id == sub_id).all()
        self.assertEqual(len(db_evals), 1)
        self.assertEqual(db_evals[0].overall_score, 90)

    # ==========================================
    # 6. ANTI-GAMING HEURISTICS
    # ==========================================
    def test_anti_gaming_heuristics(self):
        # 1. Near-zero conversation
        flags1 = run_anti_gaming_checks(
            started_at=datetime.now(timezone.utc) - timedelta(minutes=5),
            submitted_at=datetime.now(timezone.utc),
            transcript_turns=[], # 0 turns
            final_answer_text="Normal answer."
        )
        self.assertIn("near-zero conversation before submitting", flags1)

        # 2. Extremely fast submission
        flags2 = run_anti_gaming_checks(
            started_at=datetime.now(timezone.utc) - timedelta(seconds=10), # 10s difference
            submitted_at=datetime.now(timezone.utc),
            transcript_turns=[{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}],
            final_answer_text="Normal answer."
        )
        self.assertIn("submitted extremely fast", flags2)

        # 3. Pre-written answer
        pre_written_msg = "A" * 501
        flags3 = run_anti_gaming_checks(
            started_at=datetime.now(timezone.utc) - timedelta(minutes=5),
            submitted_at=datetime.now(timezone.utc),
            transcript_turns=[
                {"role": "user", "content": pre_written_msg},
                {"role": "assistant", "content": "reply"}
            ],
            final_answer_text=pre_written_msg # 100% match
        )
        self.assertIn("first message looks like a pre-written answer, not a genuine question", flags3)

    # ==========================================
    # 7. ATTEMPT HISTORY FILTERS
    # ==========================================
    def test_attempt_history_filters(self):
        if not self.has_real_db:
            self.skipTest("Skipping DB integration test.")
        token = self.get_token_for_user("user_a@example.com", "testpassword123", "User A")
        headers = {"Authorization": f"Bearer {token}"}

        # Create progress and failed submissions to verify history ignores them
        sub_progress = Submission(
            user_id=self.db.query(User).filter(User.email == "user_a@example.com").first().id,
            question_id=self.question_id,
            status="in_progress",
            started_at=datetime.now(timezone.utc)
        )
        sub_failed = Submission(
            user_id=self.db.query(User).filter(User.email == "user_a@example.com").first().id,
            question_id=self.question_id,
            status="evaluation_failed",
            started_at=datetime.now(timezone.utc)
        )
        self.db.add(sub_progress)
        self.db.add(sub_failed)
        self.db.commit()

        # Check history endpoint
        history_res = self.client.get("/api/evaluations/history", headers=headers)
        self.assertEqual(history_res.status_code, 200)
        history = history_res.json()

        # History should only return "submitted" status, check that the submission IDs do not match the pending/failed ones
        ids = [item["submission_id"] for item in history]
        self.assertNotIn(sub_progress.id, ids)
        self.assertNotIn(sub_failed.id, ids)

if __name__ == "__main__":
    unittest.main()
