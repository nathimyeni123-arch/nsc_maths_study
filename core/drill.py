"""Drill mode module for practice sessions."""

from typing import List, Dict, Optional, Callable
from datetime import datetime

from models.question import Question
from models.student import Student
from core.questions import QuestionManager
from core.grader import Grader
from core.explainer import Explainer
from data.storage import Storage
from config.settings import DRILL_QUESTIONS_DEFAULT, DRILL_WEAK_AREA_WEIGHT
from config.caps_curriculum import TOPICS_BY_ID


class DrillSession:
    """Handles drill practice sessions."""

    def __init__(self, storage: Storage, question_manager: QuestionManager):
        """Initialize drill session handler."""
        self.storage = storage
        self.question_manager = question_manager
        self.grader = Grader()
        self.explainer = Explainer()

    def get_drill_questions(self, student_id: int, topic_id: str,
                            count: int = DRILL_QUESTIONS_DEFAULT) -> List[Question]:
        """Get questions for a drill session, prioritizing weak subtopics."""
        # Get weak subtopics from previous attempts
        weak_subtopics = self.storage.get_weak_subtopics(student_id, topic_id)
        weak_ids = [st[0] for st in weak_subtopics if st[1] < 70]  # Below 70% accuracy

        return self.question_manager.get_drill_questions(
            topic_id, count, weak_ids, DRILL_WEAK_AREA_WEIGHT
        )

    def run_drill(self, student: Student, topic_id: str,
                  question_count: int, answer_callback: Callable,
                  show_explanation: bool = True) -> Dict:
        """
        Run a drill session.

        Args:
            student: The student
            topic_id: Topic to drill
            question_count: Number of questions
            answer_callback: Function(question, index, total) -> (answer, want_hint)
            show_explanation: Whether to show explanations after each question

        Returns:
            Session results dictionary
        """
        topic = TOPICS_BY_ID.get(topic_id)
        if not topic:
            return {'error': f"Topic '{topic_id}' not found"}

        questions = self.get_drill_questions(student.id, topic_id, question_count)
        if not questions:
            return {'error': f"No questions available for {topic.name}"}

        session_id = self.storage.start_session(student.id, "drill", topic_id)

        results = {
            'topic': topic.name,
            'correct': 0,
            'total': len(questions),
            'marks_earned': 0,
            'marks_possible': 0,
            'question_results': [],
            'weak_subtopics': set()
        }

        for i, question in enumerate(questions):
            # Get answer (callback may also request hint)
            answer, requested_hint = answer_callback(question, i + 1, len(questions))

            # Grade the answer
            is_correct, marks, feedback = self.grader.check_answer(question, answer)

            # Record attempt
            self.storage.record_question_attempt(
                student_id=student.id,
                session_id=session_id,
                question_id=question.id,
                topic_id=topic_id,
                subtopic_id=question.subtopic_id,
                student_answer=answer,
                correct_answer=str(question.answer),
                is_correct=is_correct,
                marks_earned=marks,
                marks_possible=question.marks
            )

            # Update topic progress
            self.storage.record_drill_attempt(student.id, topic_id, is_correct)

            # Track results
            if is_correct:
                results['correct'] += 1
            else:
                results['weak_subtopics'].add(question.subtopic_id)

            results['marks_earned'] += marks
            results['marks_possible'] += question.marks

            question_result = {
                'question': question,
                'answer': answer,
                'is_correct': is_correct,
                'marks': marks,
                'feedback': feedback,
                'used_hint': requested_hint
            }

            # Generate explanation if needed
            if show_explanation and not is_correct:
                question_result['explanation'] = self.explainer.get_full_explanation(
                    question, answer, is_correct
                )

            results['question_results'].append(question_result)

        # Calculate final stats
        results['percentage'] = (results['correct'] / results['total'] * 100) if results['total'] > 0 else 0
        results['weak_subtopics'] = list(results['weak_subtopics'])

        # End session
        self.storage.end_session(
            session_id,
            results['total'],
            results['correct'],
            results['percentage']
        )

        return results

    def format_results(self, results: Dict) -> str:
        """Format drill session results for display."""
        lines = []
        lines.append("\n" + "=" * 50)
        lines.append("         DRILL SESSION COMPLETE")
        lines.append("=" * 50)

        lines.append(f"\nTopic: {results['topic']}")
        lines.append(f"Score: {results['correct']}/{results['total']} ({results['percentage']:.1f}%)")
        lines.append(f"Marks: {results['marks_earned']:.0f}/{results['marks_possible']:.0f}")

        # Performance indicator
        if results['percentage'] >= 90:
            lines.append("\n*** Excellent! You're mastering this topic!")
        elif results['percentage'] >= 70:
            lines.append("\n[OK] Good work! Keep practicing to reach mastery.")
        elif results['percentage'] >= 50:
            lines.append("\n[~] Getting there! Focus on your weak areas.")
        else:
            lines.append("\n(!) More practice needed. Review the explanations carefully.")

        # Weak subtopics
        if results['weak_subtopics']:
            lines.append("\n" + "-" * 40)
            lines.append("Areas needing more practice:")
            for subtopic in results['weak_subtopics']:
                lines.append(f"  • {subtopic.replace('_', ' ').title()}")

        lines.append("\n" + "=" * 50)

        return "\n".join(lines)

    def get_subtopic_stats(self, student_id: int, topic_id: str) -> Dict[str, Dict]:
        """Get performance statistics by subtopic."""
        topic = TOPICS_BY_ID.get(topic_id)
        if not topic:
            return {}

        stats = {}
        weak_subtopics = self.storage.get_weak_subtopics(student_id, topic_id, limit=20)
        weak_dict = {st[0]: st[1] for st in weak_subtopics}

        for subtopic in topic.subtopics:
            accuracy = weak_dict.get(subtopic.id, None)
            stats[subtopic.id] = {
                'name': subtopic.name,
                'accuracy': accuracy,
                'status': 'not_attempted' if accuracy is None else
                          'mastered' if accuracy >= 70 else 'weak'
            }

        return stats
