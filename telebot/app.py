from flask import Flask, request
import telegram
from telebot.credentials import bot_token, bot_user_name, URL
import re
import random
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
# 2. User has typed their name
# 3. User has typed their loved one's name
# 4. User has provided short description of their loved ones
# 5. User has uploaded their latest chat with loved ones (optional) / FULLY ONBOARDED
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
    # retrieve the message in JSON and then transform it to Telegram object
    update = telegram.Update.de_json(
        request.get_json(force=True), bot)

    chat_id = update.message.chat.id
    msg_id = update.message.message_id
    text = update.message.text.strip()

    # for debugging purposes only
    print("got text message :", text)
    bot_help = """Commands: 
                - /restart: restart the bot
                - /help: print this message"""
    
    # the first time you chat with the bot AKA the welcoming message
    if text == "/start" or text == "/restart":
        user_state[chat_id] = 1

        # print the welcoming message
        bot_welcome = f"""Welcome to Sally bot!
                       Reconnect with your loved ones.

                       {bot_help}
                        
                       What's your name?"""
        # send the welcoming message
        bot.sendMessage(
            chat_id=chat_id, 
            text=bot_welcome)
    
    elif text == "/help":
        # send the welcoming message
        bot.sendMessage(
            chat_id=chat_id, 
            text=bot_help)

    else:
        try:
            if user_state[chat_id] == 1:
                user_state[chat_id] = 2
                bot.sendMessage(
                chat_id=chat_id, 
                text="Hello {}, who do you want to talk to today?".format(text))

                # Initialize user Loved Ones object
                user_loved_ones[chat_id] = LovedOnes(text)

            elif user_state[chat_id] == 2:
                msg = """Talking to {name}. Can you provide a short description about them?
                      Finish this sentence. 
                        
                      {name} is a...""".format(
                            name=text
                        )
                user_state[chat_id] = 3
                bot.sendMessage(
                chat_id=chat_id, 
                text=msg)

                user_loved_ones[chat_id].loved_ones_name = text
            elif user_state[chat_id] == 3:
                user_state[chat_id] = 4
                msg = """Thanks! If you want a better experience, please upload your
                      exported WhatsApp chat with {name}.

                      You can skip this step by typing "skip".""".format(
                        name=user_loved_ones[chat_id].loved_ones_name
                      )

                bot.sendMessage(
                chat_id=chat_id, 
                text=msg)

                user_loved_ones[chat_id].short_description = text
            elif user_state[chat_id] == 4:
                if text == "skip":
                    user_state[chat_id] = 5
                    msg = """Thanks! You can start chatting with {name} now.""".format(
                        name=user_loved_ones[chat_id].loved_ones_name
                    )

                # elif <file_uploaded>
                # TODO: Read the latest chat and update the
                # user LO's latest_chat
                # user_loved_ones[chat_id].upload_latest_chat(file)
                else:
                    msg = """If you want a better experience, please upload your
                          exported WhatsApp chat with {name}.

                          You can skip this step by typing "skip".""".format(
                            name=user_loved_ones[chat_id].loved_ones_name
                          )
                
                bot.sendMessage(
                chat_id=chat_id, 
                text=msg)

            elif user_state[chat_id] == 5:
                resp = user_loved_ones[chat_id].generate_response(text)
                bot.sendMessage(
                chat_id=chat_id, 
                text=resp)

        except Exception:
            # if things went wrong
            bot.sendMessage(
                chat_id=chat_id, 
                text="I don't quite get that. Can you type that again? If this keeps occurring, type /restart to restart the bot.", 
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
#    app.run(threaded=True)
   app.run(host='localhost', port=9000)