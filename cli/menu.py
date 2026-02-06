"""Main menu interface for the CLI application."""

import sys
from typing import Optional, Tuple

from core.engine import Engine
from core.explainer import Explainer
from cli.display import (
    clear_screen, print_header, print_subheader, print_menu,
    print_question, print_result, print_topic_list, print_welcome,
    print_goodbye, confirm, get_input, get_number, print_progress_bar
)
from cli.timer import ExamTimer, SimpleTimer
from config.caps_curriculum import TOPICS_BY_ID, ALL_TOPICS
from config.settings import DRILL_QUESTIONS_DEFAULT, TOPIC_TEST_QUESTIONS, PASS_MARK


class Menu:
    """Main menu handler for the CLI application."""

    def __init__(self):
        """Initialize the menu."""
        self.engine = Engine()
        self.running = True

    def run(self):
        """Main application loop."""
        print_welcome()
        self._select_or_create_student()

        if not self.engine.current_student:
            print("No student profile. Exiting.")
            return

        # Check for diagnostic test
        if self.engine.needs_diagnostic():
            self._offer_diagnostic()

        # Main menu loop
        while self.running:
            self._show_main_menu()

        print_goodbye()

    def _select_or_create_student(self):
        """Handle student selection or creation."""
        students = self.engine.get_all_students()

        if not students:
            print("\nNo existing profiles found. Let's create one!")
            name = get_input("Enter your name: ")
            self.engine.create_student(name)
            print(f"\nWelcome, {name}!")
            return

        print_header("SELECT PROFILE")
        print("\nExisting profiles:")
        for i, student in enumerate(students, 1):
            status = "[OK] Diagnostic done" if student.diagnostic_completed else "New"
            print(f"  [{i}] {student.name} ({status})")
        print(f"  [N] Create new profile")
        print(f"  [Q] Quit")

        while True:
            choice = get_input("\nSelect profile: ").upper()

            if choice == 'Q':
                self.running = False
                return

            if choice == 'N':
                name = get_input("Enter your name: ")
                self.engine.create_student(name)
                print(f"\nWelcome, {name}!")
                return

            try:
                index = int(choice) - 1
                if 0 <= index < len(students):
                    self.engine.load_student(students[index].id)
                    print(f"\nWelcome back, {self.engine.current_student.name}!")
                    return
            except ValueError:
                pass

            print("Invalid selection. Please try again.")

    def _offer_diagnostic(self):
        """Offer to take the diagnostic test."""
        print_header("DIAGNOSTIC TEST")
        print("""
The diagnostic test helps identify your strengths and weaknesses
across all topics in the CAPS curriculum.

This is recommended before starting your study program.
""")

        if confirm("Would you like to take the diagnostic test now?", default=True):
            self._run_diagnostic()
        else:
            print("\nYou can take the diagnostic test later from the main menu.")

    def _show_main_menu(self):
        """Show and handle main menu."""
        student = self.engine.current_student
        mock_eligible = self.engine.mock_exam.check_eligibility(student.id)

        options = [
            "Topic Drills - Practice specific topics",
            "Topic Tests - Test your knowledge (70% to pass)",
            "Progress Report - View your progress",
        ]

        if mock_eligible['eligible']:
            options.append("Mock Exam - Full paper simulation ***")
        else:
            remaining = mock_eligible['topics_remaining']
            options.append(f"Mock Exam - Locked (master {remaining} more topics) [LOCKED]")

        if not student.diagnostic_completed:
            options.append("Diagnostic Test - Assess your knowledge")

        options.append("Question Bank Status")
        options.append("Quit")

        print_menu(options, f"MAIN MENU - {student.name}")

        choice = get_number("Select option: ", 1, len(options))

        if choice == 1:
            self._topic_drills_menu()
        elif choice == 2:
            self._topic_tests_menu()
        elif choice == 3:
            self._show_progress_report()
        elif choice == 4:
            if mock_eligible['eligible']:
                self._mock_exam_menu()
            else:
                self._show_mock_exam_requirements(mock_eligible)
        elif choice == 5 and not student.diagnostic_completed:
            self._run_diagnostic()
        elif (choice == 5 and student.diagnostic_completed) or choice == 6:
            self._show_question_bank_status()
        elif choice == len(options):
            self.running = False

    def _topic_drills_menu(self):
        """Handle topic drill selection."""
        print_header("TOPIC DRILLS")

        topics = self.engine.get_topic_list()
        print_topic_list(topics)

        print(f"\n  [0] Back to main menu")
        choice = get_number("\nSelect topic: ", 0, len(topics))

        if choice == 0:
            return

        topic = topics[choice - 1]
        self._run_drill(topic['id'])

    def _run_drill(self, topic_id: str):
        """Run a drill session."""
        topic = TOPICS_BY_ID.get(topic_id)
        available = self.engine.question_manager.get_topic_question_count(topic_id)

        if available == 0:
            print(f"\nNo questions available for {topic.name} yet.")
            input("Press Enter to continue...")
            return

        print_subheader(f"DRILL: {topic.name}")
        print(f"Questions available: {available}")

        max_questions = min(available, 20)
        count = get_number(f"How many questions? (1-{max_questions}): ", 1, max_questions)

        print("\nStarting drill session...")
        print("Type 'hint' for a hint, 'skip' to skip a question.\n")

        def answer_callback(question, index, total):
            print_question(question, index, total, topic.name)

            while True:
                answer = input("Your answer: ").strip()

                if answer.lower() == 'hint':
                    print("\n" + Explainer.format_hint(question))
                    continue
                elif answer.lower() == 'skip':
                    return "", False

                return answer, False

        results = self.engine.drill.run_drill(
            self.engine.current_student,
            topic_id,
            count,
            answer_callback,
            show_explanation=True
        )

        if 'error' in results:
            print(f"\nError: {results['error']}")
        else:
            print(self.engine.drill.format_results(results))

        input("\nPress Enter to continue...")

    def _topic_tests_menu(self):
        """Handle topic test selection."""
        print_header("TOPIC TESTS")
        print(f"Pass mark: {PASS_MARK}%\n")

        statuses = self.engine.topic_test.get_all_topics_status(self.engine.current_student.id)

        # Group by paper
        print("Paper 1:")
        p1_topics = [s for s in statuses if s['paper'] == 1]
        for i, t in enumerate(p1_topics, 1):
            status = "[OK] Mastered" if t['mastered'] else f"Best: {t['best_score']:.0f}%"
            print(f"  [{i}] {t['topic_name']:<25} {status}")

        print("\nPaper 2:")
        p2_topics = [s for s in statuses if s['paper'] == 2]
        for i, t in enumerate(p2_topics, len(p1_topics) + 1):
            status = "[OK] Mastered" if t['mastered'] else f"Best: {t['best_score']:.0f}%"
            print(f"  [{i}] {t['topic_name']:<25} {status}")

        print(f"\n  [0] Back to main menu")

        choice = get_number("\nSelect topic to test: ", 0, len(statuses))

        if choice == 0:
            return

        topic = statuses[choice - 1]
        self._run_topic_test(topic['topic_id'])

    def _run_topic_test(self, topic_id: str):
        """Run a topic test."""
        topic = TOPICS_BY_ID.get(topic_id)
        available = self.engine.question_manager.get_topic_question_count(topic_id)

        if available == 0:
            print(f"\nNo questions available for {topic.name} yet.")
            input("Press Enter to continue...")
            return

        print_header(f"TOPIC TEST: {topic.name}")
        print(f"Questions: {min(TOPIC_TEST_QUESTIONS, available)}")
        print(f"Pass mark: {PASS_MARK}%")
        print("\nNo hints available during tests. Good luck!\n")

        if not confirm("Ready to begin?", default=True):
            return

        timer = SimpleTimer()
        timer.start()

        def answer_callback(question, index, total):
            print_question(question, index, total, topic.name)
            return input("Your answer: ").strip()

        results = self.engine.topic_test.run_test(
            self.engine.current_student,
            topic_id,
            answer_callback
        )

        timer.stop()

        if 'error' in results:
            print(f"\nError: {results['error']}")
        else:
            print(self.engine.topic_test.format_results(results))
            print(f"Time taken: {timer.format_elapsed()}")

        input("\nPress Enter to continue...")

    def _show_progress_report(self):
        """Display progress report."""
        report = self.engine.get_progress_report()
        print(self.engine.format_progress_report(report))
        input("\nPress Enter to continue...")

    def _show_mock_exam_requirements(self, eligibility: dict):
        """Show what's needed to unlock mock exams."""
        print_header("MOCK EXAM REQUIREMENTS")
        print("\nTo unlock mock exams, you must achieve 70% in ALL topic tests.\n")
        print("Topics still needing mastery:")

        for topic in eligibility['unmastered_topics']:
            print(f"  • {topic['name']} (current best: {topic['best_score']:.0f}%)")

        print(f"\nTopics remaining: {eligibility['topics_remaining']}")
        input("\nPress Enter to continue...")

    def _mock_exam_menu(self):
        """Handle mock exam selection."""
        print_header("MOCK EXAM")

        history = self.engine.mock_exam.get_exam_history(self.engine.current_student.id)
        if history:
            print(self.engine.mock_exam.format_history(history))

        print("\nSelect paper:")
        print("  [1] Paper 1 (3 hours) - Algebra, Sequences, Finance, Functions, Calculus, Probability")
        print("  [2] Paper 2 (3 hours) - Statistics, Analytical Geometry, Trigonometry, Euclidean Geometry")
        print("  [0] Back to main menu")

        choice = get_number("\nSelect: ", 0, 2)

        if choice == 0:
            return

        self._run_mock_exam(choice)

    def _run_mock_exam(self, paper: int):
        """Run a mock exam."""
        from config.settings import MOCK_EXAM_PAPER1_TIME, MOCK_EXAM_PAPER2_TIME

        time_limit = MOCK_EXAM_PAPER1_TIME if paper == 1 else MOCK_EXAM_PAPER2_TIME

        print_header(f"MOCK EXAM - PAPER {paper}")
        print(f"\nTime limit: {time_limit} minutes ({time_limit // 60} hours)")
        print("This simulates real NSC exam conditions.\n")
        print("Instructions:")
        print("  - Answer all questions")
        print("  - No hints available")
        print("  - Type 'end' to finish early")
        print("  - Timer will be displayed\n")

        if not confirm("Ready to begin the exam?", default=True):
            return

        print("\n[T] Starting exam...\n")

        exam_timer = ExamTimer(time_limit)
        exam_timer.start()

        def answer_callback(question, index, total, time_remaining):
            # Show timer
            remaining_str = exam_timer.format_remaining()
            print(f"\n[Time remaining: {remaining_str}]")
            print_question(question, index, total)

            while True:
                answer = input("Your answer (or 'end' to finish): ").strip()

                if answer.lower() == 'end':
                    if confirm("Are you sure you want to end the exam?"):
                        return None
                    continue

                return answer

        results = self.engine.mock_exam.run_exam(
            self.engine.current_student,
            paper,
            answer_callback
        )

        exam_timer.stop()

        if 'error' in results:
            print(f"\nError: {results['error']}")
            if 'unmastered' in results:
                print("\nYou need to master these topics first:")
                for t in results['unmastered']:
                    print(f"  • {t['name']}")
        else:
            print(self.engine.mock_exam.format_results(results))

        input("\nPress Enter to continue...")

    def _run_diagnostic(self):
        """Run the diagnostic test."""
        print_header("DIAGNOSTIC TEST")

        question_count = self.engine.diagnostic.get_question_count()
        if question_count == 0:
            print("\nNo diagnostic questions available. Please add questions to the question bank.")
            input("Press Enter to continue...")
            return

        print(f"\nThis test covers all {len(ALL_TOPICS)} topics.")
        print(f"Total questions: approximately {question_count}")
        print("\nTake your time - this is not timed.\n")

        if not confirm("Ready to begin?", default=True):
            return

        def answer_callback(question, topic_name):
            print_question(question, 1, 1, topic_name)
            return input("Your answer: ").strip()

        results = self.engine.diagnostic.run_diagnostic(
            self.engine.current_student,
            answer_callback
        )

        print(self.engine.diagnostic.format_results(results))
        input("\nPress Enter to continue...")

    def _show_question_bank_status(self):
        """Show status of question bank."""
        status = self.engine.get_question_bank_status()

        print_header("QUESTION BANK STATUS")
        print(f"\nTotal questions: {status['total_questions']}")

        print("\nPaper 1:")
        for topic_id, info in status['by_topic'].items():
            if info['paper'] == 1:
                count_status = f"{info['count']} questions" if info['count'] > 0 else "No questions yet"
                print(f"  {info['name']:<30} {count_status}")

        print("\nPaper 2:")
        for topic_id, info in status['by_topic'].items():
            if info['paper'] == 2:
                count_status = f"{info['count']} questions" if info['count'] > 0 else "No questions yet"
                print(f"  {info['name']:<30} {count_status}")

        if status['total_questions'] == 0:
            print("\n(!) No questions loaded. Add JSON files to the questions/ directory.")

        input("\nPress Enter to continue...")


def main():
    """Main entry point."""
    try:
        menu = Menu()
        menu.run()
    except KeyboardInterrupt:
        print("\n\nExiting... Your progress has been saved.")
        sys.exit(0)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
