"""Application settings and constants."""

# Database
DATABASE_NAME = "nsc_maths_study.db"

# Grading
PASS_MARK = 70  # Percentage required to pass topic tests
MASTERY_THRESHOLD = 70  # Percentage required for topic mastery

# Diagnostic test
DIAGNOSTIC_QUESTIONS_PER_TOPIC = 3

# Drill settings
DRILL_QUESTIONS_DEFAULT = 10
DRILL_WEAK_AREA_WEIGHT = 2.0  # Weight for prioritizing weak topics

# Topic test settings
TOPIC_TEST_QUESTIONS = 10

# Mock exam settings
MOCK_EXAM_PAPER1_TIME = 180  # 3 hours in minutes
MOCK_EXAM_PAPER2_TIME = 180  # 3 hours in minutes
MOCK_EXAM_PAPER1_MARKS = 150
MOCK_EXAM_PAPER2_MARKS = 150

# Question difficulty levels
DIFFICULTY_LEVELS = {
    1: "Easy",
    2: "Medium",
    3: "Hard",
    4: "Challenge"
}

# Answer tolerance for numeric questions
DEFAULT_TOLERANCE = 0.01
