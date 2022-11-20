from flask import Flask, request
import telegram
from telebot.credentials import bot_token, bot_user_name, URL
from telebot.corpus import LOW
import re
import random

global bot
global TOKEN
TOKEN = bot_token
bot = telegram.Bot(token=TOKEN)

# start the flask app
app = Flask(__name__)

@app.route('/', methods=['POST'])
def respond():
    # retrieve the message in JSON and then transform it to Telegram object
    update = telegram.Update.de_json(
        request.get_json(force=True), bot)

    chat_id = update.message.chat.id
    msg_id = update.message.message_id
    text = update.message.text

    # for debugging purposes only
    print("got text message :", text)
    
    # the first time you chat with the bot AKA the welcoming message
    if text == "/start":
        # print the welcoming message
        bot_welcome = """
        Hi there!
        """
        # send the welcoming message
        bot.sendMessage(
            chat_id=chat_id, 
            text=bot_welcome)

    else:
        try:
            return_text = 'Got it!'
            bot.sendMessage(
                chat_id=chat_id, 
                text=return_text)

        except Exception:
            # if things went wrong
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
#    app.run(threaded=True)
   app.run(host='localhost', port=8000)