import cohere
import os

from .classify import classify_text_toxicity

IS_DEBUG_MODE = True
API_KEY = os.getenv("COHERE_API_KEY")
co = cohere.Client(API_KEY)

class MessageSingle:
    def __init__(self, name, text) -> None:
        self.name = name
        self.text = text

    # Returns the number of token
    def length(self) -> int:
        return len(self.user_text.split(" ")) + self.loved_ones_text.split(" ") + 4

    def to_str(self, placeholder1, placeholder2) -> str:
        return "{user_name}: {user_text}".format(
            user_name=self.name,
            user_text=self.text,
        )

class Message:
    def __init__(self, user_text, loved_ones_text="") -> None:
        self.user_text = user_text
        self.loved_ones_text = loved_ones_text

    # Returns the number of token
    def length(self) -> int:
        return len(self.user_text.split(" ")) + self.loved_ones_text.split(" ") + 4

    def to_str(self, user_name, loved_ones_name) -> str:
        return "{user_name}: {user_text}\n{loved_ones_name}: {loved_ones_text}".format(
            user_name=user_name,
            user_text=self.user_text,
            loved_ones_name=loved_ones_name,
            loved_ones_text=self.loved_ones_text
        )
        

from datetime import datetime
def process_whatsapp_text(text):
    text = text.strip()
    text_split = text.split(':')
    try:
        # Iphone chat export
        user = text.split(':')[2].split(']')[1].strip()
    except:
        try:
            # Android chat export
            user = text.split('-')[1].split(':')[0].strip()
        except:
            # Misc chat export
            if len(text_split) > 0:
                user_split = text_split[0].split(" ")
                user = user_split[-1] if len(user_split) > 0 else ""
        
    if len(text_split) > 0:
        msg = text.split(':')[-1].strip()
    else:
        msg = ""
    return {'user': user, 'text': msg}


class LovedOnes:
    def __init__(self, user_name, loved_ones_name="", short_description="") -> None:
        self.user_name = user_name
        self.other_names = []
        self.loved_ones_name = loved_ones_name
        self.short_description = short_description
        self.latest_chat = [] # array of Message/MessageSingle
        self.MAX_PROMPT_LENGTH = 1800

    def upload_latest_chat(self, file_path: str) -> None:
        # Read text messages from whatsapp export and fill the latest_chat array
        with open(file_path, "r") as f:
            lines = f.readlines() 
            for line in lines:
                res = process_whatsapp_text(line)
                if res['text'] != "" or res['user'] != "":
                    self.latest_chat.append(MessageSingle(res['user'], res['text']))

    def update_latest_chat_user(self, user_text) -> None:
        self.latest_chat.append(Message(user_text.strip()))

    def update_latest_chat_loved_ones(self, loved_ones_text) -> None:
        trimmed_text = loved_ones_text[:loved_ones_text.find("{}:".format(self.user_name))].strip()
        trimmed_text = trimmed_text.replace("--", "").strip()

        if IS_DEBUG_MODE:
            print("Trimmed text: ", trimmed_text)

        self.latest_chat[-1].loved_ones_text = trimmed_text

    def generate_prompt(self) -> str:
        token_count = 10 + len(self.short_description.split(" ")) # Initial prompt token count
        initial_prompt = "Generates conversation with your loved ones.\n{name} is {short_description}\n\n".format(
            name = self.loved_ones_name,
            short_description = self.short_description,
        )

        if len(self.latest_chat) == 0:
            self.latest_chat.append(Message("Hello!", "Hello!"))

        # Generate messages prompt starting for the latest one
        messages_prompt = ""
        messages_idx = len(self.latest_chat)-1
        cur_messages = self.latest_chat[messages_idx].to_str(self.user_name, self.loved_ones_name) + "\n"
        cur_messages_length = len(cur_messages.split(" ")) + 2
        while (token_count + cur_messages_length < self.MAX_PROMPT_LENGTH):
            messages_prompt = cur_messages + messages_prompt
            token_count += cur_messages_length

            messages_idx -= 1
            if messages_idx < 0:
                break

            cur_messages = self.latest_chat[messages_idx].to_str(self.user_name, self.loved_ones_name) + "\n"
            cur_messages_length = len(cur_messages.split(" ")) + 2

        if IS_DEBUG_MODE:
            print("Total prompt token length: ", token_count)

        return initial_prompt + messages_prompt

    def generate_response(self, msg:str) -> str:
        resp = self._generate_response(msg)
        pred, conf = classify_text_toxicity(resp)
        # Prevent sending toxic message to our user.
        while pred == "1" and conf > 0.8:
            resp = self._generate_response(msg)
            pred, conf = classify_text_toxicity(resp)

        self.update_latest_chat_loved_ones(resp)
        return self.latest_chat[-1].loved_ones_text

    def _generate_response(self, msg:str) -> str:
        self.update_latest_chat_user(str(msg).strip())
        prompt = self.generate_prompt()

        if IS_DEBUG_MODE:
            print("------------------------------------------")
            print("prompt: ", prompt)
            print("------------------------------------------")

        user_names = ["{}:".format(self.user_name)]
        for name in user_names:
            user_names.append("{}:".format(name))

        response = co.generate(  
            model='xlarge',  
            prompt = prompt,  
            max_tokens=100,  
            temperature=1,  
            stop_sequences=user_names)

        resp_msg = response.generations[0].text

        if IS_DEBUG_MODE:
            print("------------------------------------------")
            print("resp_msg: ", resp_msg)
            print("------------------------------------------")

        return resp_msg

if __name__ == "__main__":
    # Run this file to test the API in CLI!
    print("Welcome to Sally bot!")
    print("What's your name?")
    user_name = input("Your name: ")
    lo = LovedOnes(user_name)
    print("Hello {}, who do you want to talk to today?".format(user_name))
    their_name = input("Their name: ")
    lo.loved_ones_name = their_name
    print("Talking to {}. Can you provide short description about them?".format(their_name))
    short_description = input("Input short description: ")
    lo.short_description = short_description
    # print("Can you upload your latest chat with them?")
    # input_latest_chat = input("Input whatsapp exported chat: ")
    print("Thanks! You can start chatting now.\n")
    while 1:
        msg = input("{}: ".format(user_name))
        resp = lo.generate_response(msg)
        print("{}: {}".format(lo.loved_ones_name, resp))
