from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Config(BaseSettings):
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")
    ADMIN_IDS: str = os.getenv("ADMIN_ID")
    MERCHANT_UUID: str = os.getenv("MERCHANT_UUID")
    API_KEY: str = os.getenv("API_KEY")
    YOOKASSA_SHOP_ID: str = os.getenv("YOOKASSA_SHOP_ID")
    YOOKASSA_SECRET_KEY: str = os.getenv("YOOKASSA_SECRET_KEY")
    @property
    def admin_ids(self):
        return list(map(int, self.ADMIN_IDS.split(',')))

config = Config()
