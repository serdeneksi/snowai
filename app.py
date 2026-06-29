#!/usr/bin/env python3
# SnowAI — Flask Backend (Cloudflare Workers AI)
# /opt/snowai/app.py

import json
import logging
import urllib.request
import urllib.error
from flask import Flask, request, jsonify
from flask_cors import CORS

from config import (
    CLOUDFLARE_API_TOKEN,
    CLOUDFLARE_ACCOUNT_ID,
    CLOUDFLARE_MODEL,
    SNOWAI_HOST,
    SNOWAI_PORT,
    SEVERITY_MAP
)
from teams import get_team

# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("/var/log/snowai.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("snowai")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are an IT monitoring analyst. "
    "Respond ONLY with a single-line JSON object, no markdown, no code blocks, no extra text. "
    'Format: {"analysis": "<Turkish 1-2 sentence technical analysis>", "urgency": "<Dusuk|Orta|Yuksek|Kritik>"} '
    "The analysis field must be in Turkish. Determine urgency based on alarm severity."
)


def call_cloudflare(problem: str, host: str, severity: str, duration: str) -> dict:
    severity_label = SEVERITY_MAP.get(str(severity), severity)

    user_msg = (
        "Alarm Adi: " + problem + "\n"
        "Host: " + host + "\n"
        "Ciddiyet: " + severity_label + "\n"
        "Sure: " + duration + "\n\n"
        "Bu alarm icin kisa analiz yap ve aciliyeti belirle."
    )

    payload = json.dumps({
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg}
        ]
    }).encode("utf-8")

    url = (
        "https://api.cloudflare.com/client/v4/accounts/"
        + CLOUDFLARE_ACCOUNT_ID
        + "/ai/run/"
        + CLOUDFLARE_MODEL
    )

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + CLOUDFLARE_API_TOKEN
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    raw = data["result"]["choices"][0]["message"]["content"].strip()

    # JSON fence temizligi
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    # Sadece JSON kismini al
    start = raw.find("{")
    end   = raw.rfind("}") + 1
    if start != -1 and end > start:
        raw = raw[start:end]

    return json.loads(raw)


# ---------------------------------------------------------------------------
# ROUTES
# ---------------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "snowai"})


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "JSON body bekleniyor"}), 400

    problem  = data.get("problem", "").strip()
    host     = data.get("host", "").strip()
    severity = str(data.get("severity", "0"))
    duration = data.get("duration", "Bilinmiyor")

    if not problem:
        return jsonify({"error": "'problem' alani zorunlu"}), 400

    logger.info("Analiz istegi - host=%s problem=%s severity=%s", host, problem, severity)

    try:
        ai_result = call_cloudflare(problem, host, severity, duration)
    except urllib.error.URLError as exc:
        logger.error("Cloudflare baglanti hatasi: %s", exc)
        return jsonify({"error": "Yapay zeka servisine ulasilamadi", "detail": str(exc)}), 502
    except (KeyError, json.JSONDecodeError) as exc:
        logger.error("Yanit ayristirma hatasi: %s", exc)
        return jsonify({"error": "Yapay zeka yaniti ayristirilamadi", "detail": str(exc)}), 500
    except Exception as exc:
        logger.error("Beklenmedik hata: %s", exc)
        return jsonify({"error": "Sunucu hatasi", "detail": str(exc)}), 500

    team_info = get_team(problem, host)

    response = {
        "analysis":  ai_result.get("analysis", "Analiz alinamadi."),
        "urgency":   ai_result.get("urgency", "Orta"),
        "team":      team_info["team"],
        "channel":   team_info["channel"],
        "action":    team_info["action"],
        "host":      host,
        "problem":   problem,
        "severity":  SEVERITY_MAP.get(severity, severity)
    }

    logger.info("Analiz tamamlandi - team=%s urgency=%s", response["team"], response["urgency"])
    return jsonify(response)


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logger.info("SnowAI baslatiliyor - %s:%s", SNOWAI_HOST, SNOWAI_PORT)
    app.run(host=SNOWAI_HOST, port=SNOWAI_PORT, debug=False)
