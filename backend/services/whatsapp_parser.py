import uuid
import re
from typing import List, Dict, Tuple, Optional
from backend.models.schemas import RawMessage, ParsedConversation
from backend.utils.text_utils import (
    DATE_TIME_PATTERNS,
    is_system_message,
    is_media_omitted
)

class WhatsAppParser:
    """Robust parser for WhatsApp chat exports (.txt)."""

    @staticmethod
    def parse_chat(raw_text: str, filename: str = "chat.txt") -> ParsedConversation:
        lines = raw_text.splitlines()
        messages: List[RawMessage] = []
        participants_set = set()
        msg_id_counter = 1
        current_msg: Optional[Dict] = None

        for line in lines:
            line_str = line.strip("\ufeff\r\n ")  # Strip BOM and whitespace
            if not line_str:
                continue

            matched = False
            for pattern in DATE_TIME_PATTERNS:
                match = pattern.match(line_str)
                if match:
                    raw_date, raw_time, sender_candidate, msg_text = match.groups()
                    sender_clean = sender_candidate.strip()

                    # Check if this matches a system message embedded as sender or text
                    if is_system_message(line_str) or is_system_message(msg_text):
                        matched = True
                        current_msg = None
                        break

                    # Save previous message before starting new one
                    if current_msg is not None:
                        WhatsAppParser._commit_message(current_msg, messages, participants_set, msg_id_counter)
                        msg_id_counter += 1

                    # Format clean timestamp (e.g. "10:12 AM")
                    clean_time = raw_time.strip().upper()
                    # If time does not have AM/PM, keep 24h as is
                    current_msg = {
                        "timestamp": clean_time,
                        "raw_date": raw_date.strip(),
                        "sender": sender_clean,
                        "text": msg_text.strip(),
                        "is_media": is_media_omitted(msg_text)
                    }
                    matched = True
                    break

            if not matched:
                # Could be a multiline message continuation or system line
                if current_msg is not None:
                    # Append newline and continuation line
                    current_msg["text"] += "\n" + line_str
                else:
                    # Line without active message header; check if system
                    pass

        # Commit final message
        if current_msg is not None:
            WhatsAppParser._commit_message(current_msg, messages, participants_set, msg_id_counter)

        # Fallback if no regex matched: Try splitting by colon (for simple mock lines)
        if len(messages) == 0:
            messages, participants_set = WhatsAppParser._fallback_simple_parser(lines)

        return ParsedConversation(
            conversation_id=str(uuid.uuid4())[:8],
            filename=filename,
            participants=sorted(list(participants_set)),
            messages=messages,
            total_messages=len(messages)
        )

    @staticmethod
    def _commit_message(raw_dict: dict, messages: List[RawMessage], participants_set: set, msg_id: int):
        clean_text = raw_dict["text"].strip()
        if not clean_text or is_media_omitted(clean_text):
            return

        sender = raw_dict["sender"]
        participants_set.add(sender)

        messages.append(RawMessage(
            id=msg_id,
            timestamp=raw_dict.get("timestamp", ""),
            sender=sender,
            text=clean_text,
            raw_date=raw_dict.get("raw_date", "")
        ))

    @staticmethod
    def _fallback_simple_parser(lines: List[str]) -> Tuple[List[RawMessage], set]:
        """Fallback for non-standard formats (e.g., 'Alice: Hello')"""
        messages = []
        participants = set()
        msg_id = 1
        for line in lines:
            line = line.strip()
            if not line or is_system_message(line):
                continue
            if ":" in line:
                parts = line.split(":", 1)
                sender = parts[0].strip()
                text = parts[1].strip()
                if sender and text and len(sender) < 30:
                    participants.add(sender)
                    messages.append(RawMessage(
                        id=msg_id,
                        timestamp=f"Step {msg_id}",
                        sender=sender,
                        text=text
                    ))
                    msg_id += 1
        return messages, participants
