from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class RawMessage(BaseModel):
    id: int
    timestamp: str
    sender: str
    text: str
    raw_date: Optional[str] = None
    is_system: bool = False

class ParsedConversation(BaseModel):
    conversation_id: str
    filename: Optional[str] = "chat.txt"
    participants: List[str]
    messages: List[RawMessage]
    total_messages: int

class SentimentResult(BaseModel):
    sentiment: str  # "positive", "neutral", "negative"
    sentiment_score: float  # -1.0 to 1.0
    confidence: float

class EmotionResult(BaseModel):
    dominant_emotion: str  # "frustration", "sarcasm", "calm", "hopeful", "passive_aggressive", "neutral", "anger", "joy"
    emotion_score: float
    scores: Dict[str, float]

class SarcasmResult(BaseModel):
    sarcasm_detected: bool
    sarcasm_confidence: float
    cues: List[str] = Field(default_factory=list)

class PassiveAggressionResult(BaseModel):
    passive_aggression_detected: bool
    passive_aggression_score: float
    reason: Optional[str] = None
    cues: List[str] = Field(default_factory=list)

class ToneResult(BaseModel):
    tone: str
    confidence: float
    cues: List[str] = Field(default_factory=list)

class AnalyzedMessage(BaseModel):
    id: int
    timestamp: str
    sender: str
    text: str
    sentiment: str
    sentiment_score: float
    emotion: str
    emotion_score: float
    tone: str
    sarcasm_detected: bool
    sarcasm_confidence: float
    passive_aggression_detected: bool
    passive_aggression_score: float
    emotional_intensity: float  # 0 to 100
    escalation_level: float  # 0 to 100
    badge: Dict[str, str]  # {"text": "Sarcasm", "variant": "sarcasm"}
    cues: List[str] = Field(default_factory=list)
    is_trigger: bool = False
    is_shift: bool = False
    shift_note: Optional[str] = None

class DetectedHighlight(BaseModel):
    id: str
    type: str  # "sarcasm", "passive_aggressive", "frustration", "tone_shift", "escalation", "recovery"
    title: str
    quote: str
    timestamp: str
    message_id: int
    sender: str
    emoji: str
    badge_variant: str
    explanation: str

class KeyMomentDetail(BaseModel):
    id: str
    title: str
    trigger_message_id: int
    sender: str
    quote: str
    timestamp: str
    before_state: Dict[str, Any]
    after_state: Dict[str, Any]
    cerebro_interpretation: str
    confidence: float
    shift_type: str

class ParticipantAnalysis(BaseModel):
    name: str
    message_count: int
    avg_intensity: float
    dominant_tone: str
    dominant_emotion: str
    tone_badge_variant: str
    sentiment_ratio: Dict[str, float]

class AnalysisResponse(BaseModel):
    conversation_id: str
    filename: str
    total_messages: int
    participants: List[str]
    overall_sentiment: str
    dominant_emotion: str
    dominant_emotion_percentage: float
    emotional_intensity: float  # 0 - 100 percentage
    escalation_level: str  # "Low", "Moderate", "High", "Severe"
    escalation_score: float  # 0 - 100
    messages: List[AnalyzedMessage]
    emotion_distribution: Dict[str, Dict[str, Any]]  # emotion -> {percentage, count, emoji}
    highlights: List[DetectedHighlight]
    insights: List[str]
    timeline_arc: List[Dict[str, Any]]
    key_moments: List[KeyMomentDetail]
    participants_analysis: List[ParticipantAnalysis]
    ai_powered: bool = False
