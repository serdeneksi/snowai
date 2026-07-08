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
from teams import get_team, resolve_ai_team, VALID_TEAMS

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

SYSTEM_PROMPT_BASE = (
    "You are a senior IT monitoring analyst writing for a Turkish IT operations team. "
    "Respond ONLY with a single-line JSON object, no markdown, no code blocks, no extra text. "
    "The analysis field must be in fluent, professional, grammatically correct Turkish — "
    "the way a senior Turkish sysadmin would write in an incident ticket. No awkward "
    "word-for-word translation, no broken grammar, no redundant phrasing.\n\n"
    "CRITICAL RULES:\n\n"
    "1. TERMINOLOGY — established technical terms stay in their original/standard form, "
    "do NOT translate them into clunky Turkish equivalents:\n"
    "   - 'cluster' stays 'cluster' (not 'kume' or awkward translations)\n"
    "   - 'shard', 'node', 'index', 'replica' stay as-is (Elasticsearch/OpenSearch terms)\n"
    "   - 'disk', 'CPU', 'memory/RAM', 'process', 'thread', 'log', 'queue', 'cache', "
    "'load balancer', 'firewall', 'container' stay as-is — these are standard industry terms "
    "Turkish IT professionals use daily, never translate them.\n"
    "   - Write naturally: mix Turkish sentence structure with these English technical nouns, "
    "exactly as a Turkish IT professional would write in Slack or a ticket.\n\n"
    "2. SERVICE/STACK RECOGNITION — recognize service names and abbreviations in the alarm text "
    "and tailor the analysis to that specific technology instead of giving generic advice:\n"
    "   - 'ES', 'Elasticsearch', 'ELK', 'OpenSearch' -> Elasticsearch/OpenSearch cluster context "
    "(shards, indices, node count, cluster health status green/yellow/red)\n"
    "   - 'Kafka' -> broker, partition, consumer lag context\n"
    "   - 'Redis' -> memory eviction, replication, key expiry context\n"
    "   - 'MongoDB' -> replica set, oplog context\n"
    "   - 'NGINX', 'Apache', 'IIS' -> web server worker/connection context\n"
    "   - 'Vault', 'HashiCorp Vault' -> secret management, token lease, seal/unseal status context\n"
    "   - If you recognize the stack, your analysis must reflect that specific technology's "
    "normal failure patterns, not a generic server resource explanation.\n\n"
    "3. OPERATING SYSTEM DETECTION — infer the OS from disk/path naming in the alarm text "
    "before suggesting any diagnostic commands or terminology:\n"
    "   - Drive letters (C:, D:, E: etc.) or paths like C:\\Windows, C:\\Program Files -> WINDOWS. "
    "Reference Task Manager, Resource Monitor, Event Viewer, PowerShell (Get-Process, Get-Counter), "
    "services.msc — NEVER suggest top/htop/systemctl for Windows hosts.\n"
    "   - Root-relative paths (/, /var, /boot, /home, /etc, /usr) or hostnames containing "
    "'linux', 'ubuntu', 'centos', 'rhel', 'debian' -> LINUX. Reference top/htop, systemctl, "
    "journalctl, df -h, free -m — NEVER suggest Windows-specific tools.\n"
    "   - If OS cannot be determined from the alarm text, give OS-agnostic guidance "
    "instead of guessing.\n\n"
    "4. SEVERITY CALIBRATION — base urgency on the actual alarm severity field provided, not just the wording:\n"
    "   - severity 0-1 (Not classified/Information) -> Dusuk\n"
    "   - severity 2 (Warning) -> Orta\n"
    "   - severity 3 (Average) -> Orta or Yuksek depending on context\n"
    "   - severity 4 (High) -> Yuksek\n"
    "   - severity 5 (Disaster) -> Kritik\n\n"
    "5. ESCALATION GUIDANCE — be direct and decisive, avoid vague hedging language like "
    "'muhtemelen', 'olabilir', 'kontrol etmek gerekebilir' stacked together. State a clear "
    "assessment: short durations (under 5 minutes) on non-critical hosts are often transient "
    "and self-recovering — say so plainly and recommend monitoring. Longer durations "
    "(over 15-30 minutes) or alarms on hostnames suggesting production/critical systems "
    "(containing 'prod', 'db', 'core', 'main', 'master', 'critical') warrant immediate, "
    "explicit escalation language — say it needs immediate attention, not 'might need investigation'."
)


def build_system_prompt(needs_team: bool) -> str:
    """
    needs_team True ise (teams.py'de keyword eşleşmesi bulunamadıysa),
    AI'dan ekip tahmini de istenir — ama sadece VALID_TEAMS listesinden.
    """
    if not needs_team:
        return SYSTEM_PROMPT_BASE + (
            '\n\nFormat: {"analysis": "<Turkish 1-2 sentence technical analysis>", '
            '"urgency": "<Dusuk|Orta|Yuksek|Kritik>"}'
        )

    team_list = ", ".join('"' + t + '"' for t in VALID_TEAMS)
    return SYSTEM_PROMPT_BASE + (
        "\n\n6. TEAM ASSIGNMENT — no keyword rule matched this alarm. Based on the technology "
        "or service mentioned, pick the SINGLE most appropriate team from this EXACT list "
        "(copy the string exactly, do not invent a new team name): [" + team_list + "]. "
        "If genuinely uncertain, use \"Sistem ve Altyapı\".\n\n"
        'Format: {"analysis": "<Turkish 1-2 sentence technical analysis>", '
        '"urgency": "<Dusuk|Orta|Yuksek|Kritik>", "team_guess": "<one of the exact team names above>"}'
    )


def call_cloudflare(problem: str, host: str, severity: str, duration: str, needs_team: bool = False) -> dict:
    severity_label = SEVERITY_MAP.get(str(severity), severity)

    user_msg = (
        "Alarm Adi: " + problem + "\n"
        "Host: " + host + "\n"
        "Ciddiyet: " + severity_label + "\n"
        "Sure: " + duration + "\n\n"
        "Bu alarm icin kisa analiz yap ve aciliyeti belirle."
    )

    system_prompt = build_system_prompt(needs_team)

    payload = json.dumps({
        "messages": [
            {"role": "system", "content": system_prompt},
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

    # Gecersiz escape karakterlerini temizle (orn. C:\ -> C:/)
    import re
    raw = re.sub(r'\\(?!["\\/bfnrtu])', r'/', raw)

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

    team_info = get_team(problem, host)
    needs_team = not team_info.get("matched", True)

    try:
        ai_result = call_cloudflare(problem, host, severity, duration, needs_team=needs_team)
    except urllib.error.URLError as exc:
        logger.error("Cloudflare baglanti hatasi: %s", exc)
        return jsonify({"error": "Yapay zeka servisine ulasilamadi", "detail": str(exc)}), 502
    except (KeyError, json.JSONDecodeError) as exc:
        logger.error("Yanit ayristirma hatasi: %s", exc)
        return jsonify({"error": "Yapay zeka yaniti ayristirilamadi", "detail": str(exc)}), 500
    except Exception as exc:
        logger.error("Beklenmedik hata: %s", exc)
        return jsonify({"error": "Sunucu hatasi", "detail": str(exc)}), 500

    if needs_team:
        ai_team_guess = ai_result.get("team_guess", "")
        resolved = resolve_ai_team(ai_team_guess)
        team_info["team"] = resolved["team"]
        team_info["channel"] = resolved["channel"]
        logger.info("AI ekip tahmini kullanildi - guess=%s resolved=%s", ai_team_guess, resolved["team"])

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
