import requests
import sqlite3
from config import config

YOOKASSA_URL = "https://api.yookassa.ru/v3/payments/"
CRYPTOMUS_API_URL = "https://api.cryptomus.com/v1/"

# Проверка статуса платежа в YooKassa
def check_yookassa_payment(payment_id, user_id, amount_usd):
    url = f"{YOOKASSA_URL}{payment_id}"
    response = requests.get(url, auth=(config.YOOKASSA_SHOP_ID, config.YOOKASSA_SECRET_KEY))
    data = response.json()
    
    if data.get("status") == "succeeded":
        update_user_balance(user_id, amount_usd)
        return True
    return False

# Проверка статуса платежа в Cryptomus
def check_cryptomus_payment(invoice_id, user_id, amount_usd):
    url = f"{CRYPTOMUS_API_URL}payment"
    headers = {"merchant": config.MERCHANT_UUID, "sign": config.API_KEY}
    data = {"invoice_id": invoice_id}
    
    response = requests.post(url, json=data, headers=headers)
    result = response.json()
    
    if result.get("result") == "success" and result["status"] == "paid":
        update_user_balance(user_id, amount_usd)
        return True
    return False

# Функция обновления баланса пользователя
def update_user_balance(telegram_id, amount):
    conn = sqlite3.connect("vds_shop.db")
    cursor = conn.cursor()
    try:
        with conn:
            cursor.execute("UPDATE users SET balance = balance + ? WHERE telegram_id = ?", (amount, telegram_id))
        conn.commit()
        print(f"Баланс пользователя {telegram_id} пополнен на {amount} USD.")
    except sqlite3.OperationalError as e:
        print(f"Ошибка обновления баланса: {e}")
    finally:
        conn.close()
