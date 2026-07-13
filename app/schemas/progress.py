from pydantic import BaseModel
from datetime import date
from uuid import UUID

class StudentProgressResponse(BaseModel):
    total_quizzes_taken: int
    average_quiz_score: float
    total_flashcards_generated: int

class DailyActivityResponse(BaseModel):
    activity_date: date
    minutes_spent: int