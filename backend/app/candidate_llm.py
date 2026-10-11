import os
from google import genai
from google.genai import types
from backend.app.config import GEMINI_API_KEY, GEMINI_MODEL, RUN_LLM_TESTS

if not GEMINI_MODEL:
    raise ValueError("Configuration Error: GEMINI_MODEL is required.")

client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)

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
    
    # Map roles: FastAPI database uses 'user' and 'assistant', but Gemini expects 'user' and 'model'
    contents = []
    for turn in history:
        role = "user" if turn["role"] == "user" else "model"
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=turn["content"])]
            )
        )
        
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=1000,
            )
        )
        return response.text
    except Exception as e:
        # For candidate helper, we raise the exception so the router can return a 500 error
        raise RuntimeError(f"Helper AI API call failed: {str(e)}")
