import os
import json
import re
import logging
from typing import Dict, List
from pydantic import BaseModel, Field, ValidationError
from google import genai
from google.genai import types
from backend.app.config import GEMINI_API_KEY, GEMINI_MODEL, RUN_LLM_TESTS

logger = logging.getLogger("judge_llm")

if not GEMINI_MODEL:
    raise ValueError("Configuration Error: GEMINI_MODEL is required.")

client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)

# Strict Pydantic schemas for Judge output validation
class DimensionScoresModel(BaseModel):
    clarifying_questions: int = Field(..., ge=0, le=10)
    iteration_quality: int = Field(..., ge=0, le=10)
    hallucination_catching: int = Field(..., ge=0, le=10)
    final_answer_quality: int = Field(..., ge=0, le=10)

class JudgeOutput(BaseModel):
    overall_score: int = Field(..., ge=0, le=100)
    dimension_scores: DimensionScoresModel
    reasoning: str = Field(..., min_length=1)

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
  "dimension_scores": {{
    "clarifying_questions": <0-10>,
    "iteration_quality": <0-10>,
    "hallucination_catching": <0-10>,
    "final_answer_quality": <0-10>
  }},
  "overall_score": <0-100>,
  "reasoning": "<concise explanation>"
}}

Rubric: {rubric_json}
Ground truth notes: {ground_truth_notes}
"""

def parse_and_validate_judge_response(response_text: str) -> dict:
    """
    Tries parsing response_text as JSON. Extracts the JSON object if it is
    wrapped in markdown fences or additional text, then validates it using Pydantic.
    """
    clean_text = response_text.strip()
    
    # 1. Direct parsing attempt
    try:
        data = json.loads(clean_text)
    except json.JSONDecodeError:
        # 2. Try extracting JSON using a regex looking for {...}
        match = re.search(r"(\{.*\})", clean_text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse regex-extracted JSON block: {clean_text}")
                raise ValueError("Judge output is not valid JSON") from e
        else:
            logger.error(f"No JSON block found in judge response: {clean_text}")
            raise ValueError("Judge output is not valid JSON")

    # 3. Normalize numeric scores to integers before validation
    if isinstance(data, dict):
        if "overall_score" in data and isinstance(data["overall_score"], (int, float)):
            data["overall_score"] = round(data["overall_score"])
        if "dimension_scores" in data and isinstance(data["dimension_scores"], dict):
            for k, v in data["dimension_scores"].items():
                if isinstance(v, (int, float)):
                    data["dimension_scores"][k] = round(v)

    # 4. Pydantic validation
    try:
        validated = JudgeOutput(**data)
        # Convert Pydantic model to dict
        return validated.model_dump()
    except ValidationError as e:
        logger.error(f"Validation failed for parsed Judge JSON. Data: {data}. Error: {e}")
        raise ValueError(f"Judge output validation failed: {str(e)}") from e

def call_judge_ai(
    prompt_text: str,
    context_data: str,
    transcript: List[dict],
    final_answer: str,
    ground_truth_notes: str,
    rubric_json: dict
) -> dict:
    """
    Prepares prompts, calls the Judge LLM, parses and validates the response.
    """
    # Fallback to mock response in test mode or when Gemini client is not configured
    if not RUN_LLM_TESTS or not client:
        return {
            "overall_score": 82,
            "dimension_scores": {
                "clarifying_questions": 8,
                "iteration_quality": 7,
                "hallucination_catching": 9,
                "final_answer_quality": 8
            },
            "reasoning": "Mocked Judge evaluation: The candidate successfully identified the correlation between feature removal and churn spike, and proposed a viable mitigation plan."
        }

    # Format transcript turns into plain text
    formatted_transcript = ""
    for idx, turn in enumerate(transcript):
        role = "Candidate" if turn["role"] == "user" else "Assistant"
        formatted_transcript += f"Turn {idx + 1} - {role}: {turn['content']}\n\n"

    system_prompt = JUDGE_SYSTEM_PROMPT.format(
        rubric_json=json.dumps(rubric_json),
        ground_truth_notes=ground_truth_notes
    )

    user_content = (
        f"--- Candidate Question/Task ---\n{prompt_text}\n\n"
        f"--- Public Context Provided ---\n{context_data}\n\n"
        f"--- Conversation Transcript ---\n{formatted_transcript}\n"
        f"--- Candidate's Final Submitted Answer ---\n{final_answer}\n"
    )

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=user_content,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=1500,
                response_mime_type="application/json",
            )
        )
        raw_text = response.text or ""
        return parse_and_validate_judge_response(raw_text)
    except Exception as e:
        logger.error(f"Error in call_judge_ai: {e}")
        raise RuntimeError(f"Judge AI call failed: {str(e)}")
