import json
import os
import random


class RepliesDB:
    def __init__(self, folder_path):
        self.texts = []
        for fname in os.listdir(folder_path):
            with open(os.path.join(folder_path, fname), 'r') as f:
                self.texts.append(f.read())

        if len(self.texts) == 0:
            raise Exception("No responses loaded from " + folder_path)

    def random(self):
        if len(self.texts) == 0:
            raise Exception("not initialized")

        if len(self.texts) == 1:
            return self.texts[0]

        return self.texts[random.randint(0, len(self.texts)-1)]


if __name__ == "__main__":
    d = RepliesDB('replies')
    print (d.random())