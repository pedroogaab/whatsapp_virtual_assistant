from flask import Flask, request, jsonify
import redis
import json

from ollama import chat
from ollama import ChatResponse

# Run Redis server locally
pool = redis.ConnectionPool(host="localhost", port=6379, db=0)
r = redis.Redis(connection_pool=pool, decode_responses=True) # Decode responses to strings

app = Flask(__name__)


@app.route("/send-message", methods=["POST"])
def send_message():
    data = request.get_json()
    user_message = data.get("message")
    to = data.get("to")

    # Use 10 last msgs for get the context of conversation
    last_10_message = r.lrange(to, -10, -1)
    history = []
    for msg in last_10_message:
        msg_data = json.loads(msg)
        history.append({"role": "user", "content": msg_data["user"]})
        history.append({"role": "assistant", "content": msg_data["ai"]})

    # Group the new msg with the history
    history.append({"role": "user", "content": user_message})

    response: ChatResponse = chat(
        model="llama3.2",
        messages=history,
        stream=False,
    )

    ai_response = response["message"]["content"]

    r.rpush(to, json.dumps({"user": user_message, "ai": ai_response}))

    return jsonify({"to": to, "response": ai_response})

# Get the last 10 messages of a conversation
@app.route("/history", methods=["GET"])
def get_messages():
    to = request.args.get("to")
    messages = r.lrange(to, -10, -1)
    messages = [json.loads(msg) for msg in messages]
    return jsonify({"to": to, "messages": messages})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True) # debug=True for development (auto-reload), use debug=False in production 
