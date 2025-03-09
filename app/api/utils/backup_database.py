import os
import subprocess
import requests
from datetime import datetime
from app.core.settings import get_settings

settings = get_settings()


MAX_BACKUPS = 5
BACKUP_DIR = "/var/lib/postgresql/backup/"


async def backup_database():

    if settings.DEBUG:
        print("DEBUG rejimi yoqilgan. Backup bajarilmaydi.")
        return

    os.makedirs(BACKUP_DIR, exist_ok=True)

    DB_NAME_BAZARCHI = settings.POSTGRES_DATABASE
    DB_USER_BAZARCHI = settings.POSTGRES_USER
    DB_PASSWORD_BAZARCHI = settings.POSTGRES_PASSWORD
    DB_HOST_BAZARCHI = settings.POSTGRES_HOST

    DB_NAME_PLANKA = "planka"
    DB_USER_PLANKA = "planka"
    DB_PASSWORD_PLANKA = "planka_admin"
    DB_HOST_PLANKA = "localhost"

    BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN
    CHANNEL_ID = settings.TELEGRAM_CHANNEL_ID

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_file_bazarchi = os.path.join(
        BACKUP_DIR, f"backup_bazarchi_{timestamp}.sql"
    )
    backup_file_planka = os.path.join(
        BACKUP_DIR, f"backup_planka_{timestamp}.sql"
    )

    try:

        pg_dump_cmd1 = (
            f"PGPASSWORD={DB_PASSWORD_BAZARCHI} /usr/bin/pg_dump "
            f"-U {DB_USER_BAZARCHI} -h {DB_HOST_BAZARCHI} "
            f"--inserts --if-exists {DB_NAME_BAZARCHI} > {backup_file_bazarchi}"
        )
        subprocess.run(pg_dump_cmd1, shell=True, check=True)
        print(f"Bazarchi uchun backup yaratildi: {backup_file_bazarchi}")

        pg_dump_cmd2 = (
            f"PGPASSWORD={DB_PASSWORD_PLANKA} /usr/bin/pg_dump "
            f"-U {DB_USER_PLANKA} -h {DB_HOST_PLANKA} "
            f"--inserts --if-exists {DB_NAME_PLANKA} > {backup_file_planka}"
        )
        subprocess.run(pg_dump_cmd2, shell=True, check=True)
        print(f"Planka uchun backup yaratildi: {backup_file_planka}")

        manage_old_backups("backup_bazarchi")
        manage_old_backups("backup_planka")

        send_backup_to_telegram(backup_file_bazarchi, BOT_TOKEN, CHANNEL_ID)
        send_backup_to_telegram(backup_file_planka, BOT_TOKEN, CHANNEL_ID)

    except subprocess.CalledProcessError as e:
        print(f"Backup jarayonida xatolik yuz berdi: {e}")
    except Exception as e:
        print(f"Xatolik: {e}")


def manage_old_backups(prefix):
    backups = sorted(
        [f for f in os.listdir(BACKUP_DIR) if f.startswith(
            prefix) and f.endswith(".sql")]
    )

    while len(backups) > MAX_BACKUPS:
        old_backup_path = os.path.join(BACKUP_DIR, backups[0])
        os.remove(old_backup_path)
        print(f"Eski backup o'chirildi: {old_backup_path}")
        backups.pop(0)


def send_backup_to_telegram(file_path, token, chat_id):
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    with open(file_path, 'rb') as f:
        files = {'document': f}
        payload = {'chat_id': chat_id}
        response = requests.post(url, data=payload, files=files)
        if response.status_code == 200:
            print(f"{file_path} Telegram'ga muvaffaqiyatli yuborildi.")
        else:
            print(f"Telegramga yuborishda xatolik: {response.text}")
