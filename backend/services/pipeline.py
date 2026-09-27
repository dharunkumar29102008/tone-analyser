import collections
from typing import Dict, Any, List, Optional
from backend.models.schemas import (
    ParsedConversation,
    AnalyzedMessage,
    DetectedHighlight,
    KeyMomentDetail,
    ParticipantAnalysis,
    AnalysisResponse,
    PassiveAggressionResult
)
from backend.services.whatsapp_parser import WhatsAppParser
from backend.services.sentiment_service import SentimentService
from backend.services.emotion_service import EmotionService
from backend.services.tone_service import ToneService
from backend.services.sarcasm_service import SarcasmService
from backend.services.context_service import ContextService
from backend.services.drift_engine import DriftEngine
from backend.services.trigger_detector import TriggerDetector
from backend.services.gemini_service import GeminiService
from backend.utils.text_utils import detect_passive_aggressive_cues

EMOJI_FOR_EMOTION = {
    "frustration": "😡",
    "sarcasm": "😃",
    "calm": "😌",
    "hopeful": "😇",
    "passive_aggressive": "😒",
    "neutral": "😐",
    "anger": "🤬",
    "joy": "😊",
    "disappointment": "😞",
    "sadness": "😢"
}

class AnalysisPipeline:
    """End-to-end Cerebro conversation analysis pipeline."""

    def __init__(self, drift_threshold: float = 0.25, window_size: int = 3, gemini_key: Optional[str] = None):
        self.drift_engine = DriftEngine(sensitivity_threshold=drift_threshold, window_size=window_size)
        self.gemini_service = GeminiService(api_key=gemini_key)

    def analyze_conversation(self, parsed: ParsedConversation) -> AnalysisResponse:
        analyzed_messages: List[AnalyzedMessage] = []
        raw_dicts_for_drift: List[Dict[str, Any]] = []

        recent_escalation = 10.0
        recent_tones = []

        for msg in parsed.messages:
            # 1. Sentiment
            sentiment = SentimentService.analyze_sentiment(msg.text)

            # 2. Sarcasm
            sarcasm = SarcasmService.analyze_sarcasm(msg.text, prev_context_sentiment=sentiment.sentiment_score)

            # 3. Passive-Aggression
            is_pa, pa_score, pa_cues, pa_reason = detect_passive_aggressive_cues(msg.text)
            pa_result = PassiveAggressionResult(
                passive_aggression_detected=is_pa,
                passive_aggression_score=pa_score,
                reason=pa_reason,
                cues=pa_cues
            )

            # 4. Emotion
            emotion = EmotionService.classify_emotion(msg.text, context_prev_tones=recent_tones)
            recent_tones.append(emotion.dominant_emotion)
            if len(recent_tones) > 5:
                recent_tones.pop(0)

            # 5. Tone & Badge
            tone_res, badge = ToneService.derive_tone(sentiment, emotion, sarcasm, pa_result, msg.text)

            # 6. Contextual Intensity & Escalation
            intensity = ContextService.calculate_emotional_intensity(
                sentiment, emotion, sarcasm, pa_result, msg.text, recent_escalation
            )
            recent_escalation = ContextService.calculate_escalation_level(
                sentiment, emotion, sarcasm, pa_result, recent_escalation
            )

            # Combine all detection cues
            all_cues = list(set(sarcasm.cues + pa_result.cues + tone_res.cues))

            analyzed_msg = AnalyzedMessage(
                id=msg.id,
                timestamp=msg.timestamp,
                sender=msg.sender,
                text=msg.text,
                sentiment=sentiment.sentiment,
                sentiment_score=sentiment.sentiment_score,
                emotion=emotion.dominant_emotion,
                emotion_score=emotion.emotion_score,
                tone=tone_res.tone,
                sarcasm_detected=sarcasm.sarcasm_detected,
                sarcasm_confidence=sarcasm.sarcasm_confidence,
                passive_aggression_detected=pa_result.passive_aggression_detected,
                passive_aggression_score=pa_result.passive_aggression_score,
                emotional_intensity=intensity,
                escalation_level=recent_escalation,
                badge=badge,
                cues=all_cues
            )
            analyzed_messages.append(analyzed_msg)

            raw_dicts_for_drift.append({
                "id": msg.id,
                "timestamp": msg.timestamp,
                "sender": msg.sender,
                "text": msg.text,
                "sentiment": sentiment.sentiment,
                "sentiment_score": sentiment.sentiment_score,
                "emotion": emotion.dominant_emotion,
                "emotional_intensity": intensity,
                "escalation_level": recent_escalation
            })

        # 7. Drift Engine detection
        shifts = self.drift_engine.detect_tone_shifts(raw_dicts_for_drift)

        # 8. Trigger Detection
        key_moments = TriggerDetector.identify_triggers(raw_dicts_for_drift, shifts)

        # Mark trigger and shift flags on analyzed messages
        shift_ids = {s["message_id"]: s for s in shifts}
        trigger_ids = {km.trigger_message_id: km for km in key_moments}

        for am in analyzed_messages:
            if am.id in shift_ids:
                am.is_shift = True
                am.shift_note = shift_ids[am.id]["note"]
            if am.id in trigger_ids:
                am.is_trigger = True

        # 9. Detected Highlights (Matching Reference Card)
        highlights = self._build_highlights(analyzed_messages, shifts)

        # 10. Emotion Distribution
        emotion_dist = self._build_emotion_distribution(analyzed_messages)

        # 11. Conversation Insights (AI Powered / Heuristic)
        insights = self.gemini_service.generate_conversation_insights(
            raw_dicts_for_drift, parsed.participants, shifts
        )

        # 12. Timeline Arc for Chart.js
        timeline_arc = [
            {
                "index": m.id,
                "timestamp": m.timestamp,
                "sender": m.sender,
                "text": m.text,
                "intensity": m.emotional_intensity,
                "escalation": m.escalation_level,
                "sentiment_score": m.sentiment_score,
                "emotion": m.emotion,
                "tone": m.tone,
                "badge": m.badge,
                "is_shift": m.is_shift,
                "is_trigger": m.is_trigger,
                "shift_note": m.shift_note
            }
            for m in analyzed_messages
        ]

        # 13. Participant breakdown
        participant_stats = self._build_participant_stats(analyzed_messages, parsed.participants)

        # Overall summary stats
        avg_intensity = round(sum(m.emotional_intensity for m in analyzed_messages) / max(1, len(analyzed_messages)), 1)
        peak_escalation = max(m.escalation_level for m in analyzed_messages) if analyzed_messages else 0.0

        if peak_escalation > 75:
            esc_level_str = "High"
        elif peak_escalation > 45:
            esc_level_str = "Moderate"
        else:
            esc_level_str = "Low"

        # Dominant emotion overall
        emotion_counts = collections.Counter(m.emotion for m in analyzed_messages)
        dominant_emo, dom_count = emotion_counts.most_common(1)[0] if emotion_counts else ("neutral", 0)
        dom_pct = round((dom_count / max(1, len(analyzed_messages))) * 100, 1)

        # Overall sentiment
        avg_sentiment = sum(m.sentiment_score for m in analyzed_messages) / max(1, len(analyzed_messages))
        if avg_sentiment < -0.15:
            overall_sentiment_str = "Negative Sentiment"
        elif avg_sentiment > 0.15:
            overall_sentiment_str = "Positive Sentiment"
        else:
            overall_sentiment_str = "Neutral Sentiment"

        return AnalysisResponse(
            conversation_id=parsed.conversation_id,
            filename=parsed.filename or "chat.txt",
            total_messages=parsed.total_messages,
            participants=parsed.participants,
            overall_sentiment=overall_sentiment_str,
            dominant_emotion=dominant_emo.title(),
            dominant_emotion_percentage=dom_pct,
            emotional_intensity=avg_intensity,
            escalation_level=esc_level_str,
            escalation_score=round(peak_escalation, 1),
            messages=analyzed_messages,
            emotion_distribution=emotion_dist,
            highlights=highlights,
            insights=insights,
            timeline_arc=timeline_arc,
            key_moments=key_moments,
            participants_analysis=participant_stats,
            ai_powered=self.gemini_service.is_configured()
        )

    def _build_highlights(
        self,
        messages: List[AnalyzedMessage],
        shifts: List[Dict[str, Any]]
    ) -> List[DetectedHighlight]:
        highlights = []
        msg_map = {m.id: m for m in messages}

        # 1. Sarcasm Highlight
        sarcasm_msg = next((m for m in messages if m.sarcasm_detected and m.sarcasm_confidence >= 0.5), None)
        if sarcasm_msg:
            highlights.append(DetectedHighlight(
                id="hl-1",
                type="sarcasm",
                title="Sarcasm Detected",
                quote=f'"{sarcasm_msg.text}"',
                timestamp=sarcasm_msg.timestamp,
                message_id=sarcasm_msg.id,
                sender=sarcasm_msg.sender,
                emoji="😃",
                badge_variant="sarcasm",
                explanation="Ironic quotation and rhetorical punctuation indicate sarcastic undertone."
            ))

        # 2. Passive-Aggressive Highlight
        pa_msg = next((m for m in messages if m.passive_aggression_detected and m.passive_aggression_score >= 0.4), None)
        if pa_msg:
            highlights.append(DetectedHighlight(
                id="hl-2",
                type="passive_aggressive",
                title="Passive-Aggressive Detected",
                quote=f'"{pa_msg.text}"',
                timestamp=pa_msg.timestamp,
                message_id=pa_msg.id,
                sender=pa_msg.sender,
                emoji="😒",
                badge_variant="passive-aggressive",
                explanation="Defensive deflection and tone policing indicate passive aggression."
            ))

        # 3. Frustration Highlight
        frust_msg = next((m for m in messages if m.emotion in ["frustration", "anger"] and m.id != (sarcasm_msg.id if sarcasm_msg else -1)), None)
        if frust_msg:
            highlights.append(DetectedHighlight(
                id="hl-3",
                type="frustration",
                title="Frustration Detected",
                quote=f'"{frust_msg.text}"',
                timestamp=frust_msg.timestamp,
                message_id=frust_msg.id,
                sender=frust_msg.sender,
                emoji="😡",
                badge_variant="frustrated",
                explanation="Accusatory timeline pressure elevated conversational tension."
            ))

        # 4. Tone Shift Highlight (Recovery or Escalation)
        recovery_shift = next((s for s in shifts if s["shift_type"] == "de_escalation_recovery"), None)
        if recovery_shift:
            rec_msg = msg_map.get(recovery_shift["message_id"])
            if rec_msg:
                highlights.append(DetectedHighlight(
                    id="hl-4",
                    type="tone_shift",
                    title="Tone Shift",
                    quote="Tone moves from negative → calm → hopeful towards the end.",
                    timestamp=rec_msg.timestamp,
                    message_id=rec_msg.id,
                    sender=rec_msg.sender,
                    emoji="😇",
                    badge_variant="hopeful",
                    explanation="Participants collaboratively transitioned from tension toward positive resolution."
                ))
        elif shifts:
            first_shift = shifts[0]
            s_msg = msg_map.get(first_shift["message_id"])
            if s_msg:
                highlights.append(DetectedHighlight(
                    id="hl-4",
                    type="tone_shift",
                    title="Tone Shift",
                    quote=f"Tone shifted from {first_shift['previous_state']} to {first_shift['new_state']}.",
                    timestamp=s_msg.timestamp,
                    message_id=s_msg.id,
                    sender=s_msg.sender,
                    emoji="⚡",
                    badge_variant="neutral",
                    explanation=first_shift["note"]
                ))

        # Dynamic fallback: If fewer than 2 highlights, add Peak Intensity & Strongest Emotion
        if len(highlights) < 2 and messages:
            # Peak emotional intensity
            peak_msg = max(messages, key=lambda m: m.emotional_intensity)
            if not any(h.message_id == peak_msg.id for h in highlights):
                emo_emoji = EMOJI_FOR_EMOTION.get(peak_msg.emotion, "🔥")
                highlights.append(DetectedHighlight(
                    id=f"hl-{len(highlights)+1}",
                    type="intensity_peak",
                    title=f"Peak Intensity ({int(peak_msg.emotional_intensity)}%)",
                    quote=f'"{peak_msg.text[:75]}"',
                    timestamp=peak_msg.timestamp,
                    message_id=peak_msg.id,
                    sender=peak_msg.sender,
                    emoji=emo_emoji,
                    badge_variant=peak_msg.badge.get("variant", "neutral"),
                    explanation=f"Conversational intensity peaked at {int(peak_msg.emotional_intensity)}% during this interaction."
                ))

        if len(highlights) < 3 and messages:
            # Significant emotion message
            strong_msg = next((m for m in messages if m.emotion in ["hopeful", "calm", "joy", "frustration", "sarcasm"] and not any(h.message_id == m.id for h in highlights)), None)
            if strong_msg:
                emo_emoji = EMOJI_FOR_EMOTION.get(strong_msg.emotion, "💬")
                highlights.append(DetectedHighlight(
                    id=f"hl-{len(highlights)+1}",
                    type="emotional_anchor",
                    title=f"{strong_msg.emotion.title()} Expression",
                    quote=f'"{strong_msg.text[:75]}"',
                    timestamp=strong_msg.timestamp,
                    message_id=strong_msg.id,
                    sender=strong_msg.sender,
                    emoji=emo_emoji,
                    badge_variant=strong_msg.badge.get("variant", "neutral"),
                    explanation=f"Clear expression of {strong_msg.emotion} influencing conversational sentiment."
                ))

        return highlights

    def _build_emotion_distribution(self, messages: List[AnalyzedMessage]) -> Dict[str, Dict[str, Any]]:
        counts = collections.Counter(m.emotion for m in messages)
        total = max(1, len(messages))

        # Ensure ordered categories matching reference
        ordered_emotions = ["frustration", "sarcasm", "calm", "hopeful", "passive_aggressive", "neutral"]
        dist = {}

        for emo in ordered_emotions:
            c = counts.get(emo, 0)
            pct = round((c / total) * 100)
            emoji = EMOJI_FOR_EMOTION.get(emo, "💬")
            label = "Passive Aggressive" if emo == "passive_aggressive" else emo.title()
            dist[emo] = {
                "name": label,
                "count": c,
                "percentage": pct,
                "emoji": emoji
            }

        # Any extra emotions not in standard list
        for emo, c in counts.items():
            if emo not in dist:
                pct = round((c / total) * 100)
                dist[emo] = {
                    "name": emo.title(),
                    "count": c,
                    "percentage": pct,
                    "emoji": EMOJI_FOR_EMOTION.get(emo, "💬")
                }

        return dist

    def _build_participant_stats(self, messages: List[AnalyzedMessage], participants: List[str]) -> List[ParticipantAnalysis]:
        stats = []
        for p in participants:
            p_msgs = [m for m in messages if m.sender == p]
            if not p_msgs:
                continue

            count = len(p_msgs)
            avg_int = round(sum(m.emotional_intensity for m in p_msgs) / count, 1)

            tone_counts = collections.Counter(m.tone for m in p_msgs)
            dom_tone, _ = tone_counts.most_common(1)[0]

            emo_counts = collections.Counter(m.emotion for m in p_msgs)
            dom_emo, _ = emo_counts.most_common(1)[0]

            badge_var = p_msgs[0].badge["variant"] if p_msgs else "neutral"

            sent_counts = collections.Counter(m.sentiment for m in p_msgs)
            sent_ratio = {
                "positive": round((sent_counts.get("positive", 0) / count) * 100, 1),
                "neutral": round((sent_counts.get("neutral", 0) / count) * 100, 1),
                "negative": round((sent_counts.get("negative", 0) / count) * 100, 1)
            }

            stats.append(ParticipantAnalysis(
                name=p,
                message_count=count,
                avg_intensity=avg_int,
                dominant_tone=dom_tone,
                dominant_emotion=dom_emo.title(),
                tone_badge_variant=badge_var,
                sentiment_ratio=sent_ratio
            ))

        return stats
