import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.db import get_db
from backend.app.models import Submission, Question, TranscriptTurn, Evaluation
from backend.app.schemas import SubmissionCreate, SubmissionResponse, MessageCreate, MessageResponse, SubmitFinal, EvaluationResponse
from backend.app.auth import get_current_user
from backend.app.candidate_llm import call_helper_ai
from backend.app.judge_llm import call_judge_ai
from backend.app.anti_gaming import run_anti_gaming_checks

router = APIRouter(prefix="/submissions", tags=["submissions"])
logger = logging.getLogger("submissions")

@router.post("", status_code=status.HTTP_201_CREATED)
def create_submission(
    payload: SubmissionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    question = db.query(Question).filter(Question.id == payload.question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    # Create submission
    submission = Submission(
        user_id=current_user.id,
        question_id=payload.question_id,
        status="in_progress",
        started_at=datetime.now(timezone.utc)
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    
    return {"submission_id": submission.id}

@router.get("/{submission_id}")
def get_submission(
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
    if submission.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not own this submission"
        )
    
    turns = db.query(TranscriptTurn).filter(
        TranscriptTurn.submission_id == submission.id
    ).order_by(TranscriptTurn.turn_index.asc()).all()

    return {
        "id": submission.id,
        "status": submission.status,
        "final_answer_text": submission.final_answer_text,
        "question_id": submission.question_id,
        "question": {
            "id": submission.question.id,
            "title": submission.question.title,
            "category": submission.question.category,
            "difficulty": submission.question.difficulty,
            "prompt_text": submission.question.prompt_text,
            "context_data": submission.question.context_data
        },
        "transcript": [{"role": t.role, "content": t.content} for t in turns]
    }

@router.post("/{submission_id}/message", response_model=MessageResponse)
def add_message(
    submission_id: int,
    payload: MessageCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
        
    # Ownership verification
    if submission.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not own this submission"
        )
        
    # State validation
    if submission.status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Submission is not in progress"
        )

    # Save candidate's message
    user_turn_index = db.query(TranscriptTurn).filter(
        TranscriptTurn.submission_id == submission.id
    ).count()
    
    user_turn = TranscriptTurn(
        submission_id=submission.id,
        turn_index=user_turn_index,
        role="user",
        content=payload.message,
        created_at=datetime.now(timezone.utc)
    )
    db.add(user_turn)
    db.commit()
    db.refresh(user_turn)

    # Fetch all turns for this submission to pass history to helper LLM
    db_turns = db.query(TranscriptTurn).filter(
        TranscriptTurn.submission_id == submission.id
    ).order_index = TranscriptTurn.turn_index.asc()
    
    # Wait, we need to order them correctly
    turns = db.query(TranscriptTurn).filter(
        TranscriptTurn.submission_id == submission.id
    ).order_by(TranscriptTurn.turn_index.asc()).all()
    
    history = [{"role": turn.role, "content": turn.content} for turn in turns]
    
    try:
        reply = call_helper_ai(
            prompt_text=submission.question.prompt_text,
            context_data=submission.question.context_data,
            history=history
        )
    except Exception as e:
        # If helper LLM fails, rollback the user turn we just added to keep transcript clean
        db.delete(user_turn)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Helper AI error: {str(e)}"
        )

    # Save helper AI's reply
    assistant_turn_index = db.query(TranscriptTurn).filter(
        TranscriptTurn.submission_id == submission.id
    ).count()
    
    assistant_turn = TranscriptTurn(
        submission_id=submission.id,
        turn_index=assistant_turn_index,
        role="assistant",
        content=reply,
        created_at=datetime.now(timezone.utc)
    )
    db.add(assistant_turn)
    db.commit()
    
    return {"reply": reply}

@router.post("/{submission_id}/submit", response_model=EvaluationResponse)
def submit_answer(
    submission_id: int,
    payload: SubmitFinal,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
        
    # Ownership check
    if submission.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not own this submission"
        )
        
    # Allowed states: in_progress, evaluation_failed
    if submission.status == "submitted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Submission has already been evaluated"
        )

    # First submission or retry logic
    is_retry = submission.status == "evaluation_failed"
    
    if not is_retry:
        submission.final_answer_text = payload.final_answer_text
        submission.submitted_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(submission)
    
    # Load transcript turns for anti-gaming checks and Judge evaluation
    turns = db.query(TranscriptTurn).filter(
        TranscriptTurn.submission_id == submission.id
    ).order_by(TranscriptTurn.turn_index.asc()).all()
    
    transcript_list = [{"role": turn.role, "content": turn.content} for turn in turns]

    # Run anti-gaming checks (uses original submission times)
    anti_gaming_flags = run_anti_gaming_checks(
        started_at=submission.started_at,
        submitted_at=submission.submitted_at,
        transcript_turns=transcript_list,
        final_answer_text=submission.final_answer_text
    )

    # Call Judge AI
    question = submission.question
    try:
        eval_result = call_judge_ai(
            prompt_text=question.prompt_text,
            context_data=question.context_data,
            transcript=transcript_list,
            final_answer=submission.final_answer_text,
            ground_truth_notes=question.ground_truth_notes,
            rubric_json=question.rubric_json
        )
        
        # Successful evaluation: Create evaluation record, update status to submitted.
        # To avoid duplicates on retry success, delete any existing failed evaluation entries (normally none should exist)
        db.query(Evaluation).filter(Evaluation.submission_id == submission.id).delete()
        
        evaluation = Evaluation(
            submission_id=submission.id,
            overall_score=eval_result["overall_score"],
            dimension_scores_json=eval_result["dimension_scores"],
            judge_reasoning=eval_result["reasoning"],
            anti_gaming_flags=anti_gaming_flags,
            created_at=datetime.now(timezone.utc)
        )
        db.add(evaluation)
        submission.status = "submitted"
        db.commit()
        db.refresh(evaluation)
        
        # Populate response schema fields
        # Note: mapping JSON data correctly to returning structure
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
    except Exception as e:
        logger.error(f"Judge evaluation failed for submission {submission_id}: {str(e)}", exc_info=True)
        # Transition to evaluation_failed
        submission.status = "evaluation_failed"
        db.commit()
        
        # Safe user-facing error message
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="We couldn't evaluate your response right now. Please try again."
        )
