from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.app.db import get_db
from backend.app.models import Question
from backend.app.schemas import QuestionList, QuestionDetail
from backend.app.auth import get_current_user

router = APIRouter(prefix="/questions", tags=["questions"])

@router.get("", response_model=List[QuestionList])
def list_questions(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    questions = db.query(Question).all()
    return questions

@router.get("/{question_id}", response_model=QuestionDetail)
def get_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    return question
