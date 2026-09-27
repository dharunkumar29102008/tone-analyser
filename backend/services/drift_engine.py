from typing import List, Dict, Any, Optional
import numpy as np

class DriftEngine:
    """Detects meaningful statistical and stateful changes in conversation emotional arc."""

    def __init__(self, sensitivity_threshold: float = 0.25, window_size: int = 3):
        # sensitivity_threshold: lower means more sensitive to shifts (0.15 - 0.40)
        self.sensitivity_threshold = sensitivity_threshold
        self.window_size = window_size

    def detect_tone_shifts(self, messages_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculates moving baseline and flags significant tone shift points.
        """
        if not messages_data:
            return []

        shifts = []
        intensities = [m["emotional_intensity"] for m in messages_data]
        sentiments = [m["sentiment_score"] for m in messages_data]

        for i in range(1, len(messages_data)):
            curr = messages_data[i]
            prev = messages_data[i - 1]

            # Compute recent baseline from up to window_size preceding messages
            start_idx = max(0, i - self.window_size)
            baseline_intensity = np.mean(intensities[start_idx:i])
            baseline_sentiment = np.mean(sentiments[start_idx:i])

            intensity_diff = curr["emotional_intensity"] - baseline_intensity
            sentiment_diff = curr["sentiment_score"] - baseline_sentiment

            # Combined drift magnitude normalized to [0.0, 1.0]
            magnitude = (abs(intensity_diff) / 100.0 * 0.5) + (abs(sentiment_diff) / 2.0 * 0.5)

            # Check if magnitude exceeds sensitivity threshold or emotion category flipped significantly
            is_emotion_flip = (
                prev["emotion"] != curr["emotion"] and
                (
                    (prev["emotion"] in ["calm", "neutral", "hopeful"] and curr["emotion"] in ["sarcasm", "frustration", "passive_aggressive", "anger"]) or
                    (prev["emotion"] in ["frustration", "anger", "passive_aggressive"] and curr["emotion"] in ["calm", "hopeful"])
                )
            )

            if magnitude >= self.sensitivity_threshold or is_emotion_flip:
                # Determine shift type
                if curr["emotion"] in ["frustration", "anger"] and prev["emotion"] not in ["frustration", "anger"]:
                    shift_type = "negative_escalation"
                    note = f"Shift from {prev['emotion'].title()} to {curr['emotion'].title()}"
                elif curr["emotion"] == "sarcasm":
                    shift_type = "sarcastic_diversion"
                    note = f"Sarcastic friction introduced after {prev['emotion'].title()}"
                elif curr["emotion"] == "passive_aggressive":
                    shift_type = "passive_aggressive_defensiveness"
                    note = f"Defensive passive-aggression emerged"
                elif curr["emotion"] in ["calm", "hopeful"] and prev["emotion"] in ["frustration", "anger", "passive_aggressive"]:
                    shift_type = "de_escalation_recovery"
                    note = f"De-escalation: tone moved towards {curr['emotion'].title()}"
                else:
                    shift_type = "emotional_fluctuation"
                    note = f"Emotional state shifted to {curr['emotion'].title()}"

                shifts.append({
                    "message_id": curr["id"],
                    "timestamp": curr["timestamp"],
                    "sender": curr["sender"],
                    "shift_type": shift_type,
                    "magnitude": round(float(magnitude), 3),
                    "previous_state": prev["emotion"],
                    "new_state": curr["emotion"],
                    "intensity_jump": round(float(intensity_diff), 1),
                    "sentiment_delta": round(float(sentiment_diff), 2),
                    "note": note
                })

        return shifts
