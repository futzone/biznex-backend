from typing import Optional

from pydantic import BaseModel
from PIL import Image, ImageDraw, ImageFont
import barcode
from barcode.writer import ImageWriter
from io import BytesIO


class ReceiptStyle(BaseModel):
    shop_name_font_size: Optional[int] | None = 24
    product_name_font_size: Optional[int] | None = 24
    price_font_size: Optional[int] | None = 24
    barcode_height: Optional[int] | None = 80
    barcode_width: Optional[int] | None = 400
    barcode_font_size: Optional[int] | None = 16
    barcode_text_padding: Optional[int] | None = 10
    padding: Optional[int] | None = 16
    divider_height: Optional[int] | None = 4
    divider_width: Optional[int] | None = 300


class ReceiptData(BaseModel):
    shop_name: str
    product_name: str
    barcode: str
    price: str


def generate_receipt(data: ReceiptData, style: ReceiptStyle) -> BytesIO:
    width = 600
    height = int(width * 2 / 3)
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    y = style.padding
    try:
        bold_font = ImageFont.truetype("arialbd.ttf", style.shop_name_font_size)
    except:
        bold_font = ImageFont.load_default()
    draw.text((width // 2, y), data.shop_name, font=bold_font, fill="black", anchor="mm")
    y += style.shop_name_font_size + style.padding

    draw.rectangle([
        (width // 2 - style.divider_width // 2, y),
        (width // 2 + style.divider_width // 2, y + style.divider_height)
    ], fill="black")
    y += style.divider_height + style.padding

    try:
        product_font = ImageFont.truetype("arialbd.ttf", style.product_name_font_size)
    except:
        product_font = ImageFont.load_default()
    draw.text((width // 2, y), data.product_name, font=product_font, fill="black", anchor="mm")
    y += style.product_name_font_size + style.padding

    barcode_gen = barcode.get('code128', data.barcode, writer=ImageWriter())
    barcode_io = BytesIO()
    barcode_gen.write(barcode_io)
    barcode_io.seek(0)
    barcode_img = Image.open(barcode_io)
    barcode_img = barcode_img.resize((style.barcode_width, style.barcode_height))
    image.paste(barcode_img, (width // 2 - style.barcode_width // 2, y))
    y += style.barcode_height + style.barcode_text_padding

    try:
        price_font = ImageFont.truetype("arialbd.ttf", style.price_font_size)
    except:
        price_font = ImageFont.load_default()
    draw.text((width // 2, y), f"{data.price} UZS", font=price_font, fill="black", anchor="mm")

    img_io = BytesIO()
    image.save(img_io, format="PNG")
    img_io.seek(0)
    return img_io