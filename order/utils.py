import requests
from django.conf import settings


def send_telegram_notification(order):
    """
    Telegram bot orqali faqat kafe egasiga o'zbekcha chek yuborish funksiyasi
    """
    # 📝 TO'G'RILANDI: Token va Chat ID-ni to'g'ridan-to'g'ri o'zgaruvchiga yozamiz
    bot_token = "8738213235:AAFsISWCvK27DpkXP8aOCKf56Uaj6yTZspI"
    chat_id = "8738213235"  #  Diqqat: Bu yerda kafe egasining shaxsiy Telegram ID si bo'lishi shart!

    if not bot_token or not chat_id:
        print("Telegram Bot Token yoki Chat ID sozlanmagan!")
        return False

    # 1. Sana va vaqtni formatlaymiz
    sana_str = order.created_at.strftime('%d.%m.%Y %H:%M:%S')
    sotuvchi = order.assigned_waiter.name if order.assigned_waiter else "Noma'lum"

    # 2. Xabarni o'zbekcha formatda yig'amiz (Xuddi rasmdagidek)
    text = f"🛍 <b>Sotuv #{order.id}</b>\n"
    text += f"📅 {sana_str}\n\n"
    text += f"👤 <b>Sotuvchi:</b> {sotuvchi}\n"
    text += f"💰 <b>Tranzaksiya summasi:</b> {order.total_amount:,.0f} UZS\n"
    text += f"📦 <b>Mahsulotlar soni:</b> {order.items.count()} ta\n\n"
    text += "🛒 <b>Tovarlar:</b>\n"


    for index, item in enumerate(order.items.all(), 1):
        nomi = item.product.name if item.product else "Noma'lum mahsulot"
        artikul = getattr(item.product, 'artikul', '—')
        item_total = item.qty * item.unit_price

        text += f"{index}. {nomi} / Art: {artikul} / <b>{item.qty} dona</b> x {item.unit_price:,.0f} UZS\n"
        text += f"   (Jami: {item_total:,.0f} UZS)\n"

    text += "\n✅ Qabul qilindi."

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"Telegramga xabar yuborishda xatolik: {e}")
        return False