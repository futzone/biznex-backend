from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def now_time():
    tashkent_tz = ZoneInfo('Asia/Tashkent')
    now_tashkent = datetime.now(timezone.utc).astimezone(tashkent_tz)
    return now_tashkent.replace(tzinfo=None)
