import sqlite3
import datetime
from utils import nownanos


class HistoryEntry:
    STATUS_NEW = 0
    STATUS_REPLIED = 1
    STATUS_ERROR = 2 # ever used?
    STATUS_IGNORED = 3

    def __init__(self, tw_id=0, reply_tw_id=0, time_nanos=0, status=0, reply=""):
        self.time_nanos = time_nanos
        self.tw_id = tw_id
        self.reply_tw_id = reply_tw_id
        self.status = status
        self.reply = reply

    def __str__(self):
        return f"{self.tw_id}:{self.time_nanos}:{self.status}:{self.reply}"


class History:
    def __init__(self, dbpath):
        self.path = dbpath
        self.con = None
        self.cursor = None
        self.__create_query = """
        CREATE TABLE if not exists history(tw_id int PRIMARY KEY, reply_tw_id int, time_nanos int, status int, reply text)
        """
        self.__create_idx2_query = "CREATE UNIQUE INDEX if not exists history_by_id ON history (tw_id)"


    def open(self):
        self.con = sqlite3.connect(self.path)
        self.cursor = self.con.cursor()
        self.cursor.execute(self.__create_query)
        self.cursor.execute(self.__create_idx2_query)
        self.con.commit()

    def close(self):
        self.con.commit()
        self.cursor.close()
        self.con.close()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def commit(self):
        self.con.commit()

    def insert(self, ent: HistoryEntry):
        query = 'INSERT INTO history VALUES (?, ?, ?, ?, ?)'
        arguments = (ent.tw_id, ent.reply_tw_id, ent.time_nanos, ent.status, ent.reply)

        try:
            self.cursor.execute(query, arguments)
            self.con.commit()
            return True
        except Exception as ex:
            print(f"Error inserting entry into db {self.path}: {ex}")
            return False

    def update(self, ent: HistoryEntry):
        query = "UPDATE history SET reply_tw_id=?, time_nanos=?, status=?, reply=? WHERE tw_id=?"
        arguments = (ent.reply_tw_id, ent.time_nanos, ent.status, ent.reply, ent.tw_id)

        try:
            self.cursor.execute(query, arguments)
            self.con.commit()
        except Exception as ex:
            print(f"Error updating entry in db {self.path}: {ex}")
            raise ex

    def get_recent(self, window_nanos: int):

        from_nanos = nownanos() - window_nanos

        query = "SELECT tw_id, reply_tw_id, time_nanos, status, reply FROM history WHERE time_nanos >= ? "
        arguments = (from_nanos,)

        try:
            self.cursor.execute(query, arguments)
            data = self.cursor.fetchall()
            return [HistoryEntry(d[0], d[1], d[2], d[3], d[4]) for d in data]

        except Exception as ex:
            print(f"Error reading the recent posts, {ex}")
            raise ex

    def get_by_id(self, tw_id: int):

        query = "SELECT tw_id, reply_tw_id, time_nanos, status, reply FROM history WHERE tw_id = ?"
        arguments = (tw_id,)

        try:
            self.cursor.execute(query, arguments)
            data = self.cursor.fetchone()
            return HistoryEntry(data[0], data[1], data[2], data[3], data[4])

        except Exception as ex:
            return None

    def update_status(self, tw_id: int, status: int):
        query = "UPDATE history SET status=? WHERE tw_id=?"
        arguments = (status, tw_id)

        try:
            self.cursor.execute(query, arguments)
            self.con.commit()
        except Exception as ex:
            print(f"Error updating db {self.path}: {ex}")
            raise ex


if __name__ == "__main__":
    db = History("history.db")

    with db:
        db.insert(HistoryEntry(101, 11111, nownanos(), HistoryEntry.STATUS_NEW, "Hello World 1"))
        db.insert(HistoryEntry(220, 11111, nownanos(), HistoryEntry.STATUS_NEW, "Hello World 2"))
        db.insert(HistoryEntry(330, 11111, nownanos(), HistoryEntry.STATUS_NEW, "Hello World 3"))

    with db:
        for k in db.get_recent(360 * 1e9):
            print(k)
