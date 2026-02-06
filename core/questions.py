"""Question manager for loading and serving questions."""

import json
import os
import random
from typing import List, Dict, Optional, Any
from pathlib import Path

from models.question import Question
from config.caps_curriculum import ALL_TOPICS, TOPICS_BY_ID


class QuestionManager:
    """Manages loading and retrieval of questions from JSON files."""

    def __init__(self, questions_dir: str = None):
        """Initialize the question manager."""
        if questions_dir is None:
            # Get the directory where this file is located
            base_dir = Path(__file__).parent.parent
            questions_dir = base_dir / "questions"
        self.questions_dir = Path(questions_dir)
        self._questions: Dict[str, List[Question]] = {}
        self._load_all_questions()

    def _load_all_questions(self):
        """Load all questions from JSON files."""
        for topic in ALL_TOPICS:
            paper_dir = "paper1" if topic.paper == 1 else "paper2"
            file_path = self.questions_dir / paper_dir / f"{topic.id}.json"

            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        questions = []
                        for q_data in data.get('questions', []):
                            q_data['topic_id'] = topic.id
                            questions.append(Question.from_dict(q_data))
                        self._questions[topic.id] = questions
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Warning: Error loading {file_path}: {e}")
                    self._questions[topic.id] = []
            else:
                self._questions[topic.id] = []

    def get_questions_for_topic(self, topic_id: str) -> List[Question]:
        """Get all questions for a topic."""
        return self._questions.get(topic_id, [])

    def get_questions_for_subtopic(self, topic_id: str, subtopic_id: str) -> List[Question]:
        """Get all questions for a specific subtopic."""
        return [q for q in self._questions.get(topic_id, [])
                if q.subtopic_id == subtopic_id]

    def get_questions_by_difficulty(self, topic_id: str, difficulty: int) -> List[Question]:
        """Get questions of a specific difficulty level."""
        return [q for q in self._questions.get(topic_id, [])
                if q.difficulty == difficulty]

    def get_random_questions(self, topic_id: str, count: int,
                              exclude_ids: List[str] = None,
                              difficulty_range: tuple = None) -> List[Question]:
        """Get random questions for a topic."""
        questions = self._questions.get(topic_id, [])

        if exclude_ids:
            questions = [q for q in questions if q.id not in exclude_ids]

        if difficulty_range:
            min_diff, max_diff = difficulty_range
            questions = [q for q in questions
                        if min_diff <= q.difficulty <= max_diff]

        if len(questions) <= count:
            return questions.copy()

        return random.sample(questions, count)

    def get_diagnostic_questions(self, questions_per_topic: int = 3) -> Dict[str, List[Question]]:
        """Get questions for diagnostic test - mixed difficulties per topic."""
        result = {}
        for topic in ALL_TOPICS:
            topic_questions = []
            available = self._questions.get(topic.id, [])

            if not available:
                continue

            # Try to get a mix of difficulties
            for difficulty in [1, 2, 3]:
                diff_questions = [q for q in available if q.difficulty == difficulty]
                if diff_questions:
                    topic_questions.extend(random.sample(diff_questions,
                                          min(1, len(diff_questions))))

            # Fill remaining slots with random questions
            remaining = questions_per_topic - len(topic_questions)
            if remaining > 0:
                used_ids = {q.id for q in topic_questions}
                unused = [q for q in available if q.id not in used_ids]
                if unused:
                    topic_questions.extend(random.sample(unused,
                                          min(remaining, len(unused))))

            if topic_questions:
                result[topic.id] = topic_questions

        return result

    def get_drill_questions(self, topic_id: str, count: int,
                            weak_subtopics: List[str] = None,
                            weak_weight: float = 2.0) -> List[Question]:
        """Get questions for drill mode, prioritizing weak subtopics."""
        available = self._questions.get(topic_id, [])

        if not available:
            return []

        if not weak_subtopics:
            return self.get_random_questions(topic_id, count)

        # Weight questions from weak subtopics higher
        weighted_pool = []
        for q in available:
            weight = weak_weight if q.subtopic_id in weak_subtopics else 1.0
            weighted_pool.extend([q] * int(weight))

        if len(weighted_pool) <= count:
            return list(set(weighted_pool))

        # Sample without replacement from unique questions
        selected = set()
        result = []
        while len(result) < count and weighted_pool:
            q = random.choice(weighted_pool)
            if q.id not in selected:
                selected.add(q.id)
                result.append(q)
            # Remove all instances of this question from pool
            weighted_pool = [x for x in weighted_pool if x.id != q.id]

        return result

    def get_test_questions(self, topic_id: str, count: int = 10) -> List[Question]:
        """Get questions for a topic test - balanced by subtopic and difficulty."""
        available = self._questions.get(topic_id, [])

        if not available:
            return []

        topic = TOPICS_BY_ID.get(topic_id)
        if not topic:
            return self.get_random_questions(topic_id, count)

        # Try to cover all subtopics
        questions_per_subtopic = max(1, count // len(topic.subtopics))
        result = []
        used_ids = set()

        for subtopic in topic.subtopics:
            subtopic_questions = [q for q in available
                                  if q.subtopic_id == subtopic.id and q.id not in used_ids]
            selected = random.sample(subtopic_questions,
                                    min(questions_per_subtopic, len(subtopic_questions)))
            result.extend(selected)
            used_ids.update(q.id for q in selected)

        # Fill remaining with random questions
        remaining = count - len(result)
        if remaining > 0:
            unused = [q for q in available if q.id not in used_ids]
            if unused:
                result.extend(random.sample(unused, min(remaining, len(unused))))

        random.shuffle(result)
        return result

    def get_mock_exam_questions(self, paper: int) -> List[Question]:
        """Get questions for a mock exam paper."""
        from config.caps_curriculum import PAPER1_TOPICS, PAPER2_TOPICS

        topics = PAPER1_TOPICS if paper == 1 else PAPER2_TOPICS
        result = []

        for topic in topics:
            # Get questions proportional to topic weight
            available = self._questions.get(topic.id, [])
            if not available:
                continue

            # Calculate number of questions based on marks allocation
            # Aim for roughly marks/3 questions (average 3 marks per question)
            target_count = max(3, topic.marks // 3)
            questions = self.get_random_questions(topic.id, target_count)
            result.extend(questions)

        random.shuffle(result)
        return result

    def get_question_by_id(self, question_id: str) -> Optional[Question]:
        """Get a specific question by its ID."""
        for questions in self._questions.values():
            for q in questions:
                if q.id == question_id:
                    return q
        return None

    def get_topic_question_count(self, topic_id: str) -> int:
        """Get the number of questions available for a topic."""
        return len(self._questions.get(topic_id, []))

    def get_total_question_count(self) -> int:
        """Get total number of questions across all topics."""
        return sum(len(questions) for questions in self._questions.values())
