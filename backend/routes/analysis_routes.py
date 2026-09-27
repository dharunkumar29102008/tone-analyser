import os
from flask import Blueprint, request, jsonify
from backend.services.pipeline import AnalysisPipeline
from backend.services.whatsapp_parser import WhatsAppParser
from backend.routes.upload_routes import CONVERSATIONS_STORE

analysis_bp = Blueprint("analysis_bp", __name__)

ANALYSIS_CACHE = {}
APP_SETTINGS = {
    "drift_threshold": 0.20,
    "gemini_api_key": os.getenv("GEMINI_API_KEY", "")
}

@analysis_bp.route("/analyze", methods=["POST"])
def analyze_chat():
    data = request.get_json() or {}
    conv_id = data.get("conversation_id")
    raw_text = data.get("text")
    filename = data.get("filename", "chat.txt")

    drift_threshold = float(data.get("drift_threshold", APP_SETTINGS["drift_threshold"]))
    gemini_key = data.get("gemini_api_key") or APP_SETTINGS["gemini_api_key"]

    parsed = None
    if conv_id and conv_id in CONVERSATIONS_STORE:
        parsed = CONVERSATIONS_STORE[conv_id]["parsed"]
    elif raw_text:
        parsed = WhatsAppParser.parse_chat(raw_text, filename=filename)
    else:
        # If neither provided, check if any conversation exists in store or fallback to sample
        if CONVERSATIONS_STORE:
            latest_id = list(CONVERSATIONS_STORE.keys())[-1]
            parsed = CONVERSATIONS_STORE[latest_id]["parsed"]
        else:
            sample_path = os.path.join(os.path.dirname(__file__), "..", "..", "sample_conversation.txt")
            if os.path.exists(sample_path):
                with open(sample_path, "r", encoding="utf-8") as f:
                    raw = f.read()
                parsed = WhatsAppParser.parse_chat(raw, filename="friends_chat.txt")

    if not parsed or parsed.total_messages == 0:
        return jsonify({"success": False, "error": "No conversation found to analyze. Please upload a file first."}), 400

    try:
        pipeline = AnalysisPipeline(
            drift_threshold=drift_threshold,
            window_size=3,
            gemini_key=gemini_key
        )
        result = pipeline.analyze_conversation(parsed)

        # Cache in memory
        ANALYSIS_CACHE[result.conversation_id] = result.dict()

        return jsonify({
            "success": True,
            "data": result.dict()
        })
    except Exception as e:
        return jsonify({"success": False, "error": f"Analysis failed: {str(e)}"}), 500

@analysis_bp.route("/analysis/<conversation_id>", methods=["GET"])
def get_cached_analysis(conversation_id):
    if conversation_id in ANALYSIS_CACHE:
        return jsonify({"success": True, "data": ANALYSIS_CACHE[conversation_id]})
    return jsonify({"success": False, "error": "Analysis not found"}), 404

@analysis_bp.route("/settings", methods=["GET", "POST"])
def manage_settings():
    if request.method == "POST":
        data = request.get_json() or {}
        if "drift_threshold" in data:
            APP_SETTINGS["drift_threshold"] = float(data["drift_threshold"])
        if "gemini_api_key" in data:
            APP_SETTINGS["gemini_api_key"] = data["gemini_api_key"].strip()
            # Also set in env for session
            os.environ["GEMINI_API_KEY"] = APP_SETTINGS["gemini_api_key"]

        return jsonify({
            "success": True,
            "message": "Settings updated successfully",
            "settings": {
                "drift_threshold": APP_SETTINGS["drift_threshold"],
                "has_gemini_key": bool(APP_SETTINGS["gemini_api_key"])
            }
        })

    return jsonify({
        "success": True,
        "settings": {
            "drift_threshold": APP_SETTINGS["drift_threshold"],
            "has_gemini_key": bool(APP_SETTINGS["gemini_api_key"])
        }
    })

@analysis_bp.route("/health", methods=["GET"])
def health_check():
    has_gemini = bool(APP_SETTINGS.get("gemini_api_key") or os.getenv("GEMINI_API_KEY"))
    return jsonify({
        "status": "healthy",
        "service": "CEREBRO Tone Intelligence",
        "gemini_configured": has_gemini,
        "version": "1.0.0"
    })
