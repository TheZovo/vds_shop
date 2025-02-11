import sqlite3
import uuid
import requests

import config
from payments.currency import get_usd_exchange_rate
def create_db():
    conn = sqlite3.connect("vds_shop.db")
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            balance REAL DEFAULT 0,
            promo_code TEXT DEFAULT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT,
            login TEXT,
            password TEXT,
            cores INTEGER,
            ram INTEGER,
            ssd INTEGER,
            geo TEXT,  -- добавлено поле geo
            price REAL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            ip TEXT,
            login TEXT,
            password TEXT,
            cores INTEGER,
            ram INTEGER,
            ssd INTEGER,
            geo TEXT,
            price REAL,
            purchase_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS promo_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            discount REAL,
            usage_limit INTEGER
        )
    ''')

    # Проверяем, есть ли уже поле `geo`, если нет — добавляем
    cursor.execute("PRAGMA table_info(products)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if "geo" not in columns:
        cursor.execute("ALTER TABLE products ADD COLUMN geo TEXT DEFAULT 'N/A'")  # Добавляем geo, если его нет
    conn.commit()






def create_user(telegram_id):
    conn = sqlite3.connect('vds_shop.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id FROM users WHERE telegram_id = ?
    ''', (telegram_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute('''
            INSERT INTO users (telegram_id, balance) VALUES (?, 0)
        ''', (telegram_id,))
        conn.commit()




def get_user(telegram_id):
    conn = sqlite3.connect('vds_shop.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT telegram_id, balance FROM users WHERE telegram_id = ?
    ''', (telegram_id,))
    user = cursor.fetchone()


    if user:
        return {"telegram_id": user[0], "balance": user[1]}
    return None


def get_user_balance(telegram_id):
    conn = sqlite3.connect("vds_shop.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE telegram_id = ?", (telegram_id,))
    result = cursor.fetchone()
    print(f"Текущий баланс пользователя {telegram_id}: {result[0]}")
    return result[0] if result else 0

def update_user_balance(telegram_id, amount):
    conn = sqlite3.connect("vds_shop.db")
    cursor = conn.cursor()
    
    try:
        with conn:
            cursor.execute("UPDATE users SET balance = balance + ? WHERE telegram_id = ?", (amount, telegram_id))
        conn.commit()
        print(f"Баланс пользователя {telegram_id} обновлен на {amount}.")
    except sqlite3.OperationalError as e:
        print(f"Ошибка при обновлении баланса: {e}")
    finally:
        conn.close()





COUNTRY_FLAGS = {
    "US": "🇺🇸", "RU": "🇷🇺", "DE": "🇩🇪", "FR": "🇫🇷",
    "GB": "🇬🇧", "NL": "🇳🇱", "CA": "🇨🇦", "AU": "🇦🇺",
    "IT": "🇮🇹", "ES": "🇪🇸", "PL": "🇵🇱", "BR": "🇧🇷",
    "IN": "🇮🇳", "JP": "🇯🇵", "CN": "🇨🇳", "KR": "🇰🇷",
    "MX": "🇲🇽", "AR": "🇦🇷", "ZA": "🇿🇦", "NG": "🇳🇬",
    "EG": "🇪🇬", "TR": "🇹🇷", "SA": "🇸🇦", "AE": "🇦🇪",
    "ID": "🇮🇩", "TH": "🇹🇭", "PH": "🇵🇭", "SG": "🇸🇬",
    "NZ": "🇳🇿", "FI": "🇫🇮", "SE": "🇸🇪", "NO": "🇳🇴",
    "DK": "🇩🇰", "CH": "🇨🇭", "BE": "🇧🇪", "AT": "🇦🇹",
    "PL": "🇵🇱", "PT": "🇵🇹", "GR": "🇬🇷", "CZ": "🇨🇿",
    "RO": "🇷🇴", "HU": "🇭🇺", "SK": "🇸🇰", "BG": "🇧🇬",
    "UA": "🇺🇦", "KR": "🇰🇷", "MY": "🇲🇾", "VN": "🇻🇳",
    "KW": "🇰🇼", "QA": "🇶🇦", "OM": "🇴🇲", "KW": "🇰🇼",
    "IE": "🇮🇪", "IS": "🇮🇸", "LK": "🇱🇰", "MD": "🇲🇩"
}


def get_flag(geo):
    return COUNTRY_FLAGS.get(geo, "🏳️")


def get_user_purchase_count(user_id: int) -> int:
    conn = sqlite3.connect("vds_shop.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM purchases WHERE telegram_id = ?", (user_id,))
    count = cursor.fetchone()[0]


    return count


def apply_discount(user_id, price):
    conn = sqlite3.connect("vds_shop.db")
    cursor = conn.cursor()
    cursor.execute("SELECT promo_code FROM users WHERE telegram_id = ?", (user_id,))
    promo_code = cursor.fetchone()
    
    if promo_code and promo_code[0]:
        cursor.execute("SELECT discount FROM promo_codes WHERE code = ?", (promo_code[0],))
        discount = cursor.fetchone()
        if discount:
            price *= (1 - discount[0] / 100)
    
    return round(price, 2)

def apply_promo_code(user_id, price):
    conn = sqlite3.connect('vds_shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT promo_code FROM users WHERE telegram_id = ?", (user_id,))
    promo_code = cursor.fetchone()
    
    if promo_code and promo_code[0]:
        cursor.execute("SELECT discount, usage_limit FROM promo_codes WHERE code = ?", (promo_code[0],))
        promo = cursor.fetchone()
        if promo:
            discount, usage_limit = promo
            new_price = price - (price * discount / 100)
            
            # Уменьшаем количество оставшихся использований
            cursor.execute("UPDATE promo_codes SET usage_limit = usage_limit - 1 WHERE code = ?", (promo_code[0],))
            
            # Если лимит исчерпан, удаляем промокод
            if usage_limit - 1 <= 0:
                cursor.execute("DELETE FROM promo_codes WHERE code = ?", (promo_code[0],))
            
            # Удаляем промокод у пользователя после использования
            cursor.execute("UPDATE users SET promo_code = NULL WHERE telegram_id = ?", (user_id,))
            
            conn.commit()
            print(f"Применен промокод: {promo_code[0]}, новая цена: {new_price}")
            return new_price
    print(f"Промокод не найден или не применим. Цена остается без изменений: {price}")
    return price



def create_payment(amount_rub, user_id):
    usd_rate = get_usd_exchange_rate()
    amount_usd = round(amount_rub * usd_rate, 2)
    
    data = {
        "amount": {"value": f"{amount_rub:.2f}", "currency": "RUB"},
        "confirmation": {"type": "redirect", "return_url": "https://t.me/your_bot"},
        "capture": True,
        "description": f"Пополнение баланса на {amount_usd} USD"
    }
    
    response = requests.post(
        "https://api.yookassa.ru/v3/payments", json=data,
        auth=(config.YOOKASSA_SHOP_ID, config.YOOKASSA_SECRET_KEY)
    )
    return response.json(), amount_usd

def create_crypto_invoice(amount_usd, currency, user_id):
    data = {
        "amount": amount_usd,
        "currency": "USD",
        "pay_currency": currency,
        "order_id": str(uuid.uuid4()),
        "custom_fields": {"telegram_id": user_id}
    }
    response = requests.post("https://api.cryptomus.com/v1/invoice", json=data, headers={
        "merchant": config.MERCHANT_UUID,
        "sign": config.API_KEY
    })
    return response.json().get("url")
