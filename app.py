from flask import Flask, request, jsonify
import requests

from ollama import chat
from ollama import ChatResponse

app = Flask(__name__)

@app.route('/send-message', methods=['POST'])
def send_message():
    data = request.get_json()
    user_message = data.get('message')
    to = data.get('to')

    response: ChatResponse = chat(
        model='llama3.2',
        messages=[{'role': 'user', 'content': user_message}],
        stream=False,
    )

    # For real time, strem = True
    # ai_response = ""
    # for chunk in stream:
    #     ai_response += chunk['message']['content']
    
    ai_response = response['message']['content']
        
    return jsonify({"to": to, "response": ai_response})