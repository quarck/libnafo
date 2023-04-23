import requests
import sys

import utils
from utils import find

import twitter
import auth
import post_history
import replies
import rate_limits
import os
import time
import tnotify
import datetime


class App:
	def __init__(self, storage_path, target_user_name, stats_html_file):
		self.history = post_history.History(os.path.join(storage_path, "history.db"))
		self.twitter = twitter.Twitter(auth.auth_token, auth.ct0_token)

		self.replies_db = replies.RepliesDB(os.path.join(storage_path, "replies"))

		self.target_user_name = target_user_name
		self.target_user_id = self.twitter.get_user_id(requests.Session(), target_user_name)

		self.fail_cnt = 0

		self.stats_html_file = stats_html_file

	def allowed_to_send(self):
		now = utils.nownanos()

		with self.history:
			last_day = self.history.get_recent(rate_limits.DAY_NANOS)

			if len(last_day) >= rate_limits.MAX_PER_DAY:
				print("Posting forbidden - daily rate exceeded (our self-implied)")
				return False

			last_hour = [p for p in last_day if p.time_nanos > now - rate_limits.HOUR_NANOS]
			if len(last_hour) >= rate_limits.MAX_PER_HOUR:
				print("Posting forbidden - hourly rate exceeded (our self-implied)")
				return False

			last_minute = [p for p in last_hour if p.time_nanos >= now - rate_limits.MINUTE_NANOS]
			if len(last_minute) >= rate_limits.MAX_PER_MINUTE:
				print("Posting forbidden - per minute rate exceeded (our self-implied)")
				return False

		return True

	def on_fetch_result(self, success: bool):
		if success:
			self.fail_cnt = 0
		else:
			self.fail_cnt += 1
			if self.fail_cnt > 10:
				raise Exception("More than 10 consecutive fetch failures")

	#
	# every time we start anew - we don't post replies to all the past tweets bot have missed
	# thus, first we check the current tweets and log them as "ignored"
	#
	def seed_db(self):
		tweets = self.twitter.get_user_recent_tweets(
			requests.session(),
			self.target_user_name
		)

		if tweets is None:
			raise Exception("Failed to seed the DB")

		with self.history:
			for tw_id, tw, tw_full in tweets:
				self.history.insert(post_history.HistoryEntry(tw_id, 0, 0, post_history.HistoryEntry.STATUS_IGNORED, ""))
				if tw_id != tw['id_str']:
					self.history.insert(post_history.HistoryEntry(tw['id_str'], 0, 0,
																  post_history.HistoryEntry.STATUS_IGNORED, ""))

	def iterate(self):
		print("Iterating!")

		session = requests.session()

		tweets = self.twitter.get_user_recent_tweets(
			session,
			self.target_user_name
		)

		if tweets is None or len(tweets) == 0:
			print("Failed to fetch tweets!")
			self.on_fetch_result(False)
			return

		self.on_fetch_result(True)

		with self.history:
			for tw_id, tw, tw_full in tweets:
				prev_entry = self.history.get_by_id(tw['id_str'])
				prev_entry2 = self.history.get_by_id(tw_id) # would be different in case of retweet, 'id_str' points to the original tweet
				if prev_entry is None and prev_entry2 is None:
					full_text = tw['full_text'] if 'full_text' in tw else ''
					self.post_reply(session, tw['id_str'], full_text)
					return # only do once at a time!

	def post_reply(self, session, id_str, text):
		now = utils.nownanos()

		reply = self.replies_db.random(text)

		print("Posting reply to the new tweet id ", id_str, "reply text", str(reply))

		he = post_history.HistoryEntry(id_str, 0, now, post_history.HistoryEntry.STATUS_NEW, str(reply))
		self.history.insert(he)

		try:
			reply_tw_id = reply.do_reply(self.twitter, session, id_str)
		except Exception as ex:
			print(ex, ex.__traceback__, file=sys.stderr)
			reply_tw_id = None

		if reply_tw_id is not None:
			he.reply_tw_id = reply_tw_id
			he.status = post_history.HistoryEntry.STATUS_REPLIED
		else:
			he.status = post_history.HistoryEntry.STATUS_ERROR
			self.on_fetch_result(False) # also make it count towards errors also

		self.history.update(he)

	def run(self):

		self.seed_db()

		while True:
			if not self.allowed_to_send():
				print("Not allowed to send - awaiting 5 minutes before trying anything else")
				time.sleep(60 * 5)
				continue

			self.iterate()
			self.update_stats_html()
			time.sleep(60 * 2)

	def update_stats_html(self):
		if self.stats_html_file is None or self.stats_html_file == "":
			return
		try:
			now = utils.nownanos()

			with self.history:
				last_day = [e.time_nanos for e in self.history.get_recent(rate_limits.DAY_NANOS)]

			last_hour = [p for p in last_day if p > now - rate_limits.HOUR_NANOS]
			last_minute = [p for p in last_hour if p >= now - rate_limits.MINUTE_NANOS]

			html = "<html><head><title>nibbler-stats</title></head><body><br>"
			html += f"<b>Last 24hrs:</b> {len(last_day)}<br>"
			html += f"<b>Last hour:</b> {len(last_hour)}<br>"
			html += f"<b>Last minute:</b> {len(last_minute)}<br>"

			if len(last_day) > 0:
				last_tw = datetime.datetime.fromtimestamp(max(last_day) / 1e9)
				html += f"Last timestamp: {last_tw}"

			html += "</body></html>"

			with open(self.stats_html_file, "w+") as f:
				f.write(html)

		except Exception as ex:
			print(ex)


def main():

	if len(sys.argv) < 3:
		print("""Usage:
python3 main.py <storage_folder> <twitter_username_to_watch> [html_status_file_to_update] 
""")
		return

	storage = sys.argv[1]
	tw_user = sys.argv[2]
	html_status = sys.argv[3] if len(sys.argv) == 4 else None

	print(f"Using storage folder {storage}, replying to user {tw_user}")
	if html_status is not None:
		print(f"Reporting stats into {html_status}")

	try:
		app = App(storage, tw_user, html_status)
		app.run()
	except KeyboardInterrupt as ke:
		print("terminating!")
	except Exception as ex:
		print(ex)
		tnotify.notify(f"ShitPoster bot instance {tw_user} Bot has died with exception: {ex}")


if __name__ == "__main__":
	main()
