import requests
import uuid
from config import config
import hmac
import hashlib
from flask import Flask, request, jsonify
import sqlite3

CRYPTOMUS_API_URL = "https://api.cryptomus.com/v1/"

HEADERS = {
    "Content-Type": "application/json",
    "merchant": config.MERCHANT_UUID,
    "sign": config.API_KEY
}

def get_crypto_rates():
    """Получает курс криптовалют по отношению к USD из Cryptomus."""
    url = CRYPTOMUS_API_URL + "rates"
    response = requests.get(url, headers=HEADERS)
    data = response.json()

    if data.get("result") == "success":
        return {
            "BTC": float(data["rates"]["BTC"]["USD"]),
            "USDT_TRC20": float(data["rates"]["USDT_TRC20"]["USD"]),
            "ETH": float(data["rates"]["ETH"]["USD"])
        }
    else:
        print("Ошибка получения курсов Cryptomus:", data)
        return None

def create_crypto_invoice(amount_usd, currency, user_id):
    """Создает инвойс на оплату в криптовалюте."""
    url = CRYPTOMUS_API_URL + "invoice"
    data = {
        "amount": amount_usd,
        "currency": "USD",
        "pay_currency": currency,
        "order_id": str(uuid.uuid4()),
        "lifetime": 3600,  # Время жизни счета (1 час)
        "url_return": "https://t.me/dedik_market_bot",
        "custom_fields": {"telegram_id": user_id}
    }

    response = requests.post(url, json=data, headers=HEADERS)
    data = response.json()

    if data.get("result") == "success":
        return data["url"]
    else:
        print("Ошибка создания инвойса:", data)
        return None

app = Flask(__name__)

def verify_signature(data, signature):
    """Проверяет подпись webhook-а от Cryptomus."""
    sorted_data = sorted(data.items())
    sign_data = ":".join(str(value) for _, value in sorted_data)
    generated_signature = hmac.new(
        config.CRYPTOMUS_API_KEY.encode(),
        sign_data.encode(),
        hashlib.sha256
    ).hexdigest()
    return generated_signature == signature

@app.route("/cryptomus_webhook", methods=["POST"])
def cryptomus_webhook():
    """Обработчик уведомлений от Cryptomus."""
    data = request.json
    signature = request.headers.get("Sign")

    if not verify_signature(data, signature):
        return jsonify({"status": "error", "message": "Invalid signature"}), 403

    if data["status"] == "paid":
        user_id = data["custom_fields"]["telegram_id"]
        amount_usd = float(data["amount"])

        conn = sqlite3.connect("vds_shop.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = balance + ? WHERE telegram_id = ?", (amount_usd, user_id))
        conn.commit()

        return jsonify({"status": "success"})

    return jsonify({"status": "error", "message": "Payment not completed"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)