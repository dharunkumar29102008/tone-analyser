import re
from typing import Dict, Tuple
from backend.models.schemas import EmotionResult
from backend.utils.text_utils import (
    extract_emojis,
    detect_sarcasm_cues,
    detect_passive_aggressive_cues,
    EMOJI_TONES
)

EMOTION_KEYWORDS = {
    "frustration": [
        "hours", "still", "only one", "drama", "again", "pull", "test for",
        "why", "annoying", "tired", "deadline", "irritated", "bothered", "ugh",
        "broken", "ci build", "minutes left", "ridiculous", "last minute"
    ],
    "sarcasm": [
        "almost ah", "said it was done", "last night you said", "so responsible",
        "wow great", "sure sure", "as if", "genius", "obviously", "brilliant",
        "definitely win", "great excuse"
    ],
    "calm": [
        "almost", "few bugs", "chill", "testing", "i'll finish", "now",
        "clean", "handled", "passed", "got it", "sure", "no problem", "all good",
        "fixed it", "pushing"
    ],
    "hopeful": [
        "good", "thanks", "win", "hackathon", "slides", "prep", "appreciate",
        "hustle", "let's", "great", "together", "submit", "ready", "looking forward"
    ],
    "passive_aggressive": [
        "bro chill", "not my fault", "acting weird", "fine", "whatever", "okay then",
        "do what you want", "sure do", "if you say so", "proportion", "linter warning",
        "don't blow", "not like you"
    ],
    "neutral": [
        "did you finish", "is it ready", "bro, did you", "deadline is tomorrow", "checking"
    ],
    "anger": [
        "furious", "hate", "rage", "shut up", "mad", "screw"
    ],
    "joy": [
        "haha", "awesome", "celebrate", "congrats", "yay", "fantastic"
    ]
}

class EmotionService:
    """Classifies granular conversational emotions."""

    @staticmethod
    def classify_emotion(text: str, context_prev_tones: list = None) -> EmotionResult:
        text_lower = text.lower()
        scores: Dict[str, float] = {
            "frustration": 0.05,
            "sarcasm": 0.05,
            "calm": 0.1,
            "hopeful": 0.05,
            "passive_aggressive": 0.05,
            "neutral": 0.15,
            "anger": 0.02,
            "joy": 0.05
        }

        # 1. Emoji influences
        emojis = extract_emojis(text)
        for em in emojis:
            if em in EMOJI_TONES:
                category, weight, _ = EMOJI_TONES[em]
                if category in scores:
                    scores[category] += weight * 0.7

        # 2. Linguistic cues
        # Sarcasm check
        is_sarcastic, s_conf, _ = detect_sarcasm_cues(text)
        if is_sarcastic:
            scores["sarcasm"] += s_conf * 0.85

        # Passive aggressive check
        is_pa, pa_score, _, _ = detect_passive_aggressive_cues(text)
        if is_pa:
            scores["passive_aggressive"] += pa_score * 0.85

        # 3. Keyword matching
        for emotion, keywords in EMOTION_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    scores[emotion] += 0.35

        # 4. Context awareness: preceding tension elevates frustration/sarcasm
        if context_prev_tones:
            last_tone = context_prev_tones[-1] if context_prev_tones else None
            if last_tone in ["frustrated", "tense", "sarcastic"]:
                if "chill" in text_lower or "not my fault" in text_lower:
                    scores["passive_aggressive"] += 0.35
                elif "still" in text_lower or "hours" in text_lower:
                    scores["frustration"] += 0.45
            elif last_tone in ["calm", "hopeful"]:
                if any(w in text_lower for w in ["good", "thanks", "clean", "passed", "win", "slides"]):
                    scores["hopeful"] += 0.4

        # Normalize probabilities
        total = sum(scores.values())
        norm_scores = {k: round(v / total, 3) for k, v in scores.items()}

        dominant = max(norm_scores, key=norm_scores.get)
        dominant_score = norm_scores[dominant]

        # If highest score is weak, fall back to neutral
        if dominant_score < 0.22 and not emojis and not is_sarcastic and not is_pa:
            dominant = "neutral"
            dominant_score = 0.55

        return EmotionResult(
            dominant_emotion=dominant,
            emotion_score=round(dominant_score, 2),
            scores=norm_scores
        )
