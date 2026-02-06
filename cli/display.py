"""Output formatting and display utilities."""

import os
import sys


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header(title: str, width: int = 60):
    """Print a formatted header."""
    print("\n" + "=" * width)
    padding = (width - len(title)) // 2
    print(" " * padding + title)
    print("=" * width)


def print_subheader(title: str, width: int = 60):
    """Print a formatted subheader."""
    print("\n" + "-" * width)
    print(title)
    print("-" * width)


def print_menu(options: list, title: str = "Menu"):
    """Print a numbered menu."""
    print_header(title)
    for i, option in enumerate(options, 1):
        print(f"  [{i}] {option}")
    print()


def print_question(question, index: int, total: int, topic_name: str = None):
    """Print a formatted question."""
    print("\n" + "-" * 50)
    if topic_name:
        print(f"Topic: {topic_name}")
    print(f"Question {index}/{total} | Difficulty: {'*' * question.difficulty} | Marks: {question.marks}")
    print("-" * 50)
    print(f"\n{question.question_text}\n")

    if question.question_type == "multiple_choice" and question.options:
        for i, option in enumerate(question.options):
            letter = chr(65 + i)  # A, B, C, D
            print(f"  {letter}) {option}")
        print()


def print_result(is_correct: bool, marks: float, max_marks: float, feedback: str):
    """Print question result."""
    if is_correct:
        print(f"\n[OK] Correct! ({marks:.0f}/{max_marks:.0f} marks)")
    elif marks > 0:
        print(f"\n[~] Partial ({marks:.0f}/{max_marks:.0f} marks)")
        print(f"  {feedback}")
    else:
        print(f"\n[X] Incorrect (0/{max_marks:.0f} marks)")
        print(f"  {feedback}")


def print_progress_bar(current: int, total: int, width: int = 40, label: str = ""):
    """Print a progress bar."""
    if total == 0:
        percent = 0
    else:
        percent = current / total

    filled = int(width * percent)
    bar = "█" * filled + "░" * (width - filled)
    print(f"{label}[{bar}] {current}/{total} ({percent*100:.0f}%)")


def format_time(seconds: int) -> str:
    """Format seconds as MM:SS or HH:MM:SS."""
    if seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def print_timer(seconds_remaining: int, total_seconds: int):
    """Print a timer display."""
    time_str = format_time(int(seconds_remaining))
    percent = seconds_remaining / total_seconds if total_seconds > 0 else 0

    # Color coding based on time remaining
    if percent > 0.5:
        status = "[T]"
    elif percent > 0.25:
        status = "(!)"
    else:
        status = "[!]"

    print(f"\r{status} Time: {time_str}  ", end="", flush=True)


def print_topic_list(topics: list, show_mastery: bool = True):
    """Print a list of topics."""
    print(f"\n{'#':<3} {'Topic':<30} {'Paper':>6}", end="")
    if show_mastery:
        print(f" {'Best':>8} {'Status':>10}")
    else:
        print(f" {'Questions':>10}")
    print("-" * 65)

    for i, topic in enumerate(topics, 1):
        print(f"{i:<3} {topic['name']:<30} {topic['paper']:>6}", end="")
        if show_mastery:
            status = "[OK] Mastered" if topic['mastered'] else f"  {topic['test_best']:.0f}%"
            print(f" {topic['test_best']:>7.0f}% {status:>10}")
        else:
            print(f" {topic['question_count']:>10}")


def print_welcome():
    """Print welcome message."""
    print("""
+==================================================================+
|                                                                  |
|     NSC MATHEMATICS STUDY PROGRAM                                |
|     CAPS Curriculum - Grade 12                                   |
|                                                                  |
|     Prepare for your May Exam!                                   |
|                                                                  |
+==================================================================+
""")


def print_goodbye():
    """Print goodbye message."""
    print("""
+==================================================================+
|                                                                  |
|     Good luck with your studies!                                 |
|     Your progress has been saved.                                |
|                                                                  |
+==================================================================+
""")


def confirm(prompt: str, default: bool = False) -> bool:
    """Ask for confirmation."""
    suffix = " [Y/n]: " if default else " [y/N]: "
    response = input(prompt + suffix).strip().lower()

    if not response:
        return default
    return response in ('y', 'yes')


def get_input(prompt: str, valid_options: list = None, allow_empty: bool = False) -> str:
    """Get input with optional validation."""
    while True:
        response = input(prompt).strip()

        if not response and not allow_empty:
            print("Please enter a response.")
            continue

        if valid_options and response.lower() not in [str(o).lower() for o in valid_options]:
            print(f"Please choose from: {', '.join(map(str, valid_options))}")
            continue

        return response


def get_number(prompt: str, min_val: int = None, max_val: int = None) -> int:
    """Get a number input with range validation."""
    while True:
        try:
            response = input(prompt).strip()
            value = int(response)

            if min_val is not None and value < min_val:
                print(f"Please enter a value >= {min_val}")
                continue
            if max_val is not None and value > max_val:
                print(f"Please enter a value <= {max_val}")
                continue

            return value
        except ValueError:
            print("Please enter a valid number.")
