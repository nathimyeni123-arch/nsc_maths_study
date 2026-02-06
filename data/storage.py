"""SQLite database handler for persistent storage."""

import sqlite3
import os
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from contextlib import contextmanager

from config.settings import DATABASE_NAME, MASTERY_THRESHOLD
from config.caps_curriculum import ALL_TOPICS
from models.student import Student, StudySession
from models.topic import TopicProgress


class Storage:
    """Handles all database operations."""

    def __init__(self, db_path: str = None):
        """Initialize storage with database path."""
        self.db_path = db_path or DATABASE_NAME
        self._init_database()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_database(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Students table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    diagnostic_completed INTEGER DEFAULT 0,
                    diagnostic_date TIMESTAMP,
                    total_study_time INTEGER DEFAULT 0,
                    mock_exams_completed INTEGER DEFAULT 0,
                    best_mock_paper1 REAL DEFAULT 0.0,
                    best_mock_paper2 REAL DEFAULT 0.0
                )
            ''')

            # Topics reference table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS topics (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    paper INTEGER NOT NULL,
                    weight REAL NOT NULL,
                    marks INTEGER NOT NULL
                )
            ''')

            # Topic progress table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS topic_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    topic_id TEXT NOT NULL,
                    drill_attempts INTEGER DEFAULT 0,
                    drill_correct INTEGER DEFAULT 0,
                    test_attempts INTEGER DEFAULT 0,
                    test_best_score REAL DEFAULT 0.0,
                    last_drill_date TIMESTAMP,
                    last_test_date TIMESTAMP,
                    mastered INTEGER DEFAULT 0,
                    FOREIGN KEY (student_id) REFERENCES students(id),
                    FOREIGN KEY (topic_id) REFERENCES topics(id),
                    UNIQUE(student_id, topic_id)
                )
            ''')

            # Question attempts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS question_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    session_id INTEGER,
                    question_id TEXT NOT NULL,
                    topic_id TEXT NOT NULL,
                    subtopic_id TEXT,
                    attempt_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    student_answer TEXT,
                    correct_answer TEXT,
                    is_correct INTEGER NOT NULL,
                    marks_earned REAL DEFAULT 0,
                    marks_possible REAL DEFAULT 0,
                    time_taken INTEGER,
                    FOREIGN KEY (student_id) REFERENCES students(id),
                    FOREIGN KEY (session_id) REFERENCES study_sessions(id)
                )
            ''')

            # Study sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS study_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    session_type TEXT NOT NULL,
                    topic_id TEXT,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    questions_attempted INTEGER DEFAULT 0,
                    questions_correct INTEGER DEFAULT 0,
                    score REAL,
                    FOREIGN KEY (student_id) REFERENCES students(id)
                )
            ''')

            # Mock exam results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mock_exam_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    session_id INTEGER,
                    paper INTEGER NOT NULL,
                    exam_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_marks REAL NOT NULL,
                    max_marks REAL NOT NULL,
                    percentage REAL NOT NULL,
                    time_taken INTEGER,
                    topic_breakdown TEXT,
                    FOREIGN KEY (student_id) REFERENCES students(id),
                    FOREIGN KEY (session_id) REFERENCES study_sessions(id)
                )
            ''')

            # Populate topics table
            for topic in ALL_TOPICS:
                cursor.execute('''
                    INSERT OR IGNORE INTO topics (id, name, paper, weight, marks)
                    VALUES (?, ?, ?, ?, ?)
                ''', (topic.id, topic.name, topic.paper, topic.weight, topic.marks))

    # Student operations
    def create_student(self, name: str) -> Student:
        """Create a new student profile."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO students (name) VALUES (?)',
                (name,)
            )
            student_id = cursor.lastrowid

            # Initialize topic progress for all topics
            for topic in ALL_TOPICS:
                cursor.execute('''
                    INSERT INTO topic_progress (student_id, topic_id)
                    VALUES (?, ?)
                ''', (student_id, topic.id))

            return self.get_student(student_id)

    def get_student(self, student_id: int) -> Optional[Student]:
        """Get a student by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM students WHERE id = ?', (student_id,))
            row = cursor.fetchone()
            if row:
                return Student(
                    id=row['id'],
                    name=row['name'],
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now(),
                    diagnostic_completed=bool(row['diagnostic_completed']),
                    diagnostic_date=datetime.fromisoformat(row['diagnostic_date']) if row['diagnostic_date'] else None,
                    total_study_time=row['total_study_time'] or 0,
                    mock_exams_completed=row['mock_exams_completed'] or 0,
                    best_mock_paper1=row['best_mock_paper1'] or 0.0,
                    best_mock_paper2=row['best_mock_paper2'] or 0.0
                )
            return None

    def get_all_students(self) -> List[Student]:
        """Get all students."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM students ORDER BY name')
            return [self.get_student(row['id']) for row in cursor.fetchall()]

    def update_student(self, student: Student):
        """Update student profile."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE students SET
                    name = ?,
                    diagnostic_completed = ?,
                    diagnostic_date = ?,
                    total_study_time = ?,
                    mock_exams_completed = ?,
                    best_mock_paper1 = ?,
                    best_mock_paper2 = ?
                WHERE id = ?
            ''', (
                student.name,
                int(student.diagnostic_completed),
                student.diagnostic_date.isoformat() if student.diagnostic_date else None,
                student.total_study_time,
                student.mock_exams_completed,
                student.best_mock_paper1,
                student.best_mock_paper2,
                student.id
            ))

    def mark_diagnostic_completed(self, student_id: int):
        """Mark diagnostic test as completed."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE students SET
                    diagnostic_completed = 1,
                    diagnostic_date = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), student_id))

    # Topic progress operations
    def get_topic_progress(self, student_id: int, topic_id: str) -> Optional[TopicProgress]:
        """Get progress for a specific topic."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM topic_progress
                WHERE student_id = ? AND topic_id = ?
            ''', (student_id, topic_id))
            row = cursor.fetchone()
            if row:
                return TopicProgress(
                    student_id=row['student_id'],
                    topic_id=row['topic_id'],
                    drill_attempts=row['drill_attempts'] or 0,
                    drill_correct=row['drill_correct'] or 0,
                    test_attempts=row['test_attempts'] or 0,
                    test_best_score=row['test_best_score'] or 0.0,
                    last_drill_date=datetime.fromisoformat(row['last_drill_date']) if row['last_drill_date'] else None,
                    last_test_date=datetime.fromisoformat(row['last_test_date']) if row['last_test_date'] else None,
                    mastered=bool(row['mastered'])
                )
            return None

    def get_all_topic_progress(self, student_id: int) -> Dict[str, TopicProgress]:
        """Get progress for all topics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM topic_progress WHERE student_id = ?
            ''', (student_id,))
            result = {}
            for row in cursor.fetchall():
                result[row['topic_id']] = TopicProgress(
                    student_id=row['student_id'],
                    topic_id=row['topic_id'],
                    drill_attempts=row['drill_attempts'] or 0,
                    drill_correct=row['drill_correct'] or 0,
                    test_attempts=row['test_attempts'] or 0,
                    test_best_score=row['test_best_score'] or 0.0,
                    last_drill_date=datetime.fromisoformat(row['last_drill_date']) if row['last_drill_date'] else None,
                    last_test_date=datetime.fromisoformat(row['last_test_date']) if row['last_test_date'] else None,
                    mastered=bool(row['mastered'])
                )
            return result

    def update_topic_progress(self, progress: TopicProgress):
        """Update topic progress."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE topic_progress SET
                    drill_attempts = ?,
                    drill_correct = ?,
                    test_attempts = ?,
                    test_best_score = ?,
                    last_drill_date = ?,
                    last_test_date = ?,
                    mastered = ?
                WHERE student_id = ? AND topic_id = ?
            ''', (
                progress.drill_attempts,
                progress.drill_correct,
                progress.test_attempts,
                progress.test_best_score,
                progress.last_drill_date.isoformat() if progress.last_drill_date else None,
                progress.last_test_date.isoformat() if progress.last_test_date else None,
                int(progress.mastered),
                progress.student_id,
                progress.topic_id
            ))

    def record_drill_attempt(self, student_id: int, topic_id: str, correct: bool):
        """Record a drill question attempt."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE topic_progress SET
                    drill_attempts = drill_attempts + 1,
                    drill_correct = drill_correct + ?,
                    last_drill_date = ?
                WHERE student_id = ? AND topic_id = ?
            ''', (1 if correct else 0, datetime.now().isoformat(), student_id, topic_id))

    def record_test_score(self, student_id: int, topic_id: str, score: float):
        """Record a topic test score."""
        progress = self.get_topic_progress(student_id, topic_id)
        if progress:
            new_best = max(progress.test_best_score, score)
            mastered = 1 if new_best >= MASTERY_THRESHOLD else 0
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE topic_progress SET
                        test_attempts = test_attempts + 1,
                        test_best_score = ?,
                        last_test_date = ?,
                        mastered = ?
                    WHERE student_id = ? AND topic_id = ?
                ''', (new_best, datetime.now().isoformat(), mastered, student_id, topic_id))

    def check_all_topics_mastered(self, student_id: int) -> bool:
        """Check if all topics are mastered (>= 70%)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN mastered = 1 THEN 1 ELSE 0 END) as mastered_count
                FROM topic_progress WHERE student_id = ?
            ''', (student_id,))
            row = cursor.fetchone()
            return row['total'] > 0 and row['total'] == row['mastered_count']

    # Session operations
    def start_session(self, student_id: int, session_type: str, topic_id: str = None) -> int:
        """Start a new study session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO study_sessions (student_id, session_type, topic_id, start_time)
                VALUES (?, ?, ?, ?)
            ''', (student_id, session_type, topic_id, datetime.now().isoformat()))
            return cursor.lastrowid

    def end_session(self, session_id: int, questions_attempted: int, questions_correct: int, score: float = None):
        """End a study session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE study_sessions SET
                    end_time = ?,
                    questions_attempted = ?,
                    questions_correct = ?,
                    score = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), questions_attempted, questions_correct, score, session_id))

            # Update student's total study time
            cursor.execute('SELECT student_id, start_time, end_time FROM study_sessions WHERE id = ?', (session_id,))
            row = cursor.fetchone()
            if row and row['start_time'] and row['end_time']:
                start = datetime.fromisoformat(row['start_time'])
                end = datetime.fromisoformat(row['end_time'])
                minutes = int((end - start).total_seconds() / 60)
                cursor.execute('''
                    UPDATE students SET total_study_time = total_study_time + ?
                    WHERE id = ?
                ''', (minutes, row['student_id']))

    # Question attempt operations
    def record_question_attempt(self, student_id: int, session_id: int, question_id: str,
                                 topic_id: str, subtopic_id: str, student_answer: str,
                                 correct_answer: str, is_correct: bool, marks_earned: float,
                                 marks_possible: float, time_taken: int = None):
        """Record a question attempt."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO question_attempts
                (student_id, session_id, question_id, topic_id, subtopic_id,
                 student_answer, correct_answer, is_correct, marks_earned, marks_possible, time_taken)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (student_id, session_id, question_id, topic_id, subtopic_id,
                  str(student_answer), str(correct_answer), int(is_correct),
                  marks_earned, marks_possible, time_taken))

    def get_weak_subtopics(self, student_id: int, topic_id: str, limit: int = 5) -> List[Tuple[str, float]]:
        """Get subtopics with lowest accuracy for a topic."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT subtopic_id,
                       COUNT(*) as attempts,
                       SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct,
                       CAST(SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100 as accuracy
                FROM question_attempts
                WHERE student_id = ? AND topic_id = ?
                GROUP BY subtopic_id
                ORDER BY accuracy ASC
                LIMIT ?
            ''', (student_id, topic_id, limit))
            return [(row['subtopic_id'], row['accuracy']) for row in cursor.fetchall()]

    # Mock exam operations
    def record_mock_exam(self, student_id: int, session_id: int, paper: int,
                          total_marks: float, max_marks: float, time_taken: int,
                          topic_breakdown: str):
        """Record mock exam result."""
        percentage = (total_marks / max_marks) * 100 if max_marks > 0 else 0

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Insert result
            cursor.execute('''
                INSERT INTO mock_exam_results
                (student_id, session_id, paper, total_marks, max_marks, percentage, time_taken, topic_breakdown)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (student_id, session_id, paper, total_marks, max_marks, percentage, time_taken, topic_breakdown))

            # Update student's best scores and exam count
            if paper == 1:
                cursor.execute('''
                    UPDATE students SET
                        mock_exams_completed = mock_exams_completed + 1,
                        best_mock_paper1 = MAX(best_mock_paper1, ?)
                    WHERE id = ?
                ''', (percentage, student_id))
            else:
                cursor.execute('''
                    UPDATE students SET
                        best_mock_paper2 = MAX(best_mock_paper2, ?)
                    WHERE id = ?
                ''', (percentage, student_id))

    def get_mock_exam_history(self, student_id: int) -> List[Dict[str, Any]]:
        """Get mock exam history for a student."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM mock_exam_results
                WHERE student_id = ?
                ORDER BY exam_date DESC
            ''', (student_id,))
            return [dict(row) for row in cursor.fetchall()]

    # Analytics
    def get_study_statistics(self, student_id: int) -> Dict[str, Any]:
        """Get comprehensive study statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Total questions attempted
            cursor.execute('''
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct
                FROM question_attempts WHERE student_id = ?
            ''', (student_id,))
            questions = cursor.fetchone()

            # Sessions by type
            cursor.execute('''
                SELECT session_type, COUNT(*) as count
                FROM study_sessions WHERE student_id = ?
                GROUP BY session_type
            ''', (student_id,))
            sessions = {row['session_type']: row['count'] for row in cursor.fetchall()}

            # Topic mastery count
            cursor.execute('''
                SELECT SUM(CASE WHEN mastered = 1 THEN 1 ELSE 0 END) as mastered,
                       COUNT(*) as total
                FROM topic_progress WHERE student_id = ?
            ''', (student_id,))
            mastery = cursor.fetchone()

            return {
                'total_questions': questions['total'] or 0,
                'correct_answers': questions['correct'] or 0,
                'overall_accuracy': (questions['correct'] / questions['total'] * 100) if questions['total'] else 0,
                'sessions': sessions,
                'topics_mastered': mastery['mastered'] or 0,
                'total_topics': mastery['total'] or 0
            }
