from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import config
from handlers.product_service import get_products
from functions.functions import get_flag

# Главная клавиатура
def main_keyboard(user_id):
    buttons = [
            [KeyboardButton(text="📜 Товары")],
            [
                KeyboardButton(text="Промокод"),
                KeyboardButton(text="Профиль"),
                KeyboardButton(text="Информация")
            ],
            [
                KeyboardButton(text="Мои VDS"),]
            ]
    resize_keyboard=True
    
    # отображение Админ-панели только у админов
    if user_id in config.admin_ids:
        buttons.append([KeyboardButton(text="🔧 Админ-панель")])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# Инлайн клавиатура для профиля (Пополнение баланса, Промокод, Тех. поддержка)
profile_inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="top_up")]
])

# Админ клавиатура
def get_admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💳 Изменить баланс пользователя")],
            [
                KeyboardButton(text="🛠 Добавить товар"),
                KeyboardButton(text="📝 Список товаров"),
                KeyboardButton(text="🛠 Удалить товар")
            ],
            [
                KeyboardButton(text="➕ Добавить промокод"),
                KeyboardButton(text="Рассылка")
                
                ],
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )


# Список товаров

ITEMS_PER_PAGE = 7

def create_products_keyboard(page: int):
    offset = page * ITEMS_PER_PAGE
    products = get_products(offset, ITEMS_PER_PAGE)

    inline_keyboard = []
    
    for product in products:
        product_id, cores, ram, ssd, geo, price = product
        flag = get_flag(geo)
        product_info = f"{flag} {cores} Ядер | {ram} Гб ОЗУ | {ssd} Гб SSD | {price}$"
        button = InlineKeyboardButton(text=product_info, callback_data=f"product_{product_id}")
        inline_keyboard.append([button])
    
    navigation_buttons = []

    if len(products) == ITEMS_PER_PAGE:
        navigation_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"page_{page + 1}"))

    if page > 0:
        navigation_buttons.insert(0, InlineKeyboardButton(text="◀️", callback_data=f"page_{page - 1}"))

    if navigation_buttons:
        inline_keyboard.append(navigation_buttons)
    

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def product_buy_keyboard(product_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Купить", callback_data=f"buy_{product_id}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="products_back")]
        ]
    )



def get_payment_inline_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Юкасса", callback_data="topup_yoo")],
            [InlineKeyboardButton(text="₿ Криптовалюта", callback_data="topup_crypto")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_profile")]
        ]
    )

back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_topup")]
])

def back_to_main() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
        ]
    )



crypto_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="BTC", callback_data="crypto_BTC")],
    [InlineKeyboardButton(text="USDT TRC20", callback_data="crypto_USDT_TRC20")],
    [InlineKeyboardButton(text="ETH", callback_data="crypto_ETH")],
    [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_topup")]
])
