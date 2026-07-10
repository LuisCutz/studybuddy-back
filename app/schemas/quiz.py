from pydantic import BaseModel
from uuid import UUID
from typing import List, Optional

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