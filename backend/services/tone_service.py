from typing import Dict, Any, Tuple
from backend.models.schemas import ToneResult, SentimentResult, EmotionResult, SarcasmResult, PassiveAggressionResult

class ToneService:
    """Derives conversation tone and UI badge styling matching reference specification."""

    @staticmethod
    def derive_tone(
        sentiment: SentimentResult,
        emotion: EmotionResult,
        sarcasm: SarcasmResult,
        passive_aggression: PassiveAggressionResult,
        text: str
    ) -> Tuple[ToneResult, Dict[str, str]]:
        cues = []
        variant = "neutral"
        badge_text = "Neutral"

        # 1. Check Sarcasm
        if sarcasm.sarcasm_detected and sarcasm.sarcasm_confidence >= 0.5:
            tone = "Sarcasm"
            conf = sarcasm.sarcasm_confidence
            badge_text = "Sarcasm"
            variant = "sarcasm"
            cues.extend(sarcasm.cues)

        # 2. Check Passive Aggressive
        elif passive_aggression.passive_aggression_detected and passive_aggression.passive_aggression_score >= 0.45:
            tone = "Passive Aggressive"
            conf = passive_aggression.passive_aggression_score
            badge_text = "• Passive Aggressive"
            variant = "passive-aggressive"
            cues.extend(passive_aggression.cues)

        # 3. Check Frustration / Anger
        elif emotion.dominant_emotion in ["frustration", "anger"]:
            tone = "Frustrated" if emotion.dominant_emotion == "frustration" else "Confrontational"
            conf = emotion.emotion_score
            badge_text = "Frustrated"
            variant = "frustrated"
            cues.append("Expresses mounting friction or annoyance")

        # 4. Check Hopeful / Collaborative
        elif emotion.dominant_emotion == "hopeful" or (sentiment.sentiment == "positive" and sentiment.sentiment_score > 0.4):
            tone = "Hopeful"
            conf = max(emotion.emotion_score, 0.7)
            badge_text = "Hopeful"
            variant = "hopeful"
            cues.append("Forward-looking collaborative engagement")

        # 5. Check Calm / Reassuring
        elif emotion.dominant_emotion == "calm" or any(w in text.lower() for w in ["chill", "almost", "okay", "passed", "finish it now", "clean"]):
            tone = "Calm"
            conf = 0.75
            badge_text = "Calm"
            variant = "calm"
            cues.append("Reassuring and composed response")

        # 6. Default to Neutral / Friendly
        else:
            if sentiment.sentiment == "positive":
                tone = "Friendly"
                badge_text = "Friendly"
                variant = "hopeful"
            else:
                tone = "Neutral"
                badge_text = "Neutral"
                variant = "neutral"
            conf = 0.65

        badge = {
            "text": badge_text,
            "variant": variant
        }

        return ToneResult(
            tone=tone,
            confidence=round(conf, 2),
            cues=cues
        ), badge
