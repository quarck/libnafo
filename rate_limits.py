from sqlitedict import SqliteDict
import json
import datetime
from utils import nownanos

MAX_PER_DAY = 40
MAX_PER_HOUR = 10
MAX_PER_MINUTE = 1

DAY_NANOS = 24 * 3600 * 1e9
HOUR_NANOS = 3600 * 1e9
MINUTE_NANOS = 60 * 1e9

encoder = json.JSONEncoder()
decoder = json.JSONDecoder()


class FiringHistory:
    def __init__(self, jsonstr=None):
        self.items = []
        if jsonstr is not None:
            self.items = decoder.decode(jsonstr)

    def to_json(self):
        return encoder.encode(self.items)

    def log_fire(self):
        self.items = (self.items + [nownanos()])[-MAX_PER_DAY:]

    def can_send(self):
        now = nownanos()

        daily = self.items[-MAX_PER_DAY:]
        hourly = self.items[-MAX_PER_HOUR:]
        minutly = self.items[-MAX_PER_MINUTE:]

        # Sending now will breach daily limit
        if len(daily) == MAX_PER_DAY and (now - daily[0]) <= DAY_NANOS:
            return False

        # Sending now will breach hourly limit
        if len(hourly) == MAX_PER_HOUR and (now - hourly[0]) <= HOUR_NANOS:
            return False

        # Sending now will breanch per-minute limit
        if len(minutly) == MAX_PER_MINUTE and (now - minutly[0]) <= MINUTE_NANOS:
            return False

        # We seems to be good to fire more!
        return True


class RateLimits:
    def __init__(self, db_path):
        self.path = db_path

    def can_send(self):
        with SqliteDict(self.path) as db:
            if 'json' in db:
                fr = FiringHistory(db['json'])
            else:
                fr = FiringHistory()
            return fr.can_send()

    def log_fire(self):
        with SqliteDict(self.path) as db:
            if 'json' in db:
                fr = FiringHistory(db['json'])
            else:
                fr = FiringHistory()
            fr.log_fire()
            db['json'] = fr.to_json()
            db.commit()


if __name__ == "__main__":
    import time
    hist = RateLimits("rate_limits.db")
    print (hist.can_send())
    hist.log_fire()
    print (hist.can_send())
    time.sleep(1)
    print (hist.can_send())
    for i in range(0, 12):
        hist.log_fire()
        time.sleep(0.001)
    print (hist.can_send())
