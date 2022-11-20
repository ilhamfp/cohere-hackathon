from flask import Flask, request
import telegram
from telebot.credentials import bot_token, bot_user_name, URL
import requests
import zipfile
import io
from api.generate import LovedOnes

global bot
global TOKEN
TOKEN = bot_token
bot = telegram.Bot(token=TOKEN)

# start the flask app
app = Flask(__name__)

# user_state store the state of user onboarding process.
# Each user has 5 onboarding steps
# 1. User start/restart the bot
# 2. User has typed their loved one's name
# 3. User has provided short description of their loved ones
# 4. User has uploaded their latest chat with loved ones (optional) / FULLY ONBOARDED
user_state = {}

# user_loved_ones store the mapping between user -> LovedOnes.
# We keep track of the chat messages in the LovedOnes class to provide
# context to the prompt.
user_loved_ones = {}

@app.route('/', methods=['GET'])
def home():
    return 'Welcome to Sally! Reconnect with your loved ones. Server is up.'

@app.route('/', methods=['POST'])
def respond():
    bot_help = "Commands:\n - /restart: restart the bot\n - /help: print this message"

    # retrieve the message in JSON and then transform it to Telegram object
    update = telegram.Update.de_json(
        request.get_json(force=True), bot)

    if update is None or update.message is None:
        return "ok"

    chat_id = update.message.chat.id
    msg_id = update.message.message_id
    recipient = update.message.from_user.first_name.strip()

    if update.message.text is not None:
        text = update.message.text.strip()

        # for debugging purposes only
        print("got text message :", text)
        
        # the first time you chat with the bot AKA the welcoming message
        if text == "/start" or text == "/restart":
            user_state[chat_id] = 1

            # print the welcoming message
            bot_welcome = f"Welcome to Sally bot, {recipient}!\nReconnect with your loved ones.\n\n{bot_help}\n\n\nWho do you want to talk to today?"
            # send the welcoming message
            bot.sendMessage(
                chat_id=chat_id, 
                text=bot_welcome)

            # Initialize user Loved Ones object
            user_loved_ones[chat_id] = LovedOnes(recipient)
        elif text == "/help":
            # send the welcoming message
            bot.sendMessage(
                chat_id=chat_id, 
                text=bot_help)

        else:
            try:
                if user_state[chat_id] == 1:
                    msg = "Let's talk to {name}! Can you provide a short description about them?\nFinish this sentence.\n\n{name}...".format(
                                name=text
                            )
                    user_state[chat_id] = 2
                    bot.sendMessage(
                    chat_id=chat_id, 
                    text=msg)

                    user_loved_ones[chat_id].loved_ones_name = text
                elif user_state[chat_id] == 2:
                    user_state[chat_id] = 3
                    msg = "Thanks! For better experience, please upload your exported WhatsApp chat with {name}.\n\nYou can skip this step by typing \"skip\".".format(
                            name=user_loved_ones[chat_id].loved_ones_name
                        )

                    bot.sendMessage(
                    chat_id=chat_id, 
                    text=msg)

                    user_loved_ones[chat_id].short_description = text
                elif user_state[chat_id] == 3:
                    if text.lower() == "skip":
                        user_state[chat_id] = 4
                        msg = "Thanks! You can start chatting with {name} now.".format(
                            name=user_loved_ones[chat_id].loved_ones_name
                        )

                    # elif <file_uploaded>
                    # TODO: Read the latest chat and update the
                    # user LO's latest_chat
                    # user_loved_ones[chat_id].upload_latest_chat(file)
                    else:
                        msg = "For better experience, please upload your exported WhatsApp chat with {name}.\n\nYou can skip this step by typing \"skip\".".format(
                                name=user_loved_ones[chat_id].loved_ones_name
                            )
                    
                    bot.sendMessage(
                    chat_id=chat_id, 
                    text=msg)

                elif user_state[chat_id] == 4:
                    resp = user_loved_ones[chat_id].generate_response(text)
                    bot.sendMessage(
                    chat_id=chat_id, 
                    text=resp)

            except Exception as e:
                print("Got an exception 2: ", e)
                # if things went wrong
                bot.sendMessage(
                    chat_id=chat_id, 
                    text="I don't quite get that. Can you type that again? If this keeps occurring, type /restart to restart the bot.", 
                    reply_to_message_id=msg_id)

    elif bot.getFile(update.message.document.file_id) is not None:
        try:
            return_text = 'Exported chat file received!\n\nYou can start chatting with {name} now.'.format(
                                name=user_loved_ones[chat_id].loved_ones_name
                            )
            bot.sendMessage(
                chat_id=chat_id, 
                text=return_text)
            file_url = bot.getFile(update.message.document.file_id).file_path
            file_path = "../corpus/{}".format(chat_id)
            corpus = requests.get(file_url)
            compressed_file = zipfile.ZipFile(io.BytesIO(corpus.content))
            compressed_file.extractall(f"{file_path}/extracted/")
            extracted_path = f"{file_path}/extracted/_chat.txt"
            print("extracted_path: ", extracted_path)
            user_loved_ones[chat_id].upload_latest_chat(extracted_path)
            user_state[chat_id] = 4
        except Exception as e:
                print("Got an exception 1: ", e)
                # if things went wrong
                bot.sendMessage(
                    chat_id=chat_id, 
                    text="I don't quite get that. Can you type that again? If this keeps occurring, type /restart to restart the bot.", 
                    reply_to_message_id=msg_id)
    else:
        bot.sendMessage(
            chat_id=chat_id, 
            text="I don't quite get that. How can I help you with?", 
            reply_to_message_id=msg_id)
            
    return 'ok'

@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    s = bot.setWebhook('{URL}'.format(URL=URL))
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"


@app.route('/')
def index():
   return '.'

if __name__ == '__main__':
   app.run(host='localhost', port=9000)