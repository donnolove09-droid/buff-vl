import os
import re
import json
import asyncio
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify
import pytz

from services import buff_all, DEFAULT_REGION

app = Flask(__name__)

LIKE_TRACKING_FILE = os.environ.get("LIKE_TRACKING_FILE", "like_tracking.json")
RESET_HOUR, RESET_MINUTE = 4, 30
IST = pytz.timezone("Asia/Kolkata")


# ---------- Like quota (1 lần/ngày/IP) ----------
def _load():
    if not os.path.exists(LIKE_TRACKING_FILE):
        return {}
    try:
        with open(LIKE_TRACKING_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def _save(d):
    with open(LIKE_TRACKING_FILE, "w") as f:
        json.dump(d, f)


def _next_reset():
    now = datetime.now(IST)
    r = now.replace(hour=RESET_HOUR, minute=RESET_MINUTE, second=0, microsecond=0)
    return r + timedelta(days=1) if now >= r else r


def can_like(key):
    last = _load().get(key)
    if not last:
        return True
    try:
        return datetime.fromisoformat(last) < _next_reset()
    except Exception:
        return True


def mark_like(key):
    d = _load()
    d[key] = datetime.now(IST).isoformat()
    _save(d)


# ---------- Routes ----------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/buff", methods=["POST"])
def api_buff():
    data = request.get_json(silent=True) or {}
    uid = (data.get("uid") or "").strip()

    if not re.fullmatch(r"\d{6,15}", uid):
        return jsonify({"ok": False, "error": "UID không hợp lệ (6-15 chữ số)"}), 400

    client = (request.headers.get("X-Forwarded-For", request.remote_addr) or "").split(",")[0].strip()

    try:
        result = asyncio.run(buff_all(DEFAULT_REGION, uid))

        # Ghi quota like nếu like thành công
        like_res = next((r for r in result["results"] if r["name"] == "LIKE"), None)
        if like_res and like_res["ok"]:
            mark_like(client)

        result["ok"] = True
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
