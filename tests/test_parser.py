import unittest
from backend.services.whatsapp_parser import WhatsAppParser

SAMPLE_CHAT_12H = """27/09/26, 10:12 am - Dharun: Bro, did you finish the project? The deadline is tomorrow 😅
27/09/26, 10:15 am - Aravind: Yea... almost. Just need to fix a few bugs.
27/09/26, 10:18 am - Dharun: "Almost" ah? 🤨 Last night you said it was done!"""

SAMPLE_CHAT_24H_MULTILINE = """27/09/2026, 22:12 - Alice: Hey Bob,
did you check the report?
Here is the second line.
27/09/2026, 22:15 - Bob: Yes Alice.
Messages and calls are end-to-end encrypted.
27/09/2026, 22:18 - Alice: Cool!"""

class TestWhatsAppParser(unittest.TestCase):
    def test_parse_12h(self):
        parsed = WhatsAppParser.parse_chat(SAMPLE_CHAT_12H, "sample.txt")
        self.assertEqual(parsed.total_messages, 3)
        self.assertIn("Dharun", parsed.participants)
        self.assertIn("Aravind", parsed.participants)
        self.assertEqual(parsed.messages[0].sender, "Dharun")
        self.assertTrue("deadline is tomorrow" in parsed.messages[0].text)

    def test_parse_24h_multiline_system(self):
        parsed = WhatsAppParser.parse_chat(SAMPLE_CHAT_24H_MULTILINE, "chat2.txt")
        # System message filtered out
        self.assertGreaterEqual(parsed.total_messages, 2)
        # Check multiline
        self.assertTrue("second line" in parsed.messages[0].text)

if __name__ == "__main__":
    unittest.main()
