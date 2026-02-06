"""Topic test module."""

from typing import Dict, List, Callable
from datetime import datetime

from models.question import Question
from models.student import Student
from core.questions import QuestionManager
from core.grader import Grader
from core.explainer import Explainer
from data.storage import Storage
from config.settings import TOPIC_TEST_QUESTIONS, PASS_MARK
from config.caps_curriculum import TOPICS_BY_ID


class TopicTest:
    """Handles topic tests with pass/fail threshold."""

    def __init__(self, storage: Storage, question_manager: QuestionManager):
        """Initialize topic test handler."""
        self.storage = storage
        self.question_manager = question_manager
        self.grader = Grader()
        self.explainer = Explainer()

    def get_test_questions(self, topic_id: str,
                           count: int = TOPIC_TEST_QUESTIONS) -> List[Question]:
        """Get questions for a topic test."""
        return self.question_manager.get_test_questions(topic_id, count)

    def run_test(self, student: Student, topic_id: str,
                 answer_callback: Callable) -> Dict:
        """
        Run a topic test.

        Args:
            student: The student taking the test
            topic_id: Topic to test
            answer_callback: Function(question, index, total) -> answer

        Returns:
            Test results dictionary
        """
        topic = TOPICS_BY_ID.get(topic_id)
        if not topic:
            return {'error': f"Topic '{topic_id}' not found"}

        questions = self.get_test_questions(topic_id)
        if not questions:
            return {'error': f"No questions available for {topic.name}"}

        session_id = self.storage.start_session(student.id, "test", topic_id)

        results = {
            'topic_id': topic_id,
            'topic': topic.name,
            'correct': 0,
            'total': len(questions),
            'marks_earned': 0,
            'marks_possible': 0,
            'passed': False,
            'question_results': [],
            'incorrect_questions': []
        }

        for i, question in enumerate(questions):
            # Get answer from callback
            answer = answer_callback(question, i + 1, len(questions))

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

            # Track results
            if is_correct:
                results['correct'] += 1
            else:
                results['incorrect_questions'].append(question)

            results['marks_earned'] += marks
            results['marks_possible'] += question.marks

            results['question_results'].append({
                'question': question,
                'answer': answer,
                'is_correct': is_correct,
                'marks': marks,
                'feedback': feedback
            })

        # Calculate percentage
        results['percentage'] = (results['marks_earned'] / results['marks_possible'] * 100) \
            if results['marks_possible'] > 0 else 0
        results['passed'] = results['percentage'] >= PASS_MARK

        # Record test score and potentially mark as mastered
        self.storage.record_test_score(student.id, topic_id, results['percentage'])

        # End session
        self.storage.end_session(
            session_id,
            results['total'],
            results['correct'],
            results['percentage']
        )

        return results

    def format_results(self, results: Dict, show_explanations: bool = True) -> str:
        """Format test results for display."""
        lines = []
        lines.append("\n" + "=" * 60)
        lines.append("              TOPIC TEST RESULTS")
        lines.append("=" * 60)

        lines.append(f"\nTopic: {results['topic']}")
        lines.append(f"Score: {results['marks_earned']:.0f}/{results['marks_possible']:.0f} ({results['percentage']:.1f}%)")
        lines.append(f"Questions: {results['correct']}/{results['total']} correct")
        lines.append(f"Pass mark: {PASS_MARK}%")

        # Pass/Fail status
        if results['passed']:
            lines.append("\n" + "=" * 60)
            lines.append("   *** PASSED! Topic marked as MASTERED!")
            lines.append("=" * 60)
        else:
            lines.append("\n" + "=" * 60)
            lines.append(f"   [X] NOT PASSED (need {PASS_MARK}% to pass)")
            lines.append("=" * 60)
            lines.append("\nReview the mistakes below and practice with drills before retrying.")

        # Show incorrect answers with explanations
        if not results['passed'] and results['incorrect_questions'] and show_explanations:
            lines.append("\n" + "-" * 60)
            lines.append("REVIEW YOUR MISTAKES")
            lines.append("-" * 60)

            for qr in results['question_results']:
                if not qr['is_correct']:
                    q = qr['question']
                    lines.append(f"\n* Question: {q.question_text}")
                    lines.append(f"   Your answer: {qr['answer']}")
                    lines.append(f"   Correct answer: {q.answer}")

                    if q.explanation:
                        lines.append(f"\n   Solution:")
                        for line in q.explanation.split('\n'):
                            lines.append(f"   {line}")

                    if q.common_mistakes:
                        lines.append(f"\n   Common mistakes to avoid:")
                        for cm in q.common_mistakes[:2]:
                            lines.append(f"   • {cm.mistake}")

            # Topic summary
            lines.append("\n" + self.explainer.get_topic_summary(
                results['topic_id'],
                results['incorrect_questions']
            ))

        lines.append("\n" + "=" * 60)

        return "\n".join(lines)

    def get_topic_test_status(self, student_id: int, topic_id: str) -> Dict:
        """Get test status for a topic."""
        progress = self.storage.get_topic_progress(student_id, topic_id)
        topic = TOPICS_BY_ID.get(topic_id)

        if not progress or not topic:
            return {'available': False}

        return {
            'topic_name': topic.name,
            'attempts': progress.test_attempts,
            'best_score': progress.test_best_score,
            'mastered': progress.mastered,
            'last_attempt': progress.last_test_date,
            'available': True
        }

    def get_all_topics_status(self, student_id: int) -> List[Dict]:
        """Get test status for all topics."""
        all_progress = self.storage.get_all_topic_progress(student_id)
        statuses = []

        for topic in TOPICS_BY_ID.values():
            progress = all_progress.get(topic.id)
            statuses.append({
                'topic_id': topic.id,
                'topic_name': topic.name,
                'paper': topic.paper,
                'attempts': progress.test_attempts if progress else 0,
                'best_score': progress.test_best_score if progress else 0,
                'mastered': progress.mastered if progress else False
            })

        return statuses
