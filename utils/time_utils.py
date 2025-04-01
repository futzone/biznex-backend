from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo


def now_time():
    tashkent_tz = ZoneInfo('Asia/Tashkent')
    now_tashkent = datetime.now(timezone.utc).astimezone(tashkent_tz) + timedelta(hours=5)
    return now_tashkent.replace(tzinfo=None)
