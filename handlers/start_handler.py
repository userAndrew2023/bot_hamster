from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot import bot
from config import ONE_REF_PRICE, ADMIN_IDS
from db.db import get_orders, add_order, confirm_order

drafts = {}


def clearDraft(telegram_id):
    drafts[telegram_id] = None


def getMarkupForStart():
    inline_markup = InlineKeyboardMarkup()
    inline_markup.row(InlineKeyboardButton('💎 Создать заказ', callback_data='/new_order'))
    inline_markup.row(InlineKeyboardButton('✅ Мои заказы', callback_data='/orders'),
                      InlineKeyboardButton('👉 Меню', callback_data='/menu'))
    return inline_markup


@bot.callback_query_handler(func=lambda call: call.data == '/menu')
def menu(call: CallbackQuery):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    clearDraft(call.from_user.id)
    start(call.message)
    bot.answer_callback_query(call.id)


def format_order(order: dict, new=False, username="Нет"):
    text = (f'#️⃣ Номер заказа: #{order.get("id")}\n'
            'Название: <b>Рефералы для DOGS</b>\n'
            f'Количество: <b>{order.get("count")}</b>\n'
            f'Статус: <b>{order.get("status")}</b>\n'
            f'Цена за одного: <b>{order.get("price") / order.get("count")}₽</b>\n'
            f'Сумма: <b>{order.get("price")}₽</b>\n'
            f'Дополнительно: <b>{order.get("description", "Нет")}</b>\n')
    if new:
        text = (f"<b>НОВЫЙ ЗАКАЗ #{order.get('id')} НА {order.get('price')}!!!₽\n</b>\n"
                f"Покупатель: {username}\n\n") + text
    return text


def getMarkupToConfirm(id: int):
    inline_markup = InlineKeyboardMarkup()
    inline_markup.row(InlineKeyboardButton('✅ Подтвердить', callback_data=f'/confirm:{id}'))
    return inline_markup


@bot.callback_query_handler(func=lambda call: call.data == '/orders')
def orders(call: CallbackQuery):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    clearDraft(call.from_user.id)
    order_list = get_orders(call.from_user.id)

    if len(order_list) == 0:
        bot.send_message(call.from_user.id, "Заказов еще нет")
    else:
        formatted_orders_list = list(map(lambda order: format_order(order), order_list))
        bot.send_message(call.from_user.id, '\n\n'.join(formatted_orders_list), parse_mode="HTML")

    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: '/confirm' in call.data)
def confirm(call: CallbackQuery):
    id = call.data.split(':')[1]
    confirm_order(id)
    bot.send_message(call.from_user.id, "✅ Успешно")

    bot.answer_callback_query(call.id)


def ref_count_handler(message: Message):
    try:
        count = int(message.text)
        if count < 1 or count > 200:
            raise ValueError("Количество должно быть от 1 до 200")
    except ValueError as e:
        bot.send_message(message.chat.id, str(e))
        bot.register_next_step_handler(message, ref_count_handler)
        return

    drafts[message.from_user.id] = {'count': count, 'price': count * ONE_REF_PRICE}

    bot.send_message(message.chat.id, "🔍 Добавьте описание (optional) или нажмите /skip")
    bot.register_next_step_handler(message, ref_description_handler)


def ref_description_handler(message: Message):
    user_id = message.from_user.id
    drafts[user_id]['description'] = message.text if message.text.lower() != "/skip" else "Нет"

    order = add_order(user_id, **drafts[user_id])
    bot.send_message(message.chat.id, "✅ Заказ успешно создан!")
    bot.send_message(message.chat.id, "🧑‍💻 Свяжитесь с менеджером для оплаты: <b>@aircradmin</b>", parse_mode="HTML")
    for i in ADMIN_IDS:
        bot.send_message(i, format_order(order, new=True, username=f'@{message.chat.username}'), parse_mode="HTML", reply_markup=getMarkupToConfirm(user_id))

    bot.clear_step_handler_by_chat_id(message.chat.id)
    del drafts[user_id]


@bot.callback_query_handler(func=lambda call: call.data == '/new_order')
def new_order(call: CallbackQuery):
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    clearDraft(call.from_user.id)
    bot.send_message(call.from_user.id, "🔥 Сколько рефералов хотите приобрести (1-200)")
    bot.register_next_step_handler(call.message, ref_count_handler)
    bot.answer_callback_query(call.id)


@bot.message_handler(commands=['start'])
def start(message: Message):
    text = ("<b>🌟 Главное меню @chip_hamster_refs_bot</b>\n"
            "Один реферал: <b>69 руб</b>")
    with open('images/start.png', 'rb') as file:
        bot.send_photo(message.chat.id, file, caption=text, parse_mode='HTML', reply_markup=getMarkupForStart())
