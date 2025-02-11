from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram import F
import sqlite3

from states.states import FSMStates, TopUpStates
from payments.yoo import create_payment
from handlers.admin_handlers import admin_router
from handlers.main_handlers import main_router
from keyboards.keyboards import main_keyboard, back_to_main, crypto_keyboard, back_keyboard, profile_inline_keyboard, product_buy_keyboard, get_admin_keyboard, create_products_keyboard, get_payment_inline_keyboard
from functions.functions import apply_promo_code, get_flag, get_user_balance, update_user_balance
from payments.cryptomus import create_crypto_invoice

router = Router()


router.include_routers(admin_router, main_router)


@router.callback_query(F.data == "top_up")
async def topup_handler(callback: CallbackQuery):
    await callback.message.answer("Выберите способ пополнения:", reply_markup=get_payment_inline_keyboard())
    await callback.answer()

@router.callback_query(F.data == "topup_yoo")
async def topup_yoo(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите сумму пополнения в RUB:")
    await state.set_state(TopUpStates.waiting_for_rub_amount)
    await callback.answer()

@router.message(TopUpStates.waiting_for_rub_amount)
async def process_yoo_amount(message: Message, state: FSMContext):
    try:
        amount_rub = float(message.text)
        if amount_rub < 10:
            await message.answer("Минимальная сумма пополнения — 10 RUB. Введите сумму еще раз.")
            return

        payment_info, amount_usd = create_payment(amount_rub, message.from_user.id)
        payment_url = payment_info["confirmation"]["confirmation_url"]

        await message.answer(
            f"💰 **Пополнение через YooKassa**\n\n💵 Сумма: {amount_rub} RUB (~{amount_usd} USD)\n🔗 [Ссылка для оплаты]({payment_url})", 
            disable_web_page_preview=True
        )
    except ValueError:
        await message.answer("Введите корректную сумму.")
    await state.clear()

@router.callback_query(F.data == "topup_crypto")
async def topup_crypto(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите сумму пополнения в USD:")
    await state.set_state(TopUpStates.waiting_for_crypto_amount)
    await callback.answer()

@router.message(TopUpStates.waiting_for_crypto_amount)
async def process_crypto_amount(message: Message, state: FSMContext):
    try:
        amount_usd = float(message.text)
        if amount_usd < 1:
            await message.answer("Минимальная сумма пополнения — 1 USD. Введите сумму еще раз.")
            return

        await state.update_data(amount_usd=amount_usd)
        await message.answer("Выберите криптовалюту:", reply_markup=crypto_keyboard)
        await state.set_state(TopUpStates.waiting_for_crypto_choice)
    except ValueError:
        await message.answer("Введите корректную сумму.")

@router.callback_query(F.data.startswith("crypto_"))
async def process_crypto_choice(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    amount_usd = user_data.get("amount_usd")
    crypto_currency = callback.data.split("_")[1]

    invoice_url = create_crypto_invoice(amount_usd, crypto_currency, callback.from_user.id)
    if invoice_url:
        await callback.message.answer(f"Оплатите {amount_usd} USD в {crypto_currency} по ссылке: {invoice_url}")
    else:
        await callback.message.answer("Ошибка создания счета.")
    await state.clear()

@router.callback_query(F.data == "back_to_profile")
async def back_to_profile(callback: CallbackQuery):
    balance = get_user_balance(callback.from_user.id)
    text = f"Ваш ID: {callback.from_user.id}\nВаш баланс: {balance:.2f} USD"
    await callback.message.edit_text(text, reply_markup=profile_inline_keyboard)
    await callback.answer()

@router.callback_query(F.data == "back_to_topup")
async def back_to_topup(callback: CallbackQuery):
    await callback.message.edit_text("Выберите метод пополнения:", reply_markup=get_payment_inline_keyboard())
    await callback.answer()



@router.callback_query(F.data == "products_back")
async def products_back(callback: CallbackQuery):
    keyboard = create_products_keyboard(page=0)  # Возвращаемся на первую страницу списка товаров
    await callback.message.edit_text("Выберите товар:", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("page_"))
async def page_navigation(callback_query: CallbackQuery):
    page = int(callback_query.data.split("_")[1])
    keyboard = create_products_keyboard(page)
    await callback_query.message.edit_text("Выберите товар:", reply_markup=keyboard)
    await callback_query.answer()

@router.callback_query(F.data.startswith("product_"))
async def product_details(callback_query: CallbackQuery):
    product_id = int(callback_query.data.split("_")[1])

    conn = sqlite3.connect('vds_shop.db')
    cursor = conn.cursor()

    cursor.execute("SELECT ip, login, password, cores, ram, ssd, geo, price FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()


    if product:
        ip, login, password, cores, ram, ssd, geo, price = product
        product_details = (
            f"Товар #{product_id}:\n"
            f"ОЗУ: {ram}GB\n"
            f"SSD: {ssd}GB\n"
            f"Ядра: {cores}\n"
            f"Гео: {geo}\n"
            f"Цена: {price} $"
        )
        await callback_query.message.edit_text(product_details, reply_markup=product_buy_keyboard(product_id))
        await callback_query.answer()

@router.callback_query(F.data.startswith("buy_"))
async def buy_product(callback_query: CallbackQuery):
    product_id = int(callback_query.data.split("_")[1])
    user_id = callback_query.from_user.id
    
    conn = sqlite3.connect('vds_shop.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT ip, login, password, cores, ram, ssd, geo, price FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    
    if not product:
        await callback_query.message.edit_text("Этот товар уже куплен.")
        return
    
    ip, login, password, cores, ram, ssd, geo, price = product
    
    # Применяем промокод, если он есть
    price = apply_promo_code(user_id, price)
    
    balance = get_user_balance(user_id)
    
    # Проверяем, достаточно ли средств для покупки
    if balance >= price:
        # Если промокод был, он уже изменил цену, списываем правильную сумму
        update_user_balance(user_id, -price)  # Списываем деньги с баланса

        # Сохраняем товар в таблицу `purchases`
        cursor.execute(
            "INSERT INTO purchases (telegram_id, ip, login, password, cores, ram, ssd, geo, price) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, ip, login, password, cores, ram, ssd, geo, price)
        )

        # Удаляем товар из списка доступных товаров
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
        
        flag = get_flag(geo)
        await callback_query.message.edit_text(
            f"✅ <b>Покупка успешна!</b>\n\n"
            f"🔹 <b>GEO</b> {geo, flag}\n"
            f"🔹 <b>IP:</b> {ip}\n"
            f"🔹 <b>Логин:</b> {login}\n"
            f"🔹 <b>Пароль:</b> {password}\n"
            f"🔹 <b>{cores} Ядер | {ram}GB RAM | {ssd}GB SSD</b>**\n"
            f"💰 <b>Цена:</b> {price}$", reply_markup=back_to_main()
        )
    else:
        await callback_query.message.edit_text(
            "❌ **Недостаточно средств.**\nПополните баланс, чтобы купить этот товар.",
            reply_markup=back_to_main()
        )
    
    conn.commit()
    
    await callback_query.answer()




@router.message(FSMStates.waiting_for_promo_code)
async def process_promo(message: Message, state: FSMContext):
    user_id = message.from_user.id
    promo_code = message.text.strip()
    
    conn = sqlite3.connect('vds_shop.db')
    cursor = conn.cursor()
    cursor.execute("SELECT discount, usage_limit FROM promo_codes WHERE code = ?", (promo_code,))
    promo = cursor.fetchone()
    
    if promo:
        discount, usage_limit = promo
        if usage_limit > 0:
            cursor.execute("UPDATE users SET promo_code = ? WHERE telegram_id = ?", (promo_code, user_id))
            conn.commit()
            await message.answer(f"✅ Промокод {promo_code} активирован! Скидка: {discount}%.")
        else:
            await message.answer("❌ Этот промокод уже исчерпан.")
    else:
        await message.answer("❌ Промокод недействителен.")
    await state.clear()



@router.callback_query(F.data == "back_to_main")
async def back_to_main_callback(callback: CallbackQuery):
    await callback.message.answer(
        "Приветсутсвую в VDS Market! Выберите действие:",
        reply_markup=main_keyboard(callback.from_user.id)
    )
    await callback.answer()