import unittest
from backend.services.drift_engine import DriftEngine
from backend.services.trigger_detector import TriggerDetector

class TestDriftEngine(unittest.TestCase):
    def test_drift_detection(self):
        engine = DriftEngine(sensitivity_threshold=0.25)
        # Mock emotional progression: calm -> sudden spike in tension -> recovery
        mock_messages = [
            {"id": 1, "timestamp": "10:00 AM", "sender": "Alice", "text": "Good morning", "emotional_intensity": 20.0, "sentiment_score": 0.3, "emotion": "calm"},
            {"id": 2, "timestamp": "10:02 AM", "sender": "Bob", "text": "Morning, working on it", "emotional_intensity": 22.0, "sentiment_score": 0.2, "emotion": "calm"},
            {"id": 3, "timestamp": "10:05 AM", "sender": "Alice", "text": "Are you serious? You broke production!", "emotional_intensity": 82.0, "sentiment_score": -0.8, "emotion": "frustration"},
            {"id": 4, "timestamp": "10:07 AM", "sender": "Bob", "text": "Chill out, I'm rolling it back now.", "emotional_intensity": 65.0, "sentiment_score": -0.2, "emotion": "passive_aggressive"},
            {"id": 5, "timestamp": "10:10 AM", "sender": "Alice", "text": "Great, it is back online. Thanks.", "emotional_intensity": 35.0, "sentiment_score": 0.6, "emotion": "hopeful"}
        ]

        shifts = engine.detect_tone_shifts(mock_messages)
        self.assertGreaterEqual(len(shifts), 1)

        # Trigger detection
        triggers = TriggerDetector.identify_triggers(mock_messages, shifts)
        self.assertGreaterEqual(len(triggers), 1)
        self.assertIn("Alice", [t.sender for t in triggers])

if __name__ == "__main__":
    unittest.main()
