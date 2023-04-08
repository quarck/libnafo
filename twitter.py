import requests
import sys

import utils
from utils import find

#
# Twitter current constants, perhaps these change over time?
#
CREATE_TWEET_QUERY_ID="SL7Y6NjCx8o4NkEJP3Eb2A"
GET_TWEETS_QUERY_ID="PoZUz38XdT-pXNk0FRfKSw"
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

	@staticmethod
	def parse_twitter_entries(raw_entries):

		items = []

		for re in raw_entries:

			if re['content']['entryType'] == 'TimelineTimelineItem':
				try:
					tw_res = re['content']['itemContent']['tweet_results']['result']['legacy']

					if 'retweeted_status_result' in tw_res:
						tw_res = tw_res['retweeted_status_result']['result']['legacy']
						items.append(tw_res)
					else:
						items.append(tw_res)

				except:
					print(find(re['content'], 'full_text'))
					raise

			elif re['content']['entryType'] == 'TimelineTimelineModule':
				# These don't seems to contain anything useful
				pass
			elif re['content']['entryType'] == 'TimelineTimelineCursor':
				# These don't seems to contain anything useful
				pass
			else:
				print("Warning: unrecognized entry type", re['entryType'], file=sys.stderr)

		return items

	def get_user_recent_tweets(self, session: requests.session, user_id: int, refer_username: str):

		# Has some twitter defauls encoded
		requrl = "https://twitter.com:443/i/api/graphql/" + GET_TWEETS_QUERY_ID + \
			"/UserTweets?variables=%7B%22userId%22%3A%22" + str(user_id) + \
			"%22%2C%22count%22%3A40%2C%22includePromotedContent%22%3Atrue%2C%22withQuickPromoteEligibilityTweetFields%22%3Atrue%2C%22withDownvotePerspective%22%3Afalse%2C%22withReactionsMetadata%22%3Afalse%2C%22withReactionsPerspective%22%3Afalse%2C%22withVoice%22%3Atrue%2C%22withV2Timeline%22%3Atrue%7D&features=%7B%22responsive_web_twitter_blue_verified_badge_is_enabled%22%3Atrue%2C%22responsive_web_graphql_exclude_directive_enabled%22%3Atrue%2C%22verified_phone_label_enabled%22%3Afalse%2C%22responsive_web_graphql_timeline_navigation_enabled%22%3Atrue%2C%22responsive_web_graphql_skip_user_profile_image_extensions_enabled%22%3Afalse%2C%22tweetypie_unmention_optimization_enabled%22%3Atrue%2C%22vibe_api_enabled%22%3Atrue%2C%22responsive_web_edit_tweet_api_enabled%22%3Atrue%2C%22graphql_is_translatable_rweb_tweet_is_translatable_enabled%22%3Atrue%2C%22view_counts_everywhere_api_enabled%22%3Atrue%2C%22longform_notetweets_consumption_enabled%22%3Atrue%2C%22tweet_awards_web_tipping_enabled%22%3Afalse%2C%22freedom_of_speech_not_reach_fetch_enabled%22%3Afalse%2C%22standardized_nudges_misinfo%22%3Atrue%2C%22tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled%22%3Afalse%2C%22interactive_text_enabled%22%3Atrue%2C%22responsive_web_text_conversations_enabled%22%3Afalse%2C%22longform_notetweets_richtext_consumption_enabled%22%3Afalse%2C%22responsive_web_enhance_cards_enabled%22%3Afalse%7D"

		headers = self.common_headers.copy()
		headers['Referer'] = "https://twitter.com/" + refer_username

		try:
			ret = session.get(requrl, headers=headers, cookies=self.cookies)

			if ret.status_code != 200:
				return None

			js = ret.json()

			timeline = js['data']['user']['result']['timeline_v2']['timeline']

			instructions = timeline['instructions']

			for i in instructions:
				if i['type'] == 'TimelineAddEntries':
					return self.parse_twitter_entries(i['entries'])

		except Exception as ex:
			print(ex, file=sys.stderr)

		return None

	def reply_publicly(self, session: requests.session, reply_to_tweet_id: str, reply: str, media: list=None):

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
					"media_entities": [str(m) for m in media] if media is not None else [],
					"possibly_sensitive": False
				},
				"reply": {
					"exclude_reply_user_ids": [],
					"in_reply_to_tweet_id": str(reply_to_tweet_id),
				},
				"semantic_annotation_ids": [],
				"tweet_text": reply,
				"withDownvotePerspective": False,
				"withReactionsMetadata": False,
				"withReactionsPerspective": False
				}
			}

		try:
			ret = session.post(requrl, headers=headers, json=reqdata, cookies=self.cookies)
			if ret.status_code != 200:
				return None

			return ret.json()['data']['create_tweet']['tweet_results']['result']['legacy']['id_str']

		except Exception as ex:
			print(ex, file=sys.stderr)

		return None