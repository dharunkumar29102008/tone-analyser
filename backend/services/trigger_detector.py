from typing import List, Dict, Any, Optional
from backend.models.schemas import KeyMomentDetail

class TriggerDetector:
    """Identifies the inciting trigger messages causing emotional shifts in conversation."""

    @staticmethod
    def identify_triggers(
        messages_data: List[Dict[str, Any]],
        shifts: List[Dict[str, Any]]
    ) -> List[KeyMomentDetail]:
        key_moments: List[KeyMomentDetail] = []
        msg_map = {m["id"]: m for m in messages_data}

        for idx, shift in enumerate(shifts):
            target_msg_id = shift["message_id"]
            if target_msg_id not in msg_map:
                continue

            target_msg = msg_map[target_msg_id]
            shift_type = shift["shift_type"]

            # The trigger is typically either the target message itself (if it initiates the tension/recovery)
            # or the immediate preceding message from the counterpart speaker
            prev_msg_id = target_msg_id - 1
            prev_msg = msg_map.get(prev_msg_id)

            if shift_type in ["sarcastic_diversion", "negative_escalation"]:
                # If target message introduces sarcasm or frustration, target message or previous prompt can be trigger
                trigger_msg = target_msg
                title = f"{shift['new_state'].title()} Detected" if shift_type != "sarcastic_diversion" else "Sarcasm Detected"
                conf = 0.82
                reason = (
                    f"A pointed remark ('{trigger_msg['text'][:60]}...') introduced friction, "
                    f"causing the conversation to shift from {shift['previous_state']} to {shift['new_state']}."
                )
            elif shift_type == "passive_aggressive_defensiveness":
                trigger_msg = target_msg
                title = "Passive-Aggressive Detected"
                conf = 0.78
                reason = (
                    f"In response to previous scrutiny, defensive wording ('{trigger_msg['text'][:60]}...') "
                    f"was employed, escalating conversational tension."
                )
            elif shift_type == "de_escalation_recovery":
                trigger_msg = target_msg
                title = "Tone Shift — De-escalation"
                conf = 0.85
                reason = (
                    f"The interaction shifted towards resolution as '{trigger_msg['sender']}' adopted a constructive, "
                    f"cooperative tone, transitioning from {shift['previous_state']} to {shift['new_state']}."
                )
            else:
                trigger_msg = target_msg
                title = f"Tone Shift ({shift['new_state'].title()})"
                conf = 0.74
                reason = (
                    f"Conversation tone moved from {shift['previous_state']} to {shift['new_state']} "
                    f"with a magnitude of {shift['magnitude']}."
                )

            # Before state summary
            before_intensity = prev_msg.get("emotional_intensity", 20.0) if prev_msg else 20.0
            before_emotion = shift["previous_state"].title()

            # After state summary
            after_intensity = target_msg.get("emotional_intensity", 50.0)
            after_emotion = shift["new_state"].title()

            key_moments.append(KeyMomentDetail(
                id=f"km-{idx + 1}",
                title=title,
                trigger_message_id=trigger_msg["id"],
                sender=trigger_msg["sender"],
                quote=trigger_msg["text"],
                timestamp=trigger_msg["timestamp"],
                before_state={
                    "emotion": before_emotion,
                    "intensity": f"{int(before_intensity)}%",
                    "sentiment": prev_msg.get("sentiment", "neutral").title() if prev_msg else "Neutral"
                },
                after_state={
                    "emotion": after_emotion,
                    "intensity": f"{int(after_intensity)}%",
                    "sentiment": target_msg.get("sentiment", "neutral").title()
                },
                cerebro_interpretation=reason,
                confidence=conf,
                shift_type=shift_type
            ))

        return key_moments
