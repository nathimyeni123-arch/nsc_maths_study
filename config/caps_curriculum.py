"""CAPS Curriculum definitions for NSC Grade 12 Mathematics."""

from dataclasses import dataclass
from typing import List, Dict


@dataclass
class Subtopic:
    """Represents a subtopic within a main topic."""
    id: str
    name: str
    description: str


@dataclass
class Topic:
    """Represents a CAPS curriculum topic."""
    id: str
    name: str
    paper: int  # 1 or 2
    weight: float  # Percentage weight
    marks: int  # Approximate marks allocation
    subtopics: List[Subtopic]


# Paper 1 Topics
ALGEBRA = Topic(
    id="algebra",
    name="Algebra",
    paper=1,
    weight=20.0,
    marks=30,
    subtopics=[
        Subtopic("equations", "Equations", "Linear, quadratic, simultaneous equations"),
        Subtopic("inequalities", "Inequalities", "Linear and quadratic inequalities"),
        Subtopic("exponents", "Exponents and Surds", "Laws of exponents, simplifying surds"),
        Subtopic("logarithms", "Logarithms", "Logarithmic equations and applications"),
    ]
)

PATTERNS_SEQUENCES = Topic(
    id="patterns_sequences",
    name="Patterns & Sequences",
    paper=1,
    weight=17.0,
    marks=25,
    subtopics=[
        Subtopic("arithmetic", "Arithmetic Sequences", "Tn = a + (n-1)d, sum formula"),
        Subtopic("geometric", "Geometric Sequences", "Tn = ar^(n-1), sum formulas"),
        Subtopic("sigma", "Sigma Notation", "Summation notation and calculations"),
        Subtopic("convergence", "Convergent Series", "Sum to infinity for |r| < 1"),
    ]
)

FINANCIAL_MATHS = Topic(
    id="financial_maths",
    name="Financial Mathematics",
    paper=1,
    weight=10.0,
    marks=15,
    subtopics=[
        Subtopic("compound_interest", "Compound Interest", "Growth and decay formulas"),
        Subtopic("annuities", "Annuities", "Future and present value calculations"),
        Subtopic("loans", "Loan Calculations", "Amortisation and balance calculations"),
        Subtopic("sinking_funds", "Sinking Funds", "Savings for future obligations"),
    ]
)

FUNCTIONS_GRAPHS = Topic(
    id="functions_graphs",
    name="Functions & Graphs",
    paper=1,
    weight=23.0,
    marks=35,
    subtopics=[
        Subtopic("parabola", "Parabola", "y = a(x-p)² + q, turning points, axis of symmetry"),
        Subtopic("hyperbola", "Hyperbola", "y = a/(x-p) + q, asymptotes"),
        Subtopic("exponential", "Exponential", "y = ab^(x-p) + q, growth and decay"),
        Subtopic("inverse", "Inverse Functions", "Finding and graphing inverses"),
        Subtopic("logarithmic", "Logarithmic Functions", "y = log_a(x), properties"),
    ]
)

DIFFERENTIAL_CALCULUS = Topic(
    id="differential_calculus",
    name="Differential Calculus",
    paper=1,
    weight=23.0,
    marks=35,
    subtopics=[
        Subtopic("first_principles", "First Principles", "Limit definition of derivative"),
        Subtopic("differentiation_rules", "Differentiation Rules", "Power rule, sum/difference"),
        Subtopic("tangent_normal", "Tangents and Normals", "Equations of tangent lines"),
        Subtopic("curve_sketching", "Curve Sketching", "Turning points, concavity"),
        Subtopic("optimization", "Optimization", "Maximum/minimum problems"),
        Subtopic("rates_of_change", "Rates of Change", "Applied rate problems"),
    ]
)

PROBABILITY = Topic(
    id="probability",
    name="Probability",
    paper=1,
    weight=7.0,
    marks=10,
    subtopics=[
        Subtopic("counting", "Counting Principles", "Fundamental counting principle"),
        Subtopic("permutations", "Permutations", "Arrangements with order"),
        Subtopic("combinations", "Combinations", "Selections without order"),
        Subtopic("probability_rules", "Probability Rules", "Addition and multiplication rules"),
    ]
)

# Paper 2 Topics
STATISTICS = Topic(
    id="statistics",
    name="Statistics",
    paper=2,
    weight=13.0,
    marks=20,
    subtopics=[
        Subtopic("measures_central", "Measures of Central Tendency", "Mean, median, mode"),
        Subtopic("measures_dispersion", "Measures of Dispersion", "Range, variance, std dev"),
        Subtopic("ogives", "Ogives and Percentiles", "Cumulative frequency graphs"),
        Subtopic("bivariate", "Bivariate Data", "Scatter plots, regression, correlation"),
    ]
)

ANALYTICAL_GEOMETRY = Topic(
    id="analytical_geometry",
    name="Analytical Geometry",
    paper=2,
    weight=27.0,
    marks=40,
    subtopics=[
        Subtopic("distance_midpoint", "Distance and Midpoint", "Distance formula, midpoint"),
        Subtopic("gradient", "Gradient", "Gradient formula, parallel/perpendicular lines"),
        Subtopic("straight_line", "Straight Line Equations", "Various forms of line equations"),
        Subtopic("circle", "Circle", "Equation of circle, tangents"),
    ]
)

TRIGONOMETRY = Topic(
    id="trigonometry",
    name="Trigonometry",
    paper=2,
    weight=27.0,
    marks=40,
    subtopics=[
        Subtopic("identities", "Trigonometric Identities", "Compound angle, double angle"),
        Subtopic("equations", "Trigonometric Equations", "General solutions"),
        Subtopic("graphs", "Trigonometric Graphs", "Sine, cosine, tangent graphs"),
        Subtopic("2d_problems", "2D Problems", "Sine rule, cosine rule, area rule"),
        Subtopic("3d_problems", "3D Problems", "Applications in 3D contexts"),
    ]
)

EUCLIDEAN_GEOMETRY = Topic(
    id="euclidean_geometry",
    name="Euclidean Geometry",
    paper=2,
    weight=33.0,
    marks=50,
    subtopics=[
        Subtopic("circle_theorems", "Circle Theorems", "Angles in circles, cyclic quads"),
        Subtopic("proportionality", "Proportionality Theorems", "Similar triangles, ratios"),
        Subtopic("proofs", "Geometric Proofs", "Formal proof writing"),
    ]
)

# All topics organized by paper
PAPER1_TOPICS = [
    ALGEBRA,
    PATTERNS_SEQUENCES,
    FINANCIAL_MATHS,
    FUNCTIONS_GRAPHS,
    DIFFERENTIAL_CALCULUS,
    PROBABILITY,
]

PAPER2_TOPICS = [
    STATISTICS,
    ANALYTICAL_GEOMETRY,
    TRIGONOMETRY,
    EUCLIDEAN_GEOMETRY,
]

ALL_TOPICS = PAPER1_TOPICS + PAPER2_TOPICS

# Quick lookup dictionary
TOPICS_BY_ID: Dict[str, Topic] = {topic.id: topic for topic in ALL_TOPICS}


def get_topic(topic_id: str) -> Topic:
    """Get a topic by its ID."""
    return TOPICS_BY_ID.get(topic_id)


def get_topics_for_paper(paper: int) -> List[Topic]:
    """Get all topics for a specific paper."""
    return PAPER1_TOPICS if paper == 1 else PAPER2_TOPICS
