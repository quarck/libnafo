import random

import requests
import sys

import auth
import utils
from utils import find

import time

#
# Twitter current constants, perhaps these change over time?
#
CREATE_TWEET_QUERY_ID="SL7Y6NjCx8o4NkEJP3Eb2A"
GET_TWEETS_QUERY_ID="PoZUz38XdT-pXNk0FRfKSw"
PROFILE_SPOTLIGHT_QUERY_ID = "9zwVLJ48lmVUk8u_Gh9DmA"
API_AUTH_HEADER = "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs=1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"

class Twitter:

	#
	# Use Chrome Dev Mode to extract Auth Token and X-Csrf-Token
	# From the Chrome Cookies, after logging in on the web first
	#
	def __init__(self, auth_token, ct0_token):
		self.auth_token = auth_token
		self.ct0_token = ct0_token

		self.cookies = { "auth_token": auth_token, "ct0": ct0_token }

		self.common_headers = {
			"Sec-Ch-Ua": "\"Google Chrome\";v=\"111\", \"Not A(Brand\";v=\"8\", \"Google Chrome\";v=\"111\"",
			"X-Twitter-Client-Language": "en",
			"X-Csrf-Token": ct0_token,
			"Sec-Ch-Ua-Mobile": "?0",
			"Authorization": API_AUTH_HEADER,
			"User-Agent": "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
			"Content-Type": "application/json",
			"X-Twitter-Auth-Type": "OAuth2Session",
			"X-Twitter-Active-User": "yes",
			"Sec-Ch-Ua-Platform": "\"Windows\"",
			"Accept": "*/*",
			"Sec-Fetch-Site": "same-origin",
			"Sec-Fetch-Mode": "cors",
			"Sec-Fetch-Dest": "empty",
			"Accept-Encoding": "gzip, deflate",
			"Accept-Language": "en-US,en-IE;q=0.9,en;q=0.8"
		}

		self.user_ids = {}

	@staticmethod
	def parse_twitter_entries(username, raw_entries):

		items = []

		for re in raw_entries:

			if re['entryId'].startswith('promotedTweet-'):
				continue

			if len(utils.find_value(re, username)) == 0:
				# Also a promoted but sneaky tweet
				continue

			entry_id = re['entryId'][6:]

			if re['content']['entryType'] == 'TimelineTimelineItem':

				try:
					tw_res = re['content']['itemContent']['tweet_results']['result']['legacy']['retweeted_status_result']['result']['legacy']
					items.append((entry_id, tw_res, re))
					continue
				except:
					pass

				try:
					tw_res = re['content']['itemContent']['tweet_results']['result']['legacy']
					items.append((entry_id, tw_res, re))
					continue
				except:
					pass

				try:
					tw_res = re['content']['itemContent']['tweet_results']['result']['tweet']['legacy']
					items.append((entry_id, tw_res, re))
					continue
				except:
					pass

			elif re['content']['entryType'] == 'TimelineTimelineModule':
				# These don't seems to contain anything useful
				pass
			elif re['content']['entryType'] == 'TimelineTimelineCursor':
				# These don't seems to contain anything useful
				pass
			else:
				print("Warning: unrecognized entry type", re['entryType'], file=sys.stderr)

		return items


	def get_user_id(self, session: requests.session, user_name: str):

		if user_name in self.user_ids:
			return self.user_ids[user_name]

		params = {"screen_name": user_name}
		params = requests.utils.quote(str(params).replace("'true'", 'true').replace("'false'", 'false').replace("'", '"'))

		requrl = 'https://twitter.com/i/api/graphql/' + PROFILE_SPOTLIGHT_QUERY_ID + '/ProfileSpotlightsQuery?variables=' + params
		headers = self.common_headers.copy()

		try:
			while True:
				ret = session.get(requrl, headers=headers, cookies=self.cookies)
				if ret.status_code != 429: 
					break
				print("get_user_id hit a rate limit, sleeping")
				time.sleep(60*(5 + random.randint(0, 15)))

			if ret.status_code != 200:
				return None

			js = ret.json()
			user_id = js['data']['user_result_by_screen_name']['result']['rest_id']
			self.user_ids[user_name] = user_id

			time.sleep(0.1)
			return user_id

		except Exception as ex:
			print(ex, file=sys.stderr)

		return None

	def get_user_recent_tweets(self, session: requests.session, username: str):

		true = "true"
		false = "false"

		user_id = self.get_user_id(session, username)
		if user_id is None:
			print("A")
			return None
		print(user_id)

		params = {
			"userId": str(user_id),
			"count": 40,
			"includePromotedContent": true,
			"withQuickPromoteEligibilityTweetFields": true,
			"withDownvotePerspective": false,
			"withReactionsMetadata": false,
			"withReactionsPerspective": false,
			"withVoice": true,
			"withV2Timeline": true
			}


		features = {
			"responsive_web_twitter_blue_verified_badge_is_enabled": true,
			"responsive_web_graphql_exclude_directive_enabled": true, "verified_phone_label_enabled": false,
			"responsive_web_graphql_timeline_navigation_enabled": true,
			"responsive_web_graphql_skip_user_profile_image_extensions_enabled": false,
			"tweetypie_unmention_optimization_enabled": true, "vibe_api_enabled": true,
			"responsive_web_edit_tweet_api_enabled": true,
			"graphql_is_translatable_rweb_tweet_is_translatable_enabled": true,
			"view_counts_everywhere_api_enabled": true, "longform_notetweets_consumption_enabled": true,
			"tweet_awards_web_tipping_enabled": false, "freedom_of_speech_not_reach_fetch_enabled": false,
			"standardized_nudges_misinfo": true,
			"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": false,
			"interactive_text_enabled": "true", "responsive_web_text_conversations_enabled": false,
			"longform_notetweets_richtext_consumption_enabled": false, "responsive_web_enhance_cards_enabled": false
		}

		params = requests.utils.quote(
			str(params).replace("'true'", 'true').replace("'false'", 'false').replace("'", '"'))

		features = requests.utils.quote(
			str(features).replace("'true'", 'true').replace("'false'", 'false').replace("'", '"'))

		# Has some twitter defauls encoded
		requrl = "https://twitter.com:443/i/api/graphql/" + GET_TWEETS_QUERY_ID + \
			"/UserTweets?variables=" + params + "&features=" + features

		headers = self.common_headers.copy()
		headers['Referer'] = "https://twitter.com/" + username

		try:
			while True:
				ret = session.get(requrl, headers=headers, cookies=self.cookies)

				if ret.status_code != 429: 
					break
				print("get_user_recent_tweets hit a rate limit, sleeping")
				time.sleep(60*(5 + random.randint(0, 15)))

			if ret.status_code != 200:
				print(ret, ret.status_code, ret.text)
				return None

			js = ret.json()

			timeline = js['data']['user']['result']['timeline_v2']['timeline']

			instructions = timeline['instructions']

			for i in instructions:
				if i['type'] == 'TimelineAddEntries':
					return self.parse_twitter_entries(username, i['entries'])

		except Exception as ex:
			print(ex, "sh", file=sys.stderr)

		return None

	def tweet(self, session: requests.session, reply_to_tweet_id: str, text: str = "", media: list = None):

		requrl = "https://twitter.com:443/i/api/graphql/" + CREATE_TWEET_QUERY_ID +"/CreateTweet"

		headers = self.common_headers.copy()
		headers['Origin'] = "https://twitter.com"
		headers['Referer'] = "https://twitter.com/compose/tweet"

		reqdata={
			"features": {
				"freedom_of_speech_not_reach_fetch_enabled": False,
				"graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
				"interactive_text_enabled": True,
				"longform_notetweets_consumption_enabled": True,
				"longform_notetweets_richtext_consumption_enabled": False,
				"responsive_web_edit_tweet_api_enabled": True,
				"responsive_web_enhance_cards_enabled": False,
				"responsive_web_graphql_exclude_directive_enabled": True,
				"responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
				"responsive_web_graphql_timeline_navigation_enabled": True,
				"responsive_web_text_conversations_enabled": False,
				"responsive_web_twitter_blue_verified_badge_is_enabled": True,
				"standardized_nudges_misinfo": True,
				"tweet_awards_web_tipping_enabled": False,
				"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": False,
				"tweetypie_unmention_optimization_enabled": True,
				"verified_phone_label_enabled": False,
				"vibe_api_enabled": True,
				"view_counts_everywhere_api_enabled": True
			},
			"queryId": CREATE_TWEET_QUERY_ID,
			"variables": {
				"dark_request": False,
				"media": {
					"media_entities": [{"media_id": str(m), "tagged_users": []} for m in media] if media is not None else [],
					"possibly_sensitive": False
				},
				"reply": {
					"exclude_reply_user_ids": [],
					"in_reply_to_tweet_id": str(reply_to_tweet_id),
				},
				"semantic_annotation_ids": [],
				"tweet_text": text,
				"withDownvotePerspective": False,
				"withReactionsMetadata": False,
				"withReactionsPerspective": False
				}
			}

		try:
			while True:
				ret = session.post(requrl, headers=headers, json=reqdata, cookies=self.cookies)

				if ret.status_code != 429: 
					break
				print("tweet hit a rate limit, sleeping")
				time.sleep(60*(5 + random.randint(0, 15)))

			if ret.status_code != 200:
				print (ret.text)
				return None

			return ret.json()['data']['create_tweet']['tweet_results']['result']['legacy']['id_str']

		except Exception as ex:
			print(ex, file=sys.stderr)

		return None

	def get_webkit_bundary_str(self, n = 13):
		chars = [chr(i) for i in range(ord('a'), ord('z')+1)] + \
				[chr(i) for i in range(ord('A'), ord('Z')+1)] + \
				[chr(i) for i in range(ord('0'), ord('9')+1)]
		ret = ""
		for i in range(n):
			ret = ret + chars[random.randint(0, len(chars)-1)]
		return ret

	def upload_image(self, session: requests.session, image: bytes, type: str):
		len_bytes = len(image)

		req_uri_INIT = "https://upload.twitter.com:443/i/media/upload.json?command=INIT&" + \
					f"total_bytes={len_bytes}&media_type=image%2F{type}&media_category=tweet_image"

		headers = self.common_headers.copy()
		headers['Referer'] = "https://twitter.com/"

		while True:
			init_result = session.post(req_uri_INIT, headers=headers, cookies=self.cookies)

			if init_result.status_code != 429: 
				break
			print("upload_image hit a rate limit, sleeping")
			time.sleep(60*(5 + random.randint(0, 15)))


		if init_result.status_code // 100 != 2:
			return None

		init_result = init_result.json()

		media_id = init_result['media_id']
		media_key = init_result['media_key']

		## Then actual data!
		req_uri_APPEND = f"https://upload.twitter.com:443/i/media/upload.json?command=APPEND&media_id={media_id}&segment_index=0"

		boundary = self.get_webkit_bundary_str()

		headers_post = headers.copy()
		headers_post["Content-Type"] = f"multipart/form-data; boundary=----WebKitFormBoundaryJar{boundary}"

		img_data = bytes(f"------WebKitFormBoundaryJar{boundary}\r\n" + \
				   "Content-Disposition: form-data; name=\"media\"; filename=\"blob\"\r\n" + \
				   "Content-Type: application/octet-stream\r\n" + \
				   "\r\n", 'utf-8') + \
				   image + \
				   bytes(f"\r\n------WebKitFormBoundaryJar{boundary}--\r\n", 'utf-8')

		while True:
			append_result = session.post(req_uri_APPEND, headers=headers_post, cookies=self.cookies, data=img_data)

			if append_result.status_code != 429: 
				break
			print("upload_imag[2] hit a rate limit, sleeping")
			time.sleep(60*(5 + random.randint(0, 15)))


		if append_result.status_code // 100 != 2:
			return None

		## Finalize now!

		req_uri_FINALIZE = f"https://upload.twitter.com:443/i/media/upload.json?command=FINALIZE&media_id={media_id}"

		while True:
			finalize_result = session.post(req_uri_FINALIZE, headers=headers, cookies=self.cookies)

			if finalize_result.status_code != 429: 
				break

			print("upload_imag[3] hit a rate limit, sleeping")
			time.sleep(60*(5 + random.randint(0, 15)))

		if finalize_result.status_code // 100 != 2:
			return None

		return media_id


if __name__ == "__main__":
	twitter = Twitter(auth.auth_token, auth.ct0_token)
	target_user_id = twitter.get_user_id(requests.Session(), 'mfa_russia')
	print (target_user_id)

	for entry_id, tw, tw_full in twitter.get_user_recent_tweets(
		requests.session(),
		'wallacemick'):

		full_text = tw['full_text'] if 'full_text' in tw else ''

		print()
		print (entry_id, tw['id_str'], full_text) # , tw)
		#print(tw_full)

