from pydantic import BaseModel, EmailStr, Field
from typing import List, Dict, Optional, Any
from datetime import datetime

# Auth Schemas
class UserSignup(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    token: str
    token_type: str = "bearer"

# Question Schemas
class QuestionList(BaseModel):
    id: int
    title: str
    category: str
    difficulty: str

    class Config:
        from_attributes = True

class QuestionDetail(BaseModel):
    id: int
    title: str
    category: str
    difficulty: str
    prompt_text: str
    context_data: str

    class Config:
        from_attributes = True

# Submission Schemas
class SubmissionCreate(BaseModel):
    question_id: int

class SubmissionResponse(BaseModel):
    id: int
    user_id: int
    question_id: int
    status: str
    started_at: datetime
    submitted_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    message: str = Field(..., min_length=1)

class MessageResponse(BaseModel):
    reply: str

class SubmitFinal(BaseModel):
    final_answer_text: str = Field(..., min_length=1)

# Transcript Turn Schemas
class TranscriptTurnResponse(BaseModel):
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

# Evaluation Schemas
class DimensionScores(BaseModel):
    clarifying_questions: int = Field(..., ge=0, le=10)
    iteration_quality: int = Field(..., ge=0, le=10)
    hallucination_catching: int = Field(..., ge=0, le=10)
    final_answer_quality: int = Field(..., ge=0, le=10)

class EvaluationDetail(BaseModel):
    overall_score: int = Field(..., ge=0, le=10)
    dimension_scores: DimensionScores
    reasoning: str

class EvaluationResponse(BaseModel):
    id: int
    submission_id: int
    overall_score: Optional[int]
    dimension_scores_json: Optional[Dict[str, int]]
    judge_reasoning: Optional[str]
    anti_gaming_flags: Optional[List[str]]
    created_at: datetime
    question_title: Optional[str] = None
    question_difficulty: Optional[str] = None
    question_category: Optional[str] = None
    final_answer_text: Optional[str] = None
    transcript: Optional[List[TranscriptTurnResponse]] = None

    class Config:
        from_attributes = True

# Attempt History Schema
class AttemptHistoryItem(BaseModel):
    submission_id: int
    question_title: str
    overall_score: int
    submitted_at: datetime

    class Config:
        from_attributes = True
