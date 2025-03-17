model_information = """Biznex ERP bu biznesingizni avtomatlashtirish va samaradorlikni oshirish uchun mo‘ljallangan zamonaviy tizim. U mahsulot kelib tushishidan tortib, sotuvlar, moliyaviy hisobotlar, foyda va xarajatlar tahlili, xodimlar faoliyatini monitoring qilish va ombor boshqaruvigacha bo‘lgan jarayonlarni qamrab oladi.  

Asosiy xususiyatlari:  
Sotuv jarayoni – tez va qulay tranzaksiyalar, chek bosib chiqarish, har xil to‘lov usullari qabul qilish.  
Mahsulot boshqaruvi – mahsulot qo‘shish, kategoriyalarga ajratish, ombor holatini kuzatish, narxlarni o‘zgartirish va chegirmalar qo‘shish.  
Moliyaviy hisobotlar – daromad, xarajat va sof foydani nazorat qilish, kundalik, haftalik va oylik hisobotlarni avtomatik shakllantirish.  
Ombor nazorati – mahsulot harakatlarini real vaqtda kuzatish, tugayotgan mahsulotlar haqida avtomatik bildirishnomalar olish.  
Xodimlar boshqaruvi – ish jadvali tuzish, sotuv natijalarini kuzatish, xodimlar faoliyatini tahlil qilish.  
Mijozlar bazasi – har bir mijozning xarid tarixini saqlash, individual takliflar tayyorlash, sodiqlik dasturlari va shaxsiy chegirmalar joriy qilish.  

Biznex ERP quyidagi platformalarda ishlaydi:  
Biznex App – kompyuter va noutbuk orqali sotuvlarni boshqarish, hisobotlar yaratish va biznes jarayonlarini nazorat qilish.  
Biznex Mobile – smartfon orqali mahsulotlarni kuzatish, mijozlar bilan muloqot qilish va tezkor sotuvlarni amalga oshirish.  
Biznex Bot – Telegram orqali avtomatik bildirishnomalar, kundalik hisobotlar va muhim ogohlantirishlarni olish.  

Biznex ERP tezkor, qulay va ishonchli tizim bo‘lib, internet mavjud bo‘lmagan sharoitda ham ishlaydi. U doimiy yangilanishlar va texnik qo‘llab-quvvatlashga ega.  

Narxlar:  
Standard – 349 000 UZS/oy, kichik biznes uchun.  
Pro – 549 000 UZS/oy, rivojlanayotgan bizneslar uchun.  
Premium – 989 000 UZS/oy, yirik korxonalar uchun.  

Biznex ERP yordamida biznesingizni oson va samarali boshqaring."""


def generate_response(message: str):
    from g4f.client import Client

    client = Client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": model_information,
            },
            {"role": "user", "content": message}
        ],
        web_search=False
    )
    return response.choices[0].message.content
