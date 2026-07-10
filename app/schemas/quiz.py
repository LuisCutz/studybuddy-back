from pydantic import BaseModel
from uuid import UUID
from typing import List, Optional
from datetime import datetime

class GenerateQuizRequest(BaseModel):
    document_id: UUID
    num_questions: int = 5

class QuestionResponse(BaseModel):
    id: UUID
    type: str
    prompt: str
    options: list | dict

    class Config:
        from_attributes = True

class QuizResponse(BaseModel):
    id: UUID
    subject_id: UUID
    title: str
    topic: str
    questions: List[QuestionResponse] = []

    class Config:
        from_attributes = True

class QuestionWithAnswerResponse(QuestionResponse):
    correct_answer: str
    
    class Config:
        from_attributes = True

class QuizWithAnswersResponse(QuizResponse):
    questions: list[QuestionWithAnswerResponse] = []
    
    class Config:
        from_attributes = True

class StartAttemptResponse(BaseModel):
    attempt_id: UUID
    started_at: datetime
    message: str

class SubmitAnswerRequest(BaseModel):
    question_id: UUID
    selected_option: str

class SubmitAnswerResponse(BaseModel):
    is_correct: bool
    correct_answer: str
    message: str

class FinishAttemptResponse(BaseModel):
    attempt_id: UUID
    score: float
    completed_at: datetime
    total_questions: int
    correct_answers: int