import os
import sys
import json
from dotenv import load_dotenv

# Ensure backend and root directory in path
backend_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(backend_dir)
sys.path.insert(0, root_dir)

# Load .env
env_path = os.path.join(backend_dir, ".env")
load_dotenv(env_path)
load_dotenv()

# Force live LLM calls
os.environ["RUN_LLM_TESTS"] = "true"

def main():
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    print("==================================================")
    print("      PromptBench - Live Gemini API Verification  ")
    print("==================================================")
    print(f"Target Model: {model}")
    
    if not api_key or not api_key.strip():
        print("\n[!] ERROR: GEMINI_API_KEY is not set or empty in backend/.env!")
        print("    Please ensure you have saved backend/.env with:")
        print("    GEMINI_API_KEY=your_actual_api_key_here")
        print("    GEMINI_MODEL=gemini-2.5-flash")
        sys.exit(1)
        
    masked_key = api_key[:6] + "..." + api_key[-4:] if len(api_key) > 10 else "***"
    print(f"API Key Detected: {masked_key}")
    print("\n--- 1. Testing Helper AI (candidate_llm.py) ---")
    
    from backend.app.candidate_llm import call_helper_ai
    
    prompt_text = "Diagnose the 25% churn increase at NovaSaaS."
    context_data = "NovaSaaS Q3 metric update: Churn increased by 25% following the sunset of custom reports. Support ticket volume increased 40%."
    history = [
        {"role": "user", "content": "What was the main reason for customer churn in Q3?"}
    ]
    
    try:
        reply = call_helper_ai(prompt_text, context_data, history)
        print("[+] Helper AI responded successfully!")
        print(f"Response preview:\n    \"{reply[:200]}...\"\n")
    except Exception as e:
        print(f"[-] Helper AI failed: {e}")
        sys.exit(1)
        
    print("--- 2. Testing Judge AI (judge_llm.py) ---")
    from backend.app.judge_llm import call_judge_ai
    
    transcript = [
        {"role": "user", "content": "What was the main reason for customer churn in Q3?"},
        {"role": "assistant", "content": reply}
    ]
    final_answer = (
        "Based on the data, the 25% churn surge was directly caused by deprecating custom reports, "
        "which enterprise clients depended on. I recommend immediately restoring legacy reporting access "
        "and migrating accounts gradually."
    )
    ground_truth = (
        "True root cause: Enterprise churn surged when custom reporting was decommissioned without a migration tool. "
        "A strong answer identifies this dependency and proposes restoring access or delivering an automated export tool."
    )
    rubric = {
        "dimensions": [
            {"name": "clarifying_questions", "weight": 0.25},
            {"name": "iteration_quality", "weight": 0.25},
            {"name": "hallucination_catching", "weight": 0.25},
            {"name": "final_answer_quality", "weight": 0.25}
        ]
    }
    
    try:
        eval_result = call_judge_ai(
            prompt_text=prompt_text,
            context_data=context_data,
            transcript=transcript,
            final_answer=final_answer,
            ground_truth_notes=ground_truth,
            rubric_json=rubric
        )
        print("[+] Judge AI evaluated successfully with valid schema!")
        print(f"Overall Score: {eval_result['overall_score']}/100")
        print("Dimension Scores:")
        for dim, score in eval_result['dimension_scores'].items():
            print(f"  - {dim}: {score}/10")
        print(f"Reasoning:\n  \"{eval_result['reasoning']}\"")
        print("\n==================================================")
        print("   ALL GEMINI INTEGRATION TESTS PASSED (LIVE)!    ")
        print("==================================================")
    except Exception as e:
        print(f"[-] Judge AI failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
