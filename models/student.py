"""Student profile model."""

from dataclasses import dataclass, field
from typing import Dict, Optional
from datetime import datetime


@dataclass
class Student:
    """Represents a student profile."""
    id: int
    name: str
    created_at: datetime = field(default_factory=datetime.now)
    diagnostic_completed: bool = False
    diagnostic_date: Optional[datetime] = None
    total_study_time: int = 0  # in minutes
    mock_exams_completed: int = 0
    best_mock_paper1: float = 0.0
    best_mock_paper2: float = 0.0

    @property
    def display_study_time(self) -> str:
        """Format study time for display."""
        hours = self.total_study_time // 60
        minutes = self.total_study_time % 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"


@dataclass
class StudySession:
    """Represents a study session."""
    id: int
    student_id: int
    session_type: str  # diagnostic, drill, test, mock_exam
    topic_id: Optional[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    questions_attempted: int = 0
    questions_correct: int = 0
    score: Optional[float] = None

    @property
    def duration_minutes(self) -> int:
        """Calculate session duration in minutes."""
        if self.end_time is None:
            return 0
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)

    @property
    def accuracy(self) -> float:
        """Calculate accuracy percentage."""
        if self.questions_attempted == 0:
            return 0.0
        return (self.questions_correct / self.questions_attempted) * 100
