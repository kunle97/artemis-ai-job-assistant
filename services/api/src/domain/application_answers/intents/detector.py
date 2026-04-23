"""
Intent detection logic.
"""

from src.domain.application_answers.constants import INTENT_DETECTION_THRESHOLD
from src.domain.application_answers.intents.constants import INTENT_PATTERNS


class IntentDetector:
    def __init__(self, normalize_fn, similarity_fn):
        self.normalize = normalize_fn
        self.similarity = similarity_fn

    def detect(self, question_text: str) -> str | None:
        normalized_question = self.normalize(question_text)

        best_intent = None
        best_score = 0.0

        for intent_key, patterns in INTENT_PATTERNS.items():
            for pattern in patterns:
                normalized_pattern = self.normalize(pattern)
                score = self.similarity(normalized_question, normalized_pattern)

                if score > best_score:
                    best_score = score
                    best_intent = intent_key

        if best_score >= INTENT_DETECTION_THRESHOLD:
            return best_intent

        return None