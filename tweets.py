import twitter
from twitter import Api
import re
import pickle
import os.path
import smtplib, ssl
from email.mime.text import MIMEText

# mail stuff
port = 465  # For SSL
smtp_server = "smtp.gmail.com"
sender_email = "miter909@gmail.com"  # Enter your address
receiver_email = "miter909@gmail.com"  # Enter receiver address
# password = input("Type your password and press enter: ")
password = "Test909!"
context = ssl.create_default_context()

# api stuff
api: Api = twitter.Api(consumer_key='ap1DdVqrK1PcJdjlwEcKAexPs',
                       consumer_secret='Pl9bcLJJNhfiTK2oizaJ7IuVZAyYgf9xPeOX51dUS2RRW4ODaR',
                       access_token_key='619348634-1CwbQ6sYWcc3OIF6nINq4jzPNVw65faXGjL7YMQ1',
                       access_token_secret='QtMQDq2yPOW9O98GTpiaOosyGyfST6dBYRoQfUxurFT6w')

last_id = None
new_last_id = None
id_mark = None
tick = True
counter = 0

# Get friends
users = api.GetFriends()

# For each user do everything
for u in users:

    # initialize last id to None and then attempt to load.
    user_file_name = "./u_{}.pic".format(u.id)
    last_id = None
    new_last_id = None
    id_mark = None
    tick = True
    counter = 0
    text = []

    # check if user file exists; if not create one
    if os.path.exists(user_file_name):
        with open(user_file_name, "rb") as fo1:
            try:
                last_id = pickle.load(fo1)
            except Exception as ex:
                print("User [{}] file empty. Proceeding with default value None. Exception [{}]".format(u.name, ex))

    while True:

        # get the array of 5 latest tweets up to last id
        status_stream = api.GetUserTimeline(user_id=u.id, count=5, max_id=id_mark, since_id=last_id)
        tweets_buffer = [tweet.AsDict() for tweet in status_stream]

        # record latest id once
        for t in tweets_buffer:
            if tick:
                new_last_id = t['id'] + 1
                tick = False
            # process urls if available
            myString = t['text']
            match = re.search("(?P<url>https?://[^\s]+)", myString)
            if 'media' in t.keys():
                for j in t['media']:
                    text += 'tweet: ' + t['text'] + ' url: ' + j["url"]
            elif match is not None:
                text += 'tweet: ' + t['text']

        # get id mark for the next page
        if len(tweets_buffer) > 0:
            id_mark = tweets_buffer[-1]["id"] - 1

        # do -- while end statement for loop exit.
        counter = counter + 1
        if (last_id is None and counter > 4) or len(tweets_buffer) == 0:
            break
    # if new last id then record it
    if new_last_id is not None:
        with open(user_file_name, "wb") as fo2:
            pickle.dump(new_last_id, fo2)

    # send the email
    message = MIMEText("{}".format('\n'.join(text)))
    message['Subject'] = "{}'s tweets with urls".format(u.name)
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())
