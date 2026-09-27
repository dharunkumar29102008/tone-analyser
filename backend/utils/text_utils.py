import re
from typing import List, Dict, Tuple, Optional

SYSTEM_PATTERNS = [
    r"Messages and calls are end-to-end encrypted",
    r"created group",
    r"added you",
    r"\badded [^:]+ to\b",
    r"\bleft the group\b",
    r"^[^:]+ left$",
    r"\bremoved [^:]+ from the group\b",
    r"changed the group (icon|description|name|subject|settings)",
    r"security code changed",
    r"You're now an admin",
    r"disappearing messages",
    r"This chat is with a business account",
    r"You were added",
    r"pinned a message"
]

# Media omissions
MEDIA_PATTERNS = [
    r"<Media omitted>",
    r"\(file attached\)",
    r"image omitted",
    r"video omitted",
    r"sticker omitted",
    r"audio omitted",
    r"Contact card omitted"
]

# Emoji tone dictionaries
EMOJI_TONES = {
    # Frustration / Anger
    "😡": ("frustration", 0.9, -0.8),
    "😠": ("frustration", 0.85, -0.7),
    "🤬": ("anger", 0.95, -0.9),
    "😒": ("frustration", 0.8, -0.6),
    "😤": ("frustration", 0.75, -0.5),
    "🤦": ("frustration", 0.7, -0.4),
    "🙄": ("passive_aggressive", 0.85, -0.5),
    # Sarcasm / Irony
    "🙃": ("sarcasm", 0.9, -0.2),
    "🤨": ("sarcasm", 0.8, -0.3),
    "😏": ("sarcasm", 0.75, 0.1),
    "🤡": ("sarcasm", 0.85, -0.4),
    "🤭": ("sarcasm", 0.7, 0.2),
    # Calm / Reassurance
    "😌": ("calm", 0.85, 0.4),
    "👌": ("calm", 0.7, 0.5),
    "👍": ("calm", 0.65, 0.5),
    "🤝": ("calm", 0.7, 0.6),
    "☕": ("calm", 0.6, 0.3),
    # Hopeful / Collaborative
    "😇": ("hopeful", 0.85, 0.7),
    "🚀": ("hopeful", 0.9, 0.8),
    "✨": ("hopeful", 0.8, 0.7),
    "💪": ("hopeful", 0.85, 0.75),
    "🎉": ("hopeful", 0.9, 0.9),
    "🙌": ("hopeful", 0.85, 0.8),
    "❤️": ("hopeful", 0.8, 0.8),
    "🔥": ("hopeful", 0.75, 0.6),
    # Joy / Friendly
    "😊": ("joy", 0.8, 0.7),
    "😄": ("joy", 0.85, 0.8),
    "😀": ("joy", 0.8, 0.75),
    "😅": ("calm", 0.65, 0.2),
    "😂": ("joy", 0.85, 0.7),
    "🤣": ("joy", 0.9, 0.75),
    # Sadness / Disappointment
    "😢": ("sadness", 0.85, -0.7),
    "😭": ("sadness", 0.9, -0.8),
    "😞": ("disappointment", 0.8, -0.6),
    "😔": ("disappointment", 0.75, -0.5),
    "🥺": ("disappointment", 0.7, -0.4)
}

# WhatsApp regex patterns
# Matches variants:
# 1) 27/09/26, 10:12 am - Sender: Message
# 2) 27/09/2026, 10:12 - Sender: Message (24h)
# 3) [27/09/26, 10:12:00 AM] Sender: Message (iOS)
# 4) 27.09.26, 10:12 - Sender: Message
# 5) 09/27/26, 10:12 AM - Sender: Message
DATE_TIME_PATTERNS = [
    # 27/09/26, 10:12 am - Sender: Msg (or pm/AM/PM)
    re.compile(
        r"^\[?(\d{1,4}[/\.-]\d{1,2}[/\.-]\d{1,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[apAP]\.?[mM]\.?)?)\]?\s*(?:-\s*)?([^:]+?):\s*(.*)$"
    ),
    # [27/09/2026, 10:12:30] Sender: Msg
    re.compile(
        r"^\[(\d{1,4}[/\.-]\d{1,2}[/\.-]\d{1,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[apAP]\.?[mM]\.?)?)\]\s+([^:]+?):\s*(.*)$"
    )
]

def is_system_message(text: str) -> bool:
    """Check if line is a WhatsApp system event."""
    clean = text.strip()
    for pattern in SYSTEM_PATTERNS:
        if re.search(pattern, clean, re.IGNORECASE):
            return True
    return False

def is_media_omitted(text: str) -> bool:
    """Check if message is an omitted media placeholder."""
    clean = text.strip()
    for pattern in MEDIA_PATTERNS:
        if re.search(pattern, clean, re.IGNORECASE):
            return True
    return False

def extract_emojis(text: str) -> List[str]:
    """Extract emoji characters from text."""
    # Find all characters that belong to emoji ranges or dictionary
    found = []
    for char in text:
        if char in EMOJI_TONES:
            found.append(char)
        elif ord(char) > 0x1F000:
            found.append(char)
    return found

def detect_sarcasm_cues(text: str) -> Tuple[bool, float, List[str]]:
    """Contextual sarcasm markers in text."""
    cues = []
    confidence = 0.0

    # Air quotes around words e.g. "Almost" ah?, "test"
    quotes = re.findall(r'["\']([^"\']{2,15})["\']', text)
    if quotes:
        cues.append(f'Ironic quotation: "{quotes[0]}"')
        confidence += 0.35

    # Question particle with quote or ironic suffix
    if re.search(r'["\'].*["\']\s*(?:ah|huh|\?|right)', text, re.IGNORECASE):
        cues.append("Rhetorical questioning with quote particle")
        confidence += 0.3

    # Ironic particles
    if re.search(r'\b(yeah right|as if|wow so|sure sure|oh really|totally|obviously)\b', text, re.IGNORECASE):
        cues.append("Ironic affirmation / hyperbole")
        confidence += 0.35

    # Sarcastic emojis
    emojis = extract_emojis(text)
    for em in emojis:
        if em in ["🙃", "🤨", "😏", "🤡"]:
            cues.append(f"Sarcastic emoji {em}")
            confidence += 0.3

    # Exclamation + Question combination
    if "!?" in text or "?!" in text:
        cues.append("Incredulous punctuation (!?)")
        confidence += 0.2

    confidence = min(0.95, confidence)
    return confidence >= 0.45, round(confidence, 2), cues

def detect_passive_aggressive_cues(text: str) -> Tuple[bool, float, List[str], Optional[str]]:
    """Detect passive-aggressive and blame-deflection linguistic patterns."""
    cues = []
    score = 0.0
    reason = None

    t_lower = text.strip().lower()

    # Curt one-word dismissals
    if t_lower in ["fine.", "whatever.", "k.", "cool.", "okay then.", "sure.", "do whatever."]:
        cues.append(f"Curt dismissive statement '{text.strip()}'")
        score += 0.75
        reason = "Curt dismissal conveying unexpressed frustration"

    # Defensiveness and blame shifting
    if re.search(r'\b(bro chill|relax|chill out|calm down)\b', t_lower):
        cues.append("Tone policing ('chill/relax')")
        score += 0.45
        reason = "Tone-policing the other speaker rather than addressing the core issue"

    if re.search(r'\b(not my fault|don\'t blame me|acting weird|it\'s not like)\b', t_lower):
        cues.append("Externalizing blame ('not my fault')")
        score += 0.4
        reason = "Defensive externalization of responsibility"

    if re.search(r'\b(you\'re the only one|you always|you never|typical)\b', t_lower):
        cues.append("Absolute generalization ('you always/you\'re the only one')")
        score += 0.5
        reason = "Accusatory generalization directed at recipient"

    # Ellipses with reluctant concession
    if "..." in text and any(w in t_lower for w in ["okay", "sure", "fine", "testing", "yea", "yeah"]):
        cues.append("Reluctant concession with trailing ellipses (...)")
        score += 0.35

    # Passive aggressive emoji
    if "😒" in text or "🙄" in text:
        cues.append("Disdainful emoji (😒/🙄)")
        score += 0.4

    score = min(0.95, score)
    return score >= 0.45, round(score, 2), cues, reason

def detect_code_switching(text: str) -> bool:
    """Identify colloquial code-switching markers (e.g., Hinglish / Tanglish / casual Indian English)."""
    markers = [
        r'\bbro\b', r'\bah\b', r'\bda\b', r'\byaar\b', r'\bseri\b',
        r'\benna\b', r'\bromba\b', r'\bpanra\b', r'\bhustle\b', r'\bjugaad\b'
    ]
    for m in markers:
        if re.search(m, text, re.IGNORECASE):
            return True
    return False
