from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.app.db import get_db
from backend.app.models import Submission, Question, Evaluation, TranscriptTurn
from backend.app.schemas import EvaluationResponse, AttemptHistoryItem
from backend.app.auth import get_current_user

router = APIRouter(prefix="/evaluations", tags=["evaluations"])

@router.get("/history", response_model=List[AttemptHistoryItem])
def get_attempt_history(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Fetch only completed attempts owned by current user
    results = db.query(Submission, Question, Evaluation)\
        .join(Question, Question.id == Submission.question_id)\
        .join(Evaluation, Evaluation.submission_id == Submission.id)\
        .filter(Submission.user_id == current_user.id)\
        .filter(Submission.status == "submitted")\
        .order_by(Submission.submitted_at.desc())\
        .all()
    
    history_items = []
    for submission, question, evaluation in results:
        history_items.append(AttemptHistoryItem(
            submission_id=submission.id,
            question_title=question.title,
            overall_score=evaluation.overall_score,
            submitted_at=submission.submitted_at
        ))
    return history_items

@router.get("/{submission_id}", response_model=EvaluationResponse)
def get_submission_evaluation(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    # Ownership Check
    if submission.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not own this submission"
        )
    
    # Check if submission has been graded
    if submission.status != "submitted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This submission has not been successfully evaluated."
        )
    
    evaluation = db.query(Evaluation).filter(Evaluation.submission_id == submission.id).first()
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation data not found."
        )
    
    # Fetch transcript turns
    turns = db.query(TranscriptTurn).filter(
        TranscriptTurn.submission_id == submission.id
    ).order_by(TranscriptTurn.turn_index.asc()).all()
    
    question = submission.question
    
    return EvaluationResponse(
        id=evaluation.id,
        submission_id=submission.id,
        overall_score=evaluation.overall_score,
        dimension_scores_json=evaluation.dimension_scores_json,
        judge_reasoning=evaluation.judge_reasoning,
        anti_gaming_flags=evaluation.anti_gaming_flags,
        created_at=evaluation.created_at,
        question_title=question.title,
        question_difficulty=question.difficulty,
        question_category=question.category,
        final_answer_text=submission.final_answer_text,
        transcript=[
            {"role": t.role, "content": t.content, "created_at": t.created_at}
            for t in turns
        ]
    )
