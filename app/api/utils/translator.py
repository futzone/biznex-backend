from googletrans import Translator
import json
import asyncio


async def translate_text(text, src_lang="auto"):
    translator = Translator()
    translations = {
        "uz": text,
        "en": text,
        "ru": text,
    }
    return translations
