"""Mistake explanation module."""

from typing import List, Optional
from models.question import Question, CommonMistake


class Explainer:
    """Provides detailed explanations for mistakes and solutions."""

    @staticmethod
    def get_full_explanation(question: Question, student_answer: str, is_correct: bool) -> str:
        """Get a comprehensive explanation for a question."""
        lines = []

        # Question review
        lines.append("=" * 60)
        lines.append("QUESTION REVIEW")
        lines.append("=" * 60)
        lines.append(f"\nQuestion: {question.question_text}")
        lines.append(f"Your answer: {student_answer}")
        lines.append(f"Correct answer: {question.answer}")
        lines.append(f"Result: {'[OK] CORRECT' if is_correct else '[X] INCORRECT'}")

        # Step-by-step solution
        if question.explanation:
            lines.append("\n" + "-" * 40)
            lines.append("STEP-BY-STEP SOLUTION")
            lines.append("-" * 40)
            lines.append(question.explanation)

        # Common mistakes analysis
        if not is_correct and question.common_mistakes:
            lines.append("\n" + "-" * 40)
            lines.append("COMMON MISTAKES TO AVOID")
            lines.append("-" * 40)

            # Try to identify which mistake the student might have made
            identified_mistake = Explainer._identify_mistake(
                question, student_answer, question.common_mistakes
            )

            if identified_mistake:
                lines.append(f"\n(!) You may have made this common mistake:")
                lines.append(f"   {identified_mistake.mistake}")
                lines.append(f"\n   Why this is wrong:")
                lines.append(f"   {identified_mistake.explanation}")
                lines.append("")

            lines.append("\nOther common mistakes for this type of question:")
            for i, cm in enumerate(question.common_mistakes, 1):
                if cm != identified_mistake:
                    lines.append(f"\n  {i}. {cm.mistake}")
                    lines.append(f"     → {cm.explanation}")

        # Hints for next time
        if question.hints:
            lines.append("\n" + "-" * 40)
            lines.append("HINTS FOR SIMILAR QUESTIONS")
            lines.append("-" * 40)
            for hint in question.hints:
                lines.append(f"  • {hint}")

        # NSC reference
        if question.nsc_reference:
            lines.append(f"\n[REF] Reference: {question.nsc_reference}")

        lines.append("\n" + "=" * 60)

        return "\n".join(lines)

    @staticmethod
    def _identify_mistake(question: Question, student_answer: str,
                          common_mistakes: List[CommonMistake]) -> Optional[CommonMistake]:
        """Try to identify which common mistake the student made."""
        # This is a simplified heuristic - in a real system,
        # this could use more sophisticated pattern matching

        student_answer = str(student_answer).lower().strip()

        for cm in common_mistakes:
            mistake_text = cm.mistake.lower()

            # Check for sign errors
            if "sign" in mistake_text or "negative" in mistake_text:
                try:
                    correct = float(str(question.answer))
                    student = float(student_answer)
                    if abs(student + correct) < 0.01:  # Opposite sign
                        return cm
                except (ValueError, TypeError):
                    pass

            # Check for common calculation errors
            if "calculation" in mistake_text or "arithmetic" in mistake_text:
                try:
                    correct = float(str(question.answer))
                    student = float(student_answer)
                    # Close but not quite right
                    if 0.1 < abs(student - correct) < abs(correct) * 0.5:
                        return cm
                except (ValueError, TypeError):
                    pass

            # Check for missing solutions (e.g., only one root of quadratic)
            if "missing" in mistake_text or "one solution" in mistake_text:
                if isinstance(question.answer, list):
                    try:
                        student_val = float(student_answer)
                        if any(abs(student_val - ans) < 0.01 for ans in question.answer):
                            return cm
                    except (ValueError, TypeError):
                        pass

        return None

    @staticmethod
    def get_topic_summary(topic_id: str, incorrect_questions: List[Question]) -> str:
        """Generate a summary of weak areas in a topic based on incorrect answers."""
        if not incorrect_questions:
            return "Great job! No areas need review."

        lines = []
        lines.append("=" * 60)
        lines.append("TOPIC REVIEW SUMMARY")
        lines.append("=" * 60)

        # Group by subtopic
        subtopic_errors = {}
        for q in incorrect_questions:
            if q.subtopic_id not in subtopic_errors:
                subtopic_errors[q.subtopic_id] = []
            subtopic_errors[q.subtopic_id].append(q)

        lines.append(f"\nYou need more practice in these areas:\n")

        for subtopic_id, questions in sorted(subtopic_errors.items(),
                                              key=lambda x: -len(x[1])):
            lines.append(f"* {subtopic_id.replace('_', ' ').title()}: {len(questions)} question(s) incorrect")

            # Collect unique hints from these questions
            hints = set()
            for q in questions:
                hints.update(q.hints)

            if hints:
                lines.append("   Suggested focus areas:")
                for hint in list(hints)[:3]:
                    lines.append(f"   • {hint}")
            lines.append("")

        lines.append("\nRecommendation: Use drill mode to practice these subtopics.")
        lines.append("=" * 60)

        return "\n".join(lines)

    @staticmethod
    def get_quick_feedback(is_correct: bool, marks_earned: float,
                           marks_possible: float) -> str:
        """Get quick feedback for a single answer."""
        if is_correct:
            return f"[OK] Correct! ({marks_earned}/{marks_possible} marks)"
        elif marks_earned > 0:
            return f"[~] Partial marks ({marks_earned}/{marks_possible} marks)"
        else:
            return f"[X] Incorrect (0/{marks_possible} marks)"

    @staticmethod
    def format_hint(question: Question) -> str:
        """Format hints for display during a question."""
        if not question.hints:
            return "No hints available for this question."

        lines = ["[HINT] Hints:"]
        for i, hint in enumerate(question.hints, 1):
            lines.append(f"   {i}. {hint}")
        return "\n".join(lines)
