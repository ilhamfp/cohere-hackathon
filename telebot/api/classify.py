import cohere
from cohere.classify import Example 
import os
from typing import Tuple

IS_DEBUG_MODE = False
API_KEY = os.getenv("COHERE_API_KEY")
co = cohere.Client(API_KEY)

def classify_text_toxicity(msg: str) -> Tuple[str, float]:
    resp = co.classify( 
    model='large', 
    inputs=[msg], 
    examples=[
        Example("yo how are you", "benign"), 
        Example("PUDGE MID!", "benign"), 
        Example("I would buy this again", "benign"), 
        Example("I think I saw it first", "benign"), 
        Example("bring me a potion", "benign"), 
        Example("The order is 5 days late", "benign"), 
        Example("I will honestly kill you", "toxic"), 
        Example("get rekt moron", "toxic"), 
        Example("go to hell", "toxic"), 
        Example("you are hot trash", "toxic")]
    ) 
    print(resp)
    return resp[0].prediction, resp[0].confidence

if __name__ == "__main__":
    # Run this file to test the API in CLI!
    while 1:
        msg = input("Text to classify: ")
        pred, conf = classify_text_toxicity(msg)
        print("Response: {} ({})".format(pred, conf))
