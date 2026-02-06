"""Diagnostic test module."""

from typing import Dict, List, Tuple
from datetime import datetime

from models.question import Question
from models.student import Student
from core.questions import QuestionManager
from core.grader import Grader
from data.storage import Storage
from config.settings import DIAGNOSTIC_QUESTIONS_PER_TOPIC
from config.caps_curriculum import ALL_TOPICS, TOPICS_BY_ID


class DiagnosticTest:
    """Handles the initial diagnostic test to assess student knowledge."""

    def __init__(self, storage: Storage, question_manager: QuestionManager):
        """Initialize the diagnostic test."""
        self.storage = storage
        self.question_manager = question_manager
        self.grader = Grader()

    def get_questions(self) -> Dict[str, List[Question]]:
        """Get all diagnostic test questions organized by topic."""
        return self.question_manager.get_diagnostic_questions(
            DIAGNOSTIC_QUESTIONS_PER_TOPIC
        )

    def get_question_count(self) -> int:
        """Get total number of questions in diagnostic test."""
        questions = self.get_questions()
        return sum(len(qs) for qs in questions.values())

    def run_diagnostic(self, student: Student, answer_callback) -> Dict[str, any]:
        """
        Run the diagnostic test.

        Args:
            student: The student taking the test
            answer_callback: Function that takes (question, topic_name) and returns answer string

        Returns:
            Dictionary with results including topic scores
        """
        questions = self.get_questions()
        session_id = self.storage.start_session(student.id, "diagnostic")

        results = {
            'total_correct': 0,
            'total_questions': 0,
            'total_marks': 0,
            'max_marks': 0,
            'topic_results': {},
            'weak_topics': [],
            'strong_topics': [],
            'question_results': []
        }

        # Process each topic
        for topic in ALL_TOPICS:
            topic_questions = questions.get(topic.id, [])
            if not topic_questions:
                continue

            topic_correct = 0
            topic_marks = 0
            topic_max_marks = 0

            for question in topic_questions:
                # Get answer from callback
                answer = answer_callback(question, topic.name)

                # Grade the answer
                is_correct, marks, feedback = self.grader.check_answer(question, answer)

                # Record attempt
                self.storage.record_question_attempt(
                    student_id=student.id,
                    session_id=session_id,
                    question_id=question.id,
                    topic_id=topic.id,
                    subtopic_id=question.subtopic_id,
                    student_answer=answer,
                    correct_answer=str(question.answer),
                    is_correct=is_correct,
                    marks_earned=marks,
                    marks_possible=question.marks
                )

                # Update drill stats
                self.storage.record_drill_attempt(student.id, topic.id, is_correct)

                # Accumulate results
                if is_correct:
                    topic_correct += 1
                topic_marks += marks
                topic_max_marks += question.marks
                results['total_questions'] += 1
                results['total_marks'] += marks
                results['max_marks'] += question.marks

                results['question_results'].append({
                    'question': question,
                    'answer': answer,
                    'is_correct': is_correct,
                    'marks': marks,
                    'feedback': feedback
                })

            # Calculate topic score
            topic_score = (topic_marks / topic_max_marks * 100) if topic_max_marks > 0 else 0
            results['topic_results'][topic.id] = {
                'name': topic.name,
                'correct': topic_correct,
                'total': len(topic_questions),
                'marks': topic_marks,
                'max_marks': topic_max_marks,
                'percentage': topic_score
            }
            results['total_correct'] += topic_correct

            # Categorize topic
            if topic_score >= 70:
                results['strong_topics'].append(topic.id)
            else:
                results['weak_topics'].append(topic.id)

        # End session
        overall_score = (results['total_marks'] / results['max_marks'] * 100) if results['max_marks'] > 0 else 0
        self.storage.end_session(
            session_id,
            results['total_questions'],
            results['total_correct'],
            overall_score
        )

        # Mark diagnostic as completed
        self.storage.mark_diagnostic_completed(student.id)

        results['overall_percentage'] = overall_score
        return results

    def format_results(self, results: Dict) -> str:
        """Format diagnostic results for display."""
        lines = []
        lines.append("\n" + "=" * 60)
        lines.append("           DIAGNOSTIC TEST RESULTS")
        lines.append("=" * 60)

        # Overall score
        lines.append(f"\nOverall Score: {results['total_marks']:.0f}/{results['max_marks']:.0f} ({results['overall_percentage']:.1f}%)")
        lines.append(f"Questions: {results['total_correct']}/{results['total_questions']} correct")

        # Paper 1 topics
        lines.append("\n" + "-" * 40)
        lines.append("PAPER 1 TOPICS")
        lines.append("-" * 40)
        for topic in ALL_TOPICS:
            if topic.paper == 1 and topic.id in results['topic_results']:
                tr = results['topic_results'][topic.id]
                status = "[OK]" if tr['percentage'] >= 70 else "[X]"
                lines.append(f"  {status} {tr['name']:<25} {tr['percentage']:>5.1f}%  ({tr['correct']}/{tr['total']})")

        # Paper 2 topics
        lines.append("\n" + "-" * 40)
        lines.append("PAPER 2 TOPICS")
        lines.append("-" * 40)
        for topic in ALL_TOPICS:
            if topic.paper == 2 and topic.id in results['topic_results']:
                tr = results['topic_results'][topic.id]
                status = "[OK]" if tr['percentage'] >= 70 else "[X]"
                lines.append(f"  {status} {tr['name']:<25} {tr['percentage']:>5.1f}%  ({tr['correct']}/{tr['total']})")

        # Recommendations
        lines.append("\n" + "-" * 40)
        lines.append("RECOMMENDATIONS")
        lines.append("-" * 40)

        if results['weak_topics']:
            lines.append("\n(!) Focus on these topics (below 70%):")
            for topic_id in results['weak_topics']:
                topic = TOPICS_BY_ID.get(topic_id)
                if topic:
                    lines.append(f"  • {topic.name}")

        if results['strong_topics']:
            lines.append("\n[OK] Strong performance in:")
            for topic_id in results['strong_topics']:
                topic = TOPICS_BY_ID.get(topic_id)
                if topic:
                    lines.append(f"  • {topic.name}")

        lines.append("\n" + "=" * 60)
        lines.append("Use Topic Drills to practice weak areas, then take Topic Tests.")
        lines.append("=" * 60 + "\n")

        return "\n".join(lines)
