from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
)

import os


app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("CHANNEL_SECRET"))

import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


def generate_image(prompt,number = 1,size="512x512"):
    image_resp = openai.Image.create(prompt=prompt, n = number,size=size)
    images_url = []
    for i in range(number):
        images_url.append(image_resp["data"][i].url)
    return images_url


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    images_url = generate_image(prompt = event.message.text)
    image_messages = []
    for i in range(len(images_url)):
        image_messages.append(ImageSendMessage(
            original_content = images_url[i],
            preview_content = images_url[i]
        ))
    line_bot_api.reply_message(event.reply_token,image_messages)
    return 0


if __name__ == "__main__":
    app.run()