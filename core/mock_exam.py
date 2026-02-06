"""Mock exam module with timing and full paper simulation."""

import json
from typing import Dict, List, Callable, Optional
from datetime import datetime, timedelta

from models.question import Question
from models.student import Student
from core.questions import QuestionManager
from core.grader import Grader
from data.storage import Storage
from config.settings import (
    MOCK_EXAM_PAPER1_TIME, MOCK_EXAM_PAPER2_TIME,
    MOCK_EXAM_PAPER1_MARKS, MOCK_EXAM_PAPER2_MARKS
)
from config.caps_curriculum import PAPER1_TOPICS, PAPER2_TOPICS, TOPICS_BY_ID


class MockExam:
    """Handles mock exam sessions with timing."""

    def __init__(self, storage: Storage, question_manager: QuestionManager):
        """Initialize mock exam handler."""
        self.storage = storage
        self.question_manager = question_manager
        self.grader = Grader()

    def check_eligibility(self, student_id: int) -> Dict:
        """Check if student is eligible for mock exams (all topics >= 70%)."""
        all_mastered = self.storage.check_all_topics_mastered(student_id)
        all_progress = self.storage.get_all_topic_progress(student_id)

        unmastered = []
        for topic_id, progress in all_progress.items():
            if not progress.mastered:
                topic = TOPICS_BY_ID.get(topic_id)
                if topic:
                    unmastered.append({
                        'topic_id': topic_id,
                        'name': topic.name,
                        'best_score': progress.test_best_score
                    })

        return {
            'eligible': all_mastered,
            'unmastered_topics': unmastered,
            'topics_remaining': len(unmastered)
        }

    def get_exam_questions(self, paper: int) -> List[Question]:
        """Get questions for a mock exam paper."""
        return self.question_manager.get_mock_exam_questions(paper)

    def run_exam(self, student: Student, paper: int,
                 answer_callback: Callable,
                 time_callback: Optional[Callable] = None) -> Dict:
        """
        Run a mock exam.

        Args:
            student: The student taking the exam
            paper: Paper number (1 or 2)
            answer_callback: Function(question, index, total, time_remaining) -> answer
            time_callback: Optional function to update timer display

        Returns:
            Exam results dictionary
        """
        # Check eligibility
        eligibility = self.check_eligibility(student.id)
        if not eligibility['eligible']:
            return {
                'error': 'Not eligible for mock exams',
                'unmastered': eligibility['unmastered_topics']
            }

        # Get exam parameters
        time_limit = MOCK_EXAM_PAPER1_TIME if paper == 1 else MOCK_EXAM_PAPER2_TIME
        max_marks = MOCK_EXAM_PAPER1_MARKS if paper == 1 else MOCK_EXAM_PAPER2_MARKS
        topics = PAPER1_TOPICS if paper == 1 else PAPER2_TOPICS

        questions = self.get_exam_questions(paper)
        if not questions:
            return {'error': f"No questions available for Paper {paper}"}

        session_id = self.storage.start_session(student.id, "mock_exam", f"paper{paper}")
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=time_limit)

        results = {
            'paper': paper,
            'total_marks': 0,
            'max_marks': 0,
            'correct': 0,
            'total': len(questions),
            'topic_breakdown': {t.id: {'marks': 0, 'max': 0, 'name': t.name} for t in topics},
            'question_results': [],
            'time_used': 0,
            'time_limit': time_limit,
            'completed': False
        }

        for i, question in enumerate(questions):
            # Calculate remaining time
            elapsed = datetime.now() - start_time
            remaining = max(0, time_limit * 60 - elapsed.total_seconds())

            # Check if time is up
            if remaining <= 0:
                results['time_used'] = time_limit
                break

            # Update timer if callback provided
            if time_callback:
                time_callback(remaining)

            # Get answer
            answer = answer_callback(question, i + 1, len(questions), remaining)

            # Handle early termination
            if answer is None:
                break

            # Grade the answer
            is_correct, marks, feedback = self.grader.check_answer(question, answer)

            # Record attempt
            self.storage.record_question_attempt(
                student_id=student.id,
                session_id=session_id,
                question_id=question.id,
                topic_id=question.topic_id,
                subtopic_id=question.subtopic_id,
                student_answer=answer,
                correct_answer=str(question.answer),
                is_correct=is_correct,
                marks_earned=marks,
                marks_possible=question.marks
            )

            # Update results
            if is_correct:
                results['correct'] += 1
            results['total_marks'] += marks
            results['max_marks'] += question.marks

            # Update topic breakdown
            if question.topic_id in results['topic_breakdown']:
                results['topic_breakdown'][question.topic_id]['marks'] += marks
                results['topic_breakdown'][question.topic_id]['max'] += question.marks

            results['question_results'].append({
                'question': question,
                'answer': answer,
                'is_correct': is_correct,
                'marks': marks,
                'feedback': feedback
            })

        # Calculate final time
        results['time_used'] = int((datetime.now() - start_time).total_seconds() / 60)
        results['completed'] = len(results['question_results']) == len(questions)

        # Calculate percentage (scale to max paper marks)
        actual_max = results['max_marks'] if results['max_marks'] > 0 else 1
        results['percentage'] = (results['total_marks'] / actual_max) * 100

        # Scale marks to paper total if needed
        if actual_max != max_marks:
            results['scaled_marks'] = (results['total_marks'] / actual_max) * max_marks
        else:
            results['scaled_marks'] = results['total_marks']

        # Calculate topic percentages
        for topic_id, data in results['topic_breakdown'].items():
            if data['max'] > 0:
                data['percentage'] = (data['marks'] / data['max']) * 100
            else:
                data['percentage'] = 0

        # End session
        self.storage.end_session(
            session_id,
            len(results['question_results']),
            results['correct'],
            results['percentage']
        )

        # Record mock exam result
        self.storage.record_mock_exam(
            student_id=student.id,
            session_id=session_id,
            paper=paper,
            total_marks=results['total_marks'],
            max_marks=results['max_marks'],
            time_taken=results['time_used'],
            topic_breakdown=json.dumps(results['topic_breakdown'])
        )

        return results

    def format_results(self, results: Dict) -> str:
        """Format mock exam results for display."""
        lines = []
        lines.append("\n" + "=" * 70)
        lines.append(f"           NSC MATHEMATICS PAPER {results['paper']} - MOCK EXAM RESULTS")
        lines.append("=" * 70)

        # Overall score
        lines.append(f"\nTotal Marks: {results['total_marks']:.0f}/{results['max_marks']:.0f}")
        lines.append(f"Percentage: {results['percentage']:.1f}%")
        lines.append(f"Time Used: {results['time_used']} / {results['time_limit']} minutes")

        # Completion status
        if results['completed']:
            lines.append("Status: [OK] Completed all questions")
        else:
            answered = len(results['question_results'])
            lines.append(f"Status: (!) Answered {answered}/{results['total']} questions")

        # Grade indicator
        percentage = results['percentage']
        if percentage >= 80:
            grade = "Level 7 (Outstanding)"
        elif percentage >= 70:
            grade = "Level 6 (Meritorious)"
        elif percentage >= 60:
            grade = "Level 5 (Substantial)"
        elif percentage >= 50:
            grade = "Level 4 (Adequate)"
        elif percentage >= 40:
            grade = "Level 3 (Moderate)"
        elif percentage >= 30:
            grade = "Level 2 (Elementary)"
        else:
            grade = "Level 1 (Not Achieved)"
        lines.append(f"Achievement: {grade}")

        # Topic breakdown
        lines.append("\n" + "-" * 70)
        lines.append("TOPIC BREAKDOWN")
        lines.append("-" * 70)
        lines.append(f"{'Topic':<30} {'Marks':>10} {'Percentage':>12} {'Status':>10}")
        lines.append("-" * 70)

        for topic_id, data in results['topic_breakdown'].items():
            if data['max'] > 0:
                status = "[OK]" if data['percentage'] >= 70 else "(!)" if data['percentage'] >= 50 else "[X]"
                lines.append(f"{data['name']:<30} {data['marks']:>4.0f}/{data['max']:<4.0f} "
                           f"{data['percentage']:>10.1f}%  {status:>8}")

        # Summary
        lines.append("\n" + "-" * 70)

        weak_topics = [data['name'] for data in results['topic_breakdown'].values()
                       if data['max'] > 0 and data['percentage'] < 70]
        if weak_topics:
            lines.append("Areas needing improvement:")
            for topic in weak_topics:
                lines.append(f"  • {topic}")

        lines.append("\n" + "=" * 70)

        return "\n".join(lines)

    def get_exam_history(self, student_id: int) -> List[Dict]:
        """Get mock exam history for a student."""
        return self.storage.get_mock_exam_history(student_id)

    def format_history(self, history: List[Dict]) -> str:
        """Format exam history for display."""
        if not history:
            return "No mock exams completed yet."

        lines = []
        lines.append("\n" + "=" * 60)
        lines.append("          MOCK EXAM HISTORY")
        lines.append("=" * 60)
        lines.append(f"{'Date':<20} {'Paper':>6} {'Score':>10} {'%':>8} {'Time':>8}")
        lines.append("-" * 60)

        for exam in history:
            date_str = exam['exam_date'][:10] if exam['exam_date'] else "N/A"
            lines.append(f"{date_str:<20} {exam['paper']:>6} "
                        f"{exam['total_marks']:>4.0f}/{exam['max_marks']:<4.0f} "
                        f"{exam['percentage']:>7.1f}% {exam['time_taken']:>6}m")

        lines.append("=" * 60)
        return "\n".join(lines)
