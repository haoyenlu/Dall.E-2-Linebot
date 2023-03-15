from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError , LineBotApiError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, FollowEvent , ConfirmTemplate, MessageAction ,
    TemplateSendMessage, ButtonsTemplate
)

import os


app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("CHANNEL_SECRET"))

import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

users_info = dict()

@app.route("/",methods=['GET'])
def root():
    return 'OK'


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
    except LineBotApiError as e:
        print("Got exception from LINE Messaging API: %s\n" % e.message)
        for m in e.error.details:
            print(" %s: %s" % (m.property,m.message))
        print("\n")

    return 'OK'


def generate_image(prompt,number = 1,size="512x512"):
    image_resp = openai.Image.create(prompt=prompt, n = number,size=size)
    images_url = []
    for i in range(number):
        images_url.append(image_resp["data"][i].url)
    return images_url


Welcome_Message = "Hi!\nYou can type in any message and I will generate images for you\n"    

@handler.add(FollowEvent)
def handle_follow(event):
    app.logger.info("Got follow event:" + event.source.user_id)
    users_info[event.source.user_id]["number"] = 1

    line_bot_api.reply_message(
        event.reply_token, TextSendMessage(text=Welcome_Message)
    )

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    if not users_info.has_key(event.source.user_id):
        users_info[event.source.user_id]["number"] = 1
    
    if event.message.text == "指令" or event.message.text == "command":
        command_template = ButtonsTemplate(title="Specify images number",text="How may images do you want?",actions=[
            MessageAction(label="1",text="1"),
            MessageAction(label="2",text="2"),
            MessageAction(label="3",text="3"),
            MessageAction(label="4",text="4")
        ])
        line_bot_api.reply_message(event.reply_token,TemplateSendMessage(
            alt_text="Command actions",template=command_template
        ))

    elif event.message.text.isnumeric() and int(event.message.text) <= 4 and int(event.message.text) >= 1:
        users_info[event.source.user_id]["number"] = int(event.message.text)
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text=f"OK! I will send you {event.message.text} images."))


    else:
        images_url = generate_image(prompt = event.message.text,number=users_info[event.source.user_id]["number"])
        image_messages = []
        for i in range(len(images_url)):
            image_messages.append(ImageSendMessage(
                original_content_url = images_url[i],
                preview_image_url = images_url[i]
            ))
        line_bot_api.reply_message(event.reply_token,image_messages)
    return 'OK'


if __name__ == "__main__":
    app.run()