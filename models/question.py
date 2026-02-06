"""Question model for the study program."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union


@dataclass
class CommonMistake:
    """Represents a common mistake students make."""
    mistake: str
    explanation: str


@dataclass
class SubQuestion:
    """Represents a sub-question in a multi-part question."""
    label: str  # e.g., "a", "b", "c"
    question_text: str
    answer: Any
    marks: int


@dataclass
class Question:
    """Represents a study question."""
    id: str
    topic_id: str
    subtopic_id: str
    question_type: str  # multiple_choice, numeric, expression, multi_part, proof
    difficulty: int  # 1-4
    marks: int
    question_text: str
    answer: Any  # Can be string, number, list, or dict for multi-part
    tolerance: float = 0.01
    options: Optional[List[str]] = None  # For multiple choice
    hints: List[str] = field(default_factory=list)
    explanation: str = ""
    common_mistakes: List[CommonMistake] = field(default_factory=list)
    nsc_reference: str = ""
    sub_questions: List[SubQuestion] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Question':
        """Create a Question from a dictionary (JSON data)."""
        # Handle common mistakes
        common_mistakes = []
        for cm in data.get('common_mistakes', []):
            common_mistakes.append(CommonMistake(
                mistake=cm.get('mistake', ''),
                explanation=cm.get('explanation', '')
            ))

        # Handle sub-questions
        sub_questions = []
        for sq in data.get('sub_questions', []):
            sub_questions.append(SubQuestion(
                label=sq.get('label', ''),
                question_text=sq.get('question_text', ''),
                answer=sq.get('answer'),
                marks=sq.get('marks', 1)
            ))

        return cls(
            id=data['id'],
            topic_id=data.get('topic_id', ''),
            subtopic_id=data.get('subtopic_id', ''),
            question_type=data.get('question_type', 'numeric'),
            difficulty=data.get('difficulty', 2),
            marks=data.get('marks', 1),
            question_text=data['question_text'],
            answer=data['answer'],
            tolerance=data.get('tolerance', 0.01),
            options=data.get('options'),
            hints=data.get('hints', []),
            explanation=data.get('explanation', ''),
            common_mistakes=common_mistakes,
            nsc_reference=data.get('nsc_reference', ''),
            sub_questions=sub_questions
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'topic_id': self.topic_id,
            'subtopic_id': self.subtopic_id,
            'question_type': self.question_type,
            'difficulty': self.difficulty,
            'marks': self.marks,
            'question_text': self.question_text,
            'answer': self.answer,
            'tolerance': self.tolerance,
            'options': self.options,
            'hints': self.hints,
            'explanation': self.explanation,
            'common_mistakes': [
                {'mistake': cm.mistake, 'explanation': cm.explanation}
                for cm in self.common_mistakes
            ],
            'nsc_reference': self.nsc_reference,
            'sub_questions': [
                {
                    'label': sq.label,
                    'question_text': sq.question_text,
                    'answer': sq.answer,
                    'marks': sq.marks
                }
                for sq in self.sub_questions
            ]
        }
