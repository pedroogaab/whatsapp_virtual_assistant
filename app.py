from flask import Flask, request, jsonify
import redis
import json

from ollama import chat
from ollama import ChatResponse


# Run Redis server locally
pool = redis.ConnectionPool(host="localhost", port=6379, db=0)
r = redis.Redis(
    connection_pool=pool, decode_responses=True  # Decode responses to strings
)

app = Flask(__name__)


@app.route("/send-message", methods=["POST"])
def send_message():
    data = request.get_json()
    user_message = data.get("message")
    to = data.get("to")

    # Use 2 last msgs for get the context of conversation
    last_2_message = r.lrange(to, -2, -1)
    history = []

    for msg in last_2_message:
        msg_data = json.loads(msg)
        history.append({"role": "user", "content": msg_data["user"]})
        history.append({"role": "assistant", "content": msg_data["ai"]})

    # Group the new user msg with the history
    history.append({"role": "user", "content": user_message})
    # Define a personality for the AI agent
    system = """Você é um assistente financeiro virtual que responde de forma clara e objetiva, com respostas curtas concisas e diretas. O idioma falado deve ser o português brasileiro."""
    # Combine the personality with the conversation history and the new user message
    prompt = [
        {"role": "system", "content": system},
        *history,
    ]  # *history unpacks the list
    response: ChatResponse = chat(
        model="llama3.2",
        messages=prompt,
        stream=False,
    )

    ai_response = response["message"]["content"]
    r.rpush(to, json.dumps({"user": user_message, "ai": ai_response}))

    return jsonify(
        {"AI Agent": ai_response}
    )  # jsonify convert the response to JSON format


# Get the last 10 messages of a conversation
# Usage http://127.0.0.1:5000/history?to=5515996620252
@app.route("/history", methods=["GET"])
def get_messages():
    to = request.args.get("to")
    messages = r.lrange(to, -10, -1)
    messages = [json.loads(msg) for msg in messages]
    return jsonify({"messages": messages})


if __name__ == "__main__":
    app.run(
        host="0.0.0.0", port=5000, debug=True
    )  # debug=True for development (auto-reload), use debug=False in production
