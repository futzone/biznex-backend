import html
import os
import subprocess
import requests
from datetime import datetime
from app.api.schemas.user import SendFormticket
from app.core.settings import get_settings

settings = get_settings()

token = settings.FORM_TELEGRAM_BOT_TOKEN

def send_form(data: SendFormticket):
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    # HTML teglarni oddiy tekstga o'girish
    safe_name = html.escape(data.name) if data.name else 'Kiritilmagan'
    safe_email = html.escape(data.email) if data.email else 'Kiritilmagan'
    safe_message = html.escape(data.message) if data.message else 'Kiritilmagan'

    message_text = (
        "📋 YANGI MUROJAAT 📋\n\n"
        f"👤 <b>Ism:</b> {safe_name}\n"
        f"📧 <b>Email:</b> {safe_email}\n"
        f"💬 <b>Xabar:</b>\n{safe_message}\n\n"
        f"⏱️ <b>Vaqt:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"🔔 <b>Status:</b> Yangi"
    )
    
    chat_id = settings.FORM_TELEGRAM_CHANNEL_ID
    params = {
        'chat_id': chat_id,
        'text': message_text,
        'parse_mode': 'HTML'
    }

    response = requests.post(url, json=params)
    
    return response.json()