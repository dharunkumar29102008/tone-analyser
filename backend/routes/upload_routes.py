import os
from flask import Blueprint, request, jsonify
from backend.services.whatsapp_parser import WhatsAppParser

upload_bp = Blueprint("upload_bp", __name__)

# In-memory store for session conversations
CONVERSATIONS_STORE = {}

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

@upload_bp.route("/upload", methods=["POST"])
def upload_chat_file():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file part in the request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected"}), 400

    if not file.filename.lower().endswith(".txt"):
        return jsonify({"success": False, "error": "Only WhatsApp export .txt files are supported"}), 400

    try:
        content_bytes = file.read()
        if len(content_bytes) > MAX_FILE_SIZE:
            return jsonify({"success": False, "error": "File size exceeds 5MB limit"}), 400

        # Try UTF-8 then fallback to latin-1
        try:
            content_str = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            content_str = content_bytes.decode("latin-1", errors="replace")

        parsed = WhatsAppParser.parse_chat(content_str, filename=file.filename)

        if parsed.total_messages == 0:
            return jsonify({
                "success": False,
                "error": "No valid conversation messages could be parsed. Please check if this is an exported WhatsApp .txt file."
            }), 400

        # Cache in memory
        CONVERSATIONS_STORE[parsed.conversation_id] = {
            "parsed": parsed,
            "raw_text": content_str,
            "filename": file.filename
        }

        # Return preview (first 8 messages)
        preview_messages = [
            {
                "id": m.id,
                "timestamp": m.timestamp,
                "sender": m.sender,
                "text": m.text
            }
            for m in parsed.messages[:8]
        ]

        return jsonify({
            "success": True,
            "conversation_id": parsed.conversation_id,
            "filename": parsed.filename,
            "total_messages": parsed.total_messages,
            "participants": parsed.participants,
            "preview": preview_messages
        })

    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to process file: {str(e)}"}), 500

@upload_bp.route("/upload/raw", methods=["POST"])
def upload_raw_text():
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    filename = data.get("filename", "pasted_chat.txt")

    if not text:
        return jsonify({"success": False, "error": "Text payload cannot be empty"}), 400

    try:
        parsed = WhatsAppParser.parse_chat(text, filename=filename)
        if parsed.total_messages == 0:
            return jsonify({"success": False, "error": "No conversation messages found"}), 400

        CONVERSATIONS_STORE[parsed.conversation_id] = {
            "parsed": parsed,
            "raw_text": text,
            "filename": filename
        }

        return jsonify({
            "success": True,
            "conversation_id": parsed.conversation_id,
            "filename": parsed.filename,
            "total_messages": parsed.total_messages,
            "participants": parsed.participants,
            "preview": [{"id": m.id, "timestamp": m.timestamp, "sender": m.sender, "text": m.text} for m in parsed.messages[:8]]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@upload_bp.route("/sample", methods=["GET"])
def get_sample_chat():
    """Load built-in synthetic friends_chat.txt for 1-click test."""
    try:
        sample_path = os.path.join(os.path.dirname(__file__), "..", "..", "sample_conversation.txt")
        with open(sample_path, "r", encoding="utf-8") as f:
            raw = f.read()

        parsed = WhatsAppParser.parse_chat(raw, filename="friends_chat.txt")
        CONVERSATIONS_STORE[parsed.conversation_id] = {
            "parsed": parsed,
            "raw_text": raw,
            "filename": "friends_chat.txt"
        }

        return jsonify({
            "success": True,
            "conversation_id": parsed.conversation_id,
            "filename": "friends_chat.txt",
            "total_messages": parsed.total_messages,
            "participants": parsed.participants,
            "preview": [{"id": m.id, "timestamp": m.timestamp, "sender": m.sender, "text": m.text} for m in parsed.messages[:8]]
        })
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to load sample: {str(e)}"}), 500
