"""Topic progress model."""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class TopicProgress:
    """Tracks a student's progress in a specific topic."""
    student_id: int
    topic_id: str
    drill_attempts: int = 0
    drill_correct: int = 0
    test_attempts: int = 0
    test_best_score: float = 0.0
    last_drill_date: Optional[datetime] = None
    last_test_date: Optional[datetime] = None
    mastered: bool = False

    @property
    def drill_accuracy(self) -> float:
        """Calculate drill accuracy percentage."""
        if self.drill_attempts == 0:
            return 0.0
        return (self.drill_correct / self.drill_attempts) * 100

    @property
    def is_weak(self) -> bool:
        """Check if this topic needs more practice."""
        return self.drill_accuracy < 70 or not self.mastered

    def record_drill_attempt(self, correct: bool):
        """Record a drill question attempt."""
        self.drill_attempts += 1
        if correct:
            self.drill_correct += 1
        self.last_drill_date = datetime.now()

    def record_test_score(self, score: float):
        """Record a topic test score."""
        self.test_attempts += 1
        if score > self.test_best_score:
            self.test_best_score = score
        if score >= 70:
            self.mastered = True
        self.last_test_date = datetime.now()
