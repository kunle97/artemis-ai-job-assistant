"""
Application answer resolution constants.

Holds stop words, normalization settings, scoring thresholds, and
shared resolver constants that are not intent-specific.
"""

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "about",
    "as",
    "at",
    "be",
    "by",
    "can",
    "describe",
    "did",
    "do",
    "does",
    "for",
    "from",
    "how",
    "i",
    "if",
    "in",
    "is",
    "it",
    "me",
    "most",
    "my",
    "of",
    "on",
    "or",
    "please",
    "role",
    "tell",
    "that",
    "the",
    "this",
    "to",
    "us",
    "was",
    "what",
    "when",
    "where",
    "why",
    "with",
    "you",
    "your",
}

# Similarity thresholds
SAVED_ANSWER_FUZZY_MATCH_THRESHOLD = 0.55
INTENT_DETECTION_THRESHOLD = 0.40

# Similarity scoring weights / heuristics
CONTAINMENT_SCORE_MULTIPLIER = 0.9
PREFIX_SIMILARITY_BONUS = 0.15
PREFIX_TOKEN_WINDOW = 3
MIN_PREFIX_TOKEN_COUNT = 2
MIN_SHARED_PREFIX_TOKENS = 2

# Normalization / tokenization patterns
NORMALIZE_APOSTROPHE_SOURCE = "’"
NORMALIZE_APOSTROPHE_TARGET = "'"
NON_ALPHANUMERIC_PATTERN = r"[^a-z0-9\s']"
WHITESPACE_PATTERN = r"\s+"
TOKEN_PATTERN = r"[a-z0-9]+"

# Resolution source labels
SOURCE_UNRESOLVED = "unresolved"
SOURCE_SAVED_ANSWER_EXACT = "saved_answer_exact"
SOURCE_SAVED_ANSWER_FUZZY = "saved_answer_fuzzy"
SOURCE_USER_INTENT_ANSWER = "user_intent_answer"
SOURCE_DEFAULT_INTENT_ANSWER = "default_intent_answer"