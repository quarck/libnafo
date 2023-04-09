import sys
import urllib.request ## UGGH
import auth

BASE_URI = 'https://api.telegram.org/' + auth.tg_bot_api_token + '/sendMessage?%s'


def notify(message: str):
    if auth.tg_notify_user_id == 0 or auth.tg_bot_api_token == "":
        return

    params = urllib.parse.urlencode({'chat_id': auth.tg_notify_user_id, 'text': message})

    with urllib.request.urlopen(BASE_URI % params) as f:
        _ = f.read().decode('utf-8')


if __name__ == "__main__":
    notify("test message!")