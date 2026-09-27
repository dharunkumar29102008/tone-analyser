import re
from typing import Dict, Tuple
from backend.models.schemas import SentimentResult
from backend.utils.text_utils import extract_emojis, EMOJI_TONES

# Curated high-precision lexicon for conversational tone
POSITIVE_WORDS = {
    "good": 0.6, "great": 0.8, "clean": 0.5, "thanks": 0.6, "handled": 0.6,
    "appreciate": 0.8, "hustle": 0.7, "win": 0.8, "hope": 0.6, "hopeful": 0.7,
    "awesome": 0.9, "passed": 0.6, "slides": 0.2, "perfect": 0.9, "love": 0.85,
    "nice": 0.6, "helpful": 0.7, "finished": 0.4, "done": 0.3, "yes": 0.3,
    "yeah": 0.3, "okay": 0.2, "calm": 0.5, "relax": 0.3, "resolved": 0.7
}

NEGATIVE_WORDS = {
    "bugs": -0.4, "weird": -0.4, "drama": -0.6, "fault": -0.6, "late": -0.5,
    "delay": -0.5, "deadline": -0.3, "pull": -0.3, "worst": -0.9, "bad": -0.6,
    "hate": -0.85, "annoying": -0.75, "stupid": -0.8, "fail": -0.7, "failed": -0.7,
    "angry": -0.8, "terrible": -0.85, "broken": -0.6, "tired": -0.5, "urgent": -0.4,
    "acting": -0.3, "disappointed": -0.7, "crisis": -0.8
}

INTENSIFIERS = {
    "very": 1.4, "so": 1.3, "really": 1.35, "extremely": 1.6, "totally": 1.3,
    "absolutely": 1.5, "completely": 1.4, "super": 1.3, "hyper": 1.4
}

NEGATIONS = {
    "not", "never", "no", "don't", "dont", "hardly", "barely", "scarcely", "without"
}

class SentimentService:
    """Computes fine-grained contextual sentiment scores."""

    @staticmethod
    def analyze_sentiment(text: str) -> SentimentResult:
        words = re.findall(r"\b[\w'-]+\b", text.lower())
        if not words:
            return SentimentResult(sentiment="neutral", sentiment_score=0.0, confidence=0.5)

        score = 0.0
        word_count = len(words)
        negated = False
        multiplier = 1.0

        for i, word in enumerate(words):
            if word in NEGATIONS:
                negated = True
                continue

            if word in INTENSIFIERS:
                multiplier = INTENSIFIERS[word]
                continue

            val = 0.0
            if word in POSITIVE_WORDS:
                val = POSITIVE_WORDS[word]
            elif word in NEGATIVE_WORDS:
                val = NEGATIVE_WORDS[word]

            if val != 0.0:
                if negated:
                    val = -val * 0.7
                    negated = False
                val *= multiplier
                multiplier = 1.0
                score += val

        # Emoji sentiment contribution
        emojis = extract_emojis(text)
        for em in emojis:
            if em in EMOJI_TONES:
                _, _, em_valence = EMOJI_TONES[em]
                score += em_valence * 0.7

        # Normalize score to [-1.0, 1.0]
        denom = max(1.5, (word_count ** 0.5) * 0.8)
        norm_score = max(-1.0, min(1.0, score / denom))

        # Categorize
        if norm_score > 0.15:
            sentiment = "positive"
            conf = min(0.95, 0.5 + abs(norm_score) * 0.45)
        elif norm_score < -0.15:
            sentiment = "negative"
            conf = min(0.95, 0.5 + abs(norm_score) * 0.45)
        else:
            sentiment = "neutral"
            conf = 0.75 - abs(norm_score)

        return SentimentResult(
            sentiment=sentiment,
            sentiment_score=round(norm_score, 2),
            confidence=round(conf, 2)
        )
