from sqlitedict import SqliteDict


class TwDb:
	def __init__(self, db_path):
		self.path = db_path
		self.db = None

	def __enter__(self):
		self.db = SqliteDict(self.path)
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.db.commit()
		self.db.close()
		self.db = None

	def __setitem__(self, key, value):
		self.db[key] = value

	def __getitem__(self, item):
		return self.db[item]


if __name__ == "__main__":
	db = TwDb("1.db")
	with db:
		db['aaaaaaaa'] = 1
		db['bbbbbbbb'] = 2
	with db:
		db['cccccccc'] = 1
		db['dddddddd'] = 2
