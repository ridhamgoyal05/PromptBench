from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from backend.app.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    submissions = relationship("Submission", back_populates="user", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)  # 'data_diagnosis' | 'strategy_generation' | 'customer_reasoning'
    prompt_text = Column(Text, nullable=False)
    context_data = Column(Text, nullable=False)
    ground_truth_notes = Column(Text, nullable=False)
    difficulty = Column(String, nullable=False)  # 'easy' | 'medium' | 'hard'
    rubric_json = Column(JSONB, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    submissions = relationship("Submission", back_populates="question", cascade="all, delete-orphan")

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="in_progress")  # 'in_progress' | 'submitted' | 'evaluation_failed'
    final_answer_text = Column(Text, nullable=True)
    started_at = Column(DateTime, server_default=func.now())
    submitted_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="submissions")
    question = relationship("Question", back_populates="submissions")
    transcript_turns = relationship("TranscriptTurn", back_populates="submission", cascade="all, delete-orphan")
    evaluations = relationship("Evaluation", back_populates="submission", cascade="all, delete-orphan")

class TranscriptTurn(Base):
    __tablename__ = "transcript_turns"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    turn_index = Column(Integer, nullable=False)
    role = Column(String, nullable=False)  # 'user' | 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    submission = relationship("Submission", back_populates="transcript_turns")

class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    overall_score = Column(Integer, nullable=True)
    dimension_scores_json = Column(JSONB, nullable=True)
    judge_reasoning = Column(Text, nullable=True)
    anti_gaming_flags = Column(JSONB, nullable=True)  # List of string warnings
    created_at = Column(DateTime, server_default=func.now())

    submission = relationship("Submission", back_populates="evaluations")
