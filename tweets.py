import twitter
import re
import pickle
import os.path
import json
import datetime
from dateutil import parser
from collections import defaultdict
import smtplib, ssl
from email.mime.text import MIMEText

CONFIG_FILE="./config.json"
LOG_LEVEL="WARN"
GET_LIKES=True
USE_MAIL=False


def send_email(config, urls):
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = config['sender_email']
    receiver_email = config['sender_email']
    email_password = config['email_password']
    context = ssl.create_default_context()
    # send the email
    message = MIMEText(urls)
    message['Subject'] = "Today's Twitter urls"
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())

def parse_config(filename):
    return json.load(open(filename, "r"))

def create_api(config):
    api = twitter.Api( consumer_key=config['consumer_key'],
                       consumer_secret=config['consumer_secret'],
                       access_token_key=config['access_token_key'],
                       access_token_secret=config['access_token_secret'],
                       tweet_mode="extended")
    return api

def get_last_day_tweets(api, now, max_tweets=100):
    all_tweets = []
    found_oldest = False
    oldest_id = None
    while found_oldest != True:
        tweets = api.GetHomeTimeline(count=20, trim_user=True, exclude_replies=True, max_id=oldest_id)
        if LOG_LEVEL == 'DEBUG':
            print("Found %d tweets" % len(tweets))
        for tweet in tweets:
            timestamp = parser.parse(tweet.created_at)
            diff = now - timestamp
            if diff.days >= 1:
                found_oldest = True
                break
            all_tweets.append(tweet)
            oldest_id = tweet.id
            if len(all_tweets) >= max_tweets:
                if LOG_LEVEL == 'DEBUG':
                    print("Max tweets")
                found_oldest = True
                break
            if not found_oldest:
                if LOG_LEVEL == 'DEBUG':
                    print("Many tweets")
    return all_tweets

def get_last_day_liked_tweets(api, user, now, max_tweets=100):
    all_tweets = []
    found_oldest = False
    oldest_id = None
    while found_oldest != True:
        liked_tweets = api.GetFavorites(user_id=user.id, count=20, max_id=oldest_id)
        if LOG_LEVEL == 'DEBUG':
            print("Found %d liked tweets for user %s" % (len(liked_tweets), user.screen_name))
        for tweet in liked_tweets:
            timestamp = parser.parse(tweet.created_at)
            diff = now - timestamp
            if diff.days >= 1:
                found_oldest = True
                break
            all_tweets.append(tweet)
            oldest_id = tweet.id
            if len(all_tweets) >= max_tweets:
                if LOG_LEVEL == 'DEBUG':
                    print("Max liked tweets for user", user.screen_name)
                found_oldest = True
                break
            if not found_oldest:
                if LOG_LEVEL == 'DEBUG':
                    print("Many liked tweets for user", user.screen_name)
    return all_tweets

def fetch_tweets(api, users):
    user_tweets = {}
    if LOG_LEVEL == 'DEBUG':
        print("Fetching %d users" % len(users))
    original_tweets = get_last_day_tweets(api, current_time)
    for user in users:
        if GET_LIKES:
            if user.screen_name in config['ignore_user']:
                continue
            tweets = get_last_day_liked_tweets(api, user, current_time)
            user_tweets[user] = tweets
        for tweet in original_tweets:
            if tweet.user.screen_name in config['ignore_user']:
                continue
            if tweet.user.id == user.id:
                user_tweets[user].append(tweet)
    return user_tweets

def match_urls(tweet):
    urls = []
    if tweet.urls:
        for url in tweet.urls:
            urls.append(url.expanded_url)
    #urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
    return urls

def extract_urls(user_tweets):
    annotated_urls = defaultdict(list)
    for user, tweets in user_tweets.items():
        for tweet in tweets:
            urls = match_urls(tweet)
            for url in urls:
                annotated_urls[url].append(user)
    return annotated_urls

def pretty_print(sorted_obj):
    out = ""
    for url, users in sorted_obj:
        out += url + "\n"
        out += "\t" + str([user.screen_name for user in users]) + "\n"
        out + "\n"
    return out

def sort_and_print(urls):
    arxiv = defaultdict(list)
    nonarxiv = defaultdict(list)
    for url, users in urls.items():
        if "arxiv" in url:
            arxiv[url] = users
        else:
            nonarxiv[url] = users
    sorted_arxiv = sorted(arxiv.items(), key=lambda item: len(item[1]), reverse=True)
    sorted_non_arxiv = sorted(nonarxiv.items(), key=lambda item: len(item[1]), reverse=True)
    ret = "Arxiv Links:\n"
    ret += pretty_print(sorted_arxiv)
    ret += "\n"
    ret += "Non-Arxiv:\n"
    ret += pretty_print(sorted_non_arxiv)
    return ret


if __name__ == "__main__":
    current_time = datetime.datetime.now(datetime.timezone.utc)
    config = parse_config(CONFIG_FILE)
    api = create_api(config)
    users = api.GetFriends()
    user_tweets = fetch_tweets(api, users)
    if LOG_LEVEL == 'DEBUG':
        print("Found %d tweets" % sum([len(tweets) for tweets in user_tweets.values()]))
    annotated_urls = extract_urls(user_tweets)
    pretty_print_urls = sort_and_print(annotated_urls)
    print(pretty_print_urls)
    if USE_MAIL:
        send_email(config, pretty_print_urls)













