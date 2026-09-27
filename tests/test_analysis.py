import sys
import unittest
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from backend.services.whatsapp_parser import WhatsAppParser
from backend.services.pipeline import AnalysisPipeline

class TestAnalysisPipeline(unittest.TestCase):
    def test_full_pipeline_sample(self):
        with open("sample_conversation.txt", "r", encoding="utf-8") as f:
            raw = f.read()

        parsed = WhatsAppParser.parse_chat(raw, "friends_chat.txt")
        self.assertEqual(parsed.total_messages, 12)

        pipeline = AnalysisPipeline(drift_threshold=0.20)
        res = pipeline.analyze_conversation(parsed)

        self.assertEqual(res.total_messages, 12)
        self.assertGreaterEqual(len(res.highlights), 3)
        self.assertGreaterEqual(len(res.key_moments), 1)
        self.assertGreaterEqual(len(res.insights), 2)
        self.assertIn("Aravind", res.participants)
        self.assertIn("Dharun", res.participants)

        # Print breakdown for audit
        print("\n--- Pipeline Summary ---")
        print(f"Overall Sentiment: {res.overall_sentiment}")
        print(f"Dominant Emotion: {res.dominant_emotion}")
        print(f"Avg Intensity: {res.emotional_intensity}%")
        print(f"Escalation Level: {res.escalation_level}")
        print("Emotion Distribution:")
        for k, v in res.emotion_distribution.items():
            print(f"  {v['emoji']} {v['name']}: {v['percentage']}% ({v['count']})")
        print("\nHighlights:")
        for h in res.highlights:
            print(f"  {h.emoji} {h.title}: {h.quote}")
        print("\nKey Moments:")
        for km in res.key_moments:
            print(f"  ⚡ {km.title} by {km.sender} at {km.timestamp}: {km.quote}")
            print(f"     Before: {km.before_state} -> After: {km.after_state}")
            print(f"     Reason: {km.cerebro_interpretation}")

if __name__ == "__main__":
    unittest.main()
