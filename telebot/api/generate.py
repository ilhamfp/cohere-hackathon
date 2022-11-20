import cohere
import os

IS_DEBUG_MODE = False
API_KEY = os.getenv("COHERE_API_KEY")
co = cohere.Client(API_KEY)

class Message:
    def __init__(self, user_text, loved_ones_text="") -> None:
        self.user_text = user_text
        self.loved_ones_text = loved_ones_text

    # Returns the number of token
    def length(self) -> int:
        return len(self.user_text.split(" ")) + self.loved_ones_text.split(" ")

    def to_str(self, user_name, loved_ones_name) -> str:
        return """
        {user_name}: {user_text}
        {loved_ones_name}: {loved_ones_text}
        """.format(
            user_name=user_name,
            user_text=self.user_text,
            loved_ones_name=loved_ones_name,
            loved_ones_text=self.loved_ones_text
        )
        
class LovedOnes:
    def __init__(self, user_name, loved_ones_name="", short_description="") -> None:
        self.user_name = user_name
        self.loved_ones_name = loved_ones_name
        self.short_description = short_description
        self.latest_chat = [] # array of Messages
        self.MAX_PROMPT_LENGTH = 1800

    def upload_latest_chat(self) -> None:
        # Read text messages from whatsapp export and fill the latest_chat arrays
        return 

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
        initial_prompt = """
        Generates conversation with your loved ones.
        {name} is a {short_description}
        """.format(
            name = self.loved_ones_name,
            short_description = self.short_description,
        )

        if len(self.latest_chat) == 0:
            self.latest_chat.append(Message("Hello!", "Hello!"))

        # Generate messages prompt starting for the latest one
        messages_prompt = ""
        messages_idx = len(self.latest_chat)-1
        cur_messages = self.latest_chat[messages_idx].to_str(self.user_name, self.loved_ones_name)
        cur_messages_length = len(cur_messages.split(" ")) + 2
        while (token_count + cur_messages_length < self.MAX_PROMPT_LENGTH):
            sep = "--" if messages_prompt != "" else ""
            messages_prompt = cur_messages + sep + messages_prompt
            token_count += cur_messages_length

            messages_idx -= 1
            if messages_idx < 0:
                break

            cur_messages = self.latest_chat[messages_idx].to_str(self.user_name, self.loved_ones_name)
            cur_messages_length = len(cur_messages.split(" ")) + 2

        if IS_DEBUG_MODE:
            print("Total prompt token length: ", token_count)

        return initial_prompt + messages_prompt

    def generate_response(self, msg:str) -> str:
        self.update_latest_chat_user(str(msg).strip())
        prompt = self.generate_prompt()

        if IS_DEBUG_MODE:
            print("------------------------------------------")
            print("prompt: ", prompt)
            print("------------------------------------------")

        response = co.generate(  
            model='xlarge',  
            prompt = prompt,  
            max_tokens=100,  
            temperature=0.6,  
            stop_sequences=["{}:".format(self.user_name)])

        resp_msg = response.generations[0].text

        if IS_DEBUG_MODE:
            print("------------------------------------------")
            print("resp_msg: ", resp_msg)
            print("------------------------------------------")

        self.update_latest_chat_loved_ones(resp_msg)
        return self.latest_chat[-1].loved_ones_text

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