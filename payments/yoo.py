import uuid
import requests
from config import config
from payments.currency import get_usd_exchange_rate

YOOKASSA_URL = "https://api.yookassa.ru/v3/payments"

def create_payment(amount_rub, user_id):
    """Создает платеж через YooKassa и конвертирует сумму в USD."""
    usd_rate = get_usd_exchange_rate()
    amount_usd = round(amount_rub * usd_rate, 2)

    payment_id = str(uuid.uuid4())
    headers = {"Content-Type": "application/json"}
    data = {
        "amount": {"value": f"{amount_rub:.2f}", "currency": "RUB"},
        "confirmation": {"type": "redirect", "return_url": "https://t.me/your_bot"},
        "capture": True,
        "description": f"Пополнение баланса на {amount_usd} USD (по курсу {usd_rate:.4f})"
    }

    response = requests.post(YOOKASSA_URL, json=data, headers=headers, auth=(config.YOOKASSA_SHOP_ID, config.YOOKASSA_SECRET_KEY))
    return response.json(), amount_usd