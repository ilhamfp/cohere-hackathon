import cohere
from cohere.classify import Example 
import os
from typing import Tuple

IS_DEBUG_MODE = True
API_KEY = os.getenv("COHERE_API_KEY")
co = cohere.Client(API_KEY)

def classify_text_toxicity(msg: str) -> Tuple[str, float]:
    resp = co.classify(
    model='0a833c24-9927-48ce-8910-014c37e86344-ft',
    inputs=[msg])

    if IS_DEBUG_MODE:
        print("----------classify_text_toxicity--------")
        print("msg: ", msg)
        print("classify_text_toxicity response: ", resp)
        print("----------------------------------------")
    return resp[0].prediction, resp[0].confidence

if __name__ == "__main__":
    # Run this file to test the API in CLI!
    while 1:
        msg = input("Text to classify: ")
        pred, conf = classify_text_toxicity(msg)
        print("Response: {} ({})".format(pred, conf))

