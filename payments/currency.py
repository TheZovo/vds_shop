import requests

def get_usd_exchange_rate():
    """Получает актуальный курс USD/RUB."""
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/RUB")
        data = response.json()
        return 1 / data["rates"]["USD"]  # RUB → USD
    except Exception as e:
        print(f"Ошибка получения курса валют: {e}")
        return 0.011  # Примерное значение, если API недоступно
