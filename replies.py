import os
import random
import glob
from twitter import Twitter
import requests
import re
import image_noisifier as imn


class ReplyText:
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return f"Text: {self.text}"

    def do_reply(self, t: Twitter, s: requests.session, tw_id: str):
        print(f"Tweeting text reply {self.text} in reply to {tw_id}")
        repl_id = t.tweet(s, reply_to_tweet_id=tw_id, text=self.text)
        print(f"Tweet id: {repl_id}")

        return repl_id


noisifier = imn.ImageNoisifier()


class ReplyImage:
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return f"Image: {self.path}"

    def do_reply(self, t: Twitter, s: requests.session, tw_id: str):
        global noisifier

        print(f"Tweeting image reply {self.path} in reply to {tw_id}")

        img = noisifier.noisify(self.path)
        if img is None:
            raise Exception("Failed to load img " + self.path)

        media_id = t.upload_image(s, img, 'png')
        if media_id is None:
            return None

        print(f"Media created, id: {media_id}")

        repl_id = t.tweet(s, text="", media=[media_id], reply_to_tweet_id=tw_id)
        print(f"Tweet id: {repl_id}")

        return repl_id


class RepliesContainer:
    def __init__(self, items: list, keywords: list[str] = None):
        self.items = items
        if keywords is not None:
            self.keywords = [re.compile(kw, re.IGNORECASE) for kw in keywords]
        else:
            self.keywords = []

    def interested_in_tweet(self, text: str):
        if len(self.keywords) == 0:
            return True
        lc_text = text.lower()
        return any(kw.search(lc_text) for kw in self.keywords)

    def random(self):
        if len(self.items) == 0:
            return None

        if len(self.items) == 1:
            return self.items[0]

        return self.items[random.randint(0, len(self.items)-1)]


class RepliesDB:
    def __init__(self, folder_path):
        self.containers = []
        self.load_folder(folder_path, False)

    def load_folder(self, path: str, is_sub: bool):

        keywords = []

        if is_sub:
            keywords_file = os.path.join(path, "keywords")
            if not os.path.exists(keywords_file):
                raise Exception(f"Sub-folder {path} has no 'keywords' file")

            with open(keywords_file, 'r', encoding="utf-8") as f:
                keywords = [l.strip() for l in f.readlines() if not l.startswith('#') and len(l) > 0]

        items = []

        for full_name in glob.glob(os.path.join(path, "*")):

            if os.path.split(full_name)[1] == 'keywords':
                continue

            if os.path.isdir(full_name):
                if is_sub:
                    raise Exception("Sub-Sub-folders aren't supported")
                self.load_folder(full_name, True)
                continue

            n, ext = os.path.splitext(full_name)
            ext = ext.lower()

            if ext == '.txt':
                with open(full_name, 'r', encoding="utf-8") as f:
                    items.append(ReplyText(f.read()))
            elif ext == '.png' or ext == '.jpeg' or ext == '.jpg' or ext == '.jfif':
                items.append(ReplyImage(full_name))
            else:
                raise Exception("Unrecognized reply type:" + full_name)

        #if len(items) == 0:
        #    raise Exception("No items loaded from " + path)

        self.containers.append(RepliesContainer(items, keywords))

    def random(self, reply_to_text: str):
        if len(self.containers) == 0:
            raise Exception("not initialized")

        for c in self.containers:
            if c.interested_in_tweet(reply_to_text):
                return c.random()

        return None
