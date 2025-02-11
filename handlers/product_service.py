import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

conn = sqlite3.connect("vds_shop.db")
cursor = conn.cursor()

def add_product(ip, login, password, cores, ram, ssd, geo, price):
    try:
        conn = sqlite3.connect("vds_shop.db")
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO products (ip, login, password, cores, ram, ssd, geo, price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (ip, login, password, cores, ram, ssd, geo, price))

        conn.commit()
    except Exception as e:
        logger.error(f"Ошибка при добавлении товара: {e}")
        raise e



def get_products(offset: int, limit: int):
    cursor.execute("SELECT id, cores, ram, ssd, geo, price FROM products LIMIT ? OFFSET ?", (limit, offset))
    products = cursor.fetchall()


    return products

