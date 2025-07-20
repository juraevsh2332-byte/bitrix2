import os
from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BITRIX_WEBHOOK_URL = os.getenv("BITRIX24_WEBHOOK_URL")

user_sessions = {}

def send_message(chat_id, text):
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    response = requests.post(telegram_url, json=payload)
    response.raise_for_status()

def create_bitrix_task(info):
    task_data = {
        "fields": {
            "TITLE": f"Yangi mijoz: {info['name']}",
            "DESCRIPTION": f"📞 Telefon: {info['phone']}\n🛠 Xizmat: {info['service']}\n🕒 Bog‘lanish vaqti: {info['time']}"
        }
    }
    response = requests.post(BITRIX_WEBHOOK_URL, json=task_data)
    response.raise_for_status()
    return response.json()

@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()

    if not data or "message" not in data:
        return jsonify({"status": "ignored"}), 200

    message = data["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()

    if chat_id not in user_sessions:
        user_sessions[chat_id] = {"step": 1}
        send_message(chat_id, "👋 Salom! Ismingizni kiriting:")
        return jsonify({"status": "waiting_name"}), 200

    session = user_sessions[chat_id]
    step = session["step"]

    try:
        if step == 1:
            session["name"] = text
            session["step"] = 2
            send_message(chat_id, "📞 Endi telefon raqamingizni kiriting:")
        elif step == 2:
            session["phone"] = text
            session["step"] = 3
            send_message(chat_id, "💼 Qaysi xizmatimizga qiziqasiz?")
        elif step == 3:
            session["service"] = text
            session["step"] = 4
            send_message(chat_id, "🕒 Siz bilan qachon bog'lansak bo'ladi?")
        elif step == 4:
            session["time"] = text
            create_bitrix_task(session)
            send_message(chat_id, "✅ Ma'lumot yuborildi! Tez orada siz bilan bog'lanamiz.")
            user_sessions.pop(chat_id)
    except Exception as e:
        send_message(chat_id, f"❌ Xatolik yuz berdi: {str(e)}")
        user_sessions.pop(chat_id, None)

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
