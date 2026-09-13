import os
from anthropic import Anthropic
from backend.app.config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, RUN_LLM_TESTS

if not ANTHROPIC_MODEL:
    raise ValueError("Configuration Error: ANTHROPIC_MODEL is required.")

client = None
if ANTHROPIC_API_KEY:
    client = Anthropic(api_key=ANTHROPIC_API_KEY)

CANDIDATE_SYSTEM_PROMPT = """You are a helpful AI assistant available to the candidate
for this case study. You have access only to the case context provided below.
You do NOT have access to any rubric, scoring criteria, or ground-truth answer.
Respond naturally and helpfully to the candidate's questions, as a real-world AI
assistant would in a business setting.

Case Context:
{context_data}
"""

def call_helper_ai(prompt_text: str, context_data: str, history: list) -> str:
    """
    history format: [{"role": "user"|"assistant", "content": "..."}]
    """
    # If we are in test/mock mode and RUN_LLM_TESTS is False, return a mock response
    if not RUN_LLM_TESTS or not client:
        return "Mocked Helper AI response: Let's look at the customer survey data. Many churned users specifically complained about custom reporting being removed."

    system_prompt = CANDIDATE_SYSTEM_PROMPT.format(context_data=context_data)
    
    # Map roles: FastAPI database uses 'user' and 'assistant', but Anthropic expects 'user' and 'assistant'
    messages = []
    for turn in history:
        messages.append({
            "role": turn["role"],
            "content": turn["content"]
        })
        
    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=1000,
            system=system_prompt,
            messages=messages
        )
        return response.content[0].text
    except Exception as e:
        # For candidate helper, we raise the exception so the router can return a 500 error
        raise RuntimeError(f"Helper AI API call failed: {str(e)}")
