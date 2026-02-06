"""Main orchestrator for the study program."""

from typing import Optional, Dict, List
from datetime import datetime

from data.storage import Storage
from core.questions import QuestionManager
from core.diagnostic import DiagnosticTest
from core.drill import DrillSession
from core.test import TopicTest
from core.mock_exam import MockExam
from models.student import Student
from config.caps_curriculum import ALL_TOPICS, TOPICS_BY_ID


class Engine:
    """Main orchestrator that coordinates all study components."""

    def __init__(self, db_path: str = None):
        """Initialize the engine with all components."""
        self.storage = Storage(db_path)
        self.question_manager = QuestionManager()
        self.diagnostic = DiagnosticTest(self.storage, self.question_manager)
        self.drill = DrillSession(self.storage, self.question_manager)
        self.topic_test = TopicTest(self.storage, self.question_manager)
        self.mock_exam = MockExam(self.storage, self.question_manager)
        self.current_student: Optional[Student] = None

    def create_student(self, name: str) -> Student:
        """Create a new student profile."""
        self.current_student = self.storage.create_student(name)
        return self.current_student

    def load_student(self, student_id: int) -> Optional[Student]:
        """Load an existing student profile."""
        self.current_student = self.storage.get_student(student_id)
        return self.current_student

    def get_all_students(self) -> List[Student]:
        """Get all student profiles."""
        return self.storage.get_all_students()

    def needs_diagnostic(self) -> bool:
        """Check if current student needs to take diagnostic test."""
        if not self.current_student:
            return False
        return not self.current_student.diagnostic_completed

    def get_progress_report(self) -> Dict:
        """Get comprehensive progress report for current student."""
        if not self.current_student:
            return {'error': 'No student loaded'}

        all_progress = self.storage.get_all_topic_progress(self.current_student.id)
        stats = self.storage.get_study_statistics(self.current_student.id)

        # Organize by paper
        paper1_topics = []
        paper2_topics = []

        for topic in ALL_TOPICS:
            progress = all_progress.get(topic.id)
            topic_info = {
                'id': topic.id,
                'name': topic.name,
                'weight': topic.weight,
                'drill_accuracy': progress.drill_accuracy if progress else 0,
                'drill_attempts': progress.drill_attempts if progress else 0,
                'test_best': progress.test_best_score if progress else 0,
                'test_attempts': progress.test_attempts if progress else 0,
                'mastered': progress.mastered if progress else False,
                'last_activity': max(
                    progress.last_drill_date or datetime.min,
                    progress.last_test_date or datetime.min
                ) if progress else None
            }

            if topic.paper == 1:
                paper1_topics.append(topic_info)
            else:
                paper2_topics.append(topic_info)

        # Calculate overall readiness
        mastered_count = sum(1 for t in all_progress.values() if t.mastered)
        total_topics = len(ALL_TOPICS)

        # Mock exam eligibility
        mock_eligible = self.mock_exam.check_eligibility(self.current_student.id)

        return {
            'student': self.current_student,
            'paper1_topics': paper1_topics,
            'paper2_topics': paper2_topics,
            'mastered_count': mastered_count,
            'total_topics': total_topics,
            'mastery_percentage': (mastered_count / total_topics * 100) if total_topics > 0 else 0,
            'statistics': stats,
            'mock_exam_eligible': mock_eligible['eligible'],
            'mock_exam_history': self.mock_exam.get_exam_history(self.current_student.id)
        }

    def format_progress_report(self, report: Dict) -> str:
        """Format progress report for display."""
        if 'error' in report:
            return report['error']

        lines = []
        student = report['student']

        lines.append("\n" + "=" * 70)
        lines.append(f"           PROGRESS REPORT: {student.name}")
        lines.append("=" * 70)

        # Overall stats
        lines.append(f"\nTotal Study Time: {student.display_study_time}")
        lines.append(f"Questions Attempted: {report['statistics']['total_questions']}")
        lines.append(f"Overall Accuracy: {report['statistics']['overall_accuracy']:.1f}%")
        lines.append(f"Topics Mastered: {report['mastered_count']}/{report['total_topics']} ({report['mastery_percentage']:.0f}%)")

        # Mock exam status
        if report['mock_exam_eligible']:
            lines.append("\n*** MOCK EXAMS UNLOCKED!")
            if student.best_mock_paper1 > 0:
                lines.append(f"   Best Paper 1: {student.best_mock_paper1:.1f}%")
            if student.best_mock_paper2 > 0:
                lines.append(f"   Best Paper 2: {student.best_mock_paper2:.1f}%")
        else:
            remaining = report['total_topics'] - report['mastered_count']
            lines.append(f"\n[LOCKED] Mock exams locked (master {remaining} more topics)")

        # Paper 1 topics
        lines.append("\n" + "-" * 70)
        lines.append("PAPER 1 TOPICS")
        lines.append("-" * 70)
        lines.append(f"{'Topic':<25} {'Drill':>10} {'Test':>10} {'Status':>10}")
        lines.append("-" * 70)

        for t in report['paper1_topics']:
            status = "[OK] Mastered" if t['mastered'] else f"  {t['test_best']:.0f}%"
            drill = f"{t['drill_accuracy']:.0f}%" if t['drill_attempts'] > 0 else "-"
            test = f"{t['test_best']:.0f}%" if t['test_attempts'] > 0 else "-"
            lines.append(f"{t['name']:<25} {drill:>10} {test:>10} {status:>10}")

        # Paper 2 topics
        lines.append("\n" + "-" * 70)
        lines.append("PAPER 2 TOPICS")
        lines.append("-" * 70)
        lines.append(f"{'Topic':<25} {'Drill':>10} {'Test':>10} {'Status':>10}")
        lines.append("-" * 70)

        for t in report['paper2_topics']:
            status = "[OK] Mastered" if t['mastered'] else f"  {t['test_best']:.0f}%"
            drill = f"{t['drill_accuracy']:.0f}%" if t['drill_attempts'] > 0 else "-"
            test = f"{t['test_best']:.0f}%" if t['test_attempts'] > 0 else "-"
            lines.append(f"{t['name']:<25} {drill:>10} {test:>10} {status:>10}")

        # Recommendations
        lines.append("\n" + "-" * 70)
        lines.append("RECOMMENDATIONS")
        lines.append("-" * 70)

        weak_topics = [t for t in report['paper1_topics'] + report['paper2_topics']
                       if not t['mastered']]

        if weak_topics:
            # Sort by test score (lowest first)
            weak_topics.sort(key=lambda x: x['test_best'])
            lines.append("\nFocus on these topics:")
            for t in weak_topics[:3]:
                lines.append(f"  • {t['name']} (current best: {t['test_best']:.0f}%)")
        else:
            lines.append("\n*** All topics mastered! Ready for mock exams!")

        lines.append("\n" + "=" * 70)

        return "\n".join(lines)

    def get_topic_list(self, paper: int = None) -> List[Dict]:
        """Get list of topics with basic info."""
        topics = []
        for topic in ALL_TOPICS:
            if paper is None or topic.paper == paper:
                progress = None
                if self.current_student:
                    progress = self.storage.get_topic_progress(
                        self.current_student.id, topic.id
                    )
                topics.append({
                    'id': topic.id,
                    'name': topic.name,
                    'paper': topic.paper,
                    'weight': topic.weight,
                    'mastered': progress.mastered if progress else False,
                    'test_best': progress.test_best_score if progress else 0,
                    'question_count': self.question_manager.get_topic_question_count(topic.id)
                })
        return topics

    def get_question_bank_status(self) -> Dict:
        """Get status of question bank."""
        total = self.question_manager.get_total_question_count()
        by_topic = {}

        for topic in ALL_TOPICS:
            count = self.question_manager.get_topic_question_count(topic.id)
            by_topic[topic.id] = {
                'name': topic.name,
                'count': count,
                'paper': topic.paper
            }

        return {
            'total_questions': total,
            'by_topic': by_topic
        }
