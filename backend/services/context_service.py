from typing import List, Dict, Any, Tuple
from backend.models.schemas import SentimentResult, EmotionResult, SarcasmResult, PassiveAggressionResult

class ContextService:
    """Maintains evolving multi-turn conversation state, emotional intensity, and escalation tracking."""

    @staticmethod
    def calculate_emotional_intensity(
        sentiment: SentimentResult,
        emotion: EmotionResult,
        sarcasm: SarcasmResult,
        passive_aggression: PassiveAggressionResult,
        text: str,
        recent_escalation: float = 0.0
    ) -> float:
        """
        Calculate emotional intensity (0 to 100 scale).
        Higher for strong feelings (both high tension and high excitement).
        """
        # Base from emotional polarity
        base_intensity = abs(sentiment.sentiment_score) * 45

        # Emotion specific multipliers
        emotion_weights = {
            "anger": 85,
            "frustration": 72,
            "sarcasm": 65,
            "passive_aggressive": 60,
            "hopeful": 55,
            "joy": 60,
            "calm": 25,
            "neutral": 15
        }
        e_weight = emotion_weights.get(emotion.dominant_emotion, 30)

        # Sarcasm / passive aggression bonuses
        if sarcasm.sarcasm_detected:
            base_intensity += sarcasm.sarcasm_confidence * 20
        if passive_aggression.passive_aggression_detected:
            base_intensity += passive_aggression.passive_aggression_score * 20

        # Punctuation emphasis
        if "!" in text or "?" in text:
            base_intensity += 8

        # Weighted combination
        raw_val = (base_intensity * 0.45) + (e_weight * 0.55) + (recent_escalation * 0.15)
        return round(min(100.0, max(10.0, raw_val)), 1)

    @staticmethod
    def calculate_escalation_level(
        sentiment: SentimentResult,
        emotion: EmotionResult,
        sarcasm: SarcasmResult,
        passive_aggression: PassiveAggressionResult,
        prev_escalation: float = 0.0
    ) -> float:
        """
        Calculates conversation escalation / friction level (0 to 100 scale).
        Tracks conflict build-up and de-escalation over turns.
        """
        delta = 0.0

        if emotion.dominant_emotion == "anger":
            delta += 35.0
        elif emotion.dominant_emotion == "frustration":
            delta += 25.0
        elif sarcasm.sarcasm_detected:
            delta += 18.0
        elif passive_aggression.passive_aggression_detected:
            delta += 16.0
        elif emotion.dominant_emotion in ["calm", "hopeful", "neutral"]:
            # De-escalation
            delta -= 22.0

        # Sentiment contribution
        if sentiment.sentiment_score < -0.3:
            delta += abs(sentiment.sentiment_score) * 15.0
        elif sentiment.sentiment_score > 0.3:
            delta -= sentiment.sentiment_score * 15.0

        # Smooth update with momentum
        new_escalation = (prev_escalation * 0.55) + ((prev_escalation + delta) * 0.45)
        return round(min(100.0, max(5.0, new_escalation)), 1)
