"""Answer grading module."""

import re
import math
from typing import Any, Tuple, List, Union
from models.question import Question


class Grader:
    """Handles answer checking and grading."""

    @staticmethod
    def check_answer(question: Question, student_answer: str) -> Tuple[bool, float, str]:
        """
        Check a student's answer against the correct answer.

        Returns:
            Tuple of (is_correct, marks_earned, feedback)
        """
        if question.question_type == "multiple_choice":
            return Grader._check_multiple_choice(question, student_answer)
        elif question.question_type == "numeric":
            return Grader._check_numeric(question, student_answer)
        elif question.question_type == "expression":
            return Grader._check_expression(question, student_answer)
        elif question.question_type == "multi_part":
            return Grader._check_multi_part(question, student_answer)
        elif question.question_type == "proof":
            return Grader._check_proof(question, student_answer)
        else:
            return False, 0, "Unknown question type"

    @staticmethod
    def _check_multiple_choice(question: Question, answer: str) -> Tuple[bool, float, str]:
        """Check multiple choice answer."""
        correct_answer = str(question.answer).upper().strip()
        student_answer = answer.upper().strip()

        # Handle both letter (A, B, C, D) and full answer text
        if len(student_answer) == 1 and student_answer in "ABCD":
            is_correct = student_answer == correct_answer
        else:
            # Check if the answer text matches
            is_correct = student_answer == correct_answer

        marks = question.marks if is_correct else 0
        feedback = "Correct!" if is_correct else f"Incorrect. The answer is {correct_answer}."
        return is_correct, marks, feedback

    @staticmethod
    def _check_numeric(question: Question, answer: str) -> Tuple[bool, float, str]:
        """Check numeric answer with tolerance."""
        try:
            # Clean the input
            answer = answer.strip()

            # Handle list of answers
            if isinstance(question.answer, list):
                return Grader._check_numeric_list(question, answer)

            # Parse student answer
            student_value = Grader._parse_numeric(answer)
            correct_value = float(question.answer)

            # Check with tolerance
            tolerance = question.tolerance
            is_correct = abs(student_value - correct_value) <= tolerance

            marks = question.marks if is_correct else 0
            feedback = "Correct!" if is_correct else f"Incorrect. The answer is {correct_value}."
            return is_correct, marks, feedback

        except (ValueError, TypeError) as e:
            return False, 0, f"Could not parse answer. Please enter a number. Error: {str(e)}"

    @staticmethod
    def _check_numeric_list(question: Question, answer: str) -> Tuple[bool, float, str]:
        """Check when answer is a list of numeric values (e.g., roots of equation)."""
        try:
            # Parse student answers - accept comma, semicolon, or 'and' separated
            answer = answer.replace(" and ", ",").replace(";", ",")
            student_values = []
            for part in answer.split(","):
                part = part.strip()
                if part:
                    student_values.append(Grader._parse_numeric(part))

            correct_values = [float(v) for v in question.answer]
            tolerance = question.tolerance

            # Sort both lists for comparison
            student_values.sort()
            correct_values.sort()

            if len(student_values) != len(correct_values):
                return False, 0, f"Expected {len(correct_values)} values. The answers are: {', '.join(map(str, question.answer))}"

            # Check each value
            all_correct = True
            for sv, cv in zip(student_values, correct_values):
                if abs(sv - cv) > tolerance:
                    all_correct = False
                    break

            marks = question.marks if all_correct else 0
            feedback = "Correct!" if all_correct else f"Incorrect. The answers are: {', '.join(map(str, question.answer))}"
            return all_correct, marks, feedback

        except (ValueError, TypeError):
            return False, 0, f"Could not parse answer. Please enter numbers separated by commas."

    @staticmethod
    def _parse_numeric(value: str) -> float:
        """Parse a numeric string, handling fractions and special formats."""
        value = value.strip()

        # Handle fractions (e.g., "1/2", "-3/4")
        if "/" in value:
            parts = value.split("/")
            if len(parts) == 2:
                return float(parts[0]) / float(parts[1])

        # Handle pi
        value = value.lower().replace("pi", str(math.pi))

        # Handle square roots (e.g., "sqrt(2)", "√2")
        sqrt_pattern = r"sqrt\(([^)]+)\)|√(\d+)"
        match = re.search(sqrt_pattern, value)
        if match:
            num = match.group(1) or match.group(2)
            sqrt_val = math.sqrt(float(num))
            value = re.sub(sqrt_pattern, str(sqrt_val), value)

        return float(eval(value))

    @staticmethod
    def _check_expression(question: Question, answer: str) -> Tuple[bool, float, str]:
        """Check mathematical expression (simplified comparison)."""
        # Normalize both expressions
        correct = Grader._normalize_expression(str(question.answer))
        student = Grader._normalize_expression(answer)

        is_correct = correct == student
        marks = question.marks if is_correct else 0
        feedback = "Correct!" if is_correct else f"Incorrect. The answer is {question.answer}."
        return is_correct, marks, feedback

    @staticmethod
    def _normalize_expression(expr: str) -> str:
        """Normalize a mathematical expression for comparison."""
        # Remove spaces
        expr = expr.replace(" ", "")
        # Convert to lowercase
        expr = expr.lower()
        # Standardize operators
        expr = expr.replace("×", "*").replace("÷", "/")
        # Remove unnecessary parentheses at start/end
        while expr.startswith("(") and expr.endswith(")"):
            expr = expr[1:-1]
        return expr

    @staticmethod
    def _check_multi_part(question: Question, answer: str) -> Tuple[bool, float, str]:
        """Check multi-part question answers."""
        if not question.sub_questions:
            return False, 0, "Invalid multi-part question"

        # Parse answers - expect format like "a) value b) value" or "a: value, b: value"
        answers = Grader._parse_multi_part_answer(answer, len(question.sub_questions))

        total_marks = 0
        max_marks = sum(sq.marks for sq in question.sub_questions)
        correct_parts = []
        incorrect_parts = []

        for i, sq in enumerate(question.sub_questions):
            student_part = answers.get(sq.label, answers.get(str(i), ""))

            # Create temporary question for checking
            temp_q = Question(
                id=f"{question.id}_{sq.label}",
                topic_id=question.topic_id,
                subtopic_id=question.subtopic_id,
                question_type="numeric",  # Default to numeric for sub-questions
                difficulty=question.difficulty,
                marks=sq.marks,
                question_text=sq.question_text,
                answer=sq.answer,
                tolerance=question.tolerance
            )

            is_part_correct, marks, _ = Grader._check_numeric(temp_q, student_part)
            total_marks += marks

            if is_part_correct:
                correct_parts.append(sq.label)
            else:
                incorrect_parts.append(f"{sq.label}={sq.answer}")

        is_correct = total_marks == max_marks
        if is_correct:
            feedback = "All parts correct!"
        elif total_marks > 0:
            feedback = f"Partial marks: {total_marks}/{max_marks}. Incorrect: {', '.join(incorrect_parts)}"
        else:
            feedback = f"Incorrect. Answers: {', '.join(incorrect_parts)}"

        return is_correct, total_marks, feedback

    @staticmethod
    def _parse_multi_part_answer(answer: str, num_parts: int) -> dict:
        """Parse multi-part answers into a dictionary."""
        result = {}

        # Try format: "a) value b) value" or "a: value b: value"
        patterns = [
            r"([a-z])\s*[\):\-]\s*([^a-z\)]+)",  # a) value or a: value
            r"([a-z])\s*=\s*([^,;a-z]+)",  # a = value
        ]

        for pattern in patterns:
            matches = re.findall(pattern, answer.lower())
            if matches:
                for label, value in matches:
                    result[label.strip()] = value.strip()
                if result:
                    return result

        # Fallback: split by comma/semicolon and assign to a, b, c, etc.
        parts = re.split(r"[,;]", answer)
        labels = "abcdefgh"
        for i, part in enumerate(parts):
            if i < len(labels):
                result[labels[i]] = part.strip()

        return result

    @staticmethod
    def _check_proof(question: Question, answer: str) -> Tuple[bool, float, str]:
        """
        Check proof questions - these require human judgment.
        For automated checking, look for key statements/reasons.
        """
        # For proofs, we do a simplified keyword check
        # In a real system, this would need human grading or more sophisticated NLP

        correct_answer = str(question.answer).lower()
        student_answer = answer.lower()

        # Extract key terms from the correct answer
        key_terms = [term.strip() for term in correct_answer.split(",")
                     if len(term.strip()) > 3]

        if not key_terms:
            # If no key terms defined, give full marks for any substantial answer
            if len(student_answer) > 20:
                return True, question.marks, "Answer recorded. Proofs require manual verification."
            return False, 0, "Please provide a complete proof with statements and reasons."

        # Check how many key terms are present
        matches = sum(1 for term in key_terms if term in student_answer)
        match_ratio = matches / len(key_terms)

        if match_ratio >= 0.8:
            marks = question.marks
            feedback = "Well done! Your proof contains the key elements."
        elif match_ratio >= 0.5:
            marks = question.marks * 0.5
            feedback = f"Partial marks. Missing some key elements. Expected: {question.answer}"
        else:
            marks = 0
            feedback = f"Incorrect or incomplete proof. Key elements needed: {question.answer}"

        return match_ratio >= 0.8, marks, feedback


def grade_session(questions: List[Question], answers: List[str]) -> Tuple[float, float, List[Tuple[bool, float, str]]]:
    """
    Grade a complete session of questions.

    Returns:
        Tuple of (total_marks, max_marks, list of (is_correct, marks, feedback))
    """
    grader = Grader()
    results = []
    total_marks = 0
    max_marks = 0

    for q, a in zip(questions, answers):
        is_correct, marks, feedback = grader.check_answer(q, a)
        results.append((is_correct, marks, feedback))
        total_marks += marks
        max_marks += q.marks

    return total_marks, max_marks, results
