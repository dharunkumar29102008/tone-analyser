from backend.models.schemas import SarcasmResult
from backend.utils.text_utils import detect_sarcasm_cues

class SarcasmService:
    """Contextual sarcasm and irony detector."""

    @staticmethod
    def analyze_sarcasm(text: str, prev_context_sentiment: float = 0.0) -> SarcasmResult:
        detected, confidence, cues = detect_sarcasm_cues(text)

        # Contextual boost: if previous sentiment was neutral or negative and current message
        # contains ironic affirmation or quotes, increase sarcasm confidence
        if prev_context_sentiment < 0 and detected:
            confidence = min(0.95, confidence + 0.15)
            cues.append("Preceding negative context strengthens sarcastic interpretation")

        return SarcasmResult(
            sarcasm_detected=detected,
            sarcasm_confidence=confidence,
            cues=cues
        )
