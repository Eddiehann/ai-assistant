import os
import json
import base64
from pathlib import Path
from flask import Flask, render_template, request

# Add Azure packages
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

# Create flask application object
app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])

def send_message():

    if request.method == 'GET':
        return render_template('index.html')
        
    user_input = request.form.get('message')

    # handle POST request
    if ("http://" in user_input) or ("https://" in user_input):
        response = chatbot(user_input)
        store_messages(user_input)
        store_messages(response)
        return render_template('index.html', items = message_list, message=response, image=user_input)


    elif  ("\\" in user_input) or ("/" in user_input):
        base64_image = encode_image(user_input)
        local_url = f"data:image/jpeg;base64,{base64_image}"
        response = chatbot(local_url)
        store_messages(user_input)
        store_messages(response)
        return render_template('index.html', items = message_list, message=response, image=user_input)

    else:
        response = chatbot(user_input)
        store_messages(user_input)
        store_messages(response)
        return render_template('index.html', items = message_list, message=response, image = None)


message_list = []

def store_messages(msg):
    message_list.append(msg)

# Encode the image if given local file path
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
    
# Image analyzer
def chatbot(msg):
    try:
        # Load credentials file
        with open('credentials.json') as path:
            creds = json.load(path)

        # Read credentials
        api_base = creds['endpoint']
        api_key = creds['api_key']
        deployment_name = creds['deployment']
        api_version = "2024-02-01"

        # Run client
        client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            base_url=f"{api_base}/openai/deployments/{deployment_name}"
        )
        
        if "https://" in msg or "http://" in msg:
            # Create response
            response = client.chat.completions.create(
                model=deployment_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": [
                        {
                            "type": "text",
                            "text": "Describe this picture in 50 words:"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": msg
                            }
                        }
                    ]}
                ],
                max_tokens=2000
            )
        else:
            response = client.chat.completions.create(
                model="deployment_name",
                messages = [
                    {"role": "system", "content": "You are a chatbox that replies to the customer's questions."},
                    {"role": "user", "content": f"Kindly reply to the customer. Here is the message: {msg}"}
                ]
            )

        # Output message
        response = response.choices[0].message.content
        return response

    # Catch and output exception
    except Exception as ex:
        print(ex)


if __name__ == '__main__':
    app.run()